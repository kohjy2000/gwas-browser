"""
VCF Parser Module

This module handles the parsing of VCF (Variant Call Format) files and extraction of variant information.
It provides functions to load VCF files and extract specific variants based on rsIDs.
Uses cyvcf2 for modern, fast VCF parsing.
"""

import re
import logging
import pandas as pd
from cyvcf2 import VCF  # Modern cyvcf2 library

logger = logging.getLogger(__name__)

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


def extract_user_variants(vcf_reader: VCF, target_rsids_set: set = None) -> pd.DataFrame:
    """
    Extract all variant position and allele information from VCF file regardless of ID field.
    When a variant has multiple alternate alleles, each is processed as a separate row.
    """
    logger.info("Extracting variants from VCF file based on CHROM:POS:REF:ALT.")
    variants_data = []
    total_records = 0
    
    for variant in vcf_reader:
        total_records += 1
        
        # Remove rsID filtering logic and use position information from all records
        chrom = variant.CHROM
        pos = variant.POS
        ref = variant.REF
        alts = variant.ALT  # ALT is a list of alternate allele strings, e.g., ['A', 'T']

        # Skip records missing essential information (chromosome, position, reference base, alternate alleles)
        if not all([chrom, pos, ref, alts]):
            continue

        # A single variant can have multiple alternate alleles (multi-allelic).
        # Create a separate row for each alternate allele.
        for alt_allele in alts:
            # Skip invalid alternate alleles (e.g., '.')
            if alt_allele is None or alt_allele == '.':
                 continue
            
            # Store information extracted from user VCF in dictionary
            # Use 'USER_' prefix for column names to clarify source
            variants_data.append({
                'USER_CHROM': str(chrom),
                'USER_POS': int(pos),
                'USER_REF': str(ref),
                'USER_ALT': str(alt_allele),
                # Add SNP_ID only if it exists, otherwise set to None
                'SNP_ID': variant.ID if variant.ID and variant.ID != '.' else None,
                # Can add other information here if needed (e.g., genotype)
                # 'User_Genotype': ...
            })

    logger.info(f"Processed {total_records} VCF records.")
    logger.info(f"Extracted {len(variants_data)} user variant alleles.")

    if not variants_data:
        logger.warning("No valid variant alleles were extracted from the VCF file.")
        # Specify column names for empty DataFrame for compatibility with next steps
        return pd.DataFrame(columns=['USER_CHROM', 'USER_POS', 'USER_REF', 'USER_ALT', 'SNP_ID'])
    
    # DEBUG: Log sample of extracted variants
    df = pd.DataFrame(variants_data)
    logger.info("=== DEBUG: Sample of extracted user variants ===")
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"DataFrame columns: {list(df.columns)}")
    if not df.empty:
        logger.info("Sample rows:")
        for idx, row in df.head(3).iterrows():
            logger.info(f"Row {idx}: CHROM={row['USER_CHROM']}, POS={row['USER_POS']}, REF={row['USER_REF']}, ALT={row['USER_ALT']}, SNP_ID={row['SNP_ID']}")
    
    return df