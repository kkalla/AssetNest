# AssetNest: 효율적인 자산관리를 위한 대쉬보드 앱

## 목표

- 투자 현황을 쉽게 파악할 수 있도록 대쉬보드 앱을 만든다.
- 투자 정보를 정확하게 업데이트한다.

## 컨텍스트

- DB는 supabase를 사용한다.
- 앱을 위한 API는 FastAPI를 사용한다.
- 대쉬보드는 Streamlit을 사용한다.
- supabase에는 주식별 최신 정보, 환율 정보, 계좌별 주식 보유 정보가 있음

## 기술적 참고사항

- **SQL 쿼리**: 문자열 리터럴에는 작은따옴표(`'`)를 사용해야 합니다. 큰따옴표(`"`)는 사용하지 않습니다.
- **뷰 컬럼명 변경**: `CREATE OR REPLACE VIEW` 구문으로는 뷰의 컬럼명을 변경할 수 없습니다. 컬럼명을 변경해야 할 경우, `DROP VIEW`로 기존 뷰를 삭제한 후 `CREATE VIEW`로 다시 생성해야 합니다.

## 시스템 아키텍처 설계

### 전체 구조 (3계층 아키텍처)

```
Data Layer (데이터 계층)
├── Supabase Database
│   ├── stock_info (주식 기본 정보)
│   ├── by_accounts (계좌별 보유 현황)
│   ├── profit_timeseries (손익 이력)
│   ├── currency (환율 정보)
│   └── overall_info (통합 뷰)
└── External Data Sources
    ├── FinanceDataReader (국내 주식)
    ├── yfinance (해외 주식)
    └── Alpha Vantage (해외 주식)

Application Layer (애플리케이션 계층)
├── FastAPI Server (api/)
│   ├── main.py (메인 서버)
│   ├── models.py (데이터 모델)
│   ├── database.py (DB 매니저)
│   └── __init__.py
├── Data Update Service
│   └── update_stock_info.py (가격 업데이트)
└── Utilities
    └── write_excel.py (엑셀 내보내기)

Presentation Layer (프레젠테이션 계층)
└── Streamlit Dashboard (dashboard/)
    └── main.py (대쉬보드 UI)
```

### API 엔드포인트 설계

**Portfolio API**

- `GET /api/v1/portfolio/overview` - 포트폴리오 전체 현황
- `GET /api/v1/portfolio/summary/{account}` - 계좌별 요약

**Holdings API**

- `GET /api/v1/holdings/` - 모든 보유 종목
- `GET /api/v1/holdings/{account}` - 계좌별 보유 종목
- `PUT /api/v1/holdings/{account}/{company}` - 보유 정보 수정

**Stocks API**

- `GET /api/v1/stocks/` - 모든 주식 정보
- `GET /api/v1/stocks/{symbol}` - 특정 주식 정보
- `POST /api/v1/stocks/refresh-prices` - 가격 새로고침

**Analytics API**

- `GET /api/v1/analytics/performance/{account}` - 성과 분석
- `GET /api/v1/analytics/sector-allocation/{account}` - 섹터 배분
- `GET /api/v1/analytics/region-allocation/{account}` - 지역 배분

**Currency API**

- `GET /api/v1/currency/rates` - 환율 정보
- `POST /api/v1/currency/refresh` - 환율 새로고침

### 대쉬보드 컴포넌트 설계

**메인 레이아웃**

- 사이드바: 계정 선택, 필터링, 데이터 관리
- 메인 영역: 4개 탭 (포트폴리오 개요, 보유 종목, 성과 분석, 설정)

**포트폴리오 개요 탭**

- 상단 메트릭 카드: 총 자산, 수익률, 평가손익, USD 자산
- 계좌별/지역별 자산 분배 차트
- TOP 보유 종목 테이블

**보유 종목 탭**

- 요약 정보: 보유 종목 수, 총 평가금액, 총 평가손익
- 상세 필터: 평가금액, 수익률 범위
- 인터랙티브 데이터 테이블 (정렬, 검색)

**성과 분석 탭** (Phase 3)

- 수익률 추이 차트
- 섹터별 분석
- 리스크 지표

**설정 탭**

- 환율 정보 표시
- 데이터 새로고침 버튼
- 시스템 상태 확인

### 데이터베이스 스키마 (기존 + 확장)

**기존 테이블**

- `stock_info`: 주식 기본 정보 (종목명, 심볼, 거래소, 섹터 등)
- `by_accounts`: 계좌별 보유 현황 (수량, 평균단가, 매수/매도일 등)
- `profit_timeseries`: 손익 이력 (실현손익 기록)
- `currency`: 환율 정보 (USD, EUR 등)
- `overall_info`: 통합 뷰 (포트폴리오 전체 현황)
- `symbol_table`: 종목 심볼 정보
  - `name` (종목명)
  - `symbol` (심볼/티커)
  - `exchange` (거래소: KOSPI, KOSDAQ, US 등)
  - `sector` (섹터)
  - `industry` (산업)
  - `asset_type` (자산유형: equity, bond, reit, commodity, gold, cash)
  - `region_type` (지역유형: domestic, global)
  - `latest_close` (최신 종가)
  - `marketcap` (시가총액, 십억 단위)
  - `updated_at` (업데이트 시간)

**확장 제안 테이블**

- `transactions`: 거래 이력 (매수/매도 세부 기록)
- `portfolio_snapshots`: 포트폴리오 스냅샷 (일별 자산 변화)

### 실행 방법

**1. 패키지 설치**

```bash
pip install -r requirements.txt
```

**2. 환경변수 설정** (.env 파일)

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

**3. API 서버 시작**

```bash
python start_api.py
# API 문서: http://localhost:8000/docs
```

**4. 대쉬보드 시작**

```bash
python start_dashboard.py
# 대쉬보드: http://localhost:8501
```

### 구현 단계

**Phase 1 ✅**: FastAPI 서버 기본 구조

- 기본 API 엔드포인트 구현
- Supabase 연동
- 데이터 모델 정의

**Phase 2 ✅**: Streamlit 대쉬보드

- 포트폴리오 개요 탭
- 보유 종목 탭
- 기본 차트 및 메트릭

**Phase 3** (향후 계획): 고급 분석 기능

- 성과 분석 차트
- 섹터별 분석
- 리스크 지표

**Phase 4** (향후 계획): 실시간 업데이트

- 스케줄링 기능
- 알림 시스템
- 자동화된 데이터 업데이트
