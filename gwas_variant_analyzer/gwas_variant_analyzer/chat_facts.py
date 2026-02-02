from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Fact:
    """A single fact with a stable citation ID."""
    id: str
    domain: str  # "gwas", "clinvar", or "pgx"
    category: str
    text: str
    source: dict = field(default_factory=dict)


def _make_gwas_facts(gwas_associations: list[dict]) -> list[Fact]:
    """Create facts from GWAS association data."""
    facts: list[Fact] = []
    for i, assoc in enumerate(sorted(gwas_associations, key=lambda a: (
        str(a.get("trait", "")),
        str(a.get("variant", "")),
        str(a.get("p_value", "")),
    ))):
        trait = str(assoc.get("trait", "unknown"))
        variant = str(assoc.get("variant", "unknown"))
        p_value = str(assoc.get("p_value", "unknown"))
        pubmed = str(assoc.get("pubmed_id", ""))

        fact_id = f"gwas-{i:04d}-{trait[:20].replace(' ', '_').lower()}"
        text = f"GWAS association: variant {variant} is associated with {trait} (p={p_value})"
        if pubmed:
            text += f" [PubMed:{pubmed}]"

        facts.append(Fact(
            id=fact_id,
            domain="gwas",
            category="association",
            text=text,
            source={"trait": trait, "variant": variant, "p_value": p_value, "pubmed_id": pubmed},
        ))
    return facts


def _make_clinvar_facts(clinvar_matches: list[dict]) -> list[Fact]:
    """Create facts from ClinVar match results."""
    facts: list[Fact] = []
    for i, match in enumerate(sorted(clinvar_matches, key=lambda m: (
        str(m.get("user_chrom", "")),
        int(m.get("user_pos", 0)),
        str(m.get("user_ref", "")),
        str(m.get("user_alt", "")),
    ))):
        gene = str(match.get("gene", "unknown"))
        sig = str(match.get("clinical_significance", "unknown"))
        condition = str(match.get("condition", "unknown"))
        chrom = str(match.get("user_chrom", ""))
        pos = str(match.get("user_pos", ""))
        vid = str(match.get("variation_id", ""))

        fact_id = f"clinvar-{i:04d}-{gene[:20].replace(' ', '_').lower()}"
        text = (
            f"ClinVar: variant at chr{chrom}:{pos} in gene {gene} "
            f"is classified as {sig} for condition {condition}"
        )

        facts.append(Fact(
            id=fact_id,
            domain="clinvar",
            category="pathogenicity",
            text=text,
            source={
                "gene": gene,
                "clinical_significance": sig,
                "condition": condition,
                "variation_id": vid,
            },
        ))
    return facts


def _make_pgx_facts(pgx_summary: dict) -> list[Fact]:
    """Create facts from PGx summary data."""
    facts: list[Fact] = []
    by_gene = pgx_summary.get("by_gene", [])
    counter = 0
    for gene_entry in sorted(by_gene, key=lambda g: str(g.get("gene", ""))):
        gene = str(gene_entry.get("gene", "unknown"))
        diplotypes = gene_entry.get("diplotypes", [])
        drugs = gene_entry.get("drugs", [])
        phenotypes = gene_entry.get("phenotypes", [])

        for drug in sorted(drugs):
            fact_id = f"pgx-{counter:04d}-{gene[:10].lower()}-{drug[:10].replace(' ', '_').lower()}"
            dipl_str = ", ".join(sorted(diplotypes)) if diplotypes else "unknown"
            pheno_str = ", ".join(sorted(phenotypes)) if phenotypes else "unknown"
            text = (
                f"PGx: gene {gene} (diplotype: {dipl_str}, phenotype: {pheno_str}) "
                f"has recommendation for drug {drug}"
            )
            facts.append(Fact(
                id=fact_id,
                domain="pgx",
                category="recommendation",
                text=text,
                source={"gene": gene, "drug": drug, "diplotypes": sorted(diplotypes), "phenotypes": sorted(phenotypes)},
            ))
            counter += 1
    return facts


def collect_facts(
    gwas_associations: list[dict] | None = None,
    clinvar_matches: list[dict] | None = None,
    pgx_summary: dict[str, Any] | None = None,
) -> list[Fact]:
    """
    Collect facts from all three domains into a single list with stable citation IDs.

    Args:
        gwas_associations: List of GWAS association dicts with keys:
            trait, variant, p_value, pubmed_id
        clinvar_matches: List of ClinVar match dicts (from clinvar_matcher output)
        pgx_summary: PGx summary dict (from pgx_summary.summarize_pgx output)

    Returns:
        Sorted list of Fact objects with stable, deterministic IDs.
    """
    all_facts: list[Fact] = []

    if gwas_associations:
        all_facts.extend(_make_gwas_facts(gwas_associations))
    if clinvar_matches:
        all_facts.extend(_make_clinvar_facts(clinvar_matches))
    if pgx_summary:
        all_facts.extend(_make_pgx_facts(pgx_summary))

    all_facts.sort(key=lambda f: (f.domain, f.category, f.id))
    return all_facts


def facts_to_dicts(facts: list[Fact]) -> list[dict]:
    """Convert a list of Fact objects to a list of plain dicts."""
    return [
        {
            "id": f.id,
            "domain": f.domain,
            "category": f.category,
            "text": f.text,
            "source": f.source,
        }
        for f in facts
    ]


def get_fact_ids(facts: list[Fact]) -> list[str]:
    """Return sorted list of all fact IDs (for citation validation)."""
    return sorted(f.id for f in facts)
