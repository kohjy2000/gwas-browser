# 📁 gwas_variant_analyzer/customer_friendly_processor.py
# Replace this file content completely

"""
Customer-Friendly Data Processor Module
Provides user-friendly result formatting and risk analysis in English.
"""
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def categorize_risk_level(odds_ratio: float) -> Dict[str, str]:
    """Categorize risk level based on Odds Ratio into user-friendly English categories."""
    if pd.isna(odds_ratio) or odds_ratio <= 0:
        return {"level": "Unclear", "description": "Risk assessment is not available due to data quality."}
    if odds_ratio >= 3.0:
        return {"level": "High Risk", "description": f"Associated with a {odds_ratio:.1f}x higher risk compared to the average population."}
    elif odds_ratio >= 2.0:
        return {"level": "Medium Risk", "description": f"Associated with a {odds_ratio:.1f}x higher risk compared to the average population."}
    elif odds_ratio >= 1.5:
        return {"level": "Low Risk", "description": f"Associated with a {odds_ratio:.1f}x higher risk compared to the average population."}
    elif odds_ratio >= 1.1:
        return {"level": "Slightly Elevated", "description": f"Associated with a {odds_ratio:.1f}x higher risk compared to the average population."}
    else:
        return {"level": "Protective", "description": f"Associated with a {odds_ratio:.1f}x risk, which may indicate a protective effect."}

def get_confidence_level(p_value: float, pubmed_id: Any, association_id: Any = None) -> Dict[str, Any]:
    """Determine confidence level based on P-value and publication info in English."""
    # Check if pubmed_id is valid (not None, NaN, or empty string)
    has_reference = pubmed_id and pd.notna(pubmed_id) and str(pubmed_id).strip()

    # Convert pubmed_id from float (e.g., 29878757.0) to integer string if needed
    if has_reference:
        try:
            pubmed_str = str(pubmed_id).strip()
            if '.' in pubmed_str:
                pubmed_id = str(int(float(pubmed_str)))
            else:
                pubmed_id = pubmed_str
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert PubMed ID: {pubmed_id}")
            has_reference = False

    if pd.isna(p_value):
        confidence, description = "Unclear", "Statistical significance information is not available."
    elif p_value < 5e-8:
        confidence, description = "Very High", "Result is considered genome-wide significant (p < 5e-8)."
    elif p_value < 1e-5:
        confidence, description = "High", f"Result is statistically significant (p = {p_value:.2e})."
    else:
        confidence, description = "Medium", f"Result shows moderate statistical significance (p = {p_value:.3f})."

    # Build reference URL: PubMed preferred, GWAS Catalog association URL as fallback
    if has_reference:
        reference_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}"
    elif association_id and pd.notna(association_id) and str(association_id).strip():
        reference_url = f"https://www.ebi.ac.uk/gwas/associations/{str(association_id).strip()}"
        has_reference = True
    else:
        reference_url = "https://www.ebi.ac.uk/gwas/"
        has_reference = True

    return {"confidence": confidence, "description": description, "reference": reference_url, "has_reference": bool(has_reference)}

def calculate_overall_risk_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate overall risk summary from all variants in English."""
    if results_df.empty:
        return {"overall_risk": "Inconclusive", "total_variants": 0, "summary": "No variants available for analysis.", "high_risk_count": 0, "medium_risk_count": 0, "low_risk_count": 0}
    
    total_variants = len(results_df)
    risk_counts = results_df['risk_category'].value_counts()
    high_risk_count = risk_counts.get('High Risk', 0)
    medium_risk_count = risk_counts.get('Medium Risk', 0)
    low_risk_count = risk_counts.get('Low Risk', 0)
    
    risk_score = (high_risk_count * 4 + medium_risk_count * 2 + low_risk_count * 1) / total_variants if total_variants > 0 else 0
    overall_risk = "High" if risk_score >= 3.0 else "Medium" if risk_score >= 1.5 else "Low"
    summary = f"Analyzed {total_variants} variants. Found {high_risk_count} high-risk and {medium_risk_count} medium-risk factors."
    
    return {"overall_risk": overall_risk, "summary": summary, "total_variants": total_variants, "high_risk_count": high_risk_count, "medium_risk_count": medium_risk_count, "low_risk_count": low_risk_count}

def format_customer_friendly_results(merged_data: pd.DataFrame) -> Dict[str, Any]:
    """Convert technical analysis results to a customer-friendly format in English."""
    if merged_data.empty:
        return {"success": False, "message": "No matching variants found.", "variants": [], "summary": {}}
    
    logger.info("=== DEBUG: Inside format_customer_friendly_results ===")
    logger.info(f"Input data columns: {list(merged_data.columns)}")
    logger.info(f"Input data shape: {merged_data.shape}")
    
    customer_results = []
    for idx, row in merged_data.iterrows():
        logger.info(f"=== DEBUG: Processing row {idx} ===")
        
        # DEBUG: SNP ID retrieval logic with extensive logging
        snp_id = None
        snp_id_source = "unknown"
        
        # First priority: SNP_ID column (original from GWAS data)
        if 'SNP_ID' in row and pd.notna(row['SNP_ID']) and str(row['SNP_ID']).strip() not in ['', '.', 'nan']:
            snp_id = str(row['SNP_ID']).strip()
            snp_id_source = "SNP_ID"
        # Second priority: GWAS_SNP_ID column (if renamed)
        elif 'GWAS_SNP_ID' in row and pd.notna(row['GWAS_SNP_ID']) and str(row['GWAS_SNP_ID']).strip() not in ['', '.', 'nan']:
            snp_id = str(row['GWAS_SNP_ID']).strip()
            snp_id_source = "GWAS_SNP_ID"
        # Fallback: Create from chromosome and position
        else:
            chrom = row.get('GWAS_CHROM', row.get('USER_CHROM', 'N/A'))
            pos = row.get('GWAS_POS', row.get('USER_POS', 'N/A'))
            snp_id = f"chr{chrom}:{pos}"
            snp_id_source = "position"
        
        logger.info(f"SNP ID: {snp_id} (source: {snp_id_source})")
        
        # DEBUG: PubMed ID retrieval with extensive logging
        pubmed_id = row.get('PubMed_ID')
        logger.info(f"PubMed ID raw: {pubmed_id} (type: {type(pubmed_id)})")
        
        # Log all available columns for this row to help debug
        logger.info(f"Available columns in row: {list(row.index)}")
        for col in ['SNP_ID', 'GWAS_SNP_ID', 'PubMed_ID', 'GWAS_CHROM', 'GWAS_POS', 'GWAS_Trait']:
            if col in row:
                logger.info(f"  {col}: {row[col]} (type: {type(row[col])})")
        
        risk_info = categorize_risk_level(row.get('Odds_Ratio'))
        association_id = row.get('GWAS_Association_ID')
        confidence_info = get_confidence_level(row.get('P_Value'), pubmed_id, association_id)
        
        customer_results.append({
            "snp_id": snp_id,
            "associated_disease": row.get('GWAS_Trait', 'N/A'),
            "risk_level": risk_info["level"],
            "risk_description": risk_info["description"],
            "confidence": confidence_info["confidence"],
            "confidence_description": confidence_info["description"],
            "has_reference": confidence_info["has_reference"],
            "reference": confidence_info["reference"],
            "technical_details": {  # Technical details for advanced users
                "odds_ratio": row.get('Odds_Ratio'),
                "p_value": row.get('P_Value'),
                "pubmed_id": pubmed_id,
                "chromosome": row.get('GWAS_CHROM', row.get('USER_CHROM')),
                "position": row.get('GWAS_POS', row.get('USER_POS')),
                "risk_allele": row.get('GWAS_ALT', row.get('USER_ALT')),
                "snp_id_source": snp_id_source  # Debug info
            }
        })
        
    # Sort by risk level priority
    risk_order = {"High Risk": 1, "Medium Risk": 2, "Low Risk": 3, "Slightly Elevated": 4, "Protective": 5, "Unclear": 6}
    customer_results.sort(key=lambda x: risk_order.get(x["risk_level"], 7))
    
    # Create summary DataFrame for risk calculation
    summary_df = pd.DataFrame(customer_results)
    if not summary_df.empty:
        summary_df['risk_category'] = summary_df['risk_level']
    else:
        summary_df = pd.DataFrame(columns=['risk_category'])
    
    summary = calculate_overall_risk_summary(summary_df)
    
    logger.info("=== DEBUG: Final results ===")
    logger.info(f"Generated {len(customer_results)} customer-friendly results")
    if customer_results:
        logger.info(f"First result SNP ID: {customer_results[0]['snp_id']}")
        logger.info(f"First result reference: {customer_results[0]['reference']}")
    
    return {
        "success": True, 
        "variants": customer_results, 
        "summary": summary, 
        "analysis_info": {
            "analyzed_trait": merged_data.iloc[0].get('GWAS_Trait', 'N/A') if not merged_data.empty else 'N/A'
        }
    }
