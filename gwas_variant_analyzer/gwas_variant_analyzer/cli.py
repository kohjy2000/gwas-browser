"""
Command Line Interface Module

This module provides the command-line interface for the GWAS Variant Analyzer package.
It handles argument parsing, workflow orchestration, and execution of the analysis pipeline.
"""

import os
import sys
import argparse
import logging
import pandas as pd
from typing import List, Set, Optional

from . import __version__
from .vcf_parser import load_vcf_reader, extract_user_variants
from .gwas_catalog_handler import fetch_gwas_associations_by_efo, parse_gwas_association_data
from .data_processor import (
    merge_variant_data, 
    apply_ethnicity_standardization, 
    sort_results, 
    export_results_to_file,
    filter_results_by_criteria
)
from .utils import load_app_config, setup_logging, get_efo_id_for_trait, create_default_config

logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the GWAS Variant Analyzer.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="GWAS Variant Analyzer: Analyze SNPs from VCF files in relation to GWAS Catalog data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--vcf_file', required=True, help='Path to input VCF file (can be gzipped)')
    
    # Trait specification (either traits or efo_ids must be provided)
    trait_group = parser.add_argument_group('Trait Specification')
    trait_spec = trait_group.add_mutually_exclusive_group(required=True)
    trait_spec.add_argument('--traits', nargs='+', help='Disease/trait names to analyze (space-separated)')
    trait_spec.add_argument('--efo_ids', nargs='+', help='EFO IDs to analyze (space-separated)')
    
    # Output options
    parser.add_argument('--output_file', required=True, help='Path for output results file')
    parser.add_argument('--format', choices=['tsv', 'csv', 'excel'], default='tsv',
                        help='Output file format')
    
    # Configuration options
    parser.add_argument('--config_file', help='Path to configuration file')
    parser.add_argument('--create_default_config', action='store_true',
                        help='Create a default configuration file if none exists')
    parser.add_argument('--mapping_file', help='Path to trait-to-EFO ID mapping file')
    
    # Filtering options
    filter_group = parser.add_argument_group('Filtering Options')
    filter_group.add_argument('--max_p_value', type=float, help='Maximum p-value threshold')
    filter_group.add_argument('--min_odds_ratio', type=float, help='Minimum odds ratio threshold')
    filter_group.add_argument('--ethnicity', nargs='+', help='Filter by ethnicity (space-separated)')
    
    # Logging options
    parser.add_argument('--log_level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                        help='Logging level')
    parser.add_argument('--log_file', help='Path to log file')
    
    # Version information
    parser.add_argument('--version', action='version', version=f'GWAS Variant Analyzer v{__version__}')
    
    return parser.parse_args()


def main() -> None:
    """
    Main execution function for the GWAS Variant Analyzer.
    
    This function orchestrates the entire analysis workflow:
    1. Parse command-line arguments
    2. Load configuration
    3. Set up logging
    4. Fetch GWAS associations for specified traits/EFO IDs
    5. Extract user variants from VCF file
    6. Merge user variants with GWAS data
    7. Process and sort the results
    8. Export the results to a file
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging first with basic configuration
    setup_logging(args.log_level, args.log_file)
    logger.info(f"Starting GWAS Variant Analyzer v{__version__}")
    
    try:
        # Load configuration
        config = {}
        if args.config_file:
            if os.path.exists(args.config_file):
                config = load_app_config(args.config_file)
            elif args.create_default_config:
                logger.info(f"Configuration file not found, creating default: {args.config_file}")
                config = create_default_config(args.config_file)
            else:
                logger.warning(f"Configuration file not found: {args.config_file}")
                logger.info("Using default configuration values")
        
        # Override config with command-line arguments
        filter_criteria = config.get('default_filter_criteria', {}).copy()
        if args.max_p_value is not None:
            filter_criteria['max_p_value'] = args.max_p_value
        if args.min_odds_ratio is not None:
            filter_criteria['min_odds_ratio'] = args.min_odds_ratio
        if args.ethnicity:
            filter_criteria['ethnicity_include'] = args.ethnicity
        
        # Validate input VCF file
        if not os.path.exists(args.vcf_file):
            logger.error(f"Input VCF file not found: {args.vcf_file}")
            sys.exit(1)
        
        # Process traits/EFO IDs
        efo_ids = []
        if args.efo_ids:
            efo_ids = args.efo_ids
            logger.info(f"Using provided EFO IDs: {', '.join(efo_ids)}")
        elif args.traits:
            if args.mapping_file:
                for trait in args.traits:
                    efo_id = get_efo_id_for_trait(trait, args.mapping_file)
                    if efo_id:
                        efo_ids.append(efo_id)
                    else:
                        logger.warning(f"No EFO ID found for trait: {trait}")
            else:
                logger.error("Trait names provided but no mapping file specified")
                logger.error("Please provide --mapping_file or use --efo_ids directly")
                sys.exit(1)
        
        if not efo_ids:
            logger.error("No valid EFO IDs found for analysis")
            sys.exit(1)
        
        # Fetch GWAS associations for all specified EFO IDs
        all_gwas_data = []
        for efo_id in efo_ids:
            trait_name = args.traits[efo_ids.index(efo_id)] if args.traits else efo_id
            try:
                raw_associations = fetch_gwas_associations_by_efo(efo_id, config)
                gwas_data = parse_gwas_association_data(raw_associations, trait_name)
                all_gwas_data.append(gwas_data)
                logger.info(f"Fetched {len(gwas_data)} GWAS associations for {trait_name} ({efo_id})")
            except Exception as e:
                logger.error(f"Error fetching GWAS data for {efo_id}: {str(e)}")
        
        if not all_gwas_data:
            logger.error("No GWAS data retrieved for any specified traits/EFO IDs")
            sys.exit(1)
        
        # Combine all GWAS data into a single DataFrame
        combined_gwas_data = pd.concat(all_gwas_data, ignore_index=True)
        logger.info(f"Combined GWAS data contains {len(combined_gwas_data)} associations")
        
        # Extract unique SNP IDs from GWAS data for filtering VCF
        target_rsids_set = set(combined_gwas_data['SNP_ID'].unique())
        logger.info(f"Extracted {len(target_rsids_set)} unique SNP IDs from GWAS data")
        
        # Load VCF file and extract user variants
        vcf_reader = load_vcf_reader(args.vcf_file)
        user_variants = extract_user_variants(vcf_reader, target_rsids_set)
        logger.info(f"Extracted {len(user_variants)} matching variants from user VCF")
        
        if user_variants.empty:
            logger.warning("No matching variants found in user VCF")
            sys.exit(0)
        
        # Merge user variants with GWAS data
        merged_data = merge_variant_data(user_variants, combined_gwas_data)
        logger.info(f"Merged data contains {len(merged_data)} variants")
        
        if merged_data.empty:
            logger.warning("No variants remain after merging user data with GWAS data")
            sys.exit(0)
        
        # Apply ethnicity standardization
        processed_data = apply_ethnicity_standardization(merged_data)
        
        # Apply additional filtering if specified
        if filter_criteria:
            processed_data = filter_results_by_criteria(processed_data, filter_criteria)
            logger.info(f"After filtering, {len(processed_data)} variants remain")
        
        # Sort results
        sorted_data = sort_results(processed_data, config)
        
        # Export results
        export_results_to_file(sorted_data, args.output_file, args.format)
        logger.info(f"Analysis complete. Results exported to: {args.output_file}")
        
    except Exception as e:
        logger.error(f"An error occurred during analysis: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()