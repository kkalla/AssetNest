import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestCashManagementAPI:
    """Cash Management API 엔드포인트 테스트"""

    def test_get_cash_management_summary_success(self, test_client):
        """현금 관리 요약 정보 조회 성공 테스트"""
        summary_data = {
            "total_cash": 50000000,
            "total_deposits": 30000000,
            "total_securities_balance": 20000000,
            "cash_accounts": [
                {"account": "증권사A", "balance": 15000000},
                {"account": "증권사B", "balance": 5000000},
            ],
            "deposits_count": 3,
            "last_updated": "2025-01-20T10:00:00",
        }

        with patch("api.main.db") as mock_db:
            mock_db.get_cash_management_summary = AsyncMock(return_value=summary_data)

            response = test_client.get("/api/v1/cash/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total_cash"] == 50000000
            assert data["total_deposits"] == 30000000
            assert len(data["cash_accounts"]) == 2
            mock_db.get_cash_management_summary.assert_called_once()

    def test_get_cash_management_summary_database_error(self, test_client):
        """현금 관리 요약 정보 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_cash_management_summary = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.get("/api/v1/cash/summary")

            assert response.status_code == 500
            data = response.json()
            assert "현금 관리 요약 정보 조회 중 오류가 발생했습니다" in data["detail"]

    def test_get_cash_balances_success(self, test_client):
        """증권사별 예수금 정보 조회 성공 테스트"""
        balances_data = [
            {
                "account": "증권사A",
                "krw": 15000000,
                "usd": 10000,
                "total_krw": 28850000,
                "updated_at": "2025-01-20T10:00:00",
            },
            {
                "account": "증권사B",
                "krw": 5000000,
                "usd": 5000,
                "total_krw": 11925000,
                "updated_at": "2025-01-20T10:00:00",
            },
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_cash_balances = AsyncMock(return_value=balances_data)

            response = test_client.get("/api/v1/cash/balances/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["account"] == "증권사A"
            assert data[0]["krw"] == 15000000
            mock_db.get_cash_balances.assert_called_once_with(None)

    def test_get_cash_balances_with_account_filter(self, test_client):
        """계좌 필터링하여 증권사별 예수금 정보 조회 성공 테스트"""
        balances_data = [
            {
                "account": "증권사A",
                "krw": 15000000,
                "usd": 10000,
                "total_krw": 28850000,
                "updated_at": "2025-01-20T10:00:00",
            }
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_cash_balances = AsyncMock(return_value=balances_data)

            response = test_client.get("/api/v1/cash/balances/?account=증권사A")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            mock_db.get_cash_balances.assert_called_once_with("증권사A")

    def test_get_cash_balances_database_error(self, test_client):
        """증권사별 예수금 정보 조회 DB 에러 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.get_cash_balances = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.get("/api/v1/cash/balances/")

            assert response.status_code == 500
            data = response.json()
            assert "증권사별 예수금 조회 중 오류가 발생했습니다" in data["detail"]

    def test_update_cash_balance_success(self, test_client):
        """특정 계좌 예수금 업데이트 성공 테스트"""
        from api.models import CashBalanceUpdate

        update_data = {"krw": 20000000, "usd": 15000}

        with patch("api.main.db") as mock_db:
            mock_db.update_cash_balance = AsyncMock(return_value=True)

            response = test_client.put(
                "/api/v1/cash/balances/증권사A", json=update_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert (
                "증권사A 계좌의 예수금이 성공적으로 업데이트되었습니다"
                in data["message"]
            )
            mock_db.update_cash_balance.assert_called_once_with(
                "증권사A", 20000000, 15000
            )

    def test_update_cash_balance_failure(self, test_client):
        """특정 계좌 예수금 업데이트 실패 테스트"""
        from api.models import CashBalanceUpdate

        update_data = {"krw": 20000000, "usd": 15000}

        with patch("api.main.db") as mock_db:
            mock_db.update_cash_balance = AsyncMock(return_value=False)

            response = test_client.put(
                "/api/v1/cash/balances/증권사A", json=update_data
            )

            assert response.status_code == 400
            data = response.json()
            assert "증권사A 계좌의 예수금 업데이트에 실패했습니다" in data["detail"]

    def test_update_cash_balance_database_error(self, test_client):
        """특정 계좌 예수금 업데이트 DB 에러 테스트"""
        from api.models import CashBalanceUpdate

        update_data = {"krw": 20000000, "usd": 15000}

        with patch("api.main.db") as mock_db:
            mock_db.update_cash_balance = AsyncMock(
                side_effect=Exception("Database error")
            )

            response = test_client.put(
                "/api/v1/cash/balances/증권사A", json=update_data
            )

            assert response.status_code == 500
            data = response.json()
            assert "증권사별 예수금 업데이트 중 오류가 발생했습니다" in data["detail"]

    def test_get_time_deposits_success(self, test_client):
        """예적금 정보 조회 성공 테스트"""
        deposits_data = [
            {
                "account": "증권사A",
                "invest_prod_name": "정기예금1",
                "market_value": 10000000,
                "invested_principal": 10000000,
                "maturity_date": "2025-12-31",
                "interest_rate": 0.035,
                "updated_at": "2025-01-20T10:00:00",
            },
            {
                "account": "증권사B",
                "invest_prod_name": "정기예금2",
                "market_value": 20000000,
                "invested_principal": 20000000,
                "maturity_date": "2025-06-30",
                "interest_rate": 0.04,
                "updated_at": "2025-01-20T10:00:00",
            },
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_time_deposits = AsyncMock(return_value=deposits_data)

            response = test_client.get("/api/v1/cash/deposits/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["invest_prod_name"] == "정기예금1"
            mock_db.get_time_deposits.assert_called_once_with(None)

    def test_get_time_deposits_with_account_filter(self, test_client):
        """계좌 필터링하여 예적금 정보 조회 성공 테스트"""
        deposits_data = [
            {
                "account": "증권사A",
                "invest_prod_name": "정기예금1",
                "market_value": 10000000,
                "invested_principal": 10000000,
                "maturity_date": "2025-12-31",
                "interest_rate": 0.035,
                "updated_at": "2025-01-20T10:00:00",
            }
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_time_deposits = AsyncMock(return_value=deposits_data)

            response = test_client.get("/api/v1/cash/deposits/?account=증권사A")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["account"] == "증권사A"
            mock_db.get_time_deposits.assert_called_once_with("증권사A")

    def test_create_time_deposit_success(self, test_client):
        """예적금 생성 성공 테스트"""
        deposit_data = {
            "account": "증권사A",
            "invest_prod_name": "새예적금",
            "market_value": 15000000,
            "invested_principal": 15000000,
            "maturity_date": "2025-12-31",
            "interest_rate": 0.038,
        }

        with patch("api.main.db") as mock_db:
            mock_db.create_time_deposit = AsyncMock(return_value=True)

            response = test_client.post("/api/v1/cash/deposits/", json=deposit_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "예적금이 성공적으로 생성되었습니다" in data["message"]
            mock_db.create_time_deposit.assert_called_once()

    def test_create_time_deposit_failure(self, test_client):
        """예적금 생성 실패 테스트"""
        deposit_data = {
            "account": "증권사A",
            "invest_prod_name": "새예적금",
            "market_value": 15000000,
            "invested_principal": 15000000,
            "maturity_date": "2025-12-31",
            "interest_rate": 0.038,
        }

        with patch("api.main.db") as mock_db:
            mock_db.create_time_deposit = AsyncMock(return_value=False)

            response = test_client.post("/api/v1/cash/deposits/", json=deposit_data)

            assert response.status_code == 400
            data = response.json()
            assert "예적금 생성에 실패했습니다" in data["detail"]

    def test_update_time_deposit_success(self, test_client):
        """예적금 수정 성공 테스트"""
        update_data = {
            "invest_prod_name": "수정된예적금",
            "market_value": 16000000,
            "invested_principal": 15000000,
            "maturity_date": "2025-12-31",
            "interest_rate": 0.04,
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_time_deposit = AsyncMock(return_value=True)

            response = test_client.put(
                "/api/v1/cash/deposits/증권사A", json=update_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "예적금이 성공적으로 수정되었습니다" in data["message"]
            mock_db.update_time_deposit.assert_called_once()

    def test_update_time_deposit_not_found(self, test_client):
        """존재하지 않는 예적금 수정 실패 테스트"""
        update_data = {
            "invest_prod_name": "수정된예적금",
            "market_value": 16000000,
            "invested_principal": 15000000,
            "maturity_date": "2025-12-31",
            "interest_rate": 0.04,
        }

        with patch("api.main.db") as mock_db:
            mock_db.update_time_deposit = AsyncMock(return_value=False)

            response = test_client.put(
                "/api/v1/cash/deposits/존재하지않는계좌", json=update_data
            )

            assert response.status_code == 404
            data = response.json()
            assert "예적금을 찾을 수 없거나 수정에 실패했습니다" in data["detail"]

    def test_delete_time_deposit_success(self, test_client):
        """예적금 삭제 성공 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.delete_time_deposit = AsyncMock(return_value=True)

            response = test_client.delete("/api/v1/cash/deposits/증권사A/정기예금1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "예적금이 성공적으로 삭제되었습니다" in data["message"]
            mock_db.delete_time_deposit.assert_called_once_with("증권사A", "정기예금1")

    def test_delete_time_deposit_not_found(self, test_client):
        """존재하지 않는 예적금 삭제 실패 테스트"""
        with patch("api.main.db") as mock_db:
            mock_db.delete_time_deposit = AsyncMock(return_value=False)

            response = test_client.delete(
                "/api/v1/cash/deposits/존재하지않는계좌/존재하지않는예적금"
            )

            assert response.status_code == 404
            data = response.json()
            assert "예적금을 찾을 수 없거나 삭제에 실패했습니다" in data["detail"]

    def test_update_current_cash_success(self, test_client):
        """현재 현금 업데이트 성공 테스트"""
        cash_data = {"cash": 100000000, "reason": "월급 입금"}

        with patch("api.main.db") as mock_db:
            mock_db.update_current_cash = AsyncMock(return_value=True)

            response = test_client.put("/api/v1/cash/current", json=cash_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "현재 현금이 성공적으로 업데이트되었습니다" in data["message"]
            mock_db.update_current_cash.assert_called_once_with(100000000, "월급 입금")

    def test_update_current_cash_failure(self, test_client):
        """현재 현금 업데이트 실패 테스트"""
        cash_data = {"cash": 100000000, "reason": "월급 입금"}

        with patch("api.main.db") as mock_db:
            mock_db.update_current_cash = AsyncMock(return_value=False)

            response = test_client.put("/api/v1/cash/current", json=cash_data)

            assert response.status_code == 400
            data = response.json()
            assert "현금 업데이트에 실패했습니다" in data["detail"]


class TestCashManagementAPIValidation:
    """Cash Management API 입력값 검증 테스트"""

    def test_cash_balance_update_validation(self, test_client):
        """현금 잔액 업데이트 입력값 검증 테스트"""
        # 필수 필드가 없는 경우
        invalid_data = {"krw": 1000000}  # usd 필드 없음

        response = test_client.put("/api/v1/cash/balances/증권사A", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_time_deposit_creation_validation(self, test_client):
        """예적금 생성 입력값 검증 테스트"""
        # 필수 필드가 없는 경우
        invalid_data = {
            "account": "증권사A",
            "invest_prod_name": "테스트예적금",
            # 다른 필드들 없음
        }

        response = test_client.post("/api/v1/cash/deposits/", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_current_cash_update_validation(self, test_client):
        """현재 현금 업데이트 입력값 검증 테스트"""
        # 필수 필드가 없는 경우
        invalid_data = {"cash": 1000000}  # reason 필드 없음

        response = test_client.put("/api/v1/cash/current", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_negative_cash_amount_validation(self, test_client):
        """음수 현금 금액 검증 테스트"""
        cash_data = {"cash": -1000000, "reason": "테스트"}

        response = test_client.put("/api/v1/cash/current", json=cash_data)

        # API에서 음수 값을 어떻게 처리하는지에 따라 상태 코드가 달라질 수 있음
        assert response.status_code in [400, 422]

    def test_cash_balance_response_structure_validation(self, test_client):
        """현금 잔액 응답 구조 검증 테스트"""
        balances_data = [
            {
                "account": "증권사A",
                "krw": 15000000,
                "usd": 10000,
                "total_krw": 28850000,
                "updated_at": "2025-01-20T10:00:00",
            }
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_cash_balances = AsyncMock(return_value=balances_data)

            response = test_client.get("/api/v1/cash/balances/")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            balance = data[0]
            required_fields = ["account", "krw", "usd", "total_krw", "updated_at"]
            for field in required_fields:
                assert field in balance, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(balance["account"], str)
            assert isinstance(balance["krw"], (int, float))
            assert isinstance(balance["usd"], (int, float))
            assert isinstance(balance["total_krw"], (int, float))

    def test_time_deposit_response_structure_validation(self, test_client):
        """예적금 응답 구조 검증 테스트"""
        deposits_data = [
            {
                "account": "증권사A",
                "invest_prod_name": "정기예금1",
                "market_value": 10000000,
                "invested_principal": 10000000,
                "maturity_date": "2025-12-31",
                "interest_rate": 0.035,
                "updated_at": "2025-01-20T10:00:00",
            }
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_time_deposits = AsyncMock(return_value=deposits_data)

            response = test_client.get("/api/v1/cash/deposits/")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            deposit = data[0]
            required_fields = [
                "account",
                "invest_prod_name",
                "market_value",
                "invested_principal",
                "maturity_date",
                "interest_rate",
                "updated_at",
            ]
            for field in required_fields:
                assert field in deposit, f"필수 필드 '{field}'가 응답에 없습니다"

            # 데이터 타입 검증
            assert isinstance(deposit["account"], str)
            assert isinstance(deposit["market_value"], (int, float))
            assert isinstance(deposit["invested_principal"], (int, float))
            assert isinstance(deposit["interest_rate"], (int, float))
            assert deposit["interest_rate"] >= 0


class TestCashManagementAPIPerformance:
    """Cash Management API 성능 관련 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_cash_balance_requests(self, test_client):
        """동시 현금 잔액 요청 테스트"""
        import asyncio

        balances_data = [
            {
                "account": "증권사A",
                "krw": 15000000,
                "usd": 10000,
                "total_krw": 28850000,
                "updated_at": "2025-01-20T10:00:00",
            }
        ]

        with patch("api.main.db") as mock_db:
            mock_db.get_cash_balances = AsyncMock(return_value=balances_data)

            # 3개의 동시 요청
            tasks = [test_client.get("/api/v1/cash/balances/") for _ in range(3)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 모든 요청이 성공해야 함
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200
                assert len(response.json()) == 1

            # DB가 3번 호출되었는지 확인
            assert mock_db.get_cash_balances.call_count == 3

    def test_cash_management_response_time(self, test_client):
        """현금 관리 응답 시간 테스트"""
        import time

        summary_data = {
            "total_cash": 50000000,
            "total_deposits": 30000000,
            "total_securities_balance": 20000000,
            "cash_accounts": [],
            "deposits_count": 0,
            "last_updated": "2025-01-20T10:00:00",
        }

        with patch("api.main.db") as mock_db:
            # 약간의 지연을 시뮬레이션
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms 지연
                return summary_data

            mock_db.get_cash_management_summary = delayed_response

            start_time = time.time()
            response = test_client.get("/api/v1/cash/summary")
            end_time = time.time()

            assert response.status_code == 200
            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 1초 이하)
            assert (end_time - start_time) < 1.0

    def test_large_deposits_dataset_performance(self, test_client):
        """대용량 예적금 데이터셋 성능 테스트"""
        import time

        # 100개의 대용량 예적금 데이터 생성
        large_deposits = []
        for i in range(100):
            deposit = {
                "account": f"증권사{i % 5}",
                "invest_prod_name": f"예적금{i}",
                "market_value": 10000000 + (i * 100000),
                "invested_principal": 10000000 + (i * 100000),
                "maturity_date": "2025-12-31",
                "interest_rate": 0.03 + (i * 0.001),
                "updated_at": "2025-01-20T10:00:00",
            }
            large_deposits.append(deposit)

        with patch("api.main.db") as mock_db:
            mock_db.get_time_deposits = AsyncMock(return_value=large_deposits)

            start_time = time.time()
            response = test_client.get("/api/v1/cash/deposits/")
            end_time = time.time()

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 100

            # 응답 시간이 합리적인 범위 내에 있어야 함 (여기서는 2초 이하)
            assert (end_time - start_time) < 2.0
