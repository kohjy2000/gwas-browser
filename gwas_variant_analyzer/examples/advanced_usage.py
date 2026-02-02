#!/usr/bin/env python3
"""
고급 사용 예제: GWAS Variant Analyzer 패키지의 고급 사용법을 보여줍니다.
이 예제는 여러 질병에 대한 분석을 동시에 수행하고 결과를 비교합니다.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from gwas_variant_analyzer.vcf_parser import load_vcf_reader, extract_user_variants
from gwas_variant_analyzer.gwas_catalog_handler import fetch_gwas_associations_by_efo, parse_gwas_association_data
from gwas_variant_analyzer.data_processor import merge_variant_data, apply_ethnicity_standardization, filter_results_by_criteria, sort_results
from gwas_variant_analyzer.utils import load_app_config, get_efo_id_for_trait

# 작업 디렉토리 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), 'config', 'app_config.yaml')
MAPPING_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), 'config', 'efo_mapping.json')

def analyze_disease(vcf_reader, disease_name, efo_id, config, filter_criteria=None):
    """
    특정 질병에 대한 분석을 수행합니다.
    
    Args:
        vcf_reader: VCF 파일 리더 객체
        disease_name: 질병 이름
        efo_id: 질병의 EFO ID
        config: 애플리케이션 설정
        filter_criteria: 필터링 기준 (기본값: None)
        
    Returns:
        pd.DataFrame: 분석 결과
    """
    print(f"\n{disease_name} 분석 시작 (EFO ID: {efo_id})")
    
    # GWAS 카탈로그에서 질병 관련 SNP 정보 가져오기
    print(f"GWAS 카탈로그에서 {disease_name} 관련 SNP 정보 가져오는 중...")
    raw_associations = fetch_gwas_associations_by_efo(efo_id, config)
    gwas_data = parse_gwas_association_data(raw_associations, disease_name)
    print(f"GWAS 데이터 로드 완료: {len(gwas_data)} SNP 정보")
    
    # 사용자 VCF에서 GWAS 카탈로그 유래 SNP 필터링
    print(f"사용자 VCF에서 {disease_name} 관련 SNP 추출 중...")
    target_rsids = set(gwas_data['SNP_ID'])
    user_variants = extract_user_variants(vcf_reader, target_rsids)
    print(f"사용자 VCF에서 {len(user_variants)} 개의 관련 SNP 추출 완료")
    
    # 데이터 병합 및 처리
    print("데이터 병합 및 처리 중...")
    if len(user_variants) > 0 and len(gwas_data) > 0:
        merged_data = merge_variant_data(user_variants, gwas_data)
        processed_data = apply_ethnicity_standardization(merged_data)
        
        # 결과 필터링 및 정렬
        print("결과 필터링 및 정렬 중...")
        if filter_criteria:
            filtered_data = filter_results_by_criteria(processed_data, filter_criteria)
        else:
            filtered_data = processed_data
            
        sorted_data = sort_results(filtered_data, config)
        print(f"최종 결과: {len(sorted_data)} 개의 SNP")
        return sorted_data
    else:
        print("매칭되는 SNP가 없습니다.")
        return pd.DataFrame()

def visualize_results(results_dict):
    """
    여러 질병의 분석 결과를 시각화합니다.
    
    Args:
        results_dict: 질병 이름을 키로, 분석 결과 DataFrame을 값으로 갖는 딕셔너리
    """
    # 질병별 SNP 수 비교
    diseases = list(results_dict.keys())
    snp_counts = [len(df) for df in results_dict.values()]
    
    plt.figure(figsize=(12, 6))
    plt.bar(diseases, snp_counts)
    plt.title('질병별 관련 SNP 수')
    plt.xlabel('질병')
    plt.ylabel('SNP 수')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('disease_snp_counts.png')
    print("질병별 SNP 수 비교 차트가 'disease_snp_counts.png'에 저장되었습니다.")
    
    # 각 질병별 상위 SNP의 Odds Ratio 비교
    plt.figure(figsize=(14, 8))
    
    for i, (disease, df) in enumerate(results_dict.items()):
        if not df.empty:
            # 상위 5개 SNP 선택
            top_snps = df.head(5)
            plt.subplot(len(results_dict), 1, i+1)
            plt.barh(top_snps['SNP_ID'], top_snps['Odds_Ratio'])
            plt.title(f'{disease} 상위 SNP의 Odds Ratio')
            plt.xlabel('Odds Ratio')
            plt.tight_layout()
    
    plt.savefig('top_snps_odds_ratio.png')
    print("질병별 상위 SNP의 Odds Ratio 비교 차트가 'top_snps_odds_ratio.png'에 저장되었습니다.")

def main():
    """
    고급 분석 워크플로우를 실행합니다.
    """
    print("GWAS Variant Analyzer 고급 사용 예제")
    print("=" * 50)
    
    # 1. 설정 로드
    print("1. 설정 로드 중...")
    config = load_app_config(CONFIG_PATH)
    print(f"설정 로드 완료: {len(config)} 항목\n")
    
    # 2. VCF 파일 로드 (예제용 경로, 실제 파일로 변경 필요)
    vcf_file_path = "/path/to/your/sample.vcf.gz"
    print(f"2. VCF 파일 로드 중: {vcf_file_path}")
    print("   (실제 실행 시에는 이 경로를 실제 VCF 파일 경로로 변경하세요)")
    
    # 분석할 질병 목록
    diseases = [
        ("coronary heart disease", "EFO_0000378"),
        ("type 2 diabetes", "EFO_0001360"),
        ("breast cancer", "EFO_0000305")
    ]
    
    # 필터링 기준 설정
    filter_criteria = {
        'max_p_value': 0.01,
        'min_odds_ratio': 1.5
    }
    
    # 실제 파일이 있는 경우 아래 코드의 주석을 해제하고 실행하세요
    """
    # VCF 파일 로드
    vcf_reader = load_vcf_reader(vcf_file_path)
    print(f"VCF 파일 로드 완료: {len(vcf_reader.samples)} 샘플\n")
    
    # 3. 여러 질병에 대한 분석 수행
    print("3. 여러 질병에 대한 분석 수행 중...")
    results = {}
    
    for disease_name, efo_id in diseases:
        result_df = analyze_disease(vcf_reader, disease_name, efo_id, config, filter_criteria)
        if not result_df.empty:
            results[disease_name] = result_df
            # 결과 저장
            output_file = f"{disease_name.replace(' ', '_')}_results.tsv"
            result_df.to_csv(output_file, sep='\t', index=False)
            print(f"결과가 {output_file}에 저장되었습니다.")
    
    # 4. 결과 시각화
    if results:
        print("\n4. 결과 시각화 중...")
        visualize_results(results)
    else:
        print("\n분석 결과가 없습니다.")
    """
    
    # 예제 데이터로 결과 시뮬레이션
    print("\n실제 파일 없이 예제 결과 시뮬레이션:")
    
    # 예제 결과 데이터
    example_results = {}
    
    # 코로나리 심장병 예제 결과
    example_results["coronary heart disease"] = pd.DataFrame({
        'SNP_ID': ['rs123', 'rs456', 'rs789', 'rs012', 'rs345'],
        'CHROM': ['1', '2', '3', '4', '5'],
        'POS': [100, 200, 300, 400, 500],
        'P_Value': [0.001, 0.005, 0.008, 0.009, 0.01],
        'Odds_Ratio': [2.5, 2.3, 2.0, 1.8, 1.7],
        'GWAS_Ethnicity_Processed': ['European'] * 5
    })
    
    # 제2형 당뇨병 예제 결과
    example_results["type 2 diabetes"] = pd.DataFrame({
        'SNP_ID': ['rs222', 'rs333', 'rs444', 'rs555', 'rs666'],
        'CHROM': ['2', '3', '4', '5', '6'],
        'POS': [200, 300, 400, 500, 600],
        'P_Value': [0.002, 0.003, 0.005, 0.007, 0.009],
        'Odds_Ratio': [3.0, 2.8, 2.5, 2.2, 1.9],
        'GWAS_Ethnicity_Processed': ['East Asian'] * 5
    })
    
    # 유방암 예제 결과
    example_results["breast cancer"] = pd.DataFrame({
        'SNP_ID': ['rs777', 'rs888', 'rs999'],
        'CHROM': ['7', '8', '9'],
        'POS': [700, 800, 900],
        'P_Value': [0.001, 0.004, 0.008],
        'Odds_Ratio': [3.5, 2.9, 2.1],
        'GWAS_Ethnicity_Processed': ['European'] * 3
    })
    
    # 각 질병별 결과 출력
    for disease, df in example_results.items():
        print(f"\n{disease} 분석 결과 (상위 5개 SNP):")
        print(df)
    
    print("\n이 예제는 시뮬레이션입니다. 실제 분석을 위해서는 주석 처리된 코드를 활성화하고 실제 VCF 파일 경로를 제공하세요.")

if __name__ == "__main__":
    main()
