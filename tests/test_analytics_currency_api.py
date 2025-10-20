import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestAnalyticsAPI:
    """Analytics API 엔드포인트 테스트"""

    def test_get_performance_analytics_success(
        self, test_client, sample_performance_data
    ):
        """성과 분석 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(
                return_value=sample_performance_data
            )

            response = test_client.get("/api/v1/analytics/performance/증권사A")

            assert response.status_code == 200
            data = response.json()
            assert data["account"] == "증권사A"
            assert data["total_investment"] == 7000000
            assert data["total_value"] == 7500000
            assert data["return_rate"] == 0.0714
            assert "sector_allocation" in data
            assert "region_allocation" in data
            mock_db.get_performance_data.assert_called_once_with("증권사A")

    def test_get_performance_analytics_not_found(self, test_client):
        """존재하지 않는 계좌 성과 분석 조회 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(return_value=None)

            response = test_client.get("/api/v1/analytics/performance/존재하지않는계좌")

            assert response.status_code == 404
            data = response.json()
            assert (
                "존재하지않는계좌'의 성과 데이터를 찾을 수 없습니다" in data["detail"]
            )

    def test_get_performance_analytics_database_error(self, test_client):
        """성과 분석 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.get("/api/v1/analytics/performance/증권사A")

            assert response.status_code == 500
            data = response.json()
            assert "성과 분석 데이터 조회 중 오류가 발생했습니다" in data["detail"]


class TestCurrencyAPI:
    """Currency API 엔드포인트 테스트"""

    def test_get_currency_rates_success(self, test_client, sample_currency_rates):
        """환율 정보 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=sample_currency_rates)

            response = test_client.get("/api/v1/currency/rates")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["currency"] == "USD"
            assert data[0]["rate"] == 1385.0
            assert data[1]["currency"] == "EUR"
            mock_db.get_currency_rates.assert_called_once_with(auto_update=True)

    def test_get_currency_rates_without_auto_update(
        self, test_client, sample_currency_rates
    ):
        """자동 업데이트 없이 환율 정보 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=sample_currency_rates)

            response = test_client.get("/api/v1/currency/rates?auto_update=false")

            assert response.status_code == 200
            mock_db.get_currency_rates.assert_called_once_with(auto_update=False)

    def test_get_currency_rates_empty_result(self, test_client):
        """환율 정보 없음 (빈 결과) 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=[])

            response = test_client.get("/api/v1/currency/rates")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0

    def test_get_currency_rates_database_error(self, test_client):
        """환율 정보 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = test_client.get("/api/v1/currency/rates")

            assert response.status_code == 500
            data = response.json()
            assert "환율 정보 조회 중 오류가 발생했습니다" in data["detail"]

    def test_refresh_currency_rates_success(self, test_client):
        """환율 정보 새로고침 성공 테스트 (전체)"""
        updated_rates = [
            {"currency": "USD", "rate": 1390.0, "timestamp": "2025-01-20T10:00:00"},
            {"currency": "EUR", "rate": 1510.0, "timestamp": "2025-01-20T10:00:00"},
        ]

        with patch("api.main.db") as mock_db:
            # 기존 환율 조회
            mock_db.get_currency_rates = AsyncMock(
                return_value=[
                    {"currency": "USD", "rate": 1385.0},
                    {"currency": "EUR", "rate": 1500.0},
                ]
            )
            # 환율 업데이트
            mock_db.update_currency_rates = AsyncMock(return_value=updated_rates)

            response = test_client.post("/api/v1/currency/refresh")

            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 2
            assert len(data["updated_currencies"]) == 2
            assert "USD" in data["updated_currencies"]
            assert "EUR" in data["updated_currencies"]
            assert "timestamp" in data

    def test_refresh_currency_rates_specific_currencies(self, test_client):
        """특정 통화 환율 정보 새로고침 성공 테스트"""
        updated_rates = [
            {"currency": "USD", "rate": 1390.0, "timestamp": "2025-01-20T10:00:00"}
        ]

        with patch("api.main.db") as mock_db:
            mock_db.update_currency_rates = AsyncMock(return_value=updated_rates)

            response = test_client.post("/api/v1/currency/refresh?currencies=USD")

            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 1
            assert data["updated_currencies"] == ["USD"]
            mock_db.update_currency_rates.assert_called_once_with(["USD"])

    def test_refresh_currency_rates_multiple_currencies(self, test_client):
        """여러 통화 환율 정보 새로고침 성공 테스트"""
        updated_rates = [
            {"currency": "USD", "rate": 1390.0, "timestamp": "2025-01-20T10:00:00"},
            {"currency": "JPY", "rate": 9.5, "timestamp": "2025-01-20T10:00:00"},
        ]

        with patch("api.main.db") as mock_db:
            mock_db.update_currency_rates = AsyncMock(return_value=updated_rates)

            response = test_client.post(
                "/api/v1/currency/refresh?currencies=USD&currencies=JPY"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 2
            assert set(data["updated_currencies"]) == {"USD", "JPY"}
            mock_db.update_currency_rates.assert_called_once_with(["USD", "JPY"])

    def test_refresh_currency_rates_database_error(self, test_client):
        """환율 정보 새로고침 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(
                side_effect=Exception("API rate limit exceeded")
            )

            response = test_client.post("/api/v1/currency/refresh")

            assert response.status_code == 500
            data = response.json()
            assert "환율 새로고침 중 오류가 발생했습니다" in data["detail"]

    def test_refresh_currency_rates_update_error(self, test_client):
        """환율 정보 업데이트 실패 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(
                return_value=[{"currency": "USD", "rate": 1385.0}]
            )
            mock_db.update_currency_rates = AsyncMock(
                side_effect=Exception("Update failed")
            )

            response = test_client.post("/api/v1/currency/refresh")

            assert response.status_code == 500
            data = response.json()
            assert "환율 새로고침 중 오류가 발생했습니다" in data["detail"]


class TestAnalyticsCurrencyAPIValidation:
    """Analytics 및 Currency API 입력값 검증 테스트"""

    def test_performance_data_structure_validation(
        self, test_client, sample_performance_data
    ):
        """성과 분석 데이터 구조 검증 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(
                return_value=sample_performance_data
            )

            response = test_client.get("/api/v1/analytics/performance/증권사A")

            assert response.status_code == 200
            data = response.json()

            # 필수 필드 검증
            required_fields = [
                "account",
                "total_investment",
                "total_value",
                "total_return",
                "return_rate",
                "sector_allocation",
                "region_allocation",
                "daily_returns",
                "cumulative_returns",
                "volatility",
                "sharpe_ratio",
                "max_drawdown",
                "updated_at",
            ]

            for field in required_fields:
                assert field in data, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(data["account"], str)
            assert isinstance(data["total_investment"], (int, float))
            assert isinstance(data["return_rate"], (int, float))
            assert isinstance(data["sector_allocation"], dict)
            assert isinstance(data["region_allocation"], dict)
            assert isinstance(data["daily_returns"], list)
            assert isinstance(data["volatility"], (int, float))

    def test_currency_rates_structure_validation(
        self, test_client, sample_currency_rates
    ):
        """환율 정보 데이터 구조 검증 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=sample_currency_rates)

            response = test_client.get("/api/v1/currency/rates")

            assert response.status_code == 200
            data = response.json()

            # 응답이 리스트인지 확인
            assert isinstance(data, list)
            assert len(data) > 0

            # 각 환율 정보 필드 검증
            rate = data[0]
            required_fields = ["currency", "rate", "timestamp"]

            for field in required_fields:
                assert field in rate, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 및 값 검증
            assert isinstance(rate["currency"], str)
            assert isinstance(rate["rate"], (int, float))
            assert rate["rate"] > 0
            assert isinstance(rate["timestamp"], str)

    def test_performance_data_calculation_validation(self, test_client):
        """성과 분석 데이터 계산 검증 테스트"""
        performance_data = {
            "account": "테스트계좌",
            "total_investment": 10000000,
            "total_value": 11500000,
            "total_return": 1500000,
            "return_rate": 0.15,
            "sector_allocation": {"IT": 0.6, "금융": 0.3, "제조": 0.1},
            "region_allocation": {"domestic": 0.7, "global": 0.3},
            "daily_returns": [0.01, 0.02, -0.01, 0.015, 0.005],
            "cumulative_returns": [1.01, 1.03, 1.02, 1.035, 1.04],
            "volatility": 0.12,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.05,
            "updated_at": "2025-01-20T10:00:00",
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(return_value=performance_data)

            response = test_client.get("/api/v1/analytics/performance/테스트계좌")

            assert response.status_code == 200
            data = response.json()

            # 수익률 계산 검증: (current_value - initial_investment) / initial_investment
            expected_return_rate = (
                data["total_value"] - data["total_investment"]
            ) / data["total_investment"]
            assert abs(data["return_rate"] - expected_return_rate) < 0.0001

            # 총 수익 계산 검증: current_value - initial_investment
            expected_total_return = data["total_value"] - data["total_investment"]
            assert abs(data["total_return"] - expected_total_return) < 1

            # 섹터 배분 합계 검증
            sector_sum = sum(data["sector_allocation"].values())
            assert abs(sector_sum - 1.0) < 0.0001

            # 지역 배분 합계 검증
            region_sum = sum(data["region_allocation"].values())
            assert abs(region_sum - 1.0) < 0.0001

    def test_currency_account_with_special_characters(self, test_client):
        """특수문자가 포함된 계좌명 성과 분석 조회 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(return_value=None)

            # URL 인코딩된 특수문자가 포함된 계좌명
            account_name = "미래에셋-증권%계좌"
            response = test_client.get(f"/api/v1/analytics/performance/{account_name}")

            assert response.status_code in [200, 404]  # 데이터가 없으면 404, 있으면 200

    def test_currency_refresh_response_structure_validation(self, test_client):
        """환율 새로고침 응답 구조 검증 테스트"""
        updated_rates = [
            {"currency": "USD", "rate": 1390.0, "timestamp": "2025-01-20T10:00:00"}
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=updated_rates)
            mock_db.update_currency_rates = AsyncMock(return_value=updated_rates)

            response = test_client.post("/api/v1/currency/refresh")

            assert response.status_code == 200
            data = response.json()

            # 응답 필드 검증
            required_fields = [
                "message",
                "updated_count",
                "updated_currencies",
                "timestamp",
            ]
            for field in required_fields:
                assert field in data, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(data["message"], str)
            assert isinstance(data["updated_count"], int)
            assert isinstance(data["updated_currencies"], list)
            assert isinstance(data["timestamp"], str)


class TestAnalyticsCurrencyAPIPerformance:
    """Analytics 및 Currency API 성능 관련 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(
        self, test_client, sample_performance_data
    ):
        """동시 성과 분석 요청 테스트"""
        import asyncio

        with patch("api.main.db") as mock_db:
            mock_db.get_performance_data = AsyncMock(
                return_value=sample_performance_data
            )

            # 3개의 동시 요청
            tasks = [
                test_client.get("/api/v1/analytics/performance/증권사A")
                for _ in range(3)
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert response.json()["account"] == "증권사A"

            # DB가 3번 호출되었는지 확인
            assert mock_db.get_performance_data.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_currency_requests(
        self, test_client, sample_currency_rates
    ):
        """동시 환율 정보 요청 테스트"""
        import asyncio

        with patch("api.main.db") as mock_db:
            mock_db.get_currency_rates = AsyncMock(return_value=sample_currency_rates)

            # 5개의 동시 요청
            tasks = [test_client.get("/api/v1/currency/rates") for _ in range(5)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert len(response.json()) == 2

            # DB가 5번 호출되었는지 확인
            assert mock_db.get_currency_rates.call_count == 5

    def test_performance_analytics_response_time(
        self, test_client, sample_performance_data
    ):
        """성과 분석 응답 시간 테스트"""
        import time

        with patch("api.main.db") as mock_db:
            # 약간의 지연을 시뮬레이션
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms 지연
                return sample_performance_data

            mock_db.get_performance_data = delayed_response

            start_time = time.time()
            response = test_client.get("/api/v1/analytics/performance/증권사A")
            end_time = time.time()

            assert response.status_code == 200
            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 1초 이하)
            assert (end_time - start_time) < 1.0
