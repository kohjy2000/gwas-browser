"""
Setup script for the GWAS Variant Analyzer package.
"""

from setuptools import setup, find_packages

setup(
    name="gwas_variant_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "cyvcf2>=0.30.0",
        "requests>=2.25.0",
        "pyyaml>=5.1.0",
    ],
    entry_points={
        "console_scripts": [
            "gwas-analyzer=gwas_variant_analyzer.cli:main",
        ],
    },
    author="GWAS Variant Analyzer Team",
    author_email="example@example.com",
    description="A package for analyzing SNPs from user VCF files in relation to GWAS Catalog data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/gwas_variant_analyzer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.6",
)
