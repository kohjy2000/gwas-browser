# ruff: noqa
"""
Compatibility shim.

Inner implementation lives at:
  gwas_variant_analyzer/gwas_variant_analyzer/pgx_foregenomics.py

This re-exports it so imports like `gwas_variant_analyzer.pgx_foregenomics`
work reliably when running from the repo root.
"""

from gwas_variant_analyzer.gwas_variant_analyzer.pgx_foregenomics import *  # type: ignore

