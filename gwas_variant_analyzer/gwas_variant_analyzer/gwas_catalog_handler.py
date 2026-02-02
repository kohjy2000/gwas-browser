"""
GWAS Catalog Handler Module

This module handles interaction with public APIs to fetch and parse GWAS data.
- EBI GWAS Catalog API: Fetches association data (rsID, risk allele, p-value, standardize ethnicity information and etc.) for EFO traits.
- Ensembl REST API: Fetches genomic locations (CHROM, POS) for a batch of rsIDs.

"""

import time
import logging
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import json

logger = logging.getLogger(__name__)

def _fetch_snp_locations_from_ensembl(rsids: List[str], config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Fetches genomic locations for a list of rsIDs using the Ensembl REST API (POST for batch lookup).
    """
    if not rsids:
        return {}

    genome_build = config.get('genome_build', 'GRCh38')
    request_timeout = config.get('ensembl_api_request_timeout_seconds', 120)
    max_retries = config.get('ensembl_api_max_retries', 3)
    retry_delay = config.get('ensembl_api_retry_delay_seconds', 5)  # Increased retry interval to 5 seconds
    
    server = "https://grch37.rest.ensembl.org" if genome_build == "GRCh37" else "https://rest.ensembl.org"
    ext = "/variation/human"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    # Ensembl POST /variation has a limit of 200 IDs per request
    batch_size = 200
    snp_locations = {}
    
    logger.info(f"Fetching locations for {len(rsids)} rsIDs from Ensembl (Build: {genome_build})...")

    for i in range(0, len(rsids), batch_size):
        batch = rsids[i:i + batch_size]
        data = {"ids": batch}
        
        retry_count = 0
        success = False
        while not success and retry_count < max_retries:
            try:
                response = requests.post(server + ext, headers=headers, json=data, timeout=request_timeout)
                response.raise_for_status()
                response_data = response.json()

                for rsid, snp_data in response_data.items():
                    if 'mappings' in snp_data and len(snp_data['mappings']) > 0:
                        mapping = snp_data['mappings'][0]
                        chrom = mapping.get('seq_region_name')
                        pos = mapping.get('start')

                        if chrom and pos is not None:
                            snp_locations[rsid] = {
                                'chrom': str(chrom),
                                'pos': int(pos)
                            }
                success = True  # Exit loop on success

            except requests.exceptions.RequestException as e:
                retry_count += 1
                logger.warning(f"Ensembl API request failed (attempt {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to fetch Ensembl data for a batch after {max_retries} attempts.")
                    # Continue processing even if this batch fails
                else:
                    time.sleep(retry_delay)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from Ensembl API: {e}")
                break  # JSON decode failure is not worth retrying
        
        if len(rsids) > batch_size and i + batch_size < len(rsids):
            time.sleep(1)  # Be polite to the API server

    logger.info(f"Successfully fetched locations for {len(snp_locations)} rsIDs.")
    return snp_locations

# data_processor.py의 merge_variant_data 함수를 이걸로 완전히 교체

def merge_variant_data(user_variants_df: pd.DataFrame, gwas_data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Relaxed merge: 다양한 matching 전략을 사용해 최대한 많은 variants 매칭
    """
    logger.info(f"Merging {len(user_variants_df)} user variants with {len(gwas_data_df)} GWAS variants (RELAXED mode)")
    
    if user_variants_df.empty or gwas_data_df.empty:
        logger.warning("One of the dataframes is empty")
        return pd.DataFrame()

    # chr 접두사 제거하여 chromosome 이름 통일
    user_variants_df['USER_CHROM'] = user_variants_df['USER_CHROM'].str.replace('chr', '', regex=False)
    
    # Position을 numeric으로 변환
    user_variants_df['USER_POS'] = pd.to_numeric(user_variants_df['USER_POS'], errors='coerce')
    gwas_data_df['GWAS_POS'] = pd.to_numeric(gwas_data_df['GWAS_POS'], errors='coerce')
    
    # Invalid positions 제거
    user_variants_df = user_variants_df.dropna(subset=['USER_POS'])
    gwas_data_df = gwas_data_df.dropna(subset=['GWAS_POS'])
    
    # GWAS SNP_ID 컬럼명 충돌 방지
    if 'SNP_ID' in gwas_data_df.columns:
        gwas_data_df = gwas_data_df.rename(columns={'SNP_ID': 'GWAS_SNP_ID'})
    
    all_matches = []
    
    # =========================================================
    # STRATEGY 1: Exact Match (Position + Alt Allele)
    # =========================================================
    exact_merge = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_ALT'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner',
        suffixes=('', '_gwas')
    )
    
    if not exact_merge.empty:
        exact_merge['MATCH_TYPE'] = 'exact'
        exact_merge['MATCH_CONFIDENCE'] = 'high'
        all_matches.append(exact_merge)
        logger.info(f"  ✓ Strategy 1 - Exact match (pos+alt): {len(exact_merge)} variants")
    
    # =========================================================
    # STRATEGY 2: Position Match with REF/ALT Swap
    # REF와 ALT가 뒤바뀐 경우 (reference genome 차이)
    # =========================================================
    ref_alt_swap = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_REF'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner',
        suffixes=('', '_gwas')
    )
    
    if not ref_alt_swap.empty:
        # 이미 exact match된 positions 제외
        if not exact_merge.empty:
            exact_positions = set(zip(exact_merge['USER_CHROM'], exact_merge['USER_POS']))
            ref_alt_swap = ref_alt_swap[
                ~ref_alt_swap.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in exact_positions, axis=1)
            ]
        
        if not ref_alt_swap.empty:
            ref_alt_swap['MATCH_TYPE'] = 'ref_alt_swap'
            ref_alt_swap['MATCH_CONFIDENCE'] = 'medium'
            all_matches.append(ref_alt_swap)
            logger.info(f"  ✓ Strategy 2 - REF/ALT swap: {len(ref_alt_swap)} variants")
    
    # =========================================================
    # STRATEGY 3: Position-Only Match (가장 relaxed)
    # Position만 같고 allele이 다른 경우 - 같은 위치의 다른 variant일 수 있음
    # =========================================================
    position_only = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS'],
        right_on=['GWAS_CHROM', 'GWAS_POS'],
        how='inner',
        suffixes=('', '_gwas')
    )
    
    if not position_only.empty:
        # 이미 매칭된 positions 제외
        matched_positions = set()
        for df in all_matches:
            if not df.empty:
                matched_positions.update(zip(df['USER_CHROM'], df['USER_POS']))
        
        position_only = position_only[
            ~position_only.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        
        # Allele이 최소한 하나는 일치하는지 확인 (quality control)
        def check_allele_overlap(row):
            user_alleles = {row['USER_REF'], row['USER_ALT']}
            gwas_alt = row['GWAS_ALT']
            # GWAS REF가 'N'이면 무시하고 ALT만 체크
            return gwas_alt in user_alleles or gwas_alt == 'N'
        
        position_only = position_only[position_only.apply(check_allele_overlap, axis=1)]
        
        if not position_only.empty:
            position_only['MATCH_TYPE'] = 'position_only'
            position_only['MATCH_CONFIDENCE'] = 'low'
            all_matches.append(position_only)
            logger.info(f"  ✓ Strategy 3 - Position only: {len(position_only)} variants")
    
    # =========================================================
    # STRATEGY 4: Complement Allele Match
    # A↔T, C↔G complement 관계 체크 (strand flip)
    # =========================================================
    def get_complement(allele):
        complement_map = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
        return complement_map.get(allele, allele)
    
    # Complement alleles 추가
    user_variants_df['USER_ALT_COMP'] = user_variants_df['USER_ALT'].apply(get_complement)
    gwas_data_df['GWAS_ALT_COMP'] = gwas_data_df['GWAS_ALT'].apply(get_complement)
    
    complement_merge = pd.merge(
        user_variants_df,
        gwas_data_df,
        left_on=['USER_CHROM', 'USER_POS', 'USER_ALT_COMP'],
        right_on=['GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT'],
        how='inner',
        suffixes=('', '_gwas')
    )
    
    if not complement_merge.empty:
        # 이미 매칭된 positions 제외
        matched_positions = set()
        for df in all_matches:
            if not df.empty:
                matched_positions.update(zip(df['USER_CHROM'], df['USER_POS']))
        
        complement_merge = complement_merge[
            ~complement_merge.apply(lambda x: (x['USER_CHROM'], x['USER_POS']) in matched_positions, axis=1)
        ]
        
        if not complement_merge.empty:
            complement_merge['MATCH_TYPE'] = 'complement'
            complement_merge['MATCH_CONFIDENCE'] = 'medium'
            all_matches.append(complement_merge)
            logger.info(f"  ✓ Strategy 4 - Complement match: {len(complement_merge)} variants")
    
    # Clean up temporary columns
    user_variants_df = user_variants_df.drop('USER_ALT_COMP', axis=1, errors='ignore')
    gwas_data_df = gwas_data_df.drop('GWAS_ALT_COMP', axis=1, errors='ignore')
    
    # =========================================================
    # Combine all matches
    # =========================================================
    if not all_matches:
        logger.warning("No matches found with any strategy")
        return pd.DataFrame()
    
    # 모든 매치 결합
    merged_df = pd.concat(all_matches, ignore_index=True)
    
    # SNP_ID 처리 - GWAS_SNP_ID를 기본으로 사용
    if 'GWAS_SNP_ID' in merged_df.columns:
        merged_df['SNP_ID'] = merged_df['GWAS_SNP_ID']
    elif 'SNP_ID_x' in merged_df.columns and 'SNP_ID_y' in merged_df.columns:
        merged_df['SNP_ID'] = merged_df['SNP_ID_y'].fillna(merged_df['SNP_ID_x'])
        merged_df = merged_df.drop(['SNP_ID_x', 'SNP_ID_y'], axis=1, errors='ignore')
    
    # 중복 제거 (같은 position에서 가장 confidence가 높은 것 유지)
    # Sort by confidence (high > medium > low) and keep first
    confidence_order = {'high': 0, 'medium': 1, 'low': 2}
    merged_df['confidence_rank'] = merged_df['MATCH_CONFIDENCE'].map(confidence_order)
    merged_df = merged_df.sort_values('confidence_rank')
    merged_df = merged_df.drop_duplicates(subset=['USER_CHROM', 'USER_POS'], keep='first')
    merged_df = merged_df.drop('confidence_rank', axis=1)
    
    # 통계 로깅
    logger.info("=" * 60)
    logger.info("RELAXED MERGE SUMMARY:")
    logger.info(f"  Total unique variants matched: {len(merged_df)}")
    
    if 'MATCH_TYPE' in merged_df.columns:
        logger.info("  Match type breakdown:")
        match_stats = merged_df['MATCH_TYPE'].value_counts()
        for match_type, count in match_stats.items():
            pct = count/len(merged_df)*100
            confidence = merged_df[merged_df['MATCH_TYPE'] == match_type]['MATCH_CONFIDENCE'].iloc[0]
            logger.info(f"    • {match_type} ({confidence} confidence): {count} ({pct:.1f}%)")
    
    if 'MATCH_CONFIDENCE' in merged_df.columns:
        logger.info("  Confidence breakdown:")
        conf_stats = merged_df['MATCH_CONFIDENCE'].value_counts()
        for conf, count in conf_stats.items():
            logger.info(f"    • {conf}: {count} ({count/len(merged_df)*100:.1f}%)")
    
    logger.info(f"  Improvement: {len(merged_df)/61*100:.1f}% of original strict matching")
    logger.info("=" * 60)
    
    return merged_df

def fetch_gwas_associations_by_efo(efo_id: str, config: dict) -> List[Dict]:
    """
    Fetch GWAS associations for a given EFO ID from the EBI GWAS Catalog API.
    """
    logger.info(f"Fetching GWAS associations for EFO ID: {efo_id}")
    
    api_base_url = config.get('gwas_catalog_api_base_url', 'https://www.ebi.ac.uk/gwas/rest/api')
    page_size = config.get('gwas_api_page_size', 100)
    max_retries = config.get('gwas_api_max_retries', 3)
    retry_delay = config.get('gwas_api_retry_delay_seconds', 2)
    request_timeout = config.get('gwas_api_request_timeout_seconds', 30)

    # Explicitly define headers for API requests
    headers = {'Accept': 'application/json'}
    
    endpoint = f"{api_base_url}/efoTraits/{efo_id}/associations"
    params = {'size': page_size, 'page': 0}
    
    all_associations = []
    has_next_page = True
    
    with requests.Session() as session:
        # Apply headers to the entire session
        session.headers.update(headers)

        while has_next_page:
            retry_count = 0
            success = False
            while not success and retry_count < max_retries:
                try:
                    # Now use session with configured headers for requests
                    response = session.get(endpoint, params=params, timeout=request_timeout)
                    response.raise_for_status()
                    
                    response_data = response.json()
                    page_associations = response_data.get('_embedded', {}).get('associations', [])
                    all_associations.extend(page_associations)
                    logger.debug(f"Retrieved {len(page_associations)} associations from page {params['page']}")
                    has_next_page = '_links' in response_data and 'next' in response_data['_links']
                    if has_next_page:
                        params['page'] += 1
                    success = True
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    logger.warning(f"GWAS Catalog API request failed (attempt {retry_count}/{max_retries}): {str(e)}")
                    if retry_count < max_retries:
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to fetch GWAS associations after {max_retries} attempts")
                        raise ValueError(f"Failed to fetch GWAS associations for EFO ID {efo_id}: {str(e)}")
            
            if has_next_page:
                time.sleep(config.get('gwas_api_request_delay_seconds', 1))
            
    logger.info(f"Successfully fetched {len(all_associations)} GWAS associations for EFO ID: {efo_id}")
    return all_associations

def _normalize_pubmed_id(raw_pmid) -> str:
    """Normalize a PubMed ID to a clean string integer.

    Examples:
        29878757   -> "29878757"
        29878757.0 -> "29878757"
        "29878757" -> "29878757"
        None / NaN -> ""
    """
    if raw_pmid is None:
        return ""
    s = str(raw_pmid).strip()
    if not s or s.lower() in ("none", "nan", ""):
        return ""
    # Strip trailing .0 from float-like strings (e.g. "29878757.0")
    try:
        return str(int(float(s)))
    except (ValueError, OverflowError):
        return s


def parse_gwas_association_data(raw_associations: List[Dict], trait_name: str, config: dict) -> pd.DataFrame:
    """
    Parses raw GWAS association data by first extracting rsID/risk-allele, then fetching
    genomic locations from Ensembl in a batch, and finally combining the data.
    """
    logger.info(f"Parsing {len(raw_associations)} GWAS associations to extract rsID and risk allele.")
    
    gwas_info_by_rsid_alt = {}
    all_rsids = set()

    for association in raw_associations:
        # Extract common information from each association
        
        pubmed_id = association.get('publicationInfo', {}).get('pubmedId')
        if not pubmed_id:
            study_url = association.get('_links', {}).get('study', {}).get('href')
            request_timeout = config.get('gwas_api_request_timeout_seconds', 30)
            max_retries = config.get('gwas_api_max_retries', 3)
            retry_delay = config.get('gwas_api_retry_delay_seconds', 2)
            rate_limit_per_second = config.get('study_fetch_rate_limit_per_second')

            if study_url:
                for attempt in range(max_retries):
                    try:
                        if rate_limit_per_second and rate_limit_per_second > 0:
                            time.sleep(1 / rate_limit_per_second)

                        response = requests.get(study_url, timeout=request_timeout)
                        response.raise_for_status()
                        study_json = response.json()
                        pubmed_id = study_json.get('publicationInfo', {}).get('pubmedId')
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt + 1 >= max_retries:
                            logger.warning(f"Failed to fetch study JSON for PubMed ID fill: {e}")
                        else:
                            time.sleep(retry_delay)
                    except ValueError as e:
                        logger.warning(f"Failed to parse study JSON for PubMed ID fill: {e}")
                        break
            else:
                logger.debug(f"Study link not found for association: {association.get('associationId', 'N/A')}")

        if not pubmed_id:
            logger.debug(f"PubMed ID not found in association record: {association.get('associationId', 'N/A')}")
            
        p_value = association.get('pvalue')
        odds_ratio = association.get('orPerCopyNum') or association.get('betaNum')
        ancestry_info = association.get('ancestries', {})  # Extract ancestry information
        association_id = association.get('associationId')

        for locus_item in association.get('loci', []):
            for risk_allele_detail in locus_item.get('strongestRiskAlleles', []):
                risk_allele_name = risk_allele_detail.get('riskAlleleName')
                
                current_snp_id, gwas_alt = None, None
                if risk_allele_name and risk_allele_name.startswith('rs') and '-' in risk_allele_name:
                    parts = risk_allele_name.split('-', 1)
                    current_snp_id = parts[0]
                    if len(parts) > 1 and parts[1] and parts[1] != '?':
                        gwas_alt = parts[1]
                
                if current_snp_id:
                    all_rsids.add(current_snp_id)
                    key = (current_snp_id, gwas_alt)
                    if key not in gwas_info_by_rsid_alt:
                         gwas_info_by_rsid_alt[key] = {
                            'PubMed_ID': pubmed_id,
                            'Odds_Ratio': odds_ratio,
                            'P_Value': p_value,
                            'GWAS_Association_ID': association_id,
                            'GWAS_Ancestry_Info_Raw': ancestry_info  # Store extracted ancestry information
                        }
                    else:
                        # C6.B3: prefer non-empty PubMed_ID from later records
                        existing = gwas_info_by_rsid_alt[key]
                        if pubmed_id and not existing.get('PubMed_ID'):
                            existing['PubMed_ID'] = pubmed_id

    if not all_rsids:
        logger.warning(f"No valid rsIDs with risk alleles found for trait: {trait_name}")
        return pd.DataFrame()

    # DEBUG: Log rsIDs found
    logger.info(f"=== DEBUG: Found {len(all_rsids)} unique rsIDs ===")
    logger.info(f"Sample rsIDs: {list(all_rsids)[:5]}")

    snp_locations = _fetch_snp_locations_from_ensembl(list(all_rsids), config)

    final_parsed_data = []
    for (rsid, alt), gwas_info in gwas_info_by_rsid_alt.items():
        location_info = snp_locations.get(rsid)
        if location_info:
            # C6.B3: normalize PubMed_ID to string integer
            raw_pmid = gwas_info['PubMed_ID']
            normalized_pmid = _normalize_pubmed_id(raw_pmid)

            final_parsed_data.append({
                'SNP_ID': rsid,
                'PubMed_ID': normalized_pmid,
                'Odds_Ratio': gwas_info['Odds_Ratio'],
                'P_Value': gwas_info['P_Value'],
                'GWAS_Association_ID': gwas_info.get('GWAS_Association_ID'),
                'GWAS_Trait': trait_name,
                'GWAS_Ancestry_Info_Raw': gwas_info['GWAS_Ancestry_Info_Raw'],  # Include in final data
                'GWAS_CHROM': location_info['chrom'],
                'GWAS_POS': location_info['pos'],
                'GWAS_REF': "N",  # Reference allele not available from GWAS Catalog
                'GWAS_ALT': alt
            })

    if not final_parsed_data:
        logger.warning(f"Could not map any rsIDs to genomic locations for trait: {trait_name}")
        return pd.DataFrame()

    df = pd.DataFrame(final_parsed_data)
    
    # DEBUG: Log DataFrame creation
    logger.info(f"=== DEBUG: Created DataFrame with {len(df)} rows ===")
    logger.info(f"DataFrame columns: {list(df.columns)}")
    if not df.empty:
        logger.info("Sample DataFrame rows:")
        for idx, row in df.head(3).iterrows():
            logger.info(f"Row {idx}:")
            logger.info(f"  SNP_ID: {row['SNP_ID']}")
            logger.info(f"  PubMed_ID: {row['PubMed_ID']}")
            logger.info(f"  GWAS_Trait: {row['GWAS_Trait']}")
            logger.info(f"  Odds_Ratio: {row['Odds_Ratio']}")
            logger.info(f"  P_Value: {row['P_Value']}")
    
    # Remove duplicates based on key columns
    key_columns = ['SNP_ID', 'GWAS_ALT', 'GWAS_Trait', 'PubMed_ID', 'GWAS_Association_ID']
    existing_key_columns = [col for col in key_columns if col in df.columns]
    if not df.empty and existing_key_columns:
        df = df.drop_duplicates(subset=existing_key_columns, keep='first')

    # Process ethnicity data if available
    if not df.empty:
        if 'GWAS_Ancestry_Info_Raw' in df.columns:
            logger.info("Standardizing ethnicity data and removing raw column.")
            df['GWAS_Ethnicity_Processed'] = df['GWAS_Ancestry_Info_Raw'].apply(standardize_gwas_ethnicity)
            df = df.drop(columns=['GWAS_Ancestry_Info_Raw'])    

    logger.info(f"Successfully parsed and mapped {len(df)} SNP records for trait {trait_name}")
    return df

def standardize_gwas_ethnicity(ancestry_info_raw: Any) -> str:
    """
    Standardize raw ancestry information into a sortable string format.
    
    Args:
        ancestry_info_raw (Any): Raw ancestry information from GWAS Catalog
        
    Returns:
        str: Standardized ethnicity string for sorting and display
    """
    if not ancestry_info_raw:
        return "Unknown"
    
    # Initialize result components
    ancestry_components = []
    
    # Process initial study ancestries
    if 'initialSampleDescription' in ancestry_info_raw:
        initial_samples = ancestry_info_raw['initialSampleDescription']
        
        # Extract broad ancestral categories
        initial_broad_categories = set()
        if 'ancestralGroups' in initial_samples:
            for group in initial_samples['ancestralGroups']:
                if 'ancestralGroup' in group:
                    initial_broad_categories.add(group['ancestralGroup'])
        
        # If no specific groups found, try the broad category
        if not initial_broad_categories and 'ancestryCategory' in initial_samples:
            initial_broad_categories.add(initial_samples['ancestryCategory'])
        
        # Add initial ancestry information if available
        if initial_broad_categories:
            ancestry_components.append(f"Initial: {', '.join(sorted(initial_broad_categories))}")
    
    # Process replication study ancestries
    if 'replicationSampleDescription' in ancestry_info_raw:
        replication_samples = ancestry_info_raw['replicationSampleDescription']
        
        # Extract broad ancestral categories
        replication_broad_categories = set()
        if 'ancestralGroups' in replication_samples:
            for group in replication_samples['ancestralGroups']:
                if 'ancestralGroup' in group:
                    replication_broad_categories.add(group['ancestralGroup'])
        
        # If no specific groups found, try the broad category
        if not replication_broad_categories and 'ancestryCategory' in replication_samples:
            replication_broad_categories.add(replication_samples['ancestryCategory'])
        
        # Add replication ancestry information if available
        if replication_broad_categories:
            ancestry_components.append(f"Replication: {', '.join(sorted(replication_broad_categories))}")
    
    # If no components were added, check for other ancestry information
    if not ancestry_components and 'ancestryLinks' in ancestry_info_raw:
        ancestry_links = []
        for link in ancestry_info_raw['ancestryLinks']:
            if 'populationName' in link:
                ancestry_links.append(link['populationName'])
        if ancestry_links:
            ancestry_components.append(f"Population: {', '.join(sorted(ancestry_links))}")
    
    # If still no information found, return Unknown
    if not ancestry_components:
        return "Unknown"
    
    # Join all components with semicolons
    return "; ".join(ancestry_components)

def load_gwas_data_from_cache(efo_id: str, config: dict) -> Optional[pd.DataFrame]:
    """Load GWAS data for the specified EFO ID from local cache.

    Contract (Func_Cache_Load_v1):
    - If gwas_cache_directory is missing or empty, return None.
    - If parquet exists and meta is missing, load parquet (legacy support).
    - If meta exists, enforce expiry using fetched_at and gwas_cache_expiry_days;
      expired returns None.
    - Malformed meta must not crash; treat as expired and return None.
    """
    cache_dir = config.get('gwas_cache_directory')
    if not cache_dir:
        return None

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_abs = os.path.join(project_root, cache_dir)
    cache_file = os.path.join(cache_abs, f"{efo_id}.parquet")
    meta_file = os.path.join(cache_abs, f"{efo_id}.meta.json")

    if not os.path.exists(cache_file):
        return None

    # If meta exists, enforce expiry
    if os.path.exists(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            fetched_at_str = meta.get("fetched_at", "")
            if not fetched_at_str:
                # Malformed: treat as expired
                return None
            from datetime import datetime, timezone
            fetched_at = datetime.fromisoformat(fetched_at_str)
            expiry_days = int(config.get("gwas_cache_expiry_days", 90))
            from datetime import timedelta
            if datetime.now(timezone.utc) - fetched_at > timedelta(days=expiry_days):
                logger.info(f"Cache for {efo_id} expired (fetched_at={fetched_at_str})")
                return None
        except Exception as e:
            # Malformed meta: treat as expired
            logger.warning(f"Malformed meta for {efo_id}, treating as expired: {e}")
            return None

    # Load parquet (legacy path if no meta, or valid meta)
    logger.info(f"Loading GWAS data for {efo_id} from cache: {cache_file}")
    try:
        return pd.read_parquet(cache_file)
    except Exception as e:
        logger.error(f"Failed to read cache file {cache_file}: {e}")
    return None

def save_gwas_data_to_cache(df: pd.DataFrame, efo_id: str, config: dict):
    """Save the given DataFrame to a local cache file corresponding to the EFO ID.

    Contract (Func_Cache_Save_v1):
    - If gwas_cache_directory is missing or empty, perform no writes.
    - Writes a parquet file named by efo_id.
    - Writes a meta JSON file with keys efo_id, trait, fetched_at, association_count.
    - association_count equals number of rows in the saved DataFrame.
    """
    cache_dir = config.get('gwas_cache_directory')
    if not cache_dir:
        return

    try:
        df_to_save = df.copy()

        if 'GWAS_Ancestry_Info_Raw' in df_to_save.columns:
            df_to_save['GWAS_Ethnicity_Processed'] = df_to_save['GWAS_Ancestry_Info_Raw'].apply(standardize_gwas_ethnicity)
            df_to_save = df_to_save.drop(columns=['GWAS_Ancestry_Info_Raw'])

        logger.info("Data cleaned for caching. Now saving...")
    except Exception as e:
        logger.error(f"Error during pre-cache data cleaning: {e}")
        df_to_save = df

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_abs = os.path.join(project_root, cache_dir)
    os.makedirs(cache_abs, exist_ok=True)
    cache_file = os.path.join(cache_abs, f"{efo_id}.parquet")

    try:
        df_to_save.to_parquet(cache_file, index=False)
        logger.info(f"Saved GWAS data for {efo_id} to cache: {cache_file}")
    except Exception as e:
        logger.error(f"Failed to save cache file {cache_file}: {e}")
        return

    # Write meta JSON
    from datetime import datetime, timezone
    trait = ""
    if "GWAS_Trait" in df.columns and not df.empty:
        trait = str(df["GWAS_Trait"].iloc[0])

    meta = {
        "efo_id": efo_id,
        "trait": trait,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "association_count": len(df),
    }
    meta_file = os.path.join(cache_abs, f"{efo_id}.meta.json")
    try:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved meta for {efo_id}: {meta_file}")
    except Exception as e:
        logger.error(f"Failed to write meta file {meta_file}: {e}")
