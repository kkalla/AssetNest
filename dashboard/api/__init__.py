"""
AssetNest Dashboard API 클라이언트 모듈
"""
from .client import APIClient, PortfolioAPI, HoldingsAPI, CashAPI, CurrencyAPI
from .endpoints import APIEndpoints

# API 클라이언트 인스턴스 생성
portfolio_api = PortfolioAPI(APIClient())
holdings_api = HoldingsAPI(APIClient())
cash_api = CashAPI(APIClient())
currency_api = CurrencyAPI(APIClient())

__all__ = [
    "APIClient",
    "APIEndpoints",
    "portfolio_api",
    "holdings_api",
    "cash_api",
    "currency_api"
]