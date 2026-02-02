#!/usr/bin/env python3
"""
기본 사용 예제: GWAS Variant Analyzer 패키지의 기본 사용법을 보여줍니다.
이 예제는 코로나리 심장병(Coronary Heart Disease)과 관련된 SNP를 분석합니다.
"""

import os
import pandas as pd
from gwas_variant_analyzer.vcf_parser import load_vcf_reader, extract_user_variants
from gwas_variant_analyzer.gwas_catalog_handler import fetch_gwas_associations_by_efo, parse_gwas_association_data
from gwas_variant_analyzer.data_processor import merge_variant_data, apply_ethnicity_standardization, filter_results_by_criteria, sort_results
from gwas_variant_analyzer.utils import load_app_config

# 작업 디렉토리 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), 'config', 'app_config.yaml')

def main():
    """
    기본 분석 워크플로우를 실행합니다.
    """
    print("GWAS Variant Analyzer 기본 사용 예제")
    print("=" * 50)
    
    # 1. 설정 로드
    print("1. 설정 로드 중...")
    config = load_app_config(CONFIG_PATH)
    print(f"설정 로드 완료: {len(config)} 항목\n")
    
    # 2. VCF 파일 로드 (예제용 경로, 실제 파일로 변경 필요)
    # 참고: 이 예제에서는 실제 VCF 파일이 필요합니다. 아래 경로를 실제 VCF 파일 경로로 변경하세요.
    vcf_file_path = "/path/to/your/sample.vcf.gz"
    print(f"2. VCF 파일 로드 중: {vcf_file_path}")
    print("   (실제 실행 시에는 이 경로를 실제 VCF 파일 경로로 변경하세요)")
    
    # 실제 파일이 있는 경우 아래 코드의 주석을 해제하고 실행하세요
    """
    vcf_reader = load_vcf_reader(vcf_file_path)
    print(f"VCF 파일 로드 완료: {len(vcf_reader.samples)} 샘플\n")
    
    # 3. GWAS 카탈로그에서 코로나리 심장병 관련 SNP 정보 가져오기
    print("3. GWAS 카탈로그에서 코로나리 심장병 관련 SNP 정보 가져오는 중...")
    efo_id = "EFO_0000378"  # 코로나리 심장병의 EFO ID
    raw_associations = fetch_gwas_associations_by_efo(efo_id, config)
    gwas_data = parse_gwas_association_data(raw_associations, "Coronary Heart Disease")
    print(f"GWAS 데이터 로드 완료: {len(gwas_data)} SNP 정보\n")
    
    # 4. 사용자 VCF에서 GWAS 카탈로그 유래 SNP 필터링
    print("4. 사용자 VCF에서 관련 SNP 추출 중...")
    target_rsids = set(gwas_data['SNP_ID'])
    user_variants = extract_user_variants(vcf_reader, target_rsids)
    print(f"사용자 VCF에서 {len(user_variants)} 개의 관련 SNP 추출 완료\n")
    
    # 5. 데이터 병합 및 처리
    print("5. 데이터 병합 및 처리 중...")
    merged_data = merge_variant_data(user_variants, gwas_data)
    processed_data = apply_ethnicity_standardization(merged_data)
    
    # 6. 결과 필터링 및 정렬
    print("6. 결과 필터링 및 정렬 중...")
    filter_criteria = {
        'max_p_value': 0.05,
        'min_odds_ratio': 1.2,
        'ethnicity': ['European', 'East Asian']
    }
    filtered_data = filter_results_by_criteria(processed_data, filter_criteria)
    sorted_data = sort_results(filtered_data, config)
    print(f"최종 결과: {len(sorted_data)} 개의 SNP\n")
    
    # 7. 결과 저장
    output_file = "coronary_heart_disease_results.tsv"
    print(f"7. 결과 저장 중: {output_file}")
    sorted_data.to_csv(output_file, sep='\t', index=False)
    print(f"결과가 {output_file}에 저장되었습니다.\n")
    """
    
    # 예제 데이터로 결과 시뮬레이션
    print("\n실제 파일 없이 예제 결과 시뮬레이션:")
    example_result = pd.DataFrame({
        'SNP_ID': ['rs123', 'rs456', 'rs789'],
        'CHROM': ['1', '2', '3'],
        'POS': [100, 200, 300],
        'REF': ['A', 'T', 'G'],
        'ALT': ['G', 'C', 'A'],
        'User_Genotype': ['0/1', '1/1', '0/1'],
        'User_Alleles': ['A/G', 'C/C', 'G/A'],
        'P_Value': [0.001, 0.005, 0.02],
        'Odds_Ratio': [1.5, 2.3, 1.2],
        'GWAS_Ethnicity_Processed': ['European', 'East Asian', 'European']
    })
    print(example_result)
    print("\n이 예제는 시뮬레이션입니다. 실제 분석을 위해서는 주석 처리된 코드를 활성화하고 실제 VCF 파일 경로를 제공하세요.")

if __name__ == "__main__":
    main()
