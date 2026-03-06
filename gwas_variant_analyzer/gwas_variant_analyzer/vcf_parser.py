"""
VCF Parser Module

This module handles the parsing of VCF (Variant Call Format) files and extraction of variant information.
It provides functions to load VCF files and extract specific variants based on rsIDs.
Uses cyvcf2 for modern, fast VCF parsing.
"""

import logging
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from cyvcf2 import VCF  # Modern cyvcf2 library

logger = logging.getLogger(__name__)

# Schema for variant parquet files
_VARIANT_SCHEMA = pa.schema([
    ('USER_CHROM', pa.string()),
    ('USER_POS', pa.int64()),
    ('USER_REF', pa.string()),
    ('USER_ALT', pa.string()),
    ('SNP_ID', pa.string()),
])

_VARIANT_COLUMNS = ['USER_CHROM', 'USER_POS', 'USER_REF', 'USER_ALT', 'SNP_ID']

CHUNK_SIZE = 500_000  # variants per chunk


def load_vcf_reader(vcf_file_path: str) -> VCF:
    """
    Load a VCF file and return a cyvcf2.VCF object.
    """
    logger.info(f"Loading VCF file: {vcf_file_path}")

    try:
        vcf_obj = VCF(vcf_file_path)

        if not vcf_obj.samples:
            raise ValueError("Invalid VCF file format or no samples found")

        logger.info(f"Successfully loaded VCF file with {len(vcf_obj.samples)} samples")
        return vcf_obj

    except FileNotFoundError:
        logger.error(f"VCF file not found: {vcf_file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading VCF file: {str(e)}")
        raise ValueError(f"Failed to parse VCF file: {str(e)}")


def extract_user_variants(vcf_reader: VCF, target_rsids_set: set = None,
                          parquet_path: str = None) -> "VariantStore":
    """
    Extract all variant position and allele information from VCF file.

    Streams variants to a parquet file on disk in chunks to avoid OOM.
    Returns a VariantStore object that reads from parquet lazily.
    """
    logger.info("Extracting variants from VCF file based on CHROM:POS:REF:ALT.")

    if parquet_path is None:
        parquet_path = os.path.join(os.path.dirname(os.devnull), 'variants.parquet')

    chroms, positions, refs, alts, snp_ids = [], [], [], [], []
    total_records = 0
    total_alleles = 0
    writer = None

    try:
        for variant in vcf_reader:
            total_records += 1

            chrom = variant.CHROM
            pos = variant.POS
            ref = variant.REF
            alt_list = variant.ALT

            if not all([chrom, pos, ref, alt_list]):
                continue

            for alt_allele in alt_list:
                if alt_allele is None or alt_allele == '.':
                    continue

                chroms.append(str(chrom))
                positions.append(int(pos))
                refs.append(str(ref))
                alts.append(str(alt_allele))
                snp_ids.append(variant.ID if variant.ID and variant.ID != '.' else None)
                total_alleles += 1

            # Flush chunk to parquet when buffer is full
            if len(chroms) >= CHUNK_SIZE:
                writer = _flush_chunk(chroms, positions, refs, alts, snp_ids,
                                      writer, parquet_path)
                chroms.clear()
                positions.clear()
                refs.clear()
                alts.clear()
                snp_ids.clear()

                if total_records % 1_000_000 == 0:
                    logger.info(f"  ... processed {total_records:,} records, {total_alleles:,} alleles")

    except Exception as e:
        logger.warning(f"VCF parsing stopped at record {total_records}: {e}. Returning partial results.")

    logger.info(f"Processed {total_records:,} VCF records.")
    logger.info(f"Extracted {total_alleles:,} user variant alleles.")

    # Flush remaining
    if chroms:
        writer = _flush_chunk(chroms, positions, refs, alts, snp_ids, writer, parquet_path)

    if writer is not None:
        writer.close()
        logger.info(f"Variants saved to parquet: {parquet_path}")
        return VariantStore(parquet_path, total_alleles)

    # Small file or no variants — no parquet written
    if total_alleles == 0:
        logger.warning("No valid variant alleles were extracted from the VCF file.")
        return VariantStore(None, 0)

    # Edge case: all fit in one chunk but never flushed (< CHUNK_SIZE)
    writer = _flush_chunk(chroms, positions, refs, alts, snp_ids, None, parquet_path)
    writer.close()
    return VariantStore(parquet_path, total_alleles)


def _flush_chunk(chroms, positions, refs, alts, snp_ids, writer, parquet_path):
    """Write a chunk of variants to parquet file."""
    table = pa.table({
        'USER_CHROM': pa.array(chroms, type=pa.string()),
        'USER_POS': pa.array(positions, type=pa.int64()),
        'USER_REF': pa.array(refs, type=pa.string()),
        'USER_ALT': pa.array(alts, type=pa.string()),
        'SNP_ID': pa.array(snp_ids, type=pa.string()),
    })

    if writer is None:
        writer = pq.ParquetWriter(parquet_path, _VARIANT_SCHEMA)

    writer.write_table(table)
    logger.info(f"  Flushed chunk: {len(chroms):,} alleles to {parquet_path}")
    return writer


class VariantStore:
    """
    Lazy variant store backed by a parquet file.

    Provides DataFrame-like interface but reads from disk on demand,
    avoiding loading all WGS variants into memory at once.
    """

    def __init__(self, parquet_path: str | None, count: int):
        self.parquet_path = parquet_path
        self._count = count

    def __len__(self):
        return self._count

    @property
    def empty(self):
        return self._count == 0

    @property
    def columns(self):
        return _VARIANT_COLUMNS

    def head(self, n=5) -> pd.DataFrame:
        if self.empty or self.parquet_path is None:
            return pd.DataFrame(columns=_VARIANT_COLUMNS)
        pf = pq.ParquetFile(self.parquet_path)
        batch = next(pf.iter_batches(batch_size=n))
        return batch.to_pandas()

    def to_dataframe(self) -> pd.DataFrame:
        """Read entire parquet into memory. Use only for small files."""
        if self.empty or self.parquet_path is None:
            return pd.DataFrame(columns=_VARIANT_COLUMNS)
        return pd.read_parquet(self.parquet_path)

    def iter_chunks(self, chunk_size: int = 500_000) -> "Iterator[pd.DataFrame]":
        """Iterate over variants in chunks without loading all into memory."""
        if self.empty or self.parquet_path is None:
            return
        pf = pq.ParquetFile(self.parquet_path)
        for batch in pf.iter_batches(batch_size=chunk_size):
            yield batch.to_pandas()

    def merge_with(self, other_df: pd.DataFrame, merge_fn) -> pd.DataFrame:
        """
        Merge variants with another DataFrame (e.g. GWAS data) chunk by chunk.
        Only keeps matching rows, so result fits in memory.
        """
        if self.empty or other_df.empty:
            return pd.DataFrame()

        results = []
        for chunk_df in self.iter_chunks():
            merged = merge_fn(chunk_df, other_df.copy())
            if not merged.empty:
                results.append(merged)

        if not results:
            return pd.DataFrame()
        return pd.concat(results, ignore_index=True)
