# 📁 gwas_variant_analyzer/nlp_phenotype_matcher.py
# Update the get_popular_phenotypes function with your disease list

"""
Natural Language Based Phenotype Matching Module
System for automatically finding related diseases/traits from natural language input
"""

import json
import logging
import os
from typing import Any, Dict, List
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class PhenotypeNLPMatcher:
    """Class for mapping natural language input to EFO IDs"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.efo_mapping = {}
        self.load_efo_mapping()
        self.build_disease_keywords()
    
    def load_efo_mapping(self):
        """Load disease/trait information from EFO mapping file"""
        try:
            mapping_file = self.config.get('efo_mapping_file', 'config/efo_mapping.json')
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.efo_mapping = json.load(f)
                logger.info(f"Loaded {len(self.efo_mapping)} phenotype mappings from {mapping_file}")
            else:
                # Your custom disease mapping
                self.efo_mapping = {
                    "obesity": "EFO_0001073",
                    "height growth": "OBA_2045231",
                    "coronary heart disease": "EFO_0001645",
                    "hypertension": "EFO_0000537",
                    "type 2 diabetes": "MONDO_0005148",
                    "male fertility": "EFO_0004803",
                    "androgenetic alopecia": "EFO_0004191",
                    "asthma": "MONDO_0004979",
                    "psoriasis": "EFO_0000676",
                    "breast cancer": "EFO_0000305",
                    "prostate cancer": "EFO_0001663",  # Using first EFO ID
                    "colorectal cancer": "MONDO_0005575",  # Using first EFO ID
                    "lung cancer": "EFO_0001071",
                    "depression": "MONDO_0002050",
                    "bipolar disorder": "MONDO_0004985",
                    "autism spectrum disorder": "EFO_0003758",
                    "schizophrenia": "MONDO_0005090",
                    "alzheimer's disease": "MONDO_0004975",
                    "parkinson's disease": "MONDO_0005180",
                    "crohn's disease": "EFO_0000384",
                    "ulcerative colitis": "EFO_0000729",
                    "rheumatoid arthritis": "EFO_0000685"
                }
                logger.warning(f"EFO mapping file not found: {mapping_file}, using fallback")
        except Exception as e:
            logger.error(f"Error loading EFO mapping: {e}")
            self.efo_mapping = {}
    
    def get_popular_phenotypes(self, count: int = 10) -> List[Dict[str, str]]:
        """Return list of popular diseases/traits based on your preferences"""
        # Your prioritized disease list
        popular = [
            # Metabolic & Physical traits (top priority)
            "obesity",
            "type 2 diabetes",
            "height growth",
            
            # Cardiovascular
            "coronary heart disease",
            "hypertension",
            
            # Male-specific conditions
            "male fertility",
            "androgenetic alopecia",
            
            # Cancer
            "breast cancer",
            "prostate cancer",
            "colorectal cancer",
            "lung cancer",
            
            # Mental health
            "depression",
            "schizophrenia",
            "autism spectrum disorder",
            "bipolar disorder",
            
            # Neurological
            "alzheimer's disease",
            "parkinson's disease",
            
            # Inflammatory/Autoimmune
            "asthma",
            "psoriasis",
            "crohn's disease",
            "ulcerative colitis",
            "rheumatoid arthritis"
        ]
        
        results = []
        for disease in popular[:count]:
            if disease in self.efo_mapping:
                efo_id = self.efo_mapping[disease]
                # Handle multiple EFO IDs (take first one)
                if '|' in efo_id:
                    efo_id = efo_id.split('|')[0]
                results.append({
                    'name': disease,
                    'efo_id': efo_id
                })
        
        return results
    
    def build_disease_keywords(self):
        """Build keywords from disease names for enhanced search"""
        self.disease_keywords = {}
        
        # Medical synonyms and related terms for your diseases
        medical_synonyms = {
            'obesity': ['obesity', 'overweight', 'BMI', 'body mass index', 'weight'],
            'height': ['height', 'height growth', 'stature', 'tall', 'short'],
            'heart disease': ['coronary heart disease', 'coronary artery disease', 'CAD', 'heart attack'],
            'high blood pressure': ['hypertension', 'blood pressure', 'BP'],
            'diabetes': ['type 2 diabetes', 'diabetes', 'T2D', 'blood sugar'],
            'fertility': ['male fertility', 'infertility', 'sperm', 'reproductive'],
            'hair loss': ['androgenetic alopecia', 'baldness', 'hair loss', 'male pattern baldness'],
            'asthma': ['asthma', 'breathing', 'respiratory'],
            'psoriasis': ['psoriasis', 'skin condition'],
            'cancer': ['cancer', 'tumor', 'carcinoma'],
            'depression': ['depression', 'mood disorder', 'depressive'],
            'autism': ['autism', 'autism spectrum disorder', 'ASD'],
            'schizophrenia': ['schizophrenia', 'psychosis'],
            'alzheimer': ['alzheimer', 'alzheimer\'s disease', 'dementia', 'memory loss'],
            'parkinson': ['parkinson', 'parkinson\'s disease', 'tremor'],
            'crohn': ['crohn\'s disease', 'IBD', 'inflammatory bowel'],
            'colitis': ['ulcerative colitis', 'IBD', 'bowel inflammation'],
            'arthritis': ['rheumatoid arthritis', 'RA', 'joint pain']
        }
        
        for disease_name, efo_id in self.efo_mapping.items():
            keywords = [disease_name.lower()]
            
            # Add synonyms
            for key, synonyms in medical_synonyms.items():
                if key in disease_name.lower():
                    keywords.extend(synonyms)
            
            # Handle multiple EFO IDs
            if '|' in efo_id:
                efo_id = efo_id.split('|')[0]
            
            self.disease_keywords[efo_id] = {
                'name': disease_name,
                'keywords': list(set(keywords))
            }
    
    def simple_keyword_search(self, user_input: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Keyword-based simple search"""
        user_input_lower = user_input.lower()
        matches = []
        
        for efo_id, info in self.disease_keywords.items():
            max_similarity = 0
            matched_keyword = ""
            
            for keyword in info['keywords']:
                if keyword in user_input_lower:
                    similarity = 1.0
                    matched_keyword = keyword
                    break
                else:
                    similarity = SequenceMatcher(None, keyword, user_input_lower).ratio()
                    if similarity > max_similarity:
                        max_similarity = similarity
                        matched_keyword = keyword
            
            if max_similarity > 0.3:
                matches.append({
                    'name': info['name'],
                    'efo_id': efo_id,
                    'similarity': max_similarity,
                    'matched_keyword': matched_keyword,
                    'confidence': 'medium',
                    'source': 'keyword'
                })
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:top_k]
    
    def search_phenotypes(self, user_input: str, use_llm: bool = False, top_k: int = 5) -> Dict[str, Any]:
        """Search for related phenotypes from user input"""
        if not user_input.strip():
            return {
                'success': False,
                'message': 'Please enter a search term.',
                'results': []
            }
        
        try:
            # Currently using keyword search only (no OpenAI API)
            results = self.simple_keyword_search(user_input, top_k)
            
            if not results:
                return {
                    'success': True,
                    'message': f'No diseases found related to "{user_input}".',
                    'results': [],
                    'suggestions': self.get_popular_phenotypes()
                }
            
            return {
                'success': True,
                'message': f'Found {len(results)} diseases related to "{user_input}".',
                'results': results,
                'query': user_input
            }
            
        except Exception as e:
            logger.error(f"Error searching phenotypes: {e}")
            return {
                'success': False,
                'message': 'Error occurred during search.',
                'results': []
            }
    
    # NOTE: A second get_popular_phenotypes() implementation used to exist below and caused
    # a redefinition lint error (F811). Keep only the primary implementation.
