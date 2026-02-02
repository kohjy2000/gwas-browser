"""
Unit tests for the utils module.
"""

import os
import unittest
import tempfile
import yaml
import json
import logging
from unittest.mock import patch, MagicMock

# Add parent directory to path to import package modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gwas_variant_analyzer.utils import (
    load_app_config,
    setup_logging,
    get_efo_id_for_trait,
    create_default_config
)


class TestUtils(unittest.TestCase):
    """Test cases for utils module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary files for testing
        self.temp_yaml_config = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w')
        self.temp_json_config = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w')
        self.temp_mapping_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w')
        
        # Sample config data
        self.config_data = {
            'gwas_catalog_api_base_url': 'https://test.api.url',
            'gwas_api_page_size': 50,
            'primary_sort_column': 'Odds_Ratio'
        }
        
        # Write to YAML config file
        yaml.dump(self.config_data, self.temp_yaml_config)
        self.temp_yaml_config.close()
        
        # Write to JSON config file
        json.dump(self.config_data, self.temp_json_config)
        self.temp_json_config.close()
        
        # Sample mapping data
        self.mapping_data = {
            'coronary heart disease': 'EFO_0000378',
            'type 2 diabetes': 'EFO_0001360',
            'breast cancer': 'EFO_0000305'
        }
        
        # Write to mapping file
        json.dump(self.mapping_data, self.temp_mapping_file)
        self.temp_mapping_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.temp_yaml_config.name)
        os.unlink(self.temp_json_config.name)
        os.unlink(self.temp_mapping_file.name)

    def test_load_app_config_yaml(self):
        """Test loading configuration from YAML file."""
        # Call the function
        result = load_app_config(self.temp_yaml_config.name)
        
        # Verify the result
        self.assertEqual(result, self.config_data)

    def test_load_app_config_json(self):
        """Test loading configuration from JSON file."""
        # Call the function
        result = load_app_config(self.temp_json_config.name)
        
        # Verify the result
        self.assertEqual(result, self.config_data)

    def test_load_app_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        # Call the function and check for exception
        with self.assertRaises(FileNotFoundError):
            load_app_config("nonexistent_file.yaml")

    def test_load_app_config_invalid_format(self):
        """Test loading configuration from file with unsupported format."""
        # Create a temporary file with unsupported extension
        temp_invalid = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w')
        temp_invalid.write("This is not a valid config file")
        temp_invalid.close()
        
        try:
            # Call the function and check for exception
            with self.assertRaises(ValueError):
                load_app_config(temp_invalid.name)
        finally:
            os.unlink(temp_invalid.name)

    @patch('gwas_variant_analyzer.utils.logging')
    def test_setup_logging(self, mock_logging):
        """Test setting up logging configuration."""
        # Set up mocks
        mock_root_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_root_logger
        mock_console_handler = MagicMock()
        mock_file_handler = MagicMock()
        mock_logging.StreamHandler.return_value = mock_console_handler
        mock_logging.FileHandler.return_value = mock_file_handler
        
        # Call the function with console logging only
        setup_logging('DEBUG')
        
        # Verify the result
        mock_logging.getLogger.assert_called()
        mock_root_logger.setLevel.assert_called()
        mock_logging.StreamHandler.assert_called_once()
        mock_console_handler.setFormatter.assert_called_once()
        mock_root_logger.addHandler.assert_called_with(mock_console_handler)
        
        # Call the function with file logging
        setup_logging('INFO', 'test.log')
        
        # Verify the result
        mock_logging.FileHandler.assert_called_once_with('test.log')
        mock_file_handler.setFormatter.assert_called_once()
        mock_root_logger.addHandler.assert_called_with(mock_file_handler)

    def test_get_efo_id_for_trait(self):
        """Test looking up EFO ID for trait names."""
        # Test with exact match
        result = get_efo_id_for_trait('coronary heart disease', self.temp_mapping_file.name)
        self.assertEqual(result, 'EFO_0000378')
        
        # Test with case-insensitive match
        result = get_efo_id_for_trait('Coronary Heart Disease', self.temp_mapping_file.name)
        self.assertEqual(result, 'EFO_0000378')
        
        # Test with non-existent trait
        result = get_efo_id_for_trait('nonexistent disease', self.temp_mapping_file.name)
        self.assertIsNone(result)
        
        # Test with non-existent mapping file
        result = get_efo_id_for_trait('coronary heart disease', 'nonexistent_file.json')
        self.assertIsNone(result)

    def test_create_default_config(self):
        """Test creating default configuration file."""
        # Create a temporary file path for the output
        temp_output = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False).name
        os.unlink(temp_output)  # Delete it so the function can create it
        
        try:
            # Call the function
            result = create_default_config(temp_output)
            
            # Verify the result
            self.assertTrue(os.path.exists(temp_output))
            self.assertIsInstance(result, dict)
            self.assertIn('gwas_catalog_api_base_url', result)
            self.assertIn('primary_sort_column', result)
            self.assertIn('log_level', result)
            
            # Load the created file and verify its contents
            loaded_config = load_app_config(temp_output)
            self.assertEqual(loaded_config, result)
        finally:
            # Clean up
            if os.path.exists(temp_output):
                os.unlink(temp_output)


if __name__ == '__main__':
    unittest.main()
