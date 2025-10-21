"""
AssetNest API 메인 테스트 스위트
실제 API 엔드포인트들의 동작을 검증합니다.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app
from datetime import datetime


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def sample_portfolio_overview():
    """샘플 포트폴리오 개요 데이터"""
    return {
        "total_value_krw": 100000000,
        "total_value_usd": 75000,
        "total_pnl_krw": 5000000,
        "total_pnl_usd": 3750,
        "total_return_rate": 0.0526,
        "accounts": ["증권사A", "증권사B"],
        "cash_asset_value": 20000000,
        "investment_asset_value": 80000000,
        "cash_asset_ratio": 20.0,
        "investment_asset_ratio": 80.0,
        "investment_allocations": [],
        "last_updated": datetime(2025, 1, 20, 10, 0, 0),
    }


@pytest.fixture
def sample_holdings():
    """샘플 보유 종목 데이터"""
    return [
        {
            "id": 1,
            "account": "증권사A",
            "company": "삼성전자",
            "market": "국내",
            "area": None,
            "amount": 100,
            "avg_price_krw": 70000,
            "current_price_krw": 75000,
            "principal": 7000000,
            "market_value": 7500000,
            "unrealized_pnl": 500000,
            "return_rate": 0.0714,
            "avg_price_usd": None,
            "current_price_usd": None,
            "principal_usd": None,
            "market_value_usd": None,
            "unrealized_pnl_usd": None,
            "return_rate_usd": None,
            "first_buy_at": None,
            "last_buy_at": None,
            "last_sell_at": None,
            "total_realized_pnl": None,
        }
    ]


@pytest.fixture
def sample_stock_info():
    """샘플 주식 정보 데이터"""
    return [
        {
            "name": "삼성전자",
            "symbol": "005930",
            "exchange": "KOSPI",
            "sector": "전자",
            "industry": "반도체",
            "asset_type": "equity",
            "region_type": "domestic",
            "latest_close": 75000,
            "marketcap": 4500000,
            "updated_at": datetime(2025, 1, 20, 10, 0, 0),
        }
    ]


@pytest.fixture
def sample_currency_rates():
    """샘플 환율 데이터"""
    return [
        {
            "currency": "USD",
            "rate": 1385.0,
            "timestamp": datetime(2025, 1, 20, 10, 0, 0),
        },
        {
            "currency": "EUR",
            "rate": 1500.0,
            "timestamp": datetime(2025, 1, 20, 10, 0, 0),
        },
    ]


class TestPortfolioAPI:
    """포트폴리오 API 테스트"""

    def test_get_portfolio_overview_success(self, client, sample_portfolio_overview):
        """포트폴리오 개요 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            response = client.get("/api/v1/portfolio/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["total_value_krw"] == 100000000
            assert data["total_value_usd"] == 75000
            assert data["total_return_rate"] == 0.0526
            assert len(data["accounts"]) == 2
            mock_db.get_portfolio_overview.assert_called_once_with(None)

    def test_get_portfolio_overview_with_account(
        self, client, sample_portfolio_overview
    ):
        """특정 계좌 포트폴리오 개요 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            response = client.get("/api/v1/portfolio/overview?account=증권사A")

            assert response.status_code == 200
            mock_db.get_portfolio_overview.assert_called_once_with("증권사A")

    def test_get_portfolio_overview_database_error(self, client):
        """포트폴리오 개요 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = client.get("/api/v1/portfolio/overview")

            assert response.status_code == 500
            data = response.json()
            assert "데이터 조회 중 오류가 발생했습니다" in data["detail"]


class TestHoldingsAPI:
    """보유 종목 API 테스트"""

    def test_get_all_holdings_success(self, client, sample_holdings):
        """모든 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=sample_holdings)

            response = client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["company"] == "삼성전자"
            mock_db.get_holdings.assert_called_once_with(None, None)

    def test_get_holdings_by_account_success(self, client, sample_holdings):
        """특정 계좌 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=sample_holdings)

            response = client.get("/api/v1/holdings/증권사A")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            mock_db.get_holdings.assert_called_once_with(account="증권사A")

    def test_get_holdings_by_account_not_found(self, client):
        """존재하지 않는 계좌 보유 종목 조회 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=[])

            response = client.get("/api/v1/holdings/존재하지않는계좌")

            assert response.status_code == 404
            data = response.json()
            assert "존재하지않는계좌'의 보유 종목을 찾을 수 없습니다" in data["detail"]


class TestStocksAPI:
    """주식 정보 API 테스트"""

    def test_get_all_stocks_success(self, client, sample_stock_info):
        """모든 주식 정보 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=sample_stock_info)

            response = client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "삼성전자"
            mock_db.get_all_stocks.assert_called_once()

    def test_refresh_stock_prices_success(self, client):
        """주식 가격 새로고침 성공 테스트"""
        update_result = {
            "success_count": 8,
            "fail_count": 1,
            "skip_count": 1,
            "total_count": 10,
            "failed_stocks": ["알수없는주식"],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=update_result)

            response = client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 8
            assert data["fail_count"] == 1
            assert data["total_count"] == 10
            assert "timestamp" in data
            mock_db.update_symbol_table_prices.assert_called_once()

    def test_get_all_stocks_empty_result(self, client):
        """주식 정보 없음 (빈 결과) 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=[])

            response = client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0


class TestCurrencyAPI:
    """환율 API 테스트"""

    def test_get_currency_rates_success(self, client, sample_currency_rates):
        """환율 정보 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=sample_currency_rates)

            response = client.get("/api/v1/currency/rates")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["currency"] == "USD"
            assert data[0]["rate"] == 1385.0
            mock_db.get_currency_rates.assert_called_once_with(auto_update=True)

    def test_refresh_currency_rates_success(self, client):
        """환율 정보 새로고침 성공 테스트"""
        updated_rates = [
            {
                "currency": "USD",
                "rate": 1390.0,
                "timestamp": datetime(2025, 1, 20, 10, 0, 0),
            },
            {
                "currency": "EUR",
                "rate": 1510.0,
                "timestamp": datetime(2025, 1, 20, 10, 0, 0),
            },
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(
                return_value=[
                    {"currency": "USD", "rate": 1385.0},
                    {"currency": "EUR", "rate": 1500.0},
                ]
            )
            mock_db.update_currency_rates = AsyncMock(return_value=updated_rates)

            response = client.post("/api/v1/currency/refresh")

            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 2
            assert len(data["updated_currencies"]) == 2
            assert "timestamp" in data


class TestAPIBasics:
    """API 기본 기능 테스트"""

    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AssetNest API에 오신 것을 환영합니다!" in data["message"]

    def test_api_docs_available(self, client):
        """API 문서 접근 가능 여부 테스트"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_error_responses_have_proper_structure(self, client):
        """에러 응답의 구조 확인"""
        with patch("api.main.db"):
            with patch(
                "api.main.db.get_portfolio_overview", side_effect=Exception("DB Error")
            ):
                response = client.get("/api/v1/portfolio/overview")
                assert response.status_code == 500
                data = response.json()
                assert "detail" in data


class TestAPIPerformance:
    """API 성능 관련 테스트"""

    def test_multiple_sequential_requests(self, client):
        """여러 순차 요청 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            # 3개의 순차 요청
            for _ in range(3):
                response = client.get("/api/v1/portfolio/overview")
                assert response.status_code == 200

            # DB가 3번 호출되었는지 확인
            assert mock_db.get_portfolio_overview.call_count == 3

    def test_response_time_basic(self, client):
        """기본 응답 시간 테스트"""
        import time

        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            start_time = time.time()
            response = client.get("/api/v1/portfolio/overview")
            end_time = time.time()

            assert response.status_code == 200
            # 응답 시간이 합리적인 범위 내에 있어야 함
            assert (end_time - start_time) < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
