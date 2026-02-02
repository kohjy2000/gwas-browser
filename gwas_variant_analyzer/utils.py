# ruff: noqa
"""
Compatibility shim.

This repository contains the actual package code under:
  gwas_variant_analyzer/gwas_variant_analyzer/

When running from the project root, the outer `gwas_variant_analyzer/` directory
is discovered first on sys.path and can shadow the installed package.

This module re-exports the inner implementation so imports like
`from gwas_variant_analyzer.utils import ...` work reliably.
"""

from gwas_variant_analyzer.gwas_variant_analyzer.utils import *  # type: ignore

