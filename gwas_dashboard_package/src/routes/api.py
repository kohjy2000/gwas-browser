# 📁 src/routes/api.py - Replace this file completely

"""
API routes for the GWAS Dashboard.
Handles file uploads, analysis requests, and serves data to the frontend.
"""
import os
import tempfile
import json
import logging
import pandas as pd
from flask import Blueprint, request, jsonify, current_app
import numpy as np

from gwas_variant_analyzer.utils import load_app_config, get_efo_id_for_trait
from gwas_variant_analyzer.vcf_parser import load_vcf_reader, extract_user_variants
from gwas_variant_analyzer.gwas_catalog_handler import fetch_gwas_associations_by_efo, parse_gwas_association_data, load_gwas_data_from_cache, save_gwas_data_to_cache
from gwas_variant_analyzer.data_processor import process_variants, merge_variant_data
from gwas_variant_analyzer.clinvar_matcher import match_user_variants_to_clinvar

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


def _load_trait_list():
    """Load trait list from data/trait_list.json, fallback to efo_mapping.json."""
    global _trait_list
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    trait_list_path = os.path.join(project_root, "data", "trait_list.json")
    fallback_path = os.path.join(project_root, "gwas_dashboard_package", "config", "efo_mapping.json")

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

    # Sort: score desc, then trait name asc
    scored.sort(key=lambda x: (-x[0], x[1]))

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
    """POST /api/search-traits — fuzzy search over full GWAS Catalog trait list."""
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
        variants_df = extract_user_variants(vcf_reader)
        
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
        trait_name = trait_or_efo
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
        
        user_variants_df = UPLOADS[session_id]['variants']

        if gwas_data_df.empty:
            return jsonify({
                'success': False, 
                'message': f'No genetic research data found for {trait_name}.'
            }), 404
        
        if user_variants_df.empty:
            return jsonify({
                'success': False, 
                'message': 'No analyzable variants found in VCF file.'
            }), 404
        
        # 5. DEBUG: Log data before merge to identify SNP ID issue
        current_app.logger.info("=== DEBUG: Data before merge ===")
        current_app.logger.info(f"GWAS data columns: {list(gwas_data_df.columns)}")
        current_app.logger.info(f"User variants columns: {list(user_variants_df.columns)}")
        
        if not gwas_data_df.empty:
            current_app.logger.info("GWAS data sample:")
            current_app.logger.info(gwas_data_df.head(3).to_string())
        
        if not user_variants_df.empty:
            current_app.logger.info("User variants sample:")
            current_app.logger.info(user_variants_df.head(3).to_string())
        
        # IMPORTANT: Do NOT rename SNP_ID before merge - preserve original column name
        # The merge should preserve the SNP_ID column from GWAS data
        
        # Merge data
        merged_data = merge_variant_data(user_variants_df, gwas_data_df)
        
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

        # Odds Ratio filter
        if filters['min_odds_ratio']:
            filtered_data['Odds_Ratio'] = pd.to_numeric(filtered_data['Odds_Ratio'], errors='coerce')
            filtered_data = filtered_data.dropna(subset=['Odds_Ratio'])
            filtered_data = filtered_data[filtered_data['Odds_Ratio'] >= filters['min_odds_ratio']]

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

        user_variants_df = UPLOADS[session_id].get('variants')
        if user_variants_df is None or getattr(user_variants_df, "empty", True):
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

        matches = match_user_variants_to_clinvar(
            user_variants_df=user_variants_df,
            clinvar_tsv_path=clinvar_tsv_path,
            significance_filter=significance_filter,
        )

        return jsonify({
            'success': True,
            'summary': {
                'session_id': session_id,
                'variants_count': int(len(user_variants_df)),
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
