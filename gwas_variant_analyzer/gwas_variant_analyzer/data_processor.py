"""
Variant Data Processor Module

This module is responsible for processing and merging variant data from different sources.
It merges user's VCF data with GWAS Catalog data based on genomic coordinates and alleles,
applies ethnicity standardization, and filters the results based on user-defined criteria.
"""
import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

def merge_variant_data(user_variants_df: pd.DataFrame, gwas_data_df: pd.DataFrame) -> pd.DataFrame:
    """
    ENHANCED RELAXED MERGE - 최대한 많은 variants 매칭
    """
    logger.info(f"Starting RELAXED merge: {len(user_variants_df)} user × {len(gwas_data_df)} GWAS variants")
    
    if user_variants_df.empty or gwas_data_df.empty:
        logger.warning("Empty dataframe")
        return pd.DataFrame()

    # Chromosome naming 통일 (chr 제거)
    user_variants_df = user_variants_df.copy()
    user_variants_df['USER_CHROM'] = user_variants_df['USER_CHROM'].str.replace('chr', '', regex=False)
    
    # Position numeric 변환
    user_variants_df['USER_POS'] = pd.to_numeric(user_variants_df['USER_POS'], errors='coerce')
    gwas_data_df['GWAS_POS'] = pd.to_numeric(gwas_data_df['GWAS_POS'], errors='coerce')
    
    user_variants_df = user_variants_df.dropna(subset=['USER_POS'])
    gwas_data_df = gwas_data_df.dropna(subset=['GWAS_POS'])
    
    # GWAS SNP_ID 컬럼명 변경
    if 'SNP_ID' in gwas_data_df.columns:
        gwas_data_df = gwas_data_df.rename(columns={'SNP_ID': 'GWAS_SNP_ID'})
    
    all_matches = []
    matched_positions = set()
    
    # ============================================
    # STRATEGY 1: Exact position + alt match
    # ============================================
    logger.info("  Trying Strategy 1: Exact position + alt allele...")
    exact_merge = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_ALT'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner'
    )
    
    if not exact_merge.empty:
        exact_merge['MATCH_TYPE'] = 'exact'
        exact_merge['MATCH_CONFIDENCE'] = 'high'
        all_matches.append(exact_merge)
        matched_positions.update(zip(exact_merge['USER_CHROM'], exact_merge['USER_POS']))
        logger.info(f"    ✓ Found {len(exact_merge)} exact matches")
    
    # ============================================
    # STRATEGY 2: Position + REF match (alt가 다른 경우)
    # ============================================
    logger.info("  Trying Strategy 2: Position + ref allele...")
    ref_match = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_REF'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner'
    )
    
    if not ref_match.empty:
        # 이미 매칭된 것 제외
        ref_match = ref_match[
            ~ref_match.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        if not ref_match.empty:
            ref_match['MATCH_TYPE'] = 'ref_match'
            ref_match['MATCH_CONFIDENCE'] = 'medium'
            all_matches.append(ref_match)
            matched_positions.update(zip(ref_match['USER_CHROM'], ref_match['USER_POS']))
            logger.info(f"    ✓ Found {len(ref_match)} ref matches")
    
    # ============================================
    # STRATEGY 3: Position-only match
    # ============================================
    logger.info("  Trying Strategy 3: Position only...")
    position_only = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS'],
        right_on=['GWAS_CHROM', 'GWAS_POS'],
        how='inner'
    )
    
    if not position_only.empty:
        # 이미 매칭된 것 제외
        position_only = position_only[
            ~position_only.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        
        if not position_only.empty:
            # GWAS_ALT가 'N'이 아니고 user alleles 중 하나와 일치하는지 체크
            def check_allele_compatibility(row):
                if row['GWAS_ALT'] == 'N':
                    return True  # N은 unknown이므로 허용
                user_alleles = {row['USER_REF'], row['USER_ALT']}
                return row['GWAS_ALT'] in user_alleles
            
            position_only = position_only[position_only.apply(check_allele_compatibility, axis=1)]
            
            if not position_only.empty:
                position_only['MATCH_TYPE'] = 'position_only'
                position_only['MATCH_CONFIDENCE'] = 'low'
                all_matches.append(position_only)
                matched_positions.update(zip(position_only['USER_CHROM'], position_only['USER_POS']))
                logger.info(f"    ✓ Found {len(position_only)} position-only matches")
    
    # ============================================
    # STRATEGY 4: Complement alleles (A↔T, C↔G)
    # ============================================
    logger.info("  Trying Strategy 4: Complement alleles...")
    complement_map = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    
    # Complement 계산
    user_variants_df['USER_ALT_COMP'] = user_variants_df['USER_ALT'].map(complement_map).fillna(user_variants_df['USER_ALT'])
    user_variants_df['USER_REF_COMP'] = user_variants_df['USER_REF'].map(complement_map).fillna(user_variants_df['USER_REF'])
    
    # Alt complement match
    comp_merge = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_ALT_COMP'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner'
    )
    
    if not comp_merge.empty:
        comp_merge = comp_merge[
            ~comp_merge.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        if not comp_merge.empty:
            comp_merge['MATCH_TYPE'] = 'complement'
            comp_merge['MATCH_CONFIDENCE'] = 'medium'
            all_matches.append(comp_merge)
            matched_positions.update(zip(comp_merge['USER_CHROM'], comp_merge['USER_POS']))
            logger.info(f"    ✓ Found {len(comp_merge)} complement matches")
    
    # Clean up
    user_variants_df = user_variants_df.drop(['USER_ALT_COMP', 'USER_REF_COMP'], axis=1, errors='ignore')
    
    # ============================================
    # STRATEGY 5: Nearby positions (±1bp, indel 고려)
    # ============================================
    logger.info("  Trying Strategy 5: Nearby positions (±1bp)...")
    
    # Position을 1bp 앞뒤로 확장
    gwas_expanded = []
    for offset in [-1, 0, 1]:
        gwas_temp = gwas_data_df.copy()
        gwas_temp['GWAS_POS_ORIGINAL'] = gwas_temp['GWAS_POS']
        gwas_temp['GWAS_POS'] = gwas_temp['GWAS_POS'] + offset
        gwas_temp['OFFSET'] = offset
        gwas_expanded.append(gwas_temp)
    
    gwas_expanded_df = pd.concat(gwas_expanded)
    
    nearby_merge = pd.merge(
        user_variants_df,
        gwas_expanded_df[gwas_expanded_df['OFFSET'] != 0],  # 0은 이미 처리함
        left_on=['USER_CHROM', 'USER_POS'],
        right_on=['GWAS_CHROM', 'GWAS_POS'],
        how='inner'
    )
    
    if not nearby_merge.empty:
        nearby_merge = nearby_merge[
            ~nearby_merge.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        if not nearby_merge.empty:
            nearby_merge['MATCH_TYPE'] = 'nearby'
            nearby_merge['MATCH_CONFIDENCE'] = 'very_low'
            # Original position 복원
            nearby_merge['GWAS_POS'] = nearby_merge['GWAS_POS_ORIGINAL']
            all_matches.append(nearby_merge)
            logger.info(f"    ✓ Found {len(nearby_merge)} nearby matches")
    
    # ============================================
    # Combine all matches
    # ============================================
    if not all_matches:
        logger.warning("No matches found with ANY strategy!")
        return pd.DataFrame()
    
    merged_df = pd.concat(all_matches, ignore_index=True)
    
    # SNP_ID 처리
    if 'GWAS_SNP_ID' in merged_df.columns:
        merged_df['SNP_ID'] = merged_df['GWAS_SNP_ID']
    elif 'SNP_ID_x' in merged_df.columns and 'SNP_ID_y' in merged_df.columns:
        merged_df['SNP_ID'] = merged_df['SNP_ID_y'].fillna(merged_df['SNP_ID_x'])
        merged_df = merged_df.drop(['SNP_ID_x', 'SNP_ID_y'], axis=1, errors='ignore')
    
    # 중복 제거 (confidence 높은 것 우선)
    confidence_order = {'high': 0, 'medium': 1, 'low': 2, 'very_low': 3}
    if 'MATCH_CONFIDENCE' in merged_df.columns:
        merged_df['conf_rank'] = merged_df['MATCH_CONFIDENCE'].map(confidence_order).fillna(99)
        merged_df = merged_df.sort_values('conf_rank')
        merged_df = merged_df.drop_duplicates(subset=['USER_CHROM', 'USER_POS'], keep='first')
        merged_df = merged_df.drop('conf_rank', axis=1)
    
    # 불필요한 컬럼 제거
    cols_to_drop = ['OFFSET', 'GWAS_POS_ORIGINAL', 'USER_ALT_COMP', 'USER_REF_COMP']
    merged_df = merged_df.drop(columns=[col for col in cols_to_drop if col in merged_df.columns])
    
    # 통계 출력
    logger.info("="*60)
    logger.info("RELAXED MERGE COMPLETE:")
    logger.info(f"  Total matches: {len(merged_df)} ({len(merged_df)/len(gwas_data_df)*100:.1f}% of GWAS variants)")
    
    if 'MATCH_TYPE' in merged_df.columns:
        logger.info("  By strategy:")
        for match_type, count in merged_df['MATCH_TYPE'].value_counts().items():
            conf = merged_df[merged_df['MATCH_TYPE'] == match_type]['MATCH_CONFIDENCE'].iloc[0] if 'MATCH_CONFIDENCE' in merged_df.columns else 'N/A'
            logger.info(f"    • {match_type:15s} ({conf:10s}): {count:4d} ({count/len(merged_df)*100:5.1f}%)")
    
    logger.info(f"  Improvement: {len(merged_df)}/{len(exact_merge) if not exact_merge.empty else 5} = {len(merged_df)/(len(exact_merge) if not exact_merge.empty else 5)*100:.0f}% vs original")
    logger.info("="*60)
    
    return merged_df

def apply_ethnicity_standardization(merged_data: pd.DataFrame) -> pd.DataFrame:
    """Apply ethnicity standardization if column exists"""
    # 현재는 그냥 pass through
    return merged_data


def sort_results(data: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Sort results by specified criteria"""
    if data.empty:
        return data
    
    sort_col = config.get('primary_sort_column', 'P_Value')
    ascending = config.get('primary_sort_ascending', True)
    
    if sort_col in data.columns:
        return data.sort_values(by=sort_col, ascending=ascending)
    return data


def export_results_to_file(data: pd.DataFrame, output_file: str, format: str = 'tsv'):
    """Export results to file"""
    if format == 'tsv':
        data.to_csv(output_file, sep='\t', index=False)
    elif format == 'csv':
        data.to_csv(output_file, index=False)
    elif format == 'excel':
        data.to_excel(output_file, index=False)
    logger.info(f"Results exported to {output_file}")


def filter_results_by_criteria(data: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """Apply filtering criteria to results - FIXED for quantitative traits"""
    if data.empty:
        return data
    
    filtered = data.copy()
    
    # P-value filter
    if 'max_p_value' in criteria and criteria['max_p_value'] is not None:
        filtered['P_Value'] = pd.to_numeric(filtered['P_Value'], errors='coerce')
        filtered = filtered[filtered['P_Value'] <= criteria['max_p_value']]
    
    # Odds Ratio filter - SKIP for quantitative traits with Beta values
    if 'min_odds_ratio' in criteria and criteria['min_odds_ratio'] is not None:
        # Check if this is likely Beta (quantitative trait) or OR (binary trait)
        if 'Odds_Ratio' in filtered.columns:
            # If most values are < 1, it's likely Beta coefficient, not OR
            median_value = filtered['Odds_Ratio'].median()
            if median_value > 0.5:  # Likely actual OR
                filtered['Odds_Ratio'] = pd.to_numeric(filtered['Odds_Ratio'], errors='coerce')
                filtered = filtered[filtered['Odds_Ratio'] >= criteria['min_odds_ratio']]
            else:
                logger.info("Skipping OR filter - appears to be Beta coefficient for quantitative trait")
    
    return filtered


def standardize_gwas_ethnicity(ancestry_info_raw: Any) -> str:
    """
    Standardizes raw ancestry information into a more readable format.
    (This function may not receive rich data until ancestry parsing is improved)
    """
    if not isinstance(ancestry_info_raw, dict):
        return "Unknown"

    # TODO: Implement proper ancestry standardization when rich ancestry data becomes available
    # Currently ancestry_info is {} (empty dictionary), so most cases will return 'Unknown'
    # This is a future improvement task
    return "Unknown" 


def process_variants(
    user_variants_df: pd.DataFrame,
    gwas_data_df: pd.DataFrame,
    filters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Main processing pipeline for variant data.
    """
    logger.info("Starting main variant processing pipeline...")

    # 1. Merge data
    merged_data = merge_variant_data(user_variants_df, gwas_data_df)
    
    if merged_data.empty:
        logger.warning("No overlapping variants found after merging. Processing will stop.")
        return pd.DataFrame()

    # 2. Standardize ethnicity - this section is activated for future use
    # merged_data['GWAS_Ethnicity_Processed'] = merged_data['GWAS_Ancestry_Info_Raw'].apply(standardize_gwas_ethnicity)

    # 3. Apply user-defined filters
    filtered_data = merged_data.copy()
    
    # P-value filter
    if 'max_p_value' in filters and filters['max_p_value'] is not None:
        p_value_filter = pd.to_numeric(filters['max_p_value'], errors='coerce')
        if pd.notna(p_value_filter):
            logger.info(f"Applying P-value filter: <= {p_value_filter}")
            filtered_data['P_Value'] = pd.to_numeric(filtered_data['P_Value'], errors='coerce')
            filtered_data.dropna(subset=['P_Value'], inplace=True)
            filtered_data = filtered_data[filtered_data['P_Value'] <= p_value_filter]

    # Odds Ratio filter
    if 'min_odds_ratio' in filters and filters['min_odds_ratio'] is not None:
        or_filter = pd.to_numeric(filters['min_odds_ratio'], errors='coerce')
        if pd.notna(or_filter):
            logger.info(f"Applying Odds Ratio filter: >= {or_filter}")
            filtered_data['Odds_Ratio'] = pd.to_numeric(filtered_data['Odds_Ratio'], errors='coerce')
            filtered_data.dropna(subset=['Odds_Ratio'], inplace=True)
            filtered_data = filtered_data[filtered_data['Odds_Ratio'] >= or_filter]

    # Ethnicity filter - this section is activated for future use
    if 'ethnicity' in filters and filters['ethnicity'] and filters['ethnicity'] != 'All':
        logger.info(f"Applying ethnicity filter: {filters['ethnicity']}")
        filtered_data = filtered_data[filtered_data['GWAS_Ethnicity_Processed'].str.contains(filters['ethnicity'], case=False, na=False)]

    logger.info(f"{len(filtered_data)} variants remaining after applying filters.")
    
    if filtered_data.empty:
        return pd.DataFrame()
        
    # 4. Sort results by P-value
    sorted_data = filtered_data.sort_values(by='P_Value', ascending=True)
    
    # 5. Select and rename columns for final display
    output_columns = {
        'SNP_ID': 'SNP ID (rsID)',  # Now this column should exist properly
        'GWAS_Trait': 'Associated Trait',
        'Odds_Ratio': 'Odds Ratio / Beta',
        'P_Value': 'P-Value',
        'GWAS_CHROM': 'Chromosome',
        'GWAS_POS': 'Position',
        'USER_REF': 'REF Allele',
        'GWAS_ALT': 'Risk Allele', 
        'GWAS_Ethnicity_Processed': 'Ancestry',  # Add Ancestry column to results
        'PubMed_ID': 'PubMed ID'  # Add PubMed ID column to results
    }
 
    # Select only columns that exist in the DataFrame
    final_columns = [col for col in output_columns.keys() if col in sorted_data.columns]    
    final_df = sorted_data[final_columns].rename(columns=output_columns)
      
    return final_df


def process_variants_customer_friendly(
    user_variants_df: pd.DataFrame,
    gwas_data_df: pd.DataFrame,
    filters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Customer-friendly variant processing pipeline
    """
    logger.info("Starting customer-friendly variant processing pipeline...")

    # Use existing processing logic
    merged_data = merge_variant_data(user_variants_df, gwas_data_df)
    
    if merged_data.empty:
        logger.warning("No overlapping variants found after merging.")
        # Import customer-friendly processing
        from .customer_friendly_processor import format_customer_friendly_results
        return format_customer_friendly_results(pd.DataFrame())

    # Apply filters
    filtered_data = merged_data.copy()
    
    # P-value filter
    if 'max_p_value' in filters and filters['max_p_value'] is not None:
        p_value_filter = pd.to_numeric(filters['max_p_value'], errors='coerce')
        if pd.notna(p_value_filter):
            logger.info(f"Applying P-value filter: <= {p_value_filter}")
            filtered_data['P_Value'] = pd.to_numeric(filtered_data['P_Value'], errors='coerce')
            filtered_data = filtered_data.dropna(subset=['P_Value'])
            filtered_data = filtered_data[filtered_data['P_Value'] <= p_value_filter]

    # Odds Ratio filter
    if 'min_odds_ratio' in filters and filters['min_odds_ratio'] is not None:
        or_filter = pd.to_numeric(filters['min_odds_ratio'], errors='coerce')
        if pd.notna(or_filter):
            logger.info(f"Applying Odds Ratio filter: >= {or_filter}")
            filtered_data['Odds_Ratio'] = pd.to_numeric(filtered_data['Odds_Ratio'], errors='coerce')
            filtered_data = filtered_data.dropna(subset=['Odds_Ratio'])
            filtered_data = filtered_data[filtered_data['Odds_Ratio'] >= or_filter]

    logger.info(f"{len(filtered_data)} variants remaining after applying filters.")
    
    # Convert to customer-friendly format
    from .customer_friendly_processor import format_customer_friendly_results
    return format_customer_friendly_results(filtered_data)
