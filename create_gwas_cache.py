#!/usr/bin/env python3
# 📁 create_gwas_cache.py
# 모든 질병의 GWAS 데이터를 미리 다운로드하는 스크립트

"""
GWAS Cache Builder - Fixed Version
미리 정의된 모든 질병의 GWAS 데이터를 다운로드하고 캐시에 저장
사용법: python create_gwas_cache.py
"""

import sys
import os
import time
import logging
from datetime import datetime

# 현재 폴더 구조에 맞게 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))

# gwas_variant_analyzer 경로 추가 (중복 폴더 구조 대응)
if os.path.exists(os.path.join(current_dir, 'gwas_variant_analyzer', 'gwas_variant_analyzer')):
    # 중복 폴더 구조인 경우
    sys.path.insert(0, os.path.join(current_dir, 'gwas_variant_analyzer'))
    print(f"Using nested structure: {os.path.join(current_dir, 'gwas_variant_analyzer')}")
else:
    # 일반 구조인 경우
    sys.path.insert(0, current_dir)
    print(f"Using flat structure: {current_dir}")

from gwas_variant_analyzer.utils import load_app_config
from gwas_variant_analyzer.gwas_catalog_handler import (
    fetch_gwas_associations_by_efo, 
    parse_gwas_association_data,
    save_gwas_data_to_cache
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gwas_cache_builder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 캐시할 질병 목록 (당신의 질병 목록)
DISEASES_TO_CACHE = {
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
    "prostate cancer": "EFO_0001663",
    "colorectal cancer": "MONDO_0005575",
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

def find_config_file():
    """config 파일을 여러 경로에서 찾기"""
    possible_paths = [
        'config/app_config.yaml',
        'gwas_dashboard_package/config/app_config.yaml',
        'gwas_variant_analyzer/config/app_config.yaml',
        '../gwas_dashboard_package/config/app_config.yaml',
        os.path.join(current_dir, 'gwas_dashboard_package', 'config', 'app_config.yaml'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found config file at: {path}")
            return path
    
    # 못 찾으면 파일 리스트 출력
    print("\n⚠️  Config file not found. Searching for yaml files...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'app_config.yaml':
                full_path = os.path.join(root, file)
                print(f"  Found: {full_path}")
                return full_path
    
    return None

def build_cache_for_disease(trait_name: str, efo_id: str, config: dict) -> dict:
    """
    특정 질병의 GWAS 데이터를 다운로드하고 캐시에 저장
    """
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {trait_name} ({efo_id})")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        # GWAS 데이터 fetch (개선된 함수 사용)
        logger.info(f"Fetching GWAS associations from API...")
        raw_associations = fetch_gwas_associations_by_efo(efo_id, config)
        
        if not raw_associations:
            logger.warning(f"No associations found for {trait_name}")
            return {
                'trait': trait_name,
                'efo_id': efo_id,
                'status': 'no_data',
                'associations': 0,
                'raw_count': 0,
                'time': 0
            }
        
        logger.info(f"Found {len(raw_associations)} raw associations")
        
        # Parse and process
        logger.info(f"Parsing association data...")
        gwas_data = parse_gwas_association_data(raw_associations, trait_name, config)
        
        if gwas_data.empty:
            logger.warning(f"Failed to parse data for {trait_name}")
            return {
                'trait': trait_name,
                'efo_id': efo_id,
                'status': 'parse_failed',
                'associations': 0,
                'raw_count': len(raw_associations),
                'time': time.time() - start_time
            }
        
        # Save to cache
        logger.info(f"Saving {len(gwas_data)} parsed variants to cache...")
        save_gwas_data_to_cache(gwas_data, efo_id, config)
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"✅ Successfully cached {len(gwas_data)} variants for {trait_name}")
        logger.info(f"   Raw associations: {len(raw_associations)}")
        logger.info(f"   Parsed variants: {len(gwas_data)}")
        logger.info(f"   Success rate: {len(gwas_data)/len(raw_associations)*100:.1f}%")
        logger.info(f"   Time taken: {elapsed_time:.1f} seconds")
        
        return {
            'trait': trait_name,
            'efo_id': efo_id,
            'status': 'success',
            'associations': len(gwas_data),
            'raw_count': len(raw_associations),
            'time': elapsed_time
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing {trait_name}: {str(e)}", exc_info=True)
        return {
            'trait': trait_name,
            'efo_id': efo_id,
            'status': 'error',
            'error': str(e),
            'time': time.time() - start_time
        }

def main():
    """
    모든 질병에 대한 GWAS 캐시 구축
    """
    print("\n" + "="*70)
    print(" GWAS DATA PRE-CACHING TOOL v2.0")
    print("="*70)
    
    # Config 파일 찾기
    config_path = find_config_file()
    if not config_path:
        print("\n❌ ERROR: Could not find app_config.yaml")
        print("\nPlease ensure app_config.yaml exists in one of these locations:")
        print("  - ./config/")
        print("  - ./gwas_dashboard_package/config/")
        print("  - ./gwas_variant_analyzer/config/")
        sys.exit(1)
    
    print(f"\n✓ Using config: {config_path}")
    config = load_app_config(config_path)
    
    # 캐시 디렉토리 생성
    cache_dir = config.get('gwas_cache_directory', 'data/gwas_cache')
    if not os.path.isabs(cache_dir):
        # 상대 경로인 경우 현재 디렉토리 기준으로 생성
        cache_dir = os.path.join(current_dir, cache_dir)
    
    os.makedirs(cache_dir, exist_ok=True)
    logger.info(f"Cache directory: {cache_dir}")
    
    # 이미 캐시된 파일 확인
    existing_cache = set()
    if os.path.exists(cache_dir):
        existing_cache = {f.replace('.parquet', '') for f in os.listdir(cache_dir) if f.endswith('.parquet')}
    
    if existing_cache:
        print(f"\n📂 Found {len(existing_cache)} existing cache files")
        overwrite = input("Do you want to overwrite existing cache? (y/n): ")
        if overwrite.lower() != 'y':
            # Skip already cached
            to_process = {k: v for k, v in DISEASES_TO_CACHE.items() 
                         if v.split('|')[0] not in existing_cache}
            if not to_process:
                print("All diseases already cached! Nothing to do.")
                return
            DISEASES_TO_CACHE.clear()
            DISEASES_TO_CACHE.update(to_process)
    
    # 처리할 질병 수
    total_diseases = len(DISEASES_TO_CACHE)
    print(f"\n📋 Will cache data for {total_diseases} diseases")
    print(f"⏱️  Estimated time: {total_diseases * 15}-{total_diseases * 30} seconds")
    
    # 사용자 확인
    response = input("\n🤔 Do you want to proceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # 시작 시간
    overall_start = time.time()
    results = []
    
    # 각 질병 처리
    for idx, (trait_name, efo_id) in enumerate(DISEASES_TO_CACHE.items(), 1):
        print(f"\n[{idx}/{total_diseases}] Processing {trait_name}...")
        
        # Multiple EFO IDs 처리
        if '|' in efo_id:
            efo_id = efo_id.split('|')[0]
            logger.info(f"Multiple EFO IDs detected, using first: {efo_id}")
        
        result = build_cache_for_disease(trait_name, efo_id, config)
        results.append(result)
        
        # Progress bar
        progress = idx / total_diseases * 100
        bar = '█' * int(progress/5) + '░' * (20 - int(progress/5))
        print(f"Progress: [{bar}] {progress:.1f}%")
        
        # Rate limiting
        if idx < total_diseases:
            time.sleep(1)  # API 부담 줄이기
    
    # 결과 요약
    overall_time = time.time() - overall_start
    
    print("\n" + "="*70)
    print(" CACHING COMPLETE")
    print("="*70)
    
    # 통계
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    total_variants = sum(r.get('associations', 0) for r in successful)
    total_raw = sum(r.get('raw_count', 0) for r in successful)
    
    print(f"\n📊 Summary:")
    print(f"  • Total diseases: {total_diseases}")
    print(f"  • Successful: {len(successful)}")
    print(f"  • Failed: {len(failed)}")
    print(f"  • Total raw associations: {total_raw:,}")
    print(f"  • Total parsed variants: {total_variants:,}")
    print(f"  • Parse success rate: {total_variants/max(total_raw,1)*100:.1f}%")
    print(f"  • Total time: {overall_time:.1f} seconds ({overall_time/60:.1f} minutes)")
    print(f"  • Average time per disease: {overall_time/total_diseases:.1f} seconds")
    
    # 성공한 질병 목록
    if successful:
        print(f"\n✅ Successfully cached:")
        for r in sorted(successful, key=lambda x: x['associations'], reverse=True)[:10]:
            success_rate = r['associations']/r.get('raw_count', 1)*100
            print(f"  • {r['trait']:25s}: {r['associations']:5,} variants (from {r.get('raw_count', 0):5,} raw, {success_rate:5.1f}% parsed)")
    
    # 실패한 질병 목록
    if failed:
        print(f"\n❌ Failed to cache:")
        for r in failed:
            error_msg = r.get('error', r['status'])
            print(f"  • {r['trait']}: {error_msg}")
    
    # 캐시 파일 크기
    cache_size = 0
    cache_files = []
    for filename in os.listdir(cache_dir):
        if filename.endswith('.parquet'):
            filepath = os.path.join(cache_dir, filename)
            size = os.path.getsize(filepath)
            cache_size += size
            cache_files.append((filename, size))
    
    print(f"\n💾 Cache storage:")
    print(f"  • Files created: {len(cache_files)}")
    print(f"  • Total size: {cache_size/1024/1024:.1f} MB")
    print(f"  • Average size: {cache_size/1024/1024/len(cache_files):.1f} MB per file")
    print(f"  • Location: {os.path.abspath(cache_dir)}")
    
    # 가장 큰 파일들
    if cache_files:
        print(f"\n📦 Largest cache files:")
        for filename, size in sorted(cache_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {filename}: {size/1024/1024:.1f} MB")
    
    # 다음 단계 안내
    print(f"\n🎯 Next steps:")
    print(f"  1. Cache is ready! Start your Flask app:")
    print(f"     cd gwas_dashboard_package/src && python main.py")
    print(f"  2. Cached data will be used automatically")
    print(f"  3. To refresh cache, run this script again")
    print(f"  4. To clear cache: rm -rf {cache_dir}/*.parquet")
    
    # 로그 파일 안내
    print(f"\n📄 Detailed log saved to: gwas_cache_builder.log")
    
    # Test import 확인
    print(f"\n🔍 Quick verification:")
    try:
        test_file = os.path.join(cache_dir, f"{DISEASES_TO_CACHE['obesity'].split('|')[0]}.parquet")
        if os.path.exists(test_file):
            import pandas as pd
            test_df = pd.read_parquet(test_file)
            print(f"  ✓ Test load successful: obesity cache has {len(test_df)} variants")
        else:
            print(f"  ⚠️  Could not verify cache files")
    except Exception as e:
        print(f"  ❌ Verification failed: {e}")

if __name__ == '__main__':
    main()