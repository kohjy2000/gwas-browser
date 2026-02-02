import json
import pandas as pd
from gwas_variant_analyzer.gwas_catalog_handler import parse_gwas_association_data # 실제 파일 경로에 맞게 수정
# from gwas_variant_analyzer.utils import setup_logging # 로깅을 보려면 추가

# 로깅 설정 (선택적)
# setup_logging(log_level_str='DEBUG') 

# 1단계에서 준비한 실제 API 응답의 단일 association 객체
# 아래는 예시 구조이며, 실제 복사한 JSON 객체로 대체해야 합니다.
# 따옴표 문제 등을 피하기 위해 Python 딕셔너리 형태로 직접 만들거나,
# JSON 문자열을 파일에서 읽어오거나, 삼중 따옴표로 감싸서 사용할 수 있습니다.
sample_association_json_string = """

{
"range": "[1.27-1.46]",
"pvalueDescription": " ",
"orPerCopyNum": 1.36,
"snpType": "known",
"multiSnpHaplotype": false,
"snpInteraction": false,
"pvalueMantissa": 3,
"pvalueExponent": -19,
"standardError": null,
"efoTraits": [
  {
    "trait": "coronary artery disease",
    "uri": "http://www.ebi.ac.uk/efo/EFO_0001645",
    "shortForm": "EFO_0001645"
  }
],
"backgroundEfoTraits": [],
"pvalue": 3e-19,
"loci": [
  {
    "haplotypeSnpCount": null,
    "description": "Single variant",
    "strongestRiskAlleles": [
      {
        "riskAlleleName": "rs1333049-C",
        "riskFrequency": null,
        "genomeWide": null,
        "limitedList": null,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      }
    ],
    "authorReportedGenes": [
      {
        "geneName": "intergenic",
        "entrezGeneIds": [],
        "ensemblGeneIds": []
      }
    ]
  }
],
"riskFrequency": "0.47",
"snps": [
  {
    "rsId": "rs1333049",
    "merged": 0,
    "functionalClass": "intergenic_variant",
    "lastUpdateDate": "2024-12-23T08:44:23.665+0000",
    "locations": [
      {
        "chromosomeName": "9",
        "chromosomePosition": 22125504,
        "region": {
          "name": "9p21.3"
        },
        "_links": {
          "snps": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      }
    ],
    "genomicContexts": [
      {
        "isIntergenic": false,
        "isUpstream": false,
        "isDownstream": false,
        "distance": 0,
        "gene": {
          "geneName": "CDKN2B-AS1",
          "entrezGeneIds": [
            {
              "entrezGeneId": "100048912"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000240498"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "NCBI",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": false,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      },
      {
        "isIntergenic": true,
        "isUpstream": true,
        "isDownstream": false,
        "distance": 112968,
        "gene": {
          "geneName": "UBA52P6",
          "entrezGeneIds": [
            {
              "entrezGeneId": "100130239"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000215221"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "Ensembl",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": true,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      },
      {
        "isIntergenic": false,
        "isUpstream": false,
        "isDownstream": false,
        "distance": 0,
        "gene": {
          "geneName": "CDKN2B-AS1",
          "entrezGeneIds": [
            {
              "entrezGeneId": "100048912"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000240498"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "Ensembl",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": false,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      },
      {
        "isIntergenic": true,
        "isUpstream": true,
        "isDownstream": false,
        "distance": 112882,
        "gene": {
          "geneName": "UBA52P6",
          "entrezGeneIds": [
            {
              "entrezGeneId": "100130239"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000215221"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "NCBI",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": true,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      },
      {
        "isIntergenic": true,
        "isUpstream": false,
        "isDownstream": true,
        "distance": 321320,
        "gene": {
          "geneName": "DMRTA1",
          "entrezGeneIds": [
            {
              "entrezGeneId": "63951"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000176399"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "Ensembl",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": true,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      },
      {
        "isIntergenic": true,
        "isUpstream": false,
        "isDownstream": true,
        "distance": 321320,
        "gene": {
          "geneName": "DMRTA1",
          "entrezGeneIds": [
            {
              "entrezGeneId": "63951"
            }
          ],
          "ensemblGeneIds": [
            {
              "ensemblGeneId": "ENSG00000176399"
            }
          ]
        },
        "location": {
          "chromosomeName": "9",
          "chromosomePosition": 22125504,
          "region": {
            "name": "9p21.3"
          },
          "_links": {
            "snps": {
              "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
              "templated": true
            }
          }
        },
        "source": "NCBI",
        "mappingMethod": "Ensembl_pipeline",
        "isClosestGene": true,
        "_links": {
          "snp": {
            "href": "https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs1333049{?projection}",
            "templated": true
          }
        }
      }
    ]
  }
],
"betaNum": null,
"betaUnit": null,
"betaDirection": null,
"description": null,
"_links": {
  "self": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386"
  },
  "association": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386{?projection}",
    "templated": true
  },
  "study": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386/study"
  },
  "backgroundEfoTraits": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386/backgroundEfoTraits"
  },
  "snps": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386/snps"
  },
  "efoTraits": {
    "href": "https://www.ebi.ac.uk/gwas/rest/api/associations/11386/efoTraits"
  }
}
}
"""

try:
    sample_association_object = json.loads(sample_association_json_string)
except json.JSONDecodeError as e:
    print(f"JSON 파싱 오류: {e}")
    print("sample_association_json_string 변수에 유효한 JSON 객체 문자열을 넣어주세요.")
    exit()

# parse_gwas_association_data 함수는 association 객체의 리스트를 받으므로 리스트로 감싸줍니다.
raw_associations_sample = [sample_association_object]
trait_name_sample = "coronary heart disease" # 테스트용 질병명
config_sample = {} # 현재 parse_gwas_association_data는 config를 직접 사용하진 않지만, 인자로 전달

# 함수 호출
df_result = parse_gwas_association_data(raw_associations_sample, trait_name_sample, config_sample)

# 결과 출력
print("----- Parse Result DataFrame -----")
print(df_result)

if not df_result.empty:
    print("\n----- Key Extracted Columns -----")
    # 추출하려는 주요 컬럼들을 선택하여 출력
    key_columns = ['SNP_ID', 'GWAS_CHROM', 'GWAS_POS', 'GWAS_ALT', 'GWAS_REF', 'P_Value', 'Odds_Ratio']
    # 실제 DataFrame에 있는 컬럼만 선택하도록 필터링
    existing_key_columns = [col for col in key_columns if col in df_result.columns]
    if existing_key_columns:
        print(df_result[existing_key_columns])
    else:
        print("Key columns not found in the result.")
else:
    print("Result DataFrame is empty.")

