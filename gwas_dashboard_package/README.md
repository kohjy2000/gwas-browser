# GWAS Variant Analyzer 웹 대시보드

GWAS Variant Analyzer 패키지를 위한 인터랙티브 웹 기반 대시보드 애플리케이션입니다. 이 대시보드를 통해 사용자는 VCF 파일을 업로드하고, GWAS Catalog 데이터와 비교 분석하여 질병/형질 관련 SNP를 시각적으로 탐색할 수 있습니다.

## 주요 기능

1. **VCF 파일 업로드 및 처리**
   - VCF 또는 VCF.gz 형식 파일 지원
   - 대용량 파일 처리 가능

2. **GWAS 분석 파라미터 설정**
   - 질병/형질 선택 또는 EFO ID 직접 입력
   - P-value, Odds Ratio 임계값 조정
   - 인종별 필터링 옵션

3. **인터랙티브 시각화**
   - 맨해튼 플롯(Manhattan Plot): 염색체 위치에 따른 SNP의 유의성 시각화
   - Odds Ratio 차트: 상위 SNP의 Odds Ratio 비교
   - 인종 분포 파이 차트: 결과의 인종별 분포 시각화

4. **결과 테이블 및 다운로드**
   - 상세 변이 정보를 테이블로 제공
   - TSV 또는 JSON 형식으로 결과 다운로드
   - 시각화 그래프 PNG 이미지로 저장

## 설치 및 실행 방법

### 요구 사항

- Python 3.8 이상
- Flask 및 관련 패키지
- GWAS Variant Analyzer 패키지

### 설치 단계

1. 저장소 클론:
   ```bash
   git clone https://github.com/example/gwas_dashboard.git
   cd gwas_dashboard
   ```

2. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   venv\Scripts\activate  # Windows
   ```

3. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

4. GWAS Variant Analyzer 패키지 설치:
   ```bash
   pip install -e /path/to/gwas_variant_analyzer
   ```

### 실행 방법

개발 서버 실행:
```bash
python src/main.py
```

웹 브라우저에서 다음 주소로 접속:
```
http://localhost:5000
```

## 사용 가이드

### 1. VCF 파일 업로드

1. 첫 번째 탭에서 "Select VCF File" 버튼을 클릭하여 VCF 파일(.vcf 또는 .vcf.gz)을 선택합니다.
2. "Upload and Process" 버튼을 클릭하여 파일을 업로드합니다.
3. 파일이 성공적으로 처리되면 "Analyze" 탭이 활성화됩니다.

### 2. 분석 실행

1. "Analyze" 탭에서 드롭다운 메뉴를 통해 질병/형질을 선택하거나 EFO ID를 직접 입력합니다.
2. 슬라이더를 사용하여 P-value와 Odds Ratio 임계값을 조정합니다.
3. 필요에 따라 인종 필터를 선택합니다.
4. "Run Analysis" 버튼을 클릭하여 분석을 실행합니다.

### 3. 결과 탐색

1. 분석이 완료되면 세 가지 인터랙티브 시각화가 표시됩니다:
   - Manhattan Plot: 각 점은 SNP를 나타내며, 점을 마우스 오버하면 세부 정보가 표시됩니다.
   - Odds Ratio Chart: 상위 SNP의 Odds Ratio를 비교합니다.
   - Ethnicity Chart: 결과의 인종별 분포를 보여줍니다.
2. 각 시각화는 확대/축소, 이동, 데이터 선택 등의 인터랙티브 기능을 제공합니다.
3. 결과 테이블에서 모든 변이 정보를 확인할 수 있습니다.

### 4. 결과 다운로드

1. "Download Results (TSV)" 또는 "Download Results (JSON)" 버튼을 클릭하여 분석 결과를 다운로드합니다.
2. 각 시각화 그래프 아래의 "Download Plot" 버튼을 클릭하여 PNG 이미지로 저장할 수 있습니다.

## 프로덕션 배포

프로덕션 환경에 배포하려면 다음 단계를 따르세요:

1. `debug=True` 옵션을 제거하고 적절한 로깅 설정을 추가합니다.
2. Gunicorn 또는 uWSGI와 같은 WSGI 서버를 사용합니다:
   ```bash
   pip install gunicorn
   gunicorn --bind 0.0.0.0:5000 src.main:app
   ```
3. Nginx와 같은 웹 서버를 프록시로 설정하여 정적 파일 서빙 및 보안을 강화합니다.

## 기술 스택

- **백엔드**: Flask (Python)
- **프론트엔드**: HTML, CSS, JavaScript
- **시각화**: Plotly.js
- **데이터 처리**: GWAS Variant Analyzer 패키지, Pandas

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 문의 및 기여

버그 신고, 기능 요청 또는 기여는 GitHub 이슈 트래커를 통해 제출해 주세요.
