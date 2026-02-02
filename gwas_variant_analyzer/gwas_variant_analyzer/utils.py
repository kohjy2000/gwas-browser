"""
Utilities Module

This module provides common utility functions used across the package, including
configuration loading, logging setup, and EFO ID mapping for disease/trait names.
"""

import os
import yaml
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def load_app_config(config_file_path: str) -> Dict:
    """
    Load application configuration from a YAML or JSON file.
    
    Args:
        config_file_path (str): Path to the configuration file
        
    Returns:
        Dict: Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If the configuration file does not exist
        ValueError: If the file format is not supported or the file is invalid
    """
    logger.info(f"Loading configuration from: {config_file_path}")
    
    if not os.path.exists(config_file_path):
        error_msg = f"Configuration file not found: {config_file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        # Determine file format from extension
        file_ext = os.path.splitext(config_file_path)[1].lower()
        
        if file_ext in ['.yaml', '.yml']:
            with open(config_file_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
        elif file_ext == '.json':
            with open(config_file_path, 'r') as config_file:
                config = json.load(config_file)
        else:
            error_msg = f"Unsupported configuration file format: {file_ext}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Successfully loaded configuration with {len(config)} settings")
        return config
        
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        error_msg = f"Error parsing configuration file: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def setup_logging(log_level_str: str = 'INFO', log_file: Optional[str] = None) -> None:
    """
    Configure the logging system for the application.
    
    Args:
        log_level_str (str, optional): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR'). Defaults to 'INFO'.
        log_file (str, optional): Path to log file. If None, logs to console only. Defaults to None.
    """
    # Convert string log level to logging constant
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = log_level_map.get(log_level_str.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        try:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to set up file logging: {str(e)}")
    
    logger.info(f"Logging initialized with level: {log_level_str}")


def get_efo_id_for_trait(trait_name: str, mapping_file_path: str) -> Optional[str]:
    """
    Look up the EFO ID for a given trait/disease name from a mapping file.
    
    Args:
        trait_name (str): The trait or disease name to look up
        mapping_file_path (str): Path to the mapping file (JSON or CSV)
        
    Returns:
        Optional[str]: The corresponding EFO ID, or None if not found
    """
    logger.info(f"Looking up EFO ID for trait: {trait_name}")
    
    if not os.path.exists(mapping_file_path):
        logger.error(f"Mapping file not found: {mapping_file_path}")
        return None
    
    try:
        # Determine file format from extension
        file_ext = os.path.splitext(mapping_file_path)[1].lower()
        
        mapping = {}
        
        if file_ext == '.json':
            with open(mapping_file_path, 'r') as mapping_file:
                mapping = json.load(mapping_file)
        elif file_ext == '.csv':
            import csv
            with open(mapping_file_path, 'r') as mapping_file:
                reader = csv.reader(mapping_file)
                # Skip header if present
                header = next(reader, None)
                if header and len(header) >= 2:
                    # Assuming first column is trait name, second is EFO ID
                    for row in reader:
                        if len(row) >= 2:
                            mapping[row[0].lower()] = row[1]
        else:
            logger.error(f"Unsupported mapping file format: {file_ext}")
            return None
        
        # Look up trait name (case-insensitive)
        efo_id = mapping.get(trait_name.lower())
        
        if efo_id:
            logger.info(f"Found EFO ID for '{trait_name}': {efo_id}")
        else:
            logger.warning(f"No EFO ID found for trait: {trait_name}")
        
        return efo_id
        
    except Exception as e:
        logger.error(f"Error reading mapping file: {str(e)}")
        return None


def create_default_config(config_file_path: str) -> Dict:
    """
    Create a default configuration file with sensible defaults.
    
    Args:
        config_file_path (str): Path where the configuration file should be saved
        
    Returns:
        Dict: The default configuration dictionary
    """
    logger.info(f"Creating default configuration file at: {config_file_path}")
    
    # Define default configuration
    default_config = {
        # GWAS Catalog API settings
        'gwas_catalog_api_base_url': 'https://www.ebi.ac.uk/gwas/rest/api',
        'gwas_api_page_size': 100,
        'gwas_api_max_retries': 3,
        'gwas_api_retry_delay_seconds': 2,
        'gwas_api_request_timeout_seconds': 30,
        'gwas_api_request_delay_seconds': 1,
        
        # Sorting settings
        'primary_sort_column': 'Odds_Ratio',
        'primary_sort_ascending': False,
        'secondary_sort_column': 'GWAS_Ethnicity_Processed',
        'secondary_sort_ascending': True,
        'nan_handling': 'drop',
        'nan_fill_value': 1.0,
        
        # Filtering settings
        'default_filter_criteria': {
            'max_p_value': 0.05,
            'min_odds_ratio': 1.0
        },
        
        # Logging settings
        'log_level': 'INFO',
        'log_to_file': False,
        'log_file_path': 'gwas_variant_analyzer.log'
    }
    
    try:
        # Create directory if it doesn't exist
        config_dir = os.path.dirname(config_file_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Determine file format from extension
        file_ext = os.path.splitext(config_file_path)[1].lower()
        
        if file_ext in ['.yaml', '.yml']:
            with open(config_file_path, 'w') as config_file:
                yaml.dump(default_config, config_file, default_flow_style=False)
        elif file_ext == '.json':
            with open(config_file_path, 'w') as config_file:
                json.dump(default_config, config_file, indent=2)
        else:
            logger.warning(f"Unsupported file extension: {file_ext}, defaulting to YAML")
            with open(f"{os.path.splitext(config_file_path)[0]}.yaml", 'w') as config_file:
                yaml.dump(default_config, config_file, default_flow_style=False)
        
        logger.info(f"Default configuration file created successfully")
        
    except Exception as e:
        logger.error(f"Error creating default configuration file: {str(e)}")
    
    return default_config