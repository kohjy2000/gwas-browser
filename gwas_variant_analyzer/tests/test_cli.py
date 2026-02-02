"""
Unit tests for the cli module.
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path to import package modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gwas_variant_analyzer.cli import parse_arguments, main


class TestCli(unittest.TestCase):
    """Test cases for cli module functions."""

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments(self, mock_parse_args):
        """Test argument parsing."""
        # Set up mock to return predefined args
        mock_args = MagicMock()
        mock_args.vcf_file = 'test.vcf'
        mock_args.traits = ['coronary heart disease']
        mock_args.efo_ids = None
        mock_args.output_file = 'output.tsv'
        mock_args.format = 'tsv'
        mock_args.config_file = None
        mock_args.log_level = 'INFO'
        mock_parse_args.return_value = mock_args
        
        # Call the function
        result = parse_arguments()
        
        # Verify the result
        self.assertEqual(result, mock_args)
        self.assertEqual(result.vcf_file, 'test.vcf')
        self.assertEqual(result.traits, ['coronary heart disease'])

    @patch('gwas_variant_analyzer.cli.parse_arguments')
    @patch('gwas_variant_analyzer.cli.setup_logging')
    @patch('gwas_variant_analyzer.cli.load_app_config')
    @patch('gwas_variant_analyzer.cli.get_efo_id_for_trait')
    @patch('gwas_variant_analyzer.cli.load_vcf_reader')
    @patch('gwas_variant_analyzer.cli.extract_user_variants')
    @patch('gwas_variant_analyzer.cli.fetch_gwas_associations_by_efo')
    @patch('gwas_variant_analyzer.cli.parse_gwas_association_data')
    @patch('gwas_variant_analyzer.cli.merge_variant_data')
    @patch('gwas_variant_analyzer.cli.apply_ethnicity_standardization')
    @patch('gwas_variant_analyzer.cli.filter_results_by_criteria')
    @patch('gwas_variant_analyzer.cli.sort_results')
    @patch('gwas_variant_analyzer.cli.export_results_to_file')
    @patch('gwas_variant_analyzer.cli.sys.exit')
    def test_main_success(self, mock_exit, mock_export, mock_sort, mock_filter, mock_ethnicity, 
                         mock_merge, mock_parse_gwas, mock_fetch, mock_extract, 
                         mock_load_vcf, mock_get_efo, mock_load_config, 
                         mock_setup_logging, mock_parse_args):
        """Test successful execution of the main function."""
        # Set up mock args
        mock_args = MagicMock()
        mock_args.vcf_file = 'test.vcf'
        mock_args.traits = ['coronary heart disease']
        mock_args.efo_ids = None
        mock_args.output_file = 'output.tsv'
        mock_args.format = 'tsv'
        mock_args.config_file = 'config.yaml'
        mock_args.mapping_file = 'mapping.json'
        mock_args.log_level = 'INFO'
        mock_args.log_file = None
        mock_args.max_p_value = 0.05  # Add filter criteria to ensure filter function is called
        mock_args.min_odds_ratio = 1.2
        mock_args.ethnicity = ['European']
        mock_args.create_default_config = False
        mock_parse_args.return_value = mock_args
        
        # Set up other mocks
        mock_config = {'default_filter_criteria': {'max_p_value': 0.05}}
        mock_load_config.return_value = mock_config
        mock_get_efo.return_value = 'EFO_0000378'
        
        # Set up mock for extract_user_variants to return a non-empty DataFrame
        import pandas as pd
        mock_user_variants = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456'],
            'CHROM': ['1', '2'],
            'POS': [100, 200]
        })
        mock_extract.return_value = mock_user_variants
        
        # Set up mock for parse_gwas_association_data to return a non-empty DataFrame
        mock_gwas_data = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456'],
            'PubMed_ID': ['12345678', '23456789']
        })
        mock_parse_gwas.return_value = mock_gwas_data
        
        # Set up mock for merge_variant_data to return a non-empty DataFrame
        mock_merged_data = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456'],
            'CHROM': ['1', '2'],
            'PubMed_ID': ['12345678', '23456789']
        })
        mock_merge.return_value = mock_merged_data
        
        # Reset mock_exit to ensure clean state
        mock_exit.reset_mock()
        
        # Mock file existence check
        with patch('os.path.exists', return_value=True):
            # Call the function
            main()
        
        # Verify the function calls
        mock_parse_args.assert_called_once()
        mock_setup_logging.assert_called_once()
        mock_load_config.assert_called_once()
        mock_get_efo.assert_called_once()
        mock_load_vcf.assert_called_once()
        mock_extract.assert_called_once()
        mock_fetch.assert_called_once()
        mock_parse_gwas.assert_called_once()
        mock_merge.assert_called_once()
        mock_ethnicity.assert_called_once()
        mock_filter.assert_called_once()
        mock_sort.assert_called_once()
        mock_export.assert_called_once()

    @patch('gwas_variant_analyzer.cli.parse_arguments')
    @patch('gwas_variant_analyzer.cli.setup_logging')
    @patch('gwas_variant_analyzer.cli.sys.exit')
    def test_main_vcf_not_found(self, mock_exit, mock_setup_logging, mock_parse_args):
        """Test main function when VCF file is not found."""
        # Set up mock args
        mock_args = MagicMock()
        mock_args.vcf_file = 'nonexistent.vcf'
        mock_args.traits = ['coronary heart disease']
        mock_args.efo_ids = None
        mock_args.mapping_file = 'mapping.json'
        mock_args.log_level = 'INFO'
        mock_args.log_file = None
        mock_args.config_file = None
        mock_args.create_default_config = False
        mock_parse_args.return_value = mock_args
        
        # Reset mock_exit to ensure clean state
        mock_exit.reset_mock()
        
        # Mock file existence check
        with patch('os.path.exists', return_value=False):
            # Call the function
            main()
        
        # Verify that sys.exit was called with the expected argument
        mock_exit.assert_called_with(1)

    @patch('gwas_variant_analyzer.cli.parse_arguments')
    @patch('gwas_variant_analyzer.cli.setup_logging')
    @patch('gwas_variant_analyzer.cli.sys.exit')
    def test_main_no_mapping_file(self, mock_exit, mock_setup_logging, mock_parse_args):
        """Test main function when traits are provided but no mapping file."""
        # Set up mock args
        mock_args = MagicMock()
        mock_args.vcf_file = 'test.vcf'
        mock_args.traits = ['coronary heart disease']
        mock_args.efo_ids = None
        mock_args.mapping_file = None
        mock_args.log_level = 'INFO'
        mock_args.log_file = None
        mock_parse_args.return_value = mock_args
        
        # Mock file existence check
        with patch('os.path.exists', return_value=True):
            # Call the function
            main()
        
        # Verify that sys.exit was called
        mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
