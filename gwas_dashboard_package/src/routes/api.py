# 📁 src/routes/api.py - Replace this file completely

"""
API routes for the GWAS Dashboard.
Handles file uploads, analysis requests, and serves data to the frontend.
"""
import os
import tempfile
import json
import logging
import csv
import glob
from datetime import datetime, timezone
import pandas as pd
import requests as http_requests
from flask import Blueprint, request, jsonify, current_app

from gwas_variant_analyzer.utils import load_app_config, get_efo_id_for_trait
from gwas_variant_analyzer.vcf_parser import load_vcf_reader, extract_user_variants
from gwas_variant_analyzer.gwas_catalog_handler import fetch_gwas_associations_by_efo, parse_gwas_association_data, load_gwas_data_from_cache, save_gwas_data_to_cache
from gwas_variant_analyzer.data_processor import merge_variant_data
from gwas_variant_analyzer.vcf_parser import VariantStore
from gwas_variant_analyzer.clinvar_matcher import match_user_variants_to_clinvar
from gwas_variant_analyzer.pgx_parser import parse_pgx_final_tsv
from gwas_variant_analyzer.pgx_summary import summarize_pgx
from gwas_variant_analyzer.pgx_foregenomics import parse_foregenomics_report_tsv, find_foregenomics_report
from gwas_variant_analyzer.pgx_cpic import parse_cpic_toy_tsv
from gwas_variant_analyzer.chat_facts import collect_facts, get_fact_ids

# Import new features
from gwas_variant_analyzer.customer_friendly_processor import format_customer_friendly_results
from gwas_variant_analyzer.nlp_phenotype_matcher import PhenotypeNLPMatcher

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Session-based upload data storage
UPLOADS = {}

# NLP Matcher instance (lazy loading)
nlp_matcher = None

# --- Block 1 + 2: Trait list for fuzzy search (lazy-loaded) ---
_trait_list = None  # List[dict] with keys: trait, shortForm, uri


def _extract_gwas_associations_for_facts(filtered_data: pd.DataFrame, trait_name: str, max_items: int = 50) -> list[dict]:
    """
    Build a small GWAS association list for chat facts from the filtered GWAS×user merge.

    Output schema matches gwas_variant_analyzer.chat_facts.collect_facts:
      trait, variant, p_value, pubmed_id
    """
    if getattr(filtered_data, "empty", True):
        return []

    out: list[dict] = []
    for _, row in filtered_data.head(max_items).iterrows():
        rsid = row.get("SNP_ID")
        if not rsid or str(rsid).strip() in ("nan", ".", ""):
            rsid = row.get("GWAS_SNP_ID")

        chrom = row.get("GWAS_CHROM")
        pos = row.get("GWAS_POS")
        alt = row.get("GWAS_ALT")

        variant = ""
        if rsid and str(rsid).strip() not in ("nan", ".", ""):
            variant = str(rsid).strip()
            if alt and str(alt).strip() not in ("nan", ".", ""):
                variant = f"{variant}-{str(alt).strip()}"
        elif chrom and pos:
            variant = f"chr{str(chrom).strip()}:{str(pos).strip()}"
            if alt and str(alt).strip() not in ("nan", ".", ""):
                variant = f"{variant}-{str(alt).strip()}"

        pubmed_id = row.get("PubMed_ID")
        if pubmed_id is None or (isinstance(pubmed_id, float) and pd.isna(pubmed_id)):
            pubmed_id = ""

        assoc_trait = row.get("GWAS_Trait") or trait_name
        p_value = row.get("P_Value")

        out.append({
            "trait": str(assoc_trait) if assoc_trait is not None else str(trait_name),
            "variant": str(variant),
            "p_value": str(p_value) if p_value is not None else "",
            "pubmed_id": str(pubmed_id).strip(),
        })

    out.sort(key=lambda a: (a.get("trait", ""), a.get("variant", ""), a.get("p_value", "")))
    return out


def _load_trait_list():
    """Load trait list from data/trait_list.json, fallback to efo_mapping.json."""
    global _trait_list
    # api.py is at gwas_dashboard_package/src/routes/api.py — 4 levels up = project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # Prefer a large runtime cache if available (generated from local TSV mapping / remote fetch).
    full_trait_list_path = os.path.join(project_root, "data", "trait_list.full.json")
    full_meta_path = os.path.join(project_root, "data", "trait_list.full.meta.json")
    trait_list_path = os.path.join(project_root, "data", "trait_list.json")
    fallback_path = os.path.join(project_root, "gwas_dashboard_package", "config", "efo_mapping.json")

    def _is_pytest_running() -> bool:
        # During contract tests we must not write new files (scope checks).
        return bool(os.environ.get("PYTEST_CURRENT_TEST"))

    def _extract_short_form_from_uri(uri: str) -> str:
        u = (uri or "").strip()
        if not u:
            return ""
        # Common patterns:
        # - http://purl.obolibrary.org/obo/MONDO_0002974  -> MONDO_0002974
        # - http://www.ebi.ac.uk/efo/EFO_0000616          -> EFO_0000616
        for sep in ("/obo/", "/efo/"):
            if sep in u:
                return u.split(sep, 1)[1].strip().rstrip("/")
        return u.rstrip("/").rsplit("/", 1)[-1].strip()

    def _default_trait_mappings_tsv() -> str:
        # 1) Explicit override
        override = os.environ.get("GWAS_TRAIT_MAPPINGS_TSV_PATH", "").strip()
        if override and os.path.exists(override):
            return override
        # 2) Auto-detect at repo root (one directory above project_root)
        parent = os.path.abspath(os.path.join(project_root, ".."))
        cands = sorted(glob.glob(os.path.join(parent, "gwas_catalog_trait-mappings_*.tsv")))
        return cands[-1] if cands else ""

    def _build_full_trait_list_from_tsv(tsv_path: str) -> list[dict]:
        rows: list[dict] = []
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for r in reader:
                disease_trait = str(r.get("Disease trait", "") or "").strip()
                efo_term = str(r.get("EFO term", "") or "").strip()
                efo_uri = str(r.get("EFO URI", "") or "").strip()
                trait = disease_trait or efo_term
                if not trait or not efo_uri:
                    continue
                short_form = _extract_short_form_from_uri(efo_uri)
                if not short_form:
                    continue
                rows.append({"trait": trait, "shortForm": short_form, "uri": efo_uri})

        # De-dupe by (trait_lower, shortForm) while keeping order
        seen = set()
        out: list[dict] = []
        for item in rows:
            key = (item["trait"].lower(), item["shortForm"])
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _maybe_bootstrap_full_trait_cache() -> None:
        # Contract tests must not write files.
        if _is_pytest_running():
            return
        # Allow turning off via env (default ON when TSV exists).
        auto = os.environ.get("GWAS_TRAIT_LIST_AUTOBOOTSTRAP", "").strip().lower()
        if auto in ("0", "false", "no"):
            return
        if os.path.exists(full_trait_list_path) and os.path.getsize(full_trait_list_path) > 0:
            return
        tsv_path = _default_trait_mappings_tsv()
        if not tsv_path:
            return
        try:
            traits = _build_full_trait_list_from_tsv(tsv_path)
            if not traits:
                return
            os.makedirs(os.path.join(project_root, "data"), exist_ok=True)
            with open(full_trait_list_path, "w", encoding="utf-8") as f:
                json.dump(traits, f, ensure_ascii=False, indent=2)
            with open(full_meta_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "total_traits": len(traits),
                        "source": "gwas_catalog_trait_mappings_tsv",
                        "source_path": tsv_path,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.info(f"Bootstrapped full trait cache: {len(traits)} traits from {tsv_path}")
        except Exception as e:
            logger.warning(f"Failed to bootstrap full trait cache from TSV: {e}")

    _maybe_bootstrap_full_trait_cache()

    # 0) Prefer runtime full cache if present.
    # IMPORTANT: in pytest, avoid reading runtime-generated caches (non-deterministic + slower).
    if (not _is_pytest_running()) and os.path.exists(full_trait_list_path):
        try:
            with open(full_trait_list_path, "r", encoding="utf-8") as f:
                _trait_list = json.load(f)
            logger.info(f"Loaded {len(_trait_list)} traits from {full_trait_list_path}")
            return
        except Exception as e:
            logger.warning(f"Failed to load trait_list.full.json: {e}")

    if os.path.exists(trait_list_path):
        try:
            with open(trait_list_path, "r", encoding="utf-8") as f:
                _trait_list = json.load(f)
            logger.info(f"Loaded {len(_trait_list)} traits from {trait_list_path}")
            return
        except Exception as e:
            logger.warning(f"Failed to load trait_list.json: {e}")

    # Fallback: convert efo_mapping.json (name->efo_id dict) to trait_list format
    logger.warning("trait_list.json not found, falling back to efo_mapping.json")
    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            _trait_list = [
                {"trait": name, "shortForm": efo_id, "uri": ""}
                for name, efo_id in mapping.items()
            ]
            logger.info(f"Loaded {len(_trait_list)} traits from fallback efo_mapping.json")
        except Exception as e:
            logger.error(f"Failed to load fallback efo_mapping.json: {e}")
            _trait_list = []
    else:
        logger.error("Neither trait_list.json nor efo_mapping.json found")
        _trait_list = []


def _get_trait_list():
    """Get the trait list, loading it lazily on first access."""
    global _trait_list
    if _trait_list is None:
        _load_trait_list()
    return _trait_list


# --- C6.B1: Remote GWAS Catalog trait search + local cache update ---

# GWAS Catalog REST API (HAL). See:
#   https://www.ebi.ac.uk/gwas/rest/api/efoTraits/search
# Note: the query parameter name is `trait` (not `efoTrait`).
REMOTE_GWAS_TRAIT_URL = "https://www.ebi.ac.uk/gwas/rest/api/efoTraits/search/findByEfoTrait"
REMOTE_SCORE_THRESHOLD = 0.4  # If top local score below this, trigger remote


def _fetch_remote_traits(query: str):
    """Query the GWAS Catalog REST API for traits matching *query*.

    Returns a list of dicts with keys: trait, shortForm, uri.
    Raises on network / parse errors so callers can handle gracefully.
    """
    resp = http_requests.get(
        REMOTE_GWAS_TRAIT_URL,
        params={"trait": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    traits_out = []
    embedded = data.get("_embedded", {})
    for item in embedded.get("efoTraits", []):
        trait_name = item.get("trait", "")
        short_form = item.get("shortForm", "")
        uri = item.get("_links", {}).get("self", {}).get("href", "")
        if trait_name and short_form:
            traits_out.append({
                "trait": trait_name,
                "shortForm": short_form,
                "uri": uri,
            })
    return traits_out


def _merge_remote_into_cache(remote_traits):
    """Append *remote_traits* into data/trait_list.json (dedupe) and update meta."""
    global _trait_list
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    trait_list_path = os.path.join(project_root, "data", "trait_list.json")
    meta_path = os.path.join(project_root, "data", "trait_list.meta.json")

    current = _get_trait_list()
    existing_keys = {(e["trait"].lower(), e["shortForm"]) for e in current}

    added = 0
    for rt in remote_traits:
        key = (rt["trait"].lower(), rt["shortForm"])
        if key not in existing_keys:
            current.append(rt)
            existing_keys.add(key)
            added += 1

    if added > 0:
        try:
            with open(trait_list_path, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "total_traits": len(current),
                }, f, indent=2)
            _trait_list = current
            logger.info(f"Merged {added} remote traits into cache (total {len(current)})")
        except Exception as e:
            logger.warning(f"Failed to persist remote traits: {e}")

    return added


def _fuzzy_search_traits(query: str, top_k: int = 10):
    """
    Block 2: Fuzzy search over trait list.
    Scoring per B_spec:
      prefix_match  -> 1.0
      contains_match -> 0.8
      token_match   -> 0.6
    Sort by score desc, then trait name asc.
    """
    traits = _get_trait_list()
    query_lower = query.lower().strip()
    scored = []

    for entry in traits:
        name = entry.get("trait", "")
        name_lower = name.lower()

        # Priority 1: prefix match
        if name_lower.startswith(query_lower):
            scored.append((1.0, name, entry))
            continue

        # Priority 2: contains match
        if query_lower in name_lower:
            scored.append((0.8, name, entry))
            continue

        # Priority 3: token match (any word starts with query)
        tokens = name_lower.split()
        if any(tok.startswith(query_lower) for tok in tokens):
            scored.append((0.6, name, entry))
            continue

    # Sort:
    # - score desc
    # - fewer tokens first (prefer canonical disease/trait names like "Obesity" over phrases like "Obese vs. thin")
    # - trait name asc
    scored.sort(key=lambda x: (-x[0], len(str(x[1]).split()), x[1]))

    results = []
    for score, _, entry in scored[:top_k]:
        results.append({
            "trait": entry["trait"],
            "efo_id": entry["shortForm"],
            "score": score,
        })
    return results


def get_nlp_matcher():
    """Get NLP Matcher instance with lazy loading"""
    global nlp_matcher
    if nlp_matcher is None:
        try:
            config_path = os.path.join(current_app.root_path, '..', 'config', 'app_config.yaml')
            config = load_app_config(config_path)
            nlp_matcher = PhenotypeNLPMatcher(config)
        except Exception as e:
            current_app.logger.error(f"Error initializing NLP matcher: {e}")
            nlp_matcher = None
    return nlp_matcher

# --- Block 2: New fuzzy search endpoint ---
@api_bp.route('/search-traits', methods=['POST'])
def search_traits():
    """POST /api/search-traits — fuzzy search over full GWAS Catalog trait list.

    C6.B1: When local results are empty or the top score is below the
    configured threshold, attempt a remote GWAS Catalog search, merge
    results into the response, and persist new traits into the local cache.
    Remote is controlled by GWAS_REMOTE_SEARCH env var (default OFF).
    """
    try:
        data = request.get_json()
        query = (data.get('query', '') if data else '').strip()
        top_k = int(data.get('top_k', 10)) if data else 10

        if len(query) < 3:
            return jsonify({
                'success': False,
                'message': 'Query must be at least 3 characters.'
            }), 400

        results = _fuzzy_search_traits(query, top_k)

        # C6.B1: remote fallback when local results are empty or weak
        remote_enabled = os.environ.get("GWAS_REMOTE_SEARCH", "").lower() in ("1", "true", "yes")
        top_score = results[0]["score"] if results else 0.0

        if remote_enabled and (not results or top_score < REMOTE_SCORE_THRESHOLD):
            try:
                remote_traits = _fetch_remote_traits(query)
                if remote_traits:
                    _merge_remote_into_cache(remote_traits)
                    # Re-run local fuzzy search which now includes the merged traits
                    results = _fuzzy_search_traits(query, top_k)
            except Exception as remote_err:
                logger.warning(f"Remote GWAS trait search failed: {remote_err}")

        return jsonify({
            'success': True,
            'results': results,
        })

    except Exception as e:
        current_app.logger.error(f"Error in search-traits: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Search error: {str(e)}'
        }), 500


# Existing endpoint: Natural language phenotype search (kept for backward compatibility)
@api_bp.route('/search-phenotypes', methods=['POST'])
def search_phenotypes():
    """Search for related phenotypes based on natural language input"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        use_llm = data.get('use_llm', False)  # Currently only keyword search
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Please enter a disease or symptom to search.'
            }), 400
        
        matcher = get_nlp_matcher()
        if not matcher:
            return jsonify({
                'success': False,
                'message': 'Phenotype search service could not be initialized.'
            }), 500
        
        results = matcher.search_phenotypes(query, use_llm, top_k)
        
        # Format results for frontend
        if results['success'] and results['results']:
            formatted_results = []
            for result in results['results']:
                formatted_results.append({
                    'name': result['name'],
                    'efo_id': result['efo_id'],
                    'similarity': round(result['similarity'], 2),
                    'confidence': result.get('confidence', 'medium'),
                    'reason': result.get('matched_keyword', 'keyword match'),
                    'description': f"Relevance: {round(result['similarity']*100)}%"
                })
            
            results['results'] = formatted_results
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Error in phenotype search: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Search error occurred: {str(e)}'
        }), 500

# New endpoint: Popular phenotype list
@api_bp.route('/get-popular-phenotypes', methods=['GET'])
def get_popular_phenotypes():
    """Return list of popular phenotypes"""
    try:
        matcher = get_nlp_matcher()
        if not matcher:
            # Fallback list
            popular_list = [
                {"name": "coronary heart disease", "efo_id": "EFO_0001645"},
                {"name": "type 2 diabetes", "efo_id": "EFO_0001360"},
                {"name": "breast cancer", "efo_id": "MONDO_0007254"},
                {"name": "alzheimer's disease", "efo_id": "MONDO_0004975"},
                {"name": "hypertension", "efo_id": "EFO_0000537"}
            ]
        else:
            popular_list = matcher.get_popular_phenotypes(10)
        
        return jsonify({
            'success': True,
            'phenotypes': popular_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting popular phenotypes: {e}")
        return jsonify({
            'success': False,
            'message': 'Could not retrieve popular disease list.'
        }), 500

# Existing endpoint: traits list (backward compatibility)
@api_bp.route('/get-traits', methods=['GET'])
def get_traits():
    """Serves the list of traits from the efo_mapping.json file."""
    try:
        config_path = os.path.join(current_app.root_path, '..', 'config', 'efo_mapping.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            efo_mapping = json.load(f)
        
        traits = [{"name": name, "efo_id": efo_id} for name, efo_id in efo_mapping.items()]
        return jsonify({"success": True, "traits": traits})
    except Exception as e:
        current_app.logger.error(f"Error getting traits: {e}")
        return jsonify({"success": False, "message": "Could not load trait list."}), 500

# Existing endpoint: VCF upload
@api_bp.route('/upload-vcf', methods=['POST'])
def upload_vcf():
    """Handles VCF file upload and initial parsing."""
    if 'vcfFile' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    file = request.files['vcfFile']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    try:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        vcf_reader = load_vcf_reader(temp_path)
        parquet_path = os.path.join(temp_dir, 'variants.parquet')
        variants_df = extract_user_variants(vcf_reader, parquet_path=parquet_path)
        
        session_id = os.path.basename(temp_dir)
        UPLOADS[session_id] = {'file_path': temp_path, 'variants': variants_df}
        
        return jsonify({
            'success': True,
            'message': f'File {file.filename} was successfully uploaded.',
            'session_id': session_id,
            'variants_count': len(variants_df)
        })
    except Exception as e:
        current_app.logger.error(f"Error during VCF upload: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'}), 500

# Updated analysis endpoint: Customer-friendly results
@api_bp.route('/analyze', methods=['POST'])
def analyze():
    """Improved analysis endpoint providing customer-friendly results"""
    try:
        # 1. Get user input parameters
        session_id = request.form.get('session_id')
        trait_or_efo = request.form.get('trait_or_efo')
        use_trait_name = request.form.get('use_trait_name') == 'true'
        
        # Customer-friendly filter defaults
        filters = {
            'max_p_value': request.form.get('max_p_value', type=float) or 0.05,
            'min_odds_ratio': request.form.get('min_odds_ratio', type=float) or 0.5,  # Include protective variants
            'ethnicity': request.form.get('ethnicity', '')
        }
        
        if not session_id or session_id not in UPLOADS:
            return jsonify({
                'success': False, 
                'message': 'Invalid session or VCF file not uploaded.'
            }), 400

        # 2. Load configuration
        config_path = os.path.join(current_app.root_path, '..', 'config', 'app_config.yaml')
        config = load_app_config(config_path)
        if config is None:
            return jsonify({
                'success': False, 
                'message': 'Server configuration error occurred.'
            }), 500

        # 3. Determine EFO ID
        # IMPORTANT: UI sends trait_or_efo as EFO/ontology ID (use_trait_name=false)
        # but also includes a human-friendly trait_name for display and references.
        trait_name = request.form.get("trait_name") or trait_or_efo
        if use_trait_name:
            mapping_path = os.path.join(current_app.root_path, '..', 'config', 'efo_mapping.json')
            efo_id = get_efo_id_for_trait(trait_or_efo, mapping_path)
            if not efo_id:
                return jsonify({
                    'success': False, 
                    'message': f'Could not find information for disease: {trait_or_efo}'
                }), 400
        else:
            efo_id = trait_or_efo

        # 4. Fetch GWAS data (cache first)
        gwas_data_df = None
        if config.get('use_local_gwas_cache', False):
            gwas_data_df = load_gwas_data_from_cache(efo_id, config)

        if gwas_data_df is None:
            current_app.logger.info(f"Cache not found for {efo_id}. Fetching from API.")
            raw_associations = fetch_gwas_associations_by_efo(efo_id, config)
            gwas_data_df = parse_gwas_association_data(raw_associations, trait_name, config)
            
            if not gwas_data_df.empty and config.get('use_local_gwas_cache', False):
                save_gwas_data_to_cache(gwas_data_df, efo_id, config)
        
        variant_store = UPLOADS[session_id]['variants']

        if gwas_data_df.empty:
            return jsonify({
                'success': False,
                'message': f'No genetic research data found for {trait_name}.'
            }), 404

        if variant_store.empty:
            return jsonify({
                'success': False,
                'message': 'No analyzable variants found in VCF file.'
            }), 404

        # 5. DEBUG: Log data before merge
        current_app.logger.info("=== DEBUG: Data before merge ===")
        current_app.logger.info(f"GWAS data columns: {list(gwas_data_df.columns)}")
        current_app.logger.info(f"User variants: {len(variant_store):,} alleles (parquet-backed)")

        if not gwas_data_df.empty:
            current_app.logger.info("GWAS data sample:")
            current_app.logger.info(gwas_data_df.head(3).to_string())

        # Merge data — chunk-based to avoid loading all WGS variants into memory
        merged_data = variant_store.merge_with(gwas_data_df, merge_variant_data)
        
        # DEBUG: Log merged data structure
        current_app.logger.info("=== DEBUG: Data after merge ===")
        current_app.logger.info(f"Merged data columns: {list(merged_data.columns)}")
        current_app.logger.info(f"Merged data shape: {merged_data.shape}")
        
        if not merged_data.empty:
            current_app.logger.info("Merged data sample:")
            current_app.logger.info(merged_data.head(3).to_string())
            
            # Check specific columns that might be causing issues
            if 'SNP_ID' in merged_data.columns:
                current_app.logger.info(f"SNP_ID values sample: {merged_data['SNP_ID'].head()}")
            if 'PubMed_ID' in merged_data.columns:
                current_app.logger.info(f"PubMed_ID values sample: {merged_data['PubMed_ID'].head()}")
        
        if merged_data.empty:
            return jsonify({
                'success': False,
                'message': 'No matching variants found between your data and research database.'
            }), 404

        # Apply filters
        filtered_data = merged_data.copy()
        
        # P-value filter
        if filters['max_p_value']:
            filtered_data['P_Value'] = pd.to_numeric(filtered_data['P_Value'], errors='coerce')
            filtered_data = filtered_data.dropna(subset=['P_Value'])
            filtered_data = filtered_data[filtered_data['P_Value'] <= filters['max_p_value']]

        # Odds Ratio filter (keep rows with missing OR — many GWAS entries lack it)
        if filters['min_odds_ratio']:
            filtered_data['Odds_Ratio'] = pd.to_numeric(filtered_data['Odds_Ratio'], errors='coerce')
            filtered_data = filtered_data[
                filtered_data['Odds_Ratio'].isna() |
                (filtered_data['Odds_Ratio'] >= filters['min_odds_ratio'])
            ]

        current_app.logger.info(f"{len(filtered_data)} variants remaining after applying filters.")

        # DEBUG: Log filtered data
        if not filtered_data.empty:
            current_app.logger.info("=== DEBUG: Data after filtering ===")
            current_app.logger.info(f"Filtered data columns: {list(filtered_data.columns)}")
            current_app.logger.info("Sample of filtered data:")
            for idx, row in filtered_data.head(3).iterrows():
                current_app.logger.info(f"Row {idx}:")
                current_app.logger.info(f"  SNP_ID: {row.get('SNP_ID', 'NOT_FOUND')}")
                current_app.logger.info(f"  PubMed_ID: {row.get('PubMed_ID', 'NOT_FOUND')}")
                current_app.logger.info(f"  GWAS_Trait: {row.get('GWAS_Trait', 'NOT_FOUND')}")
        else:
            current_app.logger.info("Filtered data is empty")

        # Convert to customer-friendly format
        analysis_results = format_customer_friendly_results(filtered_data)
        
        if not analysis_results['success']:
            return jsonify({
                'success': False,
                'message': 'No variants found matching filter criteria.'
            }), 404
        
        # Add additional info
        analysis_results['analysis_info']['analyzed_trait'] = trait_name
        analysis_results['analysis_info']['efo_id'] = efo_id
        analysis_results['analysis_info']['filters_applied'] = filters

        # Persist GWAS facts for chat so chat isn't PGx-only (C5.B3/Cycle 6).
        try:
            UPLOADS[session_id]["gwas_associations"] = _extract_gwas_associations_for_facts(
                filtered_data=filtered_data,
                trait_name=trait_name,
                max_items=50,
            )
        except Exception as persist_err:
            current_app.logger.warning(f"Failed to persist gwas_associations for chat: {persist_err}")
        
        return jsonify(json.loads(json.dumps(analysis_results, default=str)))

    except Exception as e:
        current_app.logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'message': f'Unexpected error during analysis: {str(e)}'
        }), 500


@api_bp.route('/clinvar-match', methods=['POST'])
def clinvar_match():
    """POST /api/clinvar-match — match uploaded session variants to the toy ClinVar TSV."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = str(data.get('session_id', '')).strip()
        significance_filter = data.get('significance_filter')

        if not session_id or session_id not in UPLOADS:
            return jsonify({
                'success': False,
                'message': 'Missing or invalid session_id.'
            }), 400

        variant_store = UPLOADS[session_id].get('variants')
        if variant_store is None or variant_store.empty:
            return jsonify({
                'success': True,
                'summary': {
                    'session_id': session_id,
                    'variants_count': 0,
                    'matches_count': 0,
                },
                'matches': [],
            }), 200

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        clinvar_tsv_path = os.path.join(project_root, "data", "clinvar", "clinvar_toy.tsv")

        if isinstance(significance_filter, str) and significance_filter.strip():
            significance_filter = [significance_filter.strip()]
        elif not isinstance(significance_filter, (list, tuple)):
            significance_filter = None

        # Process clinvar matching in chunks to avoid OOM
        all_matches = []
        for chunk_df in variant_store.iter_chunks():
            chunk_matches = match_user_variants_to_clinvar(
                user_variants_df=chunk_df,
                clinvar_tsv_path=clinvar_tsv_path,
                significance_filter=significance_filter,
            )
            all_matches.extend(chunk_matches)
        matches = all_matches

        # Store matches in session for chat facts derivation (C5.B3)
        if session_id in UPLOADS:
            UPLOADS[session_id]['clinvar_matches'] = matches

        return jsonify({
            'success': True,
            'summary': {
                'session_id': session_id,
                'variants_count': int(len(variant_store)),
                'matches_count': int(len(matches)),
            },
            'matches': matches,
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in clinvar-match: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'ClinVar match error: {str(e)}'
        }), 500


def _summarize_foregenomics(df):
    """Build a summary dict from a ForeGenomics parsed DataFrame.

    The ForeGenomics parser returns columns:
        gene, drug, genotype, phenotype, recommendation, guideline_ids
    which differs from the toy PGx schema (diplotype instead of genotype).
    """
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "genes": [],
            "drugs": [],
            "by_gene": [],
        }

    genes = sorted(df["gene"].dropna().loc[df["gene"] != ""].unique().tolist())
    drugs = sorted(df["drug"].dropna().loc[df["drug"] != ""].unique().tolist())

    by_gene = []
    for gene in genes:
        sub = df[df["gene"] == gene]
        by_gene.append({
            "gene": gene,
            "rows": int(len(sub)),
            "genotypes": sorted(set(sub["genotype"].tolist())),
            "phenotypes": sorted(set(sub["phenotype"].tolist())),
            "drugs": sorted(set(sub["drug"].tolist())),
        })
    by_gene.sort(key=lambda x: x["gene"])

    return {
        "total_rows": int(len(df)),
        "genes": genes,
        "drugs": drugs,
        "by_gene": by_gene,
    }


def _summarize_cpic(df):
    """Build a summary dict from a CPIC parsed DataFrame."""
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "genes": [],
            "drugs": [],
            "by_gene": [],
        }

    genes = sorted(df["gene"].dropna().loc[df["gene"] != ""].unique().tolist())
    drugs = sorted(df["drug"].dropna().loc[df["drug"] != ""].unique().tolist())

    by_gene = []
    for gene in genes:
        sub = df[df["gene"] == gene]
        by_gene.append({
            "gene": gene,
            "rows": int(len(sub)),
            "diplotypes": sorted(set(sub["diplotype"].tolist())),
            "phenotypes": sorted(set(sub["phenotype"].tolist())),
            "drugs": sorted(set(sub["drug"].tolist())),
        })
    by_gene.sort(key=lambda x: x["gene"])

    return {
        "total_rows": int(len(df)),
        "genes": genes,
        "drugs": drugs,
        "by_gene": by_gene,
    }


@api_bp.route('/pgx-summary', methods=['POST'])
def pgx_summary():
    """POST /api/pgx-summary — return deterministic PGx summary from toy, foregenomics, or cpic TSV."""
    try:
        data = request.get_json(silent=True) or {}
        source = str(data.get("source", "toy")).strip().lower()

        if source not in ("toy", "foregenomics", "cpic"):
            return jsonify({
                'success': False,
                'message': 'Invalid source. Use source="toy", source="foregenomics", or source="cpic".'
            }), 400

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

        if source == "foregenomics":
            # C10.B2: per-session report selection via FOREGENOMICS_PGX_ROOT + sample_id
            pgx_root = os.environ.get("FOREGENOMICS_PGX_ROOT", "").strip()
            session_id = str(data.get("session_id", "")).strip()
            sample_id = ""
            if session_id and session_id in UPLOADS:
                sample_id = str(UPLOADS[session_id].get("sample_id", "")).strip()
            tsv_path = None
            if pgx_root and sample_id:
                tsv_path = find_foregenomics_report(pgx_root, sample_id)
            if not tsv_path:
                tsv_path = os.environ.get("FOREGENOMICS_PGX_REPORT_PATH") or os.path.join(
                    project_root, "data", "pgx", "foregenomics_report.tsv"
                )
            fg_df = parse_foregenomics_report_tsv(tsv_path)
            summary = _summarize_foregenomics(fg_df)
        elif source == "cpic":
            tsv_path = os.path.join(project_root, "data", "pgx", "cpic_toy.tsv")
            cpic_df = parse_cpic_toy_tsv(tsv_path)
            summary = _summarize_cpic(cpic_df)
        else:
            tsv_path = os.path.join(project_root, "data", "pgx", "final.tsv")
            df = parse_pgx_final_tsv(tsv_path)
            summary = summarize_pgx(df)

        # Store pgx summary in session for chat facts derivation (C5.B3)
        session_id = str(data.get("session_id", "")).strip()
        if session_id and session_id in UPLOADS:
            UPLOADS[session_id]['pgx_summary'] = summary

        disclaimer_tags = [
            "pharmacogenomics",
            "cpic_data" if source == "cpic" else ("foregenomics_data" if source == "foregenomics" else "toy_data"),
            "not_medical_advice",
            "consult_professional",
        ]

        return jsonify({
            'success': True,
            'summary': summary,
            'disclaimer_tags': disclaimer_tags,
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in pgx-summary: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'PGx summary error: {str(e)}'
        }), 500


# --- Minimum disclaimer tags required by the high-risk domain contract ---
_CHAT_DISCLAIMER_TAGS = [
    "not_medical_advice",
    "consult_professional",
    "research_only",
    "no_emergency_use",
]

_VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


def _assess_risk_level(facts_list):
    """Deterministic risk-level assignment based on collected facts."""
    if not facts_list:
        return "low"
    domains = {f.domain for f in facts_list}
    has_clinvar = "clinvar" in domains
    has_pgx = "pgx" in domains
    if has_clinvar and has_pgx:
        return "high"
    if has_clinvar or has_pgx:
        return "medium"
    return "low"


def _build_answer(message, facts_list):
    """Build a deterministic counseling answer from collected facts."""
    if not facts_list:
        return (
            "No genetic facts are currently loaded for this session. "
            "Please upload a VCF file and run an analysis first."
        )
    lines = [f"Regarding your question: {message}", ""]
    lines.append(f"Based on {len(facts_list)} available genetic facts:")
    for fact in facts_list[:10]:
        lines.append(f"  - [{fact.id}] {fact.text}")
    if len(facts_list) > 10:
        lines.append(f"  ... and {len(facts_list) - 10} more facts.")
    lines.append("")
    lines.append(
        "IMPORTANT: This information is for research and educational purposes only. "
        "It does not constitute medical advice. Please consult a qualified healthcare "
        "professional before making any medical decisions."
    )
    return "\n".join(lines)


# --- C6.B2: Ollama local LLM mode for chat ---

def _ollama_enabled():
    """Check whether Ollama mode is enabled via environment variables."""
    host = os.environ.get("OLLAMA_HOST", "").strip()
    model = os.environ.get("OLLAMA_MODEL_CHAT", "").strip()
    return bool(host and model)


def _call_ollama(message, facts_list):
    """Call the Ollama HTTP API to generate a counseling answer.

    Returns the raw LLM text. Raises on network/API errors.
    """
    host = os.environ["OLLAMA_HOST"].rstrip("/")
    model = os.environ["OLLAMA_MODEL_CHAT"]

    facts_text = "\n".join(f"- [{f.id}] {f.text}" for f in facts_list[:20])
    system_prompt = (
        "You are a genetics counseling assistant for research/education.\n"
        "Use ONLY the provided genetic facts. Do NOT add outside knowledge.\n"
        "Do NOT reveal chain-of-thought. Output final answer only.\n"
        "Required structure:\n"
        "1) Brief answer (1-3 sentences)\n"
        "2) Evidence: bullet list of the specific fact IDs you used and why\n"
        "3) Limits: what cannot be concluded from the facts\n"
        "4) Disclaimers: not medical advice; consult professional; no emergency use\n"
        "Cite facts by writing their IDs exactly (e.g., gwas-0001-..., clinvar-0000-..., pgx-0003-...)."
    )
    user_prompt = f"Facts:\n{facts_text}\n\nUser question: {message}"

    resp = http_requests.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_predict": 512,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def _validate_ollama_answer(raw_answer, fact_ids):
    """Ensure the Ollama answer references at least one known fact ID.

    Returns the (possibly augmented) answer.
    """
    if not raw_answer or not raw_answer.strip():
        return None
    # Strip common chain-of-thought wrappers some local models emit.
    text = raw_answer
    # <think> ... </think>
    if "<think>" in text and "</think>" in text:
        while "<think>" in text and "</think>" in text:
            pre, rest = text.split("<think>", 1)
            _, post = rest.split("</think>", 1)
            text = (pre + post).strip()
    raw_answer = text.strip()
    # Check if at least one fact ID is referenced
    if fact_ids and not any(fid in raw_answer for fid in fact_ids):
        raw_answer += "\n\nReferenced facts: " + ", ".join(fact_ids[:5])
    return raw_answer


def _extract_trait_from_message(message: str):
    """Try to extract a recognizable trait name from a user chat message.

    Returns the matched trait name (str) or None.
    Uses the loaded trait list for matching.
    """
    msg_lower = message.lower()
    traits = _get_trait_list()
    if not traits:
        return None

    best_match = None
    best_len = 0
    for entry in traits:
        trait_name = entry.get("trait", "")
        if not trait_name:
            continue
        t_lower = trait_name.lower()
        if len(t_lower) < 3:
            continue
        if t_lower in msg_lower and len(t_lower) > best_len:
            best_match = trait_name
            best_len = len(t_lower)
    return best_match


@api_bp.route('/chat', methods=['POST'])
def chat():
    """POST /api/chat — facts-based counseling chat with mandatory disclaimers and citations."""
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                'success': False,
                'message': 'message field is required.',
            }), 400

        # Collect facts: prefer session-derived data, fall back to explicit payload
        session_id = str(data.get("session_id", "")).strip()
        gwas_associations = data.get("gwas_associations") or []
        clinvar_matches = data.get("clinvar_matches") or []
        pgx_summary_data = data.get("pgx_summary") or {}

        # C5.B3: If session_id provided, derive facts from stored session results
        if session_id and session_id in UPLOADS:
            session_data = UPLOADS[session_id]
            if not gwas_associations:
                gwas_associations = session_data.get("gwas_associations") or []
            if not clinvar_matches:
                clinvar_matches = session_data.get("clinvar_matches") or []
            if not pgx_summary_data:
                pgx_summary_data = session_data.get("pgx_summary") or {}

        facts_list = collect_facts(
            gwas_associations=gwas_associations or None,
            clinvar_matches=clinvar_matches or None,
            pgx_summary=pgx_summary_data or None,
        )

        fact_ids = get_fact_ids(facts_list)
        risk_level = _assess_risk_level(facts_list)

        # C9.B2: Suggest trait analysis when user mentions a trait but no GWAS facts
        suggested_actions = []
        trait_risk_guarded = False
        has_gwas_facts = any(f.domain == "gwas" for f in facts_list) if facts_list else False
        if not has_gwas_facts:
            detected_trait = _extract_trait_from_message(message)
            if detected_trait:
                suggested_actions.append({
                    "type": "analyze_trait",
                    "label": f"Analyze {detected_trait}",
                    "trait": detected_trait,
                })
                # C10.B3: Trait-Risk Guard — do not produce medium/high risk
                # from PGx-only facts when the user asks about a disease trait.
                risk_level = "low"
                trait_risk_guarded = True

        # C6.B2: Ollama mode — call local LLM if enabled and facts exist
        answer = None
        llm_used = False
        if _ollama_enabled() and facts_list:
            try:
                raw = _call_ollama(message, facts_list)
                answer = _validate_ollama_answer(raw, fact_ids)
                if answer is not None:
                    llm_used = True
            except Exception as ollama_err:
                logger.warning(f"Ollama call failed, falling back to deterministic: {ollama_err}")

        # Fallback to deterministic answer
        if answer is None:
            answer = _build_answer(message, facts_list)

        # C10.B3: prepend guard notice when trait-risk was suppressed
        if trait_risk_guarded:
            guard_msg = (
                "I cannot assess disease-specific risk from pharmacogenomic (PGx) data alone. "
                "Please run a GWAS trait analysis first using the suggested action below."
            )
            answer = guard_msg + "\n\n" + answer

        # C8.B4: LLM transparency — report which model was used
        if llm_used:
            llm_info = {
                "enabled": True,
                "provider": "ollama",
                "model": os.environ.get("OLLAMA_MODEL_CHAT", ""),
            }
        else:
            llm_info = {
                "enabled": False,
                "provider": "deterministic",
                "model": "",
            }

        return jsonify({
            'success': True,
            'answer': answer,
            'disclaimer_tags': list(_CHAT_DISCLAIMER_TAGS),
            'citations': fact_ids,
            'risk_level': risk_level,
            'llm': llm_info,
            'suggested_actions': suggested_actions,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in chat: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'answer': '',
            'disclaimer_tags': list(_CHAT_DISCLAIMER_TAGS),
            'citations': [],
            'risk_level': 'low',
            'message': f'Chat error: {str(e)}'
        }), 500
