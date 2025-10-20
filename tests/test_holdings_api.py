import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestHoldingsAPI:
    """Holdings API 엔드포인트 테스트"""

    def test_get_all_holdings_success(self, test_client, sample_holdings):
        """모든 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=sample_holdings)

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["company"] == "삼성전자"
            assert data[1]["company"] == "Apple Inc."
            mock_db.get_holdings.assert_called_once_with(None, None)

    def test_get_all_holdings_with_account_filter(self, test_client, sample_holdings):
        """계좌 필터링하여 모든 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            # 특정 계좌 필터링 결과
            filtered_holdings = [
                h for h in sample_holdings if h["account"] == "증권사A"
            ]
            mock_db.get_holdings = AsyncMock(return_value=filtered_holdings)

            response = test_client.get("/api/v1/holdings/?account=증권사A")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            mock_db.get_holdings.assert_called_once_with("증권사A", None)

    def test_get_all_holdings_with_market_filter(self, test_client, sample_holdings):
        """시장 필터링하여 모든 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            # 특정 시장 필터링 결과
            filtered_holdings = [h for h in sample_holdings if h["market"] == "KOSPI"]
            mock_db.get_holdings = AsyncMock(return_value=filtered_holdings)

            response = test_client.get("/api/v1/holdings/?market=KOSPI")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["market"] == "KOSPI"
            mock_db.get_holdings.assert_called_once_with(None, "KOSPI")

    def test_get_all_holdings_with_both_filters(self, test_client, sample_holdings):
        """계좌와 시장 필터링하여 모든 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            # 두 필터 모두 적용된 결과
            filtered_holdings = [
                h
                for h in sample_holdings
                if h["account"] == "증권사A" and h["market"] == "KOSPI"
            ]
            mock_db.get_holdings = AsyncMock(return_value=filtered_holdings)

            response = test_client.get("/api/v1/holdings/?account=증권사A&market=KOSPI")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            assert data[0]["market"] == "KOSPI"
            mock_db.get_holdings.assert_called_once_with("증권사A", "KOSPI")

    def test_get_all_holdings_empty_result(self, test_client):
        """보유 종목 없음 (빈 결과) 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=[])

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
            assert data == []

    def test_get_all_holdings_database_error(self, test_client):
        """보유 종목 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 500
            data = response.json()
            assert "보유 종목 조회 중 오류가 발생했습니다" in data["detail"]

    def test_get_holdings_by_account_success(self, test_client, sample_holdings):
        """특정 계좌 보유 종목 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            # 특정 계좌 종목만 필터링
            account_holdings = [h for h in sample_holdings if h["account"] == "증권사A"]
            mock_db.get_holdings = AsyncMock(return_value=account_holdings)

            response = test_client.get("/api/v1/holdings/증권사A")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            assert data[0]["company"] == "삼성전자"
            mock_db.get_holdings.assert_called_once_with(account="증권사A")

    def test_get_holdings_by_account_not_found(self, test_client):
        """존재하지 않는 계좌 보유 종목 조회 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=[])

            response = test_client.get("/api/v1/holdings/존재하지않는계좌")

            assert response.status_code == 404
            data = response.json()
            assert "존재하지않는계좌'의 보유 종목을 찾을 수 없습니다" in data["detail"]

    def test_get_holdings_by_account_database_error(self, test_client):
        """특정 계좌 보유 종목 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(side_effect=Exception("Database error"))

            response = test_client.get("/api/v1/holdings/증권사A")

            assert response.status_code == 500
            data = response.json()
            assert "계좌별 보유 종목 조회 중 오류가 발생했습니다" in data["detail"]

    def test_get_holdings_by_account_with_special_characters(self, test_client):
        """특수문자가 포함된 계좌명 조회 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=[])

            # URL 인코딩된 특수문자가 포함된 계좌명
            account_name = "미래에셋-증권%계좌"
            response = test_client.get(f"/api/v1/holdings/{account_name}")

            assert response.status_code in [200, 404]  # 데이터가 없으면 404, 있으면 200


class TestHoldingsAPIValidation:
    """Holdings API 입력값 검증 테스트"""

    def test_holdings_response_structure_validation(self, test_client, sample_holdings):
        """보유 종목 응답 구조 검증 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=sample_holdings)

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()

            # 응답이 리스트인지 확인
            assert isinstance(data, list)
            assert len(data) > 0

            # 각 보유 종목 필드 검증
            holding = data[0]
            required_fields = [
                "account",
                "company",
                "market",
                "amount",
                "avg_price_krw",
                "current_price_krw",
                "principal",
                "market_value",
                "unrealized_pnl",
                "return_rate",
                "currency",
                "sector",
                "asset_type",
                "region_type",
            ]

            for field in required_fields:
                assert field in holding, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(holding["amount"], (int, float))
            assert isinstance(holding["market_value"], (int, float))
            assert isinstance(holding["return_rate"], (int, float))
            assert isinstance(holding["currency"], str)
            assert isinstance(holding["asset_type"], str)

    def test_holdings_financial_calculations_validation(self, test_client):
        """보유 종목 금융 계산 검증 테스트"""
        sample_holding = {
            "account": "증권사A",
            "company": "테스트주식",
            "market": "KOSPI",
            "amount": 100,
            "avg_price_krw": 50000,
            "current_price_krw": 55000,
            "principal": 5000000,
            "market_value": 5500000,
            "unrealized_pnl": 500000,
            "return_rate": 0.1,
            "currency": "KRW",
            "sector": "테스트",
            "asset_type": "equity",
            "region_type": "domestic",
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=[sample_holding])

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()
            holding = data[0]

            # 수익률 계산 검증: (current_price - avg_price) / avg_price
            expected_return_rate = (
                holding["current_price_krw"] - holding["avg_price_krw"]
            ) / holding["avg_price_krw"]
            assert abs(holding["return_rate"] - expected_return_rate) < 0.0001

            # 평가손익 계산 검증: (current_price - avg_price) * amount
            expected_pnl = (
                holding["current_price_krw"] - holding["avg_price_krw"]
            ) * holding["amount"]
            assert abs(holding["unrealized_pnl"] - expected_pnl) < 1

            # 평가금액 계산 검증: current_price * amount
            expected_market_value = holding["current_price_krw"] * holding["amount"]
            assert abs(holding["market_value"] - expected_market_value) < 1

    def test_holdings_edge_cases(self, test_client):
        """보유 종목 엣지 케이스 테스트"""
        edge_case_holdings = [
            # 수익률 0% 케이스
            {
                "account": "증권사A",
                "company": "수익률0테스트",
                "market": "KOSPI",
                "amount": 100,
                "avg_price_krw": 50000,
                "current_price_krw": 50000,
                "principal": 5000000,
                "market_value": 5000000,
                "unrealized_pnl": 0,
                "return_rate": 0.0,
                "currency": "KRW",
                "sector": "테스트",
                "asset_type": "equity",
                "region_type": "domestic",
            },
            # 손실 케이스
            {
                "account": "증권사B",
                "company": "손실테스트",
                "market": "KOSDAQ",
                "amount": 50,
                "avg_price_krw": 20000,
                "current_price_krw": 15000,
                "principal": 1000000,
                "market_value": 750000,
                "unrealized_pnl": -250000,
                "return_rate": -0.25,
                "currency": "KRW",
                "sector": "테스트",
                "asset_type": "equity",
                "region_type": "domestic",
            },
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=edge_case_holdings)

            response = test_client.get("/api/v1/holdings/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # 손익 계산 검증
            profit_holding = data[0]
            loss_holding = data[1]

            assert profit_holding["return_rate"] == 0.0
            assert profit_holding["unrealized_pnl"] == 0

            assert loss_holding["return_rate"] == -0.25
            assert loss_holding["unrealized_pnl"] == -250000


class TestHoldingsAPIPerformance:
    """Holdings API 성능 관련 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_holdings_requests(self, test_client, sample_holdings):
        """동시 보유 종목 요청 테스트"""
        import asyncio

        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=sample_holdings)

            # 5개의 동시 요청
            tasks = [test_client.get("/api/v1/holdings/") for _ in range(5)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert len(response.json()) == 2

            # DB가 5번 호출되었는지 확인
            assert mock_db.get_holdings.call_count == 5

    def test_large_holdings_dataset_performance(self, test_client):
        """대용량 보유 종목 데이터셋 성능 테스트"""
        import time

        # 100개의 대용량 더미 데이터 생성
        large_holdings = []
        for i in range(100):
            holding = {
                "account": f"증권사{i % 5}",
                "company": f"테스트주식{i}",
                "market": "KOSPI" if i % 2 == 0 else "KOSDAQ",
                "amount": 100 + i,
                "avg_price_krw": 10000 + (i * 100),
                "current_price_krw": 11000 + (i * 100),
                "principal": (100 + i) * (10000 + (i * 100)),
                "market_value": (100 + i) * (11000 + (i * 100)),
                "unrealized_pnl": (100 + i) * 1000,
                "return_rate": 0.1,
                "currency": "KRW",
                "sector": "테스트",
                "asset_type": "equity",
                "region_type": "domestic",
            }
            large_holdings.append(holding)

        with patch("api.main.db") as mock_db:
            mock_db.get_holdings = AsyncMock(return_value=large_holdings)

            start_time = time.time()
            response = test_client.get("/api/v1/holdings/")
            end_time = time.time()

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 100

            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 2초 이하)
            assert (end_time - start_time) < 2.0

    def test_holdings_caching_behavior(self, test_client, sample_holdings):
        """보유 종목 캐싱 동작 테스트"""
        with patch("api.main.db") as mock_db:
            call_count = 0

            async def counted_holdings(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                return sample_holdings

            mock_db.get_holdings = counted_holdings

            # 동일한 요청을 여러 번 보냄
            for _ in range(3):
                response = test_client.get("/api/v1/holdings/")
                assert response.status_code == 200

            # 현재 구현에서는 매번 DB 호출됨 (캐싱 없음)
            assert call_count == 3
