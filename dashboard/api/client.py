"""
통합 API 클라이언트
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import streamlit as st

from .endpoints import APIEndpoints
from dashboard.config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """통합 API 클라이언트"""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = base_url or settings.API_BASE_URL
        self.timeout = timeout or settings.API_TIMEOUT
        self.session = requests.Session()

        # 기본 헤더 설정
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """API 요청 공통 메소드"""
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"📡 API 요청: {method.upper()} {url}")

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                timeout=self.timeout,
                **kwargs
            )

            if response.status_code == 200:
                logger.info(f"✅ API 응답 성공: {url}")
                return response.json()
            else:
                error_msg = f"API 오류: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                st.error(error_msg)
                return None

        except requests.RequestException as e:
            error_msg = f"API 요청 실패: {str(e)}"
            logger.error(f"💥 {error_msg}")
            st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")
            return None
        except Exception as e:
            error_msg = f"알 수 없는 오류: {str(e)}"
            logger.error(f"💥 {error_msg}")
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")
            return None

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """GET 요청"""
        return self._make_request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """POST 요청"""
        return self._make_request("POST", endpoint, json_data=json_data, **kwargs)

    def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """PUT 요청"""
        return self._make_request("PUT", endpoint, json_data=json_data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """DELETE 요청"""
        return self._make_request("DELETE", endpoint, **kwargs)


class PortfolioAPI:
    """포트폴리오 관련 API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_overview(self, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """포트폴리오 개요 조회"""
        endpoint = APIEndpoints.get_portfolio_overview_url()
        params = {"account": account} if account else None
        return self.client.get(endpoint, params=params)

    def get_summary(self, account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """포트폴리오 요약 조회"""
        endpoint = APIEndpoints.get_portfolio_summary_url(account)
        return self.client.get(endpoint)

    def get_allocation(self, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """자산 분배 정보 조회"""
        endpoint = APIEndpoints.PORTFOLIO_ALLOCATION
        params = {"account": account} if account else None
        return self.client.get(endpoint, params=params)


class HoldingsAPI:
    """보유 종목 관련 API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_holdings(
        self,
        account: Optional[str] = None,
        market: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """보유 종목 조회"""
        endpoint = APIEndpoints.get_holdings_url(account, market)
        result = self.client.get(endpoint)
        return result if isinstance(result, list) else []

    def refresh_prices(self) -> bool:
        """주식 가격 새로고침"""
        endpoint = APIEndpoints.STOCKS_REFRESH_PRICES
        result = self.client.post(endpoint)
        return result is not None


class CashAPI:
    """현금 관리 관련 API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_summary(self) -> Optional[Dict[str, Any]]:
        """현금 관리 요약 조회"""
        endpoint = APIEndpoints.CASH_SUMMARY
        return self.client.get(endpoint)

    def get_balances(self, account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """증권사별 예수금 조회"""
        endpoint = APIEndpoints.get_cash_balances_url(account)
        result = self.client.get(endpoint)
        return result if isinstance(result, list) else []

    def update_balance(
        self,
        account: str,
        krw: Optional[float] = None,
        usd: Optional[float] = None
    ) -> bool:
        """예수금 업데이트"""
        endpoint = APIEndpoints.build_url(APIEndpoints.CASH_BALANCES_BY_ACCOUNT, account=account)
        update_data = {}
        if krw is not None:
            update_data["krw"] = krw
        if usd is not None:
            update_data["usd"] = usd

        result = self.client.put(endpoint, json_data=update_data)
        return result is not None

    def get_time_deposits(self, account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """예적금 정보 조회"""
        endpoint = APIEndpoints.get_time_deposits_url(account)
        result = self.client.get(endpoint)
        return result if isinstance(result, list) else []

    def create_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: float,
        invested_principal: float,
        maturity_date: Optional[str] = None,
        interest_rate: Optional[float] = None
    ) -> bool:
        """예적금 생성"""
        endpoint = APIEndpoints.CASH_DEPOSITS
        create_data = {
            "account": account,
            "invest_prod_name": invest_prod_name,
            "market_value": market_value,
            "invested_principal": invested_principal,
        }
        if maturity_date:
            create_data["maturity_date"] = maturity_date
        if interest_rate is not None:
            create_data["interest_rate"] = interest_rate

        result = self.client.post(endpoint, json_data=create_data)
        return result is not None

    def update_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: Optional[float] = None,
        invested_principal: Optional[float] = None,
        maturity_date: Optional[str] = None,
        interest_rate: Optional[float] = None
    ) -> bool:
        """예적금 수정"""
        endpoint = APIEndpoints.build_url(APIEndpoints.CASH_DEPOSITS_BY_ACCOUNT, account=account)
        update_data = {"invest_prod_name": invest_prod_name}

        if market_value is not None:
            update_data["market_value"] = market_value
        if invested_principal is not None:
            update_data["invested_principal"] = invested_principal
        if maturity_date is not None:
            update_data["maturity_date"] = maturity_date
        if interest_rate is not None:
            update_data["interest_rate"] = interest_rate

        result = self.client.put(endpoint, json_data=update_data)
        return result is not None

    def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        endpoint = APIEndpoints.build_url(
            APIEndpoints.CASH_DEPOSITS_DELETE,
            account=account,
            product_name=invest_prod_name
        )
        result = self.client.delete(endpoint)
        return result is not None

    def update_current_cash(self, cash: float, reason: Optional[str] = None) -> bool:
        """현재 현금 업데이트"""
        endpoint = APIEndpoints.CASH_CURRENT
        update_data = {"cash": cash}
        if reason:
            update_data["reason"] = reason

        result = self.client.put(endpoint, json_data=update_data)
        return result is not None


class CurrencyAPI:
    """환율 관련 API"""

    def __init__(self, client: APIClient):
        self.client = client

    def get_rates(self) -> Optional[List[Dict[str, Any]]]:
        """환율 정보 조회"""
        endpoint = APIEndpoints.CURRENCY_RATES
        result = self.client.get(endpoint)
        return result if isinstance(result, list) else []


# 전역 API 클라이언트 인스턴스
api_client = APIClient()

# API 서비스 인스턴스
portfolio_api = PortfolioAPI(api_client)
holdings_api = HoldingsAPI(api_client)
cash_api = CashAPI(api_client)
currency_api = CurrencyAPI(api_client)