import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestPortfolioAPI:
    """Portfolio API 엔드포인트 테스트"""

    def test_get_portfolio_overview_success(
        self, test_client, sample_portfolio_overview
    ):
        """포트폴리오 개요 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            response = test_client.get("/api/v1/portfolio/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["total_value_krw"] == 100000000
            assert data["total_value_usd"] == 75000
            assert data["total_return_rate"] == 0.0526
            assert len(data["accounts"]) == 2
            mock_db.get_portfolio_overview.assert_called_once_with(None)

    def test_get_portfolio_overview_with_account(
        self, test_client, sample_portfolio_overview
    ):
        """특정 계좌 포트폴리오 개요 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            response = test_client.get("/api/v1/portfolio/overview?account=증권사A")

            assert response.status_code == 200
            mock_db.get_portfolio_overview.assert_called_once_with("증권사A")

    def test_get_portfolio_overview_database_error(self, test_client):
        """포트폴리오 개요 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = test_client.get("/api/v1/portfolio/overview")

            assert response.status_code == 500
            data = response.json()
            assert "데이터 조회 중 오류가 발생했습니다" in data["detail"]

    def test_get_asset_allocation_success(self, test_client, sample_asset_allocation):
        """자산 분배 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_asset_allocation = AsyncMock(
                return_value=sample_asset_allocation
            )

            response = test_client.get("/api/v1/portfolio/allocation")

            assert response.status_code == 200
            data = response.json()
            assert data["total_portfolio_value"] == 100000000
            assert len(data["allocations"]) == 3
            assert data["by_asset_type"]["equity"] == 0.7
            mock_db.get_asset_allocation.assert_called_once_with(None, True)

    def test_get_asset_allocation_with_account(
        self, test_client, sample_asset_allocation
    ):
        """특정 계좌 자산 분배 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_asset_allocation = AsyncMock(
                return_value=sample_asset_allocation
            )

            response = test_client.get(
                "/api/v1/portfolio/allocation?account=증권사A&auto_add_unmatched=false"
            )

            assert response.status_code == 200
            mock_db.get_asset_allocation.assert_called_once_with("증권사A", False)

    def test_get_asset_allocation_database_error(self, test_client):
        """자산 분배 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_asset_allocation = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.get("/api/v1/portfolio/allocation")

            assert response.status_code == 500
            data = response.json()
            assert "자산 분배 조회 중 오류가 발생했습니다" in data["detail"]

    def test_get_unmatched_products_success(self, test_client):
        """매칭되지 않는 상품 조회 성공 테스트"""
        sample_unmatched = {
            "total_count": 5,
            "accounts_with_unmatched": 3,
            "last_updated": "2025-01-20T10:00:00",
            "unmatched_products": [
                {
                    "invest_prod_name": "알수없는펀드A",
                    "company": "미래에셋증권",
                    "valuation_amount": 5000000,
                    "profit_loss": 100000,
                    "profit_loss_rate": 0.02,
                    "updated_at": "2025-01-20T10:00:00",
                }
            ],
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_unmatched_products = AsyncMock(return_value=sample_unmatched)

            response = test_client.get("/api/v1/validation/unmatched-products")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 5
            assert len(data["unmatched_products"]) == 1
            mock_db.get_unmatched_products.assert_called_once_with(None)

    def test_get_unmatched_products_with_account(self, test_client):
        """특정 계좌 매칭되지 않는 상품 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_unmatched_products = AsyncMock(
                return_value={"total_count": 0, "unmatched_products": []}
            )

            response = test_client.get(
                "/api/v1/validation/unmatched-products?account=증권사A"
            )

            assert response.status_code == 200
            mock_db.get_unmatched_products.assert_called_once_with("증권사A")

    def test_get_unmatched_products_database_error(self, test_client):
        """매칭되지 않는 상품 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_unmatched_products = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.get("/api/v1/validation/unmatched-products")

            assert response.status_code == 500
            data = response.json()
            assert "매칭되지 않는 상품 조회 중 오류가 발생했습니다" in data["detail"]


class TestPortfolioAPIValidation:
    """Portfolio API 입력값 검증 테스트"""

    def test_portfolio_overview_invalid_parameter_type(self, test_client):
        """잘못된 파라미터 타입 테스트"""
        # FastAPI는 자동으로 타입 변환을 시도하므로 일반적으로 성공함
        response = test_client.get("/api/v1/portfolio/overview?account=123")
        # 이 테스트는 파라미터 처리 로직을 확인하기 위함
        assert response.status_code in [200, 422]

    def test_asset_allocation_invalid_boolean_parameter(self, test_client):
        """잘못된 boolean 파라미터 테스트"""
        response = test_client.get(
            "/api/v1/portfolio/allocation?auto_add_unmatched=invalid"
        )
        # FastAPI는 boolean 파라미터에 대해 엄격한 검증을 함
        assert response.status_code == 422

    def test_get_portfolio_overview_empty_response(self, test_client):
        """빈 포트폴리오 데이터 응답 테스트"""
        empty_overview = {
            "total_value_krw": 0,
            "total_value_usd": 0,
            "total_pnl_krw": 0,
            "total_pnl_usd": 0,
            "total_return_rate": 0,
            "accounts": [],
            "last_updated": "2025-01-20T10:00:00",
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(return_value=empty_overview)

            response = test_client.get("/api/v1/portfolio/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["total_value_krw"] == 0
            assert len(data["accounts"]) == 0

    def test_get_asset_allocation_empty_response(self, test_client):
        """빈 자산 분배 데이터 응답 테스트"""
        empty_allocation = {
            "total_portfolio_value": 0,
            "allocations": [],
            "by_asset_type": {"equity": 0, "bond": 0, "cash": 0},
            "by_region": {"domestic": 0, "global": 0},
            "by_currency": {"krw": 0, "usd": 0},
            "total_assets": 0,
            "updated_at": "2025-01-20T10:00:00",
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_asset_allocation = AsyncMock(return_value=empty_allocation)

            response = test_client.get("/api/v1/portfolio/allocation")

            assert response.status_code == 200
            data = response.json()
            assert data["total_portfolio_value"] == 0
            assert len(data["allocations"]) == 0


class TestPortfolioAPIPerformance:
    """Portfolio API 성능 관련 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_portfolio_overview_requests(
        self, test_client, sample_portfolio_overview
    ):
        """동시 포트폴리오 개요 요청 테스트"""
        import asyncio

        with patch("api.main.db") as mock_db:
            mock_db.get_portfolio_overview = AsyncMock(
                return_value=sample_portfolio_overview
            )

            # 10개의 동시 요청
            tasks = [test_client.get("/api/v1/portfolio/overview") for _ in range(10)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert response.json()["total_value_krw"] == 100000000

            # DB가 10번 호출되었는지 확인
            assert mock_db.get_portfolio_overview.call_count == 10

    def test_portfolio_overview_response_time(
        self, test_client, sample_portfolio_overview
    ):
        """포트폴리오 개요 응답 시간 테스트"""
        import time

        with patch("api.main.db") as mock_db:
            # 약간의 지연을 시뮬레이션
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms 지연
                return sample_portfolio_overview

            mock_db.get_portfolio_overview = delayed_response

            start_time = time.time()
            response = test_client.get("/api/v1/portfolio/overview")
            end_time = time.time()

            assert response.status_code == 200
            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 1초 이하)
            assert (end_time - start_time) < 1.0
