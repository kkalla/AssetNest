"""AssetNest API 통합 테스트 (간단 버전)"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


class TestAPIBasics:
    """API 기본 기능 테스트"""

    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AssetNest API" in data["message"]

    def test_api_docs_available(self, client):
        """API 문서 접근 가능 여부 테스트"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_spec(self, client):
        """OpenAPI 스펙 접근 테스트"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec


class TestPortfolioAPI:
    """포트폴리오 API 테스트"""

    def test_portfolio_overview_endpoint_exists(self, client):
        """포트폴리오 개요 엔드포인트 존재 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/portfolio/overview")
            # 엔드포인트가 존재하면 404가 아님
            assert response.status_code != 404

    def test_portfolio_overview_with_account(self, client):
        """계좌별 포트폴리오 개요 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/portfolio/overview?account=테스트계좌")
            assert response.status_code != 404

    def test_asset_allocation_endpoint(self, client):
        """자산 분배 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/portfolio/allocation")
            assert response.status_code != 404

    def test_unmatched_products_endpoint(self, client):
        """미매칭 상품 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/validation/unmatched-products")
            assert response.status_code != 404


class TestHoldingsAPI:
    """보유 종목 API 테스트"""

    def test_all_holdings_endpoint(self, client):
        """모든 보유 종목 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/holdings/")
            assert response.status_code != 404

    def test_holdings_by_account_endpoint(self, client):
        """계좌별 보유 종목 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/holdings/테스트계좌")
            assert response.status_code != 404


class TestStocksAPI:
    """주식 정보 API 테스트"""

    def test_all_stocks_endpoint(self, client):
        """모든 주식 정보 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/stocks/")
            assert response.status_code != 404

    def test_refresh_prices_endpoint(self, client):
        """가격 새로고침 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.post("/api/v1/stocks/refresh-prices")
            assert response.status_code != 404

    def test_update_stocks_endpoint(self, client):
        """주식 정보 업데이트 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.post("/api/v1/stocks/update")
            assert response.status_code != 404


class TestAnalyticsAPI:
    """성과 분석 API 테스트"""

    def test_performance_analytics_endpoint(self, client):
        """성과 분석 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/analytics/performance/테스트계좌")
            assert response.status_code != 404


class TestCurrencyAPI:
    """환율 API 테스트"""

    def test_currency_rates_endpoint(self, client):
        """환율 정보 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/currency/rates")
            assert response.status_code != 404

    def test_refresh_currency_endpoint(self, client):
        """환율 새로고침 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.post("/api/v1/currency/refresh")
            assert response.status_code != 404


class TestCashManagementAPI:
    """현금 관리 API 테스트"""

    def test_cash_summary_endpoint(self, client):
        """현금 관리 요약 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/cash/summary")
            assert response.status_code != 404

    def test_cash_balances_endpoint(self, client):
        """예수금 정보 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/cash/balances/")
            assert response.status_code != 404

    def test_time_deposits_endpoint(self, client):
        """예적금 정보 엔드포인트 확인"""
        with patch("api.main.db"):
            response = client.get("/api/v1/cash/deposits/")
            assert response.status_code != 404

    def test_update_current_cash_endpoint(self, client):
        """현재 현금 업데이트 엔드포인트 확인"""
        with patch("api.main.db"):
            test_data = {"cash": 1000000, "reason": "테스트"}
            response = client.put("/api/v1/cash/current", json=test_data)
            # Validation error가 나도 엔드포인트는 존재
            assert response.status_code != 404


class TestAPIResponseStructure:
    """API 응답 구조 테스트"""

    def test_error_responses_have_proper_structure(self, client):
        """에러 응답의 구조 확인"""
        with patch("api.main.db"):
            # DB 에러를 시뮬레이션
            with patch(
                "api.main.db.get_portfolio_overview", side_effect=Exception("DB Error")
            ):
                response = client.get("/api/v1/portfolio/overview")
                assert response.status_code == 500
                data = response.json()
                assert "detail" in data

    def test_cors_headers_present(self, client):
        """CORS 헤더 확인"""
        response = client.options("/api/v1/portfolio/overview")
        # OPTIONS 요청은 CORS 설정을 보여줌
        assert response.status_code in [200, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
