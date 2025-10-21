"""
API 엔드포인트 정의
"""
from typing import Dict, Any, Optional


class APIEndpoints:
    """API 엔드포인트 상수"""

    # 포트폴리오 관련
    PORTFOLIO_OVERVIEW = "/portfolio/overview"
    PORTFOLIO_SUMMARY = "/portfolio/summary"
    PORTFOLIO_ALLOCATION = "/portfolio/allocation"

    # 보유 종목 관련
    HOLDINGS = "/holdings/"
    HOLDINGS_BY_ACCOUNT = "/holdings/{account}"

    # 현금 관리 관련
    CASH_SUMMARY = "/cash/summary"
    CASH_BALANCES = "/cash/balances/"
    CASH_BALANCES_BY_ACCOUNT = "/cash/balances/{account}"
    CASH_DEPOSITS = "/cash/deposits/"
    CASH_DEPOSITS_BY_ACCOUNT = "/cash/deposits/{account}"
    CASH_DEPOSITS_DELETE = "/cash/deposits/{account}/{product_name}"
    CASH_CURRENT = "/cash/current"

    # 환율 관련
    CURRENCY_RATES = "/currency/rates"
    CURRENCY_REFRESH = "/currency/refresh"

    # 주식 관련
    STOCKS_REFRESH_PRICES = "/stocks/refresh-prices"

    # 성과 분석 관련
    ANALYTICS_PERFORMANCE = "/analytics/performance/{account}"
    ANALYTICS_SECTOR_ALLOCATION = "/analytics/sector-allocation/{account}"
    ANALYTICS_REGION_ALLOCATION = "/analytics/region-allocation/{account}"

    @staticmethod
    def build_url(endpoint: str, **kwargs) -> str:
        """엔드포인트 URL 빌드"""
        if kwargs:
            return endpoint.format(**kwargs)
        return endpoint

    @staticmethod
    def get_portfolio_overview_url() -> str:
        """포트폴리오 개요 URL"""
        return APIEndpoints.PORTFOLIO_OVERVIEW

    @staticmethod
    def get_portfolio_summary_url(account: Optional[str] = None) -> str:
        """포트폴리오 요약 URL"""
        if account:
            return f"{APIEndpoints.PORTFOLIO_SUMMARY}/{account}"
        return APIEndpoints.PORTFOLIO_SUMMARY

    @staticmethod
    def get_holdings_url(account: Optional[str] = None, market: Optional[str] = None) -> str:
        """보유 종목 URL"""
        params = []
        if account:
            params.append(f"account={account}")
        if market:
            params.append(f"market={market}")

        base_url = APIEndpoints.HOLDINGS
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url

    @staticmethod
    def get_cash_balances_url(account: Optional[str] = None) -> str:
        """증권사별 예수금 URL"""
        if account:
            return APIEndpoints.build_url(APIEndpoints.CASH_BALANCES_BY_ACCOUNT, account=account)
        return APIEndpoints.CASH_BALANCES

    @staticmethod
    def get_time_deposits_url(account: Optional[str] = None) -> str:
        """예적금 URL"""
        if account:
            return APIEndpoints.build_url(APIEndpoints.CASH_DEPOSITS_BY_ACCOUNT, account=account)
        return APIEndpoints.CASH_DEPOSITS