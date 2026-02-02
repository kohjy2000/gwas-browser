"""
Unit tests for the gwas_catalog_handler module.
"""

import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import package modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gwas_variant_analyzer.gwas_catalog_handler import (
    fetch_gwas_associations_by_efo,
    parse_gwas_association_data,
    standardize_gwas_ethnicity
)


class TestGwasCatalogHandler(unittest.TestCase):
    """Test cases for gwas_catalog_handler module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample config for testing
        self.test_config = {
            'gwas_catalog_api_base_url': 'https://www.ebi.ac.uk/gwas/rest/api',
            'gwas_api_page_size': 10,
            'gwas_api_max_retries': 2,
            'gwas_api_retry_delay_seconds': 0.1,
            'gwas_api_request_timeout_seconds': 5
        }
        
        # Sample GWAS association data for testing
        self.sample_association = {
            'publicationInfo': {'pubmedId': '12345678'},
            'pvalue': '5e-8',
            'orPerCopyNum': '1.5',
            'loci': [{
                'strongestRiskAlleles': [
                    {'riskAlleleName': 'rs123-A'},
                    {'riskAlleleName': 'rs456-G'}
                ]
            }],
            'ancestries': {
                'initialSampleDescription': {
                    'ancestralGroups': [
                        {'ancestralGroup': 'European'}
                    ],
                    'ancestryCategory': 'European'
                },
                'replicationSampleDescription': {
                    'ancestralGroups': [
                        {'ancestralGroup': 'East Asian'}
                    ],
                    'ancestryCategory': 'East Asian'
                }
            }
        }

    @patch('gwas_variant_analyzer.gwas_catalog_handler.requests.get')
    def test_fetch_gwas_associations_by_efo(self, mock_get):
        """Test fetching GWAS associations for an EFO ID."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '_embedded': {
                'associations': [self.sample_association]
            },
            '_links': {}  # No next page
        }
        mock_get.return_value = mock_response
        
        # Call the function
        result = fetch_gwas_associations_by_efo('EFO_0000378', self.test_config)
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.sample_association)
        mock_get.assert_called_once()

    @patch('gwas_variant_analyzer.gwas_catalog_handler.requests.get')
    def test_fetch_gwas_associations_pagination(self, mock_get):
        """Test fetching GWAS associations with pagination."""
        # Set up mock responses for two pages
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            '_embedded': {
                'associations': [self.sample_association]
            },
            '_links': {
                'next': {'href': 'next_page_url'}
            }
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            '_embedded': {
                'associations': [self.sample_association]
            },
            '_links': {}  # No next page
        }
        
        # Set up mock to return different responses on successive calls
        mock_get.side_effect = [mock_response1, mock_response2]
        
        # Call the function
        result = fetch_gwas_associations_by_efo('EFO_0000378', self.test_config)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch('gwas_variant_analyzer.gwas_catalog_handler.requests.get')
    def test_fetch_gwas_associations_retry(self, mock_get):
        """Test retry logic when API request fails."""
        # Set up mock to fail once then succeed
        mock_error_response = MagicMock()
        mock_error_response.raise_for_status.side_effect = Exception("API Error")
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            '_embedded': {
                'associations': [self.sample_association]
            },
            '_links': {}
        }
        
        # Update test_config to have shorter retry delay for faster tests
        test_config = self.test_config.copy()
        test_config['gwas_api_retry_delay_seconds'] = 0.01
        
        # Use side_effect with RequestException instead of generic Exception
        from requests.exceptions import RequestException
        mock_get.side_effect = [RequestException("API Error"), mock_success_response]
        
        # Call the function
        result = fetch_gwas_associations_by_efo('EFO_0000378', test_config)
        
        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(mock_get.call_count, 2)

    def test_parse_gwas_association_data(self):
        """Test parsing GWAS association data."""
        # Call the function with sample data
        result = parse_gwas_association_data([self.sample_association], "Coronary Heart Disease")
        
        # Verify the result
        self.assertEqual(len(result), 2)  # Two SNPs in the sample association
        self.assertTrue("rs123" in result["SNP_ID"].values)
        self.assertTrue("rs456" in result["SNP_ID"].values)
        self.assertEqual(result["PubMed_ID"].iloc[0], "12345678")
        self.assertEqual(result["Odds_Ratio"].iloc[0], 1.5)
        self.assertEqual(result["P_Value"].iloc[0], 5e-8)
        self.assertEqual(result["GWAS_Trait"].iloc[0], "Coronary Heart Disease")

    def test_parse_gwas_association_data_empty(self):
        """Test parsing empty GWAS association data."""
        # Call the function with empty data
        result = parse_gwas_association_data([], "Coronary Heart Disease")
        
        # Verify the result
        self.assertTrue(result.empty)
        self.assertEqual(list(result.columns), [
            'SNP_ID', 'PubMed_ID', 'Odds_Ratio', 'P_Value', 
            'GWAS_Trait', 'GWAS_Ancestry_Info_Raw'
        ])

    def test_standardize_gwas_ethnicity(self):
        """Test standardizing GWAS ethnicity information."""
        # Test with complete ancestry info
        result = standardize_gwas_ethnicity(self.sample_association['ancestries'])
        self.assertEqual(result, "Initial: European; Replication: East Asian")
        
        # Test with initial ancestry only
        ancestry_initial_only = {
            'initialSampleDescription': {
                'ancestralGroups': [
                    {'ancestralGroup': 'European'}
                ]
            }
        }
        result = standardize_gwas_ethnicity(ancestry_initial_only)
        self.assertEqual(result, "Initial: European")
        
        # Test with no ancestry info
        result = standardize_gwas_ethnicity({})
        self.assertEqual(result, "Unknown")
        
        # Test with None
        result = standardize_gwas_ethnicity(None)
        self.assertEqual(result, "Unknown")


if __name__ == '__main__':
    unittest.main()
