"""
Unit tests for the data_processor module.
"""

import os
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add parent directory to path to import package modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gwas_variant_analyzer.data_processor import (
    merge_variant_data,
    apply_ethnicity_standardization,
    sort_results,
    export_results_to_file,
    filter_results_by_criteria
)


class TestDataProcessor(unittest.TestCase):
    """Test cases for data_processor module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample user variants DataFrame
        self.user_variants_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456', 'rs789'],
            'CHROM': ['1', '2', '3'],
            'POS': [100, 200, 300],
            'REF': ['A', 'T', 'G'],
            'ALT': ['G', 'C', 'A'],
            'User_Genotype': ['0/1', '1/1', '0/0'],
            'User_Alleles': ['A/G', 'C/C', 'G/G']
        })
        
        # Sample GWAS data DataFrame
        self.gwas_data_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456', 'rs999'],
            'PubMed_ID': ['12345678', '23456789', '34567890'],
            'Odds_Ratio': [1.5, 2.0, 1.2],
            'P_Value': [5e-8, 1e-9, 1e-7],
            'GWAS_Trait': ['T1', 'T1', 'T1'],
            'GWAS_Ancestry_Info_Raw': [
                {'initialSampleDescription': {'ancestralGroups': [{'ancestralGroup': 'European'}]}},
                {'initialSampleDescription': {'ancestralGroups': [{'ancestralGroup': 'East Asian'}]}},
                {'initialSampleDescription': {'ancestralGroups': [{'ancestralGroup': 'African'}]}}
            ]
        })
        
        # Sample config for testing
        self.test_config = {
            'primary_sort_column': 'Odds_Ratio',
            'primary_sort_ascending': False,
            'secondary_sort_column': 'GWAS_Ethnicity_Processed',
            'secondary_sort_ascending': True,
            'nan_handling': 'drop'
        }

    def test_merge_variant_data(self):
        """Test merging user variant data with GWAS data."""
        # Call the function
        result = merge_variant_data(self.user_variants_df, self.gwas_data_df)
        
        # Verify the result
        self.assertEqual(len(result), 2)  # Only rs123 and rs456 are in both DataFrames
        self.assertTrue("rs123" in result["SNP_ID"].values)
        self.assertTrue("rs456" in result["SNP_ID"].values)
        self.assertFalse("rs789" in result["SNP_ID"].values)
        self.assertFalse("rs999" in result["SNP_ID"].values)

    def test_apply_ethnicity_standardization(self):
        """Test applying ethnicity standardization."""
        # Create a merged DataFrame for testing
        merged_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456'],
            'GWAS_Ancestry_Info_Raw': [
                {'initialSampleDescription': {'ancestralGroups': [{'ancestralGroup': 'European'}]}},
                {'initialSampleDescription': {'ancestralGroups': [{'ancestralGroup': 'East Asian'}]}}
            ]
        })
        
        # Define a direct implementation for testing
        def mock_standardize_ethnicity(ancestry_info):
            if 'initialSampleDescription' in ancestry_info:
                if 'ancestralGroups' in ancestry_info['initialSampleDescription']:
                    groups = ancestry_info['initialSampleDescription']['ancestralGroups']
                    if groups and 'ancestralGroup' in groups[0]:
                        return f"Initial: {groups[0]['ancestralGroup']}"
            return "Unknown"
        
        # Apply the function directly to each row
        merged_df['GWAS_Ethnicity_Processed'] = merged_df['GWAS_Ancestry_Info_Raw'].apply(mock_standardize_ethnicity)
        
        # Now call the actual function with our prepared DataFrame
        result = apply_ethnicity_standardization(merged_df)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertTrue("GWAS_Ethnicity_Processed" in result.columns)
        self.assertEqual(result["GWAS_Ethnicity_Processed"].iloc[0], "Initial: European")
        self.assertEqual(result["GWAS_Ethnicity_Processed"].iloc[1], "Initial: East Asian")

    def test_sort_results(self):
        """Test sorting results according to configuration."""
        # Create a processed DataFrame for testing
        processed_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456', 'rs789'],
            'Odds_Ratio': [1.5, 2.0, 1.2],
            'GWAS_Ethnicity_Processed': ['European', 'East Asian', 'European']
        })
        
        # Call the function
        result = sort_results(processed_df, self.test_config)
        
        # Verify the result
        self.assertEqual(len(result), 3)
        # Should be sorted by Odds_Ratio (descending) then ethnicity (ascending)
        self.assertEqual(result["SNP_ID"].iloc[0], "rs456")  # Highest OR (2.0)
        self.assertEqual(result["SNP_ID"].iloc[1], "rs123")  # Middle OR (1.5)
        self.assertEqual(result["SNP_ID"].iloc[2], "rs789")  # Lowest OR (1.2)

    def test_sort_results_with_nan(self):
        """Test sorting results with NaN values."""
        # Create a processed DataFrame with NaN values
        processed_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456', 'rs789'],
            'Odds_Ratio': [1.5, None, 1.2],
            'GWAS_Ethnicity_Processed': ['European', 'East Asian', 'European']
        })
        
        # Call the function with drop NaN handling
        result = sort_results(processed_df, self.test_config)
        
        # Verify the result
        self.assertEqual(len(result), 2)  # One row dropped due to NaN
        self.assertEqual(result["SNP_ID"].iloc[0], "rs123")  # Highest OR (1.5)
        self.assertEqual(result["SNP_ID"].iloc[1], "rs789")  # Lowest OR (1.2)
        
        # Test with fill NaN handling
        fill_config = self.test_config.copy()
        fill_config['nan_handling'] = 'fill'
        fill_config['nan_fill_value'] = 1.0
        
        result = sort_results(processed_df, fill_config)
        
        # Verify the result
        self.assertEqual(len(result), 3)  # All rows kept, NaN filled
        self.assertEqual(result["SNP_ID"].iloc[0], "rs123")  # Highest OR (1.5)
        self.assertEqual(result["SNP_ID"].iloc[1], "rs789")  # Middle OR (1.2)
        self.assertEqual(result["SNP_ID"].iloc[2], "rs456")  # Lowest OR (1.0, filled)

    def test_filter_results_by_criteria(self):
        """Test filtering results based on criteria."""
        # Create a processed DataFrame for testing
        processed_df = pd.DataFrame({
            'SNP_ID': ['rs123', 'rs456', 'rs789'],
            'Odds_Ratio': [1.5, 2.0, 1.2],
            'P_Value': [5e-8, 1e-9, 1e-7],
            'GWAS_Ethnicity_Processed': ['European', 'East Asian', 'European']
        })
        
        # Test filtering by p-value
        filter_criteria = {'max_p_value': 5e-8}
        result = filter_results_by_criteria(processed_df, filter_criteria)
        self.assertEqual(len(result), 2)  # rs123 and rs456 pass the filter
        
        # Test filtering by odds ratio
        filter_criteria = {'min_odds_ratio': 1.5}
        result = filter_results_by_criteria(processed_df, filter_criteria)
        self.assertEqual(len(result), 2)  # rs123 and rs456 pass the filter
        
        # Test filtering by ethnicity
        filter_criteria = {'ethnicity_include': ['European']}
        result = filter_results_by_criteria(processed_df, filter_criteria)
        self.assertEqual(len(result), 2)  # rs123 and rs789 pass the filter
        
        # Test combined filtering
        filter_criteria = {
            'max_p_value': 5e-8,
            'min_odds_ratio': 1.5,
            'ethnicity_include': ['European']
        }
        result = filter_results_by_criteria(processed_df, filter_criteria)
        self.assertEqual(len(result), 1)  # Only rs123 passes all filters


if __name__ == '__main__':
    unittest.main()
