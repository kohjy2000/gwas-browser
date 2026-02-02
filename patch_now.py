#!/usr/bin/env python3
# patch_now.py - data_processor.py를 강제로 패치

import os
import shutil
from datetime import datetime

# 새로운 merge_variant_data 함수 (일부분만 - 실제로는 전체 필요)
NEW_FUNCTION_START = '''def merge_variant_data(user_variants_df: pd.DataFrame, gwas_data_df: pd.DataFrame) -> pd.DataFrame:
    """ENHANCED RELAXED MERGE - Maximum variant matching"""
    logger.info(f"Starting RELAXED merge: {len(user_variants_df)} user × {len(gwas_data_df)} GWAS variants")
    
    if user_variants_df.empty or gwas_data_df.empty:
        logger.warning("Empty dataframe")
        return pd.DataFrame()

    # Chromosome naming
    user_variants_df = user_variants_df.copy()
    user_variants_df['USER_CHROM'] = user_variants_df['USER_CHROM'].str.replace('chr', '', regex=False)
    
    # Position numeric
    user_variants_df['USER_POS'] = pd.to_numeric(user_variants_df['USER_POS'], errors='coerce')
    gwas_data_df['GWAS_POS'] = pd.to_numeric(gwas_data_df['GWAS_POS'], errors='coerce')
    
    user_variants_df = user_variants_df.dropna(subset=['USER_POS'])
    gwas_data_df = gwas_data_df.dropna(subset=['GWAS_POS'])
    
    # GWAS SNP_ID rename
    if 'SNP_ID' in gwas_data_df.columns:
        gwas_data_df = gwas_data_df.rename(columns={'SNP_ID': 'GWAS_SNP_ID'})
    
    all_matches = []
    matched_positions = set()
    
    # ============================================
    # STRATEGY 1: Exact position + alt match
    # ============================================
    logger.info("  Trying Strategy 1: Exact position + alt allele...")
'''

def find_data_processor_files():
    """모든 data_processor.py 파일 찾기"""
    files = []
    for root, dirs, filenames in os.walk('.'):
        if 'data_processor.py' in filenames:
            filepath = os.path.join(root, 'data_processor.py')
            files.append(filepath)
    return files

def check_file_version(filepath):
    """파일 버전 확인"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "Trying Strategy" in content:
        return "NEW"
    elif "=== DEBUG: Pre-merge" in content:
        return "OLD"
    else:
        return "UNKNOWN"

def main():
    print("="*60)
    print("DATA_PROCESSOR.PY DIRECT PATCH")
    print("="*60)
    
    # 1. 모든 data_processor.py 찾기
    files = find_data_processor_files()
    print(f"\nFound {len(files)} data_processor.py files:")
    
    for filepath in files:
        version = check_file_version(filepath)
        print(f"  {filepath}: {version}")
        
        if version == "OLD":
            # 백업
            backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(filepath, backup_path)
            print(f"    → Backed up to {backup_path}")
            
            # 패치 필요 표시
            print(f"    ⚠️  NEEDS PATCH!")
            print(f"    Please manually replace merge_variant_data function")
            print(f"    The function should start with:")
            print(f'    {NEW_FUNCTION_START[:100]}...')
    
    # 2. 실제 import 경로 확인
    print("\n" + "="*60)
    print("CHECKING ACTUAL IMPORT PATH")
    print("="*60)
    
    try:
        import gwas_variant_analyzer.data_processor as dp
        actual_path = dp.__file__
        print(f"Python imports from: {actual_path}")
        version = check_file_version(actual_path)
        print(f"Version: {version}")
        
        if version == "OLD":
            print("\n🚨 THIS IS THE FILE THAT NEEDS TO BE UPDATED!")
            print(f"   Edit this file: {actual_path}")
            print(f"   Replace the merge_variant_data function")
    except ImportError as e:
        print(f"Cannot import: {e}")
    
    # 3. 캐시 삭제 명령
    print("\n" + "="*60)
    print("CLEAR CACHE COMMANDS")
    print("="*60)
    print("Run these commands:")
    print("  1. pkill -f main.py")
    print("  2. find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null")
    print("  3. find . -name '*.pyc' -delete")
    print("  4. python main.py --no-debug")

if __name__ == "__main__":
    main()