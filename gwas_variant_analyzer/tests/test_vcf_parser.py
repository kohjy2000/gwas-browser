"""
Unit tests for the vcf_parser module.
"""

import os
import unittest
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

# Add parent directory to path to import package modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gwas_variant_analyzer.vcf_parser import load_vcf_reader, extract_user_variants


class TestVcfParser(unittest.TestCase):
    """Test cases for vcf_parser module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary VCF file for testing
        self.vcf_content = """##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1
1\t100\trs123\tA\tG\t100\tPASS\t.\tGT\t0/1
2\t200\trs456\tT\tC\t100\tPASS\t.\tGT\t1/1
3\t300\trs789;rs999\tG\tA\t100\tPASS\t.\tGT\t0/0
4\t400\t.\tC\tT\t100\tPASS\t.\tGT\t0/1
"""
        self.temp_vcf = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.temp_vcf.write(self.vcf_content)
        self.temp_vcf.close()

    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.temp_vcf.name)

    @patch('gwas_variant_analyzer.vcf_parser.VCF')
    def test_load_vcf_reader(self, mock_vcf_class):
        """Test loading a VCF file."""
        # Set up mock
        mock_vcf_obj = MagicMock()
        mock_vcf_obj.samples = ['SAMPLE1']
        mock_vcf_class.return_value = mock_vcf_obj

        # Call the function
        result = load_vcf_reader(self.temp_vcf.name)

        # Verify the result
        self.assertEqual(result, mock_vcf_obj)
        mock_vcf_class.assert_called_once_with(self.temp_vcf.name)

    @patch('gwas_variant_analyzer.vcf_parser.VCF')
    def test_load_vcf_reader_file_not_found(self, mock_vcf_class):
        """Test loading a non-existent VCF file."""
        # Set up mock to raise FileNotFoundError
        mock_vcf_class.side_effect = FileNotFoundError("File not found")

        # Call the function and check for exception
        with self.assertRaises(FileNotFoundError):
            load_vcf_reader("nonexistent_file.vcf")

    @patch('gwas_variant_analyzer.vcf_parser.VCF')
    def test_extract_user_variants_all(self, mock_vcf_class):
        """Test extracting all variants from a VCF file."""
        # Set up mock VCF reader and variants
        mock_vcf_obj = MagicMock()
        
        # Create mock variants
        variants = []
        
        # Variant 1: rs123, heterozygous
        variant1 = MagicMock()
        variant1.ID = "rs123"
        variant1.CHROM = "1"
        variant1.POS = 100
        variant1.REF = "A"
        variant1.ALT = ["G"]
        variant1.gt_types = [1]  # HET
        variants.append(variant1)
        
        # Variant 2: rs456, homozygous alt
        variant2 = MagicMock()
        variant2.ID = "rs456"
        variant2.CHROM = "2"
        variant2.POS = 200
        variant2.REF = "T"
        variant2.ALT = ["C"]
        variant2.gt_types = [2]  # HOM_ALT
        variants.append(variant2)
        
        # Variant 3: multiple rsIDs
        variant3 = MagicMock()
        variant3.ID = "rs789;rs999"
        variant3.CHROM = "3"
        variant3.POS = 300
        variant3.REF = "G"
        variant3.ALT = ["A"]
        variant3.gt_types = [0]  # HOM_REF
        variants.append(variant3)
        
        # Variant 4: no rsID
        variant4 = MagicMock()
        variant4.ID = "."
        variant4.CHROM = "4"
        variant4.POS = 400
        variant4.REF = "C"
        variant4.ALT = ["T"]
        variant4.gt_types = [1]  # HET
        variants.append(variant4)
        
        # Set up the mock VCF object to return our variants
        mock_vcf_obj.__iter__.return_value = variants
        
        # Call the function
        result = extract_user_variants(mock_vcf_obj)
        
        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        # Should have 4 rows (rs123, rs456, rs789, rs999)
        # Note: The rs789;rs999 variant creates two entries in the result
        self.assertEqual(len(result), 4)
        # Check that rsIDs are correctly extracted
        self.assertTrue("rs123" in result["SNP_ID"].values)
        self.assertTrue("rs456" in result["SNP_ID"].values)
        self.assertTrue("rs789" in result["SNP_ID"].values)
        # Check that record without rsID is skipped
        self.assertFalse("." in result["SNP_ID"].values)

    @patch('gwas_variant_analyzer.vcf_parser.VCF')
    def test_extract_user_variants_filtered(self, mock_vcf_class):
        """Test extracting variants filtered by target rsIDs."""
        # Set up mock VCF reader and variants
        mock_vcf_obj = MagicMock()
        
        # Create mock variants (same as previous test)
        variants = []
        
        # Variant 1: rs123, heterozygous
        variant1 = MagicMock()
        variant1.ID = "rs123"
        variant1.CHROM = "1"
        variant1.POS = 100
        variant1.REF = "A"
        variant1.ALT = ["G"]
        variant1.gt_types = [1]  # HET
        variants.append(variant1)
        
        # Variant 2: rs456, homozygous alt
        variant2 = MagicMock()
        variant2.ID = "rs456"
        variant2.CHROM = "2"
        variant2.POS = 200
        variant2.REF = "T"
        variant2.ALT = ["C"]
        variant2.gt_types = [2]  # HOM_ALT
        variants.append(variant2)
        
        # Set up the mock VCF object to return our variants
        mock_vcf_obj.__iter__.return_value = variants
        
        # Call the function with target_rsids_set
        target_rsids = {"rs123"}
        result = extract_user_variants(mock_vcf_obj, target_rsids)
        
        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        # Should have 1 row (rs123)
        self.assertEqual(len(result), 1)
        # Check that only rs123 is included
        self.assertTrue("rs123" in result["SNP_ID"].values)
        self.assertFalse("rs456" in result["SNP_ID"].values)


if __name__ == '__main__':
    unittest.main()
