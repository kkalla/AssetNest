import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestStocksAPI:
    """Stocks API 엔드포인트 테스트"""

    def test_get_all_stocks_success(self, test_client, sample_stock_info):
        """모든 주식 정보 조회 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=sample_stock_info)

            response = test_client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "삼성전자"
            assert data[1]["name"] == "Apple Inc."
            mock_db.get_all_stocks.assert_called_once()

    def test_get_all_stocks_empty_result(self, test_client):
        """주식 정보 없음 (빈 결과) 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=[])

            response = test_client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
            assert data == []

    def test_get_all_stocks_database_error(self, test_client):
        """주식 정보 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = test_client.get("/api/v1/stocks/")

            assert response.status_code == 500
            data = response.json()
            assert "주식 정보 조회 중 오류가 발생했습니다" in data["detail"]

    def test_refresh_stock_prices_success(self, test_client):
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

            response = test_client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 8
            assert data["fail_count"] == 1
            assert data["skip_count"] == 1
            assert data["total_count"] == 10
            assert "timestamp" in data
            mock_db.update_symbol_table_prices.assert_called_once()

    def test_refresh_stock_prices_all_success(self, test_client):
        """주식 가격 새로고침 전체 성공 테스트"""
        update_result = {
            "success_count": 10,
            "fail_count": 0,
            "skip_count": 0,
            "total_count": 10,
            "failed_stocks": [],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=update_result)

            response = test_client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 10
            assert data["fail_count"] == 0
            assert data["skip_count"] == 0

    def test_refresh_stock_prices_partial_failure(self, test_client):
        """주식 가격 새로고침 부분 실패 테스트"""
        update_result = {
            "success_count": 5,
            "fail_count": 3,
            "skip_count": 2,
            "total_count": 10,
            "failed_stocks": ["실패주식1", "실패주식2", "실패주식3"],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=update_result)

            response = test_client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 5
            assert data["fail_count"] == 3
            assert data["skip_count"] == 2
            assert len(data["failed_stocks"]) == 3

    def test_refresh_stock_prices_database_error(self, test_client):
        """주식 가격 새로고침 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(
                side_effect=Exception("API rate limit exceeded")
            )

            response = test_client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 500
            data = response.json()
            assert "가격 업데이트 중 오류가 발생했습니다" in data["detail"]

    def test_update_stocks_success(self, test_client):
        """주식 정보 전체 업데이트 성공 테스트"""
        price_result = {
            "success_count": 8,
            "fail_count": 1,
            "skip_count": 1,
            "total_count": 10,
            "failed_stocks": ["실패주식"],
        }

        sector_result = {
            "success_count": 9,
            "fail_count": 1,
            "total_count": 10,
            "failed_stocks": ["섹터실패주식"],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=price_result)
            mock_db.update_symbol_sector_info = AsyncMock(return_value=sector_result)

            response = test_client.post("/api/v1/stocks/update")

            assert response.status_code == 200
            data = response.json()

            # 가격 업데이트 결과 검증
            assert "price_update" in data
            assert data["price_update"]["success_count"] == 8
            assert data["price_update"]["fail_count"] == 1
            assert data["price_update"]["skip_count"] == 1

            # 섹터 정보 업데이트 결과 검증
            assert "sector_update" in data
            assert data["sector_update"]["success_count"] == 9
            assert data["sector_update"]["fail_count"] == 1

            # 전체 응답 구조 검증
            assert "message" in data
            assert "timestamp" in data

            # 함수 호출 순서 확인
            mock_db.update_symbol_table_prices.assert_called_once()
            mock_db.update_symbol_sector_info.assert_called_once()

    def test_update_stocks_price_update_failure(self, test_client):
        """주식 정보 업데이트 - 가격 업데이트 실패 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(
                side_effect=Exception("Price API error")
            )

            response = test_client.post("/api/v1/stocks/update")

            assert response.status_code == 500
            data = response.json()
            assert "주식 정보 업데이트 중 오류가 발생했습니다" in data["detail"]
            mock_db.update_symbol_table_prices.assert_called_once()
            mock_db.update_symbol_sector_info.assert_not_called()

    def test_update_stocks_sector_update_failure(self, test_client):
        """주식 정보 업데이트 - 섹터 정보 업데이트 실패 테스트"""
        price_result = {
            "success_count": 10,
            "fail_count": 0,
            "skip_count": 0,
            "total_count": 10,
            "failed_stocks": [],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=price_result)
            mock_db.update_symbol_sector_info = AsyncMock(
                side_effect=Exception("Sector API error")
            )

            response = test_client.post("/api/v1/stocks/update")

            assert response.status_code == 500
            data = response.json()
            assert "주식 정보 업데이트 중 오류가 발생했습니다" in data["detail"]
            mock_db.update_symbol_table_prices.assert_called_once()
            mock_db.update_symbol_sector_info.assert_called_once()


class TestStocksAPIValidation:
    """Stocks API 입력값 검증 테스트"""

    def test_stocks_response_structure_validation(self, test_client, sample_stock_info):
        """주식 정보 응답 구조 검증 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=sample_stock_info)

            response = test_client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()

            # 응답이 리스트인지 확인
            assert isinstance(data, list)
            assert len(data) > 0

            # 각 주식 정보 필드 검증
            stock = data[0]
            required_fields = [
                "name",
                "symbol",
                "exchange",
                "sector",
                "industry",
                "asset_type",
                "region_type",
                "latest_close",
                "marketcap",
                "updated_at",
            ]

            for field in required_fields:
                assert field in stock, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(stock["name"], str)
            assert isinstance(stock["symbol"], str)
            assert isinstance(stock["exchange"], str)
            assert isinstance(stock["latest_close"], (int, float))
            assert isinstance(stock["marketcap"], (int, float))
            assert isinstance(stock["asset_type"], str)
            assert isinstance(stock["region_type"], str)

    def test_refresh_prices_response_structure_validation(self, test_client):
        """가격 새로고침 응답 구조 검증 테스트"""
        update_result = {
            "success_count": 5,
            "fail_count": 2,
            "skip_count": 1,
            "total_count": 8,
            "failed_stocks": ["실패1", "실패2"],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=update_result)

            response = test_client.post("/api/v1/stocks/refresh-prices")

            assert response.status_code == 200
            data = response.json()

            # 응답 필드 검증
            required_fields = [
                "message",
                "success_count",
                "fail_count",
                "skip_count",
                "total_count",
                "timestamp",
            ]

            for field in required_fields:
                assert field in data, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 및 값 검증
            assert isinstance(data["message"], str)
            assert isinstance(data["success_count"], int)
            assert isinstance(data["fail_count"], int)
            assert isinstance(data["skip_count"], int)
            assert isinstance(data["total_count"], int)
            assert (
                data["total_count"]
                == data["success_count"] + data["fail_count"] + data["skip_count"]
            )

    def test_update_stocks_response_structure_validation(self, test_client):
        """주식 정보 전체 업데이트 응답 구조 검증 테스트"""
        price_result = {
            "success_count": 8,
            "fail_count": 1,
            "skip_count": 1,
            "total_count": 10,
            "failed_stocks": ["실패"],
        }

        sector_result = {
            "success_count": 9,
            "fail_count": 1,
            "total_count": 10,
            "failed_stocks": ["섹터실패"],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=price_result)
            mock_db.update_symbol_sector_info = AsyncMock(return_value=sector_result)

            response = test_client.post("/api/v1/stocks/update")

            assert response.status_code == 200
            data = response.json()

            # 응답 필드 검증
            required_fields = ["message", "price_update", "sector_update", "timestamp"]

            for field in required_fields:
                assert field in data, f"필수 필드 '{field}'가 응답에 없습니다"

            # price_update 필드 구조 검증
            price_update = data["price_update"]
            price_fields = ["success_count", "fail_count", "skip_count", "total_count"]
            for field in price_fields:
                assert field in price_update, f"price_update 필드 '{field}'가 없습니다"

            # sector_update 필드 구조 검증
            sector_update = data["sector_update"]
            sector_fields = ["success_count", "fail_count", "total_count"]
            for field in sector_fields:
                assert (
                    field in sector_update
                ), f"sector_update 필드 '{field}'가 없습니다"

    def test_stock_data_consistency_validation(self, test_client):
        """주식 데이터 일관성 검증 테스트"""
        # 다양한 거래소의 주식 데이터
        diverse_stocks = [
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
                "updated_at": "2025-01-20T10:00:00",
            },
            {
                "name": "Apple Inc.",
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "sector": "IT",
                "industry": "컴퓨터",
                "asset_type": "equity",
                "region_type": "global",
                "latest_close": 175.50,
                "marketcap": 2700000,
                "updated_at": "2025-01-20T10:00:00",
            },
            {
                "name": "TIGER 미국S&P500",
                "symbol": "371460",
                "exchange": "KRX",
                "sector": "ETF",
                "industry": "인덱스펀드",
                "asset_type": "etf",
                "region_type": "global",
                "latest_close": 15000,
                "marketcap": 500000,
                "updated_at": "2025-01-20T10:00:00",
            },
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=diverse_stocks)

            response = test_client.get("/api/v1/stocks/")

            assert response.status_code == 200
            data = response.json()

            # 다양한 자산 유형 확인
            asset_types = set(stock["asset_type"] for stock in data)
            assert "equity" in asset_types

            # 다양한 지역 유형 확인
            region_types = set(stock["region_type"] for stock in data)
            assert "domestic" in region_types
            assert "global" in region_types

            # 다양한 거래소 확인
            exchanges = set(stock["exchange"] for stock in data)
            assert len(exchanges) >= 2

            # 모든 주식에 필수 필드가 있는지 확인
            for stock in data:
                assert stock["latest_close"] > 0
                assert stock["marketcap"] >= 0
                assert stock["sector"]  # 빈 문자열 아님
                assert stock["exchange"]  # 빈 문자열 아름


class TestStocksAPIPerformance:
    """Stocks API 성능 관련 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_stocks_requests(self, test_client, sample_stock_info):
        """동시 주식 정보 요청 테스트"""
        import asyncio

        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=sample_stock_info)

            # 5개의 동시 요청
            tasks = [test_client.get("/api/v1/stocks/") for _ in range(5)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert len(response.json()) == 2

            # DB가 5번 호출되었는지 확인
            assert mock_db.get_all_stocks.call_count == 5

    def test_large_stocks_dataset_performance(self, test_client):
        """대용량 주식 정보 데이터셋 성능 테스트"""
        import time

        # 200개의 대용량 더미 데이터 생성
        large_stocks = []
        exchanges = ["KOSPI", "KOSDAQ", "NASDAQ", "NYSE"]
        sectors = ["IT", "금융", "제조", "바이오", "에너지"]

        for i in range(200):
            stock = {
                "name": f"테스트주식{i}",
                "symbol": f"{i:06d}" if i % 2 == 0 else f"TEST{i}",
                "exchange": exchanges[i % len(exchanges)],
                "sector": sectors[i % len(sectors)],
                "industry": f"산업{i}",
                "asset_type": "equity",
                "region_type": "domestic" if i % 3 == 0 else "global",
                "latest_close": 10000 + (i * 100),
                "marketcap": 1000000 + (i * 10000),
                "updated_at": "2025-01-20T10:00:00",
            }
            large_stocks.append(stock)

        with patch("api.main.db") as mock_db:
            mock_db.get_all_stocks = AsyncMock(return_value=large_stocks)

            start_time = time.time()
            response = test_client.get("/api/v1/stocks/")
            end_time = time.time()

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 200

            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 3초 이하)
            assert (end_time - start_time) < 3.0

    def test_refresh_prices_performance(self, test_client):
        """가격 새로고침 성능 테스트"""
        import time

        # 대용량 업데이트 결과 시뮬레이션
        large_update_result = {
            "success_count": 150,
            "fail_count": 20,
            "skip_count": 30,
            "total_count": 200,
            "failed_stocks": [f"실패주식{i}" for i in range(20)],
        }

        with patch("api.main.db") as mock_db:
            # 2초 지연 시뮬레이션
            async def delayed_update(*args, **kwargs):
                await asyncio.sleep(0.5)  # 500ms 지연
                return large_update_result

            mock_db.update_symbol_table_prices = delayed_update

            start_time = time.time()
            response = test_client.post("/api/v1/stocks/refresh-prices")
            end_time = time.time()

            assert response.status_code == 200
            data = response.json()
            assert data["success_count"] == 150

            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 5초 이하)
            assert (end_time - start_time) < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_update_operations(self, test_client):
        """동시 업데이트 작업 테스트"""
        import asyncio

        price_result = {
            "success_count": 10,
            "fail_count": 0,
            "skip_count": 0,
            "total_count": 10,
            "failed_stocks": [],
        }

        sector_result = {
            "success_count": 10,
            "fail_count": 0,
            "total_count": 10,
            "failed_stocks": [],
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_symbol_table_prices = AsyncMock(return_value=price_result)
            mock_db.update_symbol_sector_info = AsyncMock(return_value=sector_result)

            # 3개의 동시 업데이트 요청
            tasks = [test_client.post("/api/v1/stocks/update") for _ in range(3)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200

            # 각 함수가 3번씩 호출되었는지 확인
            assert mock_db.update_symbol_table_prices.call_count == 3
            assert mock_db.update_symbol_sector_info.call_count == 3
