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

    Args:
        vcf_file_path (str): Path to the VCF file (can be compressed with .gz)

    Returns:
        cyvcf2.VCF: A cyvcf2 VCF object for the specified file

    Raises:
        FileNotFoundError: If the VCF file does not exist
        ValueError: If the file is not a valid VCF file
    """
    logger.info(f"Loading VCF file: {vcf_file_path}")

    try:
        # cyvcf2 automatically handles both compressed and uncompressed files
        vcf_obj = VCF(vcf_file_path)

        # Validate that it's a proper VCF by checking for samples
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
                          parquet_path: str = None) -> pd.DataFrame:
    """
    Extract all variant position and allele information from VCF file.

    For large WGS files, streams variants in chunks to a parquet file on disk
    to avoid OOM, then returns a lazy-loadable DataFrame wrapper.
    For small files (< CHUNK_SIZE), returns a regular in-memory DataFrame.
    """
    logger.info("Extracting variants from VCF file based on CHROM:POS:REF:ALT.")

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
            if total_alleles >= CHUNK_SIZE and len(chroms) >= CHUNK_SIZE:
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

    # If we used chunked writing, flush remaining and read back
    if writer is not None:
        if chroms:
            _flush_chunk(chroms, positions, refs, alts, snp_ids, writer, parquet_path)
        writer.close()
        logger.info(f"Variants saved to parquet: {parquet_path}")
        df = pd.read_parquet(parquet_path)
    else:
        # Small file — build DataFrame directly in memory
        if not chroms:
            logger.warning("No valid variant alleles were extracted from the VCF file.")
            return pd.DataFrame(columns=_VARIANT_COLUMNS)

        df = pd.DataFrame({
            'USER_CHROM': chroms,
            'USER_POS': positions,
            'USER_REF': refs,
            'USER_ALT': alts,
            'SNP_ID': snp_ids,
        })

    logger.info(f"DataFrame shape: {df.shape}")
    if not df.empty:
        for idx, row in df.head(3).iterrows():
            logger.info(f"Row {idx}: CHROM={row['USER_CHROM']}, POS={row['USER_POS']}, "
                         f"REF={row['USER_REF']}, ALT={row['USER_ALT']}, SNP_ID={row['SNP_ID']}")

    return df


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
