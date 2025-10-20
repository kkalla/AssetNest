# AssetNest API 테스트 가이드

AssetNest 자산관리 대쉬보드 API를 위한 종합적인 테스트 스위트입니다.

## 📋 목차

- [테스트 구조](#테스트-구조)
- [설정 방법](#설정-방법)
- [테스트 실행](#테스트-실행)
- [테스트 커버리지](#테스트-커버리지)
- [테스트 종류](#테스트-종류)
- [모킹 전략](#모킹-전략)
- [문제 해결](#문제-해결)

## 🏗️ 테스트 구조

```
tests/
├── __init__.py                 # 테스트 패키지 초기화
├── test_portfolio_api.py       # 포트폴리오 API 테스트
├── test_holdings_api.py        # 보유 종목 API 테스트
├── test_stocks_api.py          # 주식 정보 API 테스트
├── test_analytics_currency_api.py  # 성과 분석 및 환율 API 테스트
└── test_cash_management_api.py    # 현금 관리 API 테스트
```

### 주요 파일 설명

- **`conftest.py`**: 공통 fixture와 테스트 설정
- **`pytest.ini`**: pytest 설정 파일
- **`test-requirements.txt`**: 테스트 의존성 패키지

## ⚙️ 설정 방법

### 1. 의존성 설치

```bash
pip install -r test-requirements.txt
```

### 2. 환경변수 설정

테스트 실행을 위해 필요한 환경변수:

```bash
# .env 파일
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

### 3. 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_portfolio_api.py

# 특정 테스트 클래스 실행
pytest tests/test_portfolio_api.py::TestPortfolioAPI

# 특정 테스트 메서드 실행
pytest tests/test_portfolio_api.py::TestPortfolioAPI::test_get_portfolio_overview_success

# 마커로 테스트 필터링
pytest -m api
pytest -m performance
pytest -m validation
```

## 🧪 테스트 실행 옵션

### 기본 실행 옵션

```bash
# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=api --cov-report=html

# 실패한 테스트만 다시 실행
pytest --lf

# 실행 시간별 정렬
pytest --durations=10

# 병렬 실행
pytest -n auto
```

### CI/CD 환경에서의 실행

```bash
# 헤드리스 모드
pytest --tb=short --no-header

# JUnit XML 리포트 생성
pytest --junitxml=test-results.xml
```

## 📊 테스트 커버리지

### 커버리지 확인

```bash
# 전체 커버리지 확인
pytest --cov=api --cov-report=term-missing

# HTML 리포트 생성
pytest --cov=api --cov-report=html

# 커버리지 타겟 설정
pytest --cov=api --cov-fail-under=80
```

### 커버리지 기준

- **목표**: 80% 이상의 코드 커버리지
- **필수**: 모든 API 엔드포인트 테스트
- **권장**: 에러 케이스 및 엣지 케이스 포함

## 🎯 테스트 종류

### 1. 단위 테스트 (Unit Tests)

- 개별 함수/메서드 테스트
- 모의 데이터 사용
- 빠른 실행 속도

### 2. API 테스트 (Integration Tests)

- 전체 API 엔드포인트 테스트
- 데이터 흐름 검증
- 응답 구조 확인

### 3. 성능 테스트 (Performance Tests)

- 응답 시간 측정
- 동시 요청 처리
- 대용량 데이터 처리

### 4. 검증 테스트 (Validation Tests)

- 입력값 검증
- 데이터 타입 확인
- 에러 처리 검증

## 🎭 모킹 전략

### 데이터베이스 모킹

```python
# 실제 DB 연결을 피하기 위한 모킹
with patch('api.main.db') as mock_db:
    mock_db.get_portfolio_overview = AsyncMock(return_value=sample_data)
```

### 샘플 데이터 Fixtures

```python
@pytest.fixture
def sample_portfolio_overview():
    return {
        "total_value_krw": 100000000,
        "total_value_usd": 75000,
        # ... 더 많은 데이터
    }
```

### 외부 API 모킹

```python
# Alpha Vantage API 모킹
with patch('alpha_vantage.timeseries.TimeSeries.get_intraday') as mock_api:
    mock_api.return_value = {"mock": "data"}
```

## 🔧 테스트 패턴

### 성공 케이스 테스트

```python
async def test_get_portfolio_overview_success(self, test_client, sample_portfolio_overview):
    with patch('api.main.db') as mock_db:
        mock_db.get_portfolio_overview = AsyncMock(return_value=sample_portfolio_overview)

        response = await test_client.get("/api/v1/portfolio/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_value_krw"] == 100000000
```

### 에러 케이스 테스트

```python
async def test_get_portfolio_overview_database_error(self, test_client):
    with patch('api.main.db') as mock_db:
        mock_db.get_portfolio_overview = AsyncMock(side_effect=Exception("DB Error"))

        response = await test_client.get("/api/v1/portfolio/overview")

        assert response.status_code == 500
```

### 성능 테스트

```python
async def test_concurrent_requests(self, test_client):
    import asyncio

    tasks = [test_client.get("/api/v1/portfolio/overview") for _ in range(5)]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 200
```

## 🚨 문제 해결

### 일반적인 문제

1. **모듈 임포트 에러**

   ```bash
   # Python 경로 확인
   python -c "import sys; print(sys.path)"

   # PYTHONPATH 설정
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **비동기 테스트 에러**

   ```bash
   # asyncio 모드 확인
   pytest --asyncio-mode=auto
   ```

3. **데이터베이스 연결 에러**
   - 환경변수 확인
   - Mock이 올바르게 설정되었는지 확인

### 디버깅 팁

```bash
# 특정 테스트 디버깅
pytest -s -vv tests/test_portfolio_api.py::TestPortfolioAPI::test_get_portfolio_overview_success

# 실패 지점에서 PDB 시작
pytest --pdb

# 모든 테스트 실행 중 디버깅
pytest --pdb -x
```

## 📈 테스트 리포트

### 리포트 생성

```bash
# HTML 리포트
pytest --html=test-report.html --self-contained-html

# JSON 리포트
pytest --json-report --json-report-file=test-report.json
```

### 커버리지 리포트

```bash
# HTML 커버리지 리포트
pytest --cov=api --cov-report=html
open htmlcov/index.html
```

## 🔄 CI/CD 통합

### GitHub Actions 예시

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test-requirements.txt
      - name: Run tests
        run: pytest --cov=api --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📝 테스트 작성 가이드

### 새 테스트 추가 시

1. **테스트 명명**: `test_[기능]_[시나리오]`
2. **AAA 패턴**: Arrange, Act, Assert
3. **Descriptive 설명**: 명확한 테스트 설명
4. **독립성**: 각 테스트는 독립적으로 실행
5. **재사용성**: Fixture 활용

### 예시

```python
async def test_create_deposit_missing_required_field(self, test_client):
    """필수 필드 누락 시 예적금 생성 실패 테스트"""
    # Arrange - 필수 필드 누락된 데이터
    invalid_data = {"account": "증권사A"}

    # Act - API 호출
    response = await test_client.post("/api/v1/cash/deposits/", json=invalid_data)

    # Assert - 결과 확인
    assert response.status_code == 422
```

## 🎯 품질 기준

- ✅ 모든 API 엔드포인트 테스트 커버리지
- ✅ 성공, 실패, 엣지 케이스 포함
- ✅ 최소 80% 코드 커버리지
- ✅ 명확한 테스트 설명
- ✅ 재사용 가능한 Fixture 활용
- ✅ 성능 기준 준수 (응답 시간 < 2초)

---

이 테스트 스위트는 AssetNest API의 안정성과 신뢰성을 보장하기 위해 지속적으로 개선될 것입니다.
