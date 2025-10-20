"""Database models and schemas for AssetNest API."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class DatabaseModels:
    """데이터베이스 모델 정의 클래스."""

    # 포트폴리오 관련 모델
    class PortfolioOverview(BaseModel):
        total_value_krw: float
        total_value_usd: float
        total_pnl_krw: float
        total_pnl_usd: float
        total_return_rate: float
        accounts: List[str]
        cash_asset_value: float = 0.0
        investment_asset_value: float = 0.0
        cash_asset_ratio: float = 0.0
        investment_asset_ratio: float = 0.0
        investment_allocations: List[Dict[str, Any]] = []
        last_updated: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    class HoldingResponse(BaseModel):
        id: int
        account: str
        company: str
        market: str
        area: Optional[str] = None
        amount: int
        avg_price_krw: float
        current_price_krw: float
        principal: float
        market_value: float
        unrealized_pnl: float
        return_rate: float
        avg_price_usd: Optional[float] = None
        current_price_usd: Optional[float] = None
        principal_usd: Optional[float] = None
        market_value_usd: Optional[float] = None
        unrealized_pnl_usd: Optional[float] = None
        return_rate_usd: Optional[float] = None
        first_buy_at: Optional[date] = None
        last_buy_at: Optional[date] = None
        last_sell_at: Optional[date] = None
        total_realized_pnl: Optional[float] = None

    class AssetAllocation(BaseModel):
        asset_category: str
        holdings_count: int
        total_market_value: float
        allocation_percentage: float
        holdings: List[str] = []

    class AssetAllocationResponse(BaseModel):
        total_portfolio_value: float
        allocations: List["DatabaseModels.AssetAllocation"]
        account: Optional[str] = None
        last_updated: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    class UnmatchedProduct(BaseModel):
        account: str
        invest_prod_name: str
        amount: int
        avg_price_krw: Optional[float] = None
        avg_price_usd: Optional[float] = None
        first_buy_at: Optional[date] = None
        last_buy_at: Optional[date] = None

    class UnmatchedProductsResponse(BaseModel):
        unmatched_products: List["DatabaseModels.UnmatchedProduct"]
        total_count: int
        accounts_with_unmatched: List[str]
        last_updated: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    class PortfolioSummary(BaseModel):
        account: str
        valuation_amount: int
        profit_loss: int
        profit_loss_rate: float
        updated_at: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    class TopHolding(BaseModel):
        name: str
        symbol: str
        valuation_amount: int
        profit_loss: int
        profit_loss_rate: float
        account: str
        sector: Optional[str] = None
        updated_at: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    class HoldingDetail(BaseModel):
        account: str
        name: str
        symbol: str
        quantity: int
        average_price: float
        current_price: float
        valuation_amount: float
        profit_loss: float
        profit_loss_rate: float
        currency: str
        sector: Optional[str] = None
        asset_type: Optional[str] = None
        region_type: Optional[str] = None
        updated_at: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    # 주식 관련 모델
    class StockInfo(BaseModel):
        id: int
        company: str
        symbol: str
        exchange: str
        sector: Optional[str] = None
        industry: Optional[str] = None
        area: Optional[str] = None
        latest_close: Optional[float] = None
        marketcap: Optional[float] = None
        updated_at: Optional[datetime] = None

    class PerformanceData(BaseModel):
        account: str
        total_investment: float
        total_value: float
        total_return: float
        return_rate: float
        sector_allocation: Dict[str, float]
        region_allocation: Dict[str, float]

    # 현금 관련 모델
    class CashBalance(BaseModel):
        account: str
        krw: float
        usd: float
        updated_at: datetime

    class TimeDeposit(BaseModel):
        account: str
        invest_prod_name: str
        market_value: int
        invested_principal: int
        maturity_date: Optional[datetime] = None
        interest_rate: Optional[float] = None
        updated_at: datetime

    class BSTimeseries(BaseModel):
        date: datetime
        cash: int
        time_deposit: int
        security_cash_balance: int

    class CashBalanceUpdate(BaseModel):
        krw: Optional[float] = None
        usd: Optional[float] = None

    class TimeDepositCreate(BaseModel):
        account: str
        invest_prod_name: str
        market_value: int
        invested_principal: int
        maturity_date: Optional[datetime] = None
        interest_rate: Optional[float] = None

    class TimeDepositUpdate(BaseModel):
        market_value: Optional[int] = None
        invested_principal: Optional[int] = None
        maturity_date: Optional[datetime] = None
        interest_rate: Optional[float] = None

    class CashManagementSummary(BaseModel):
        total_cash: int
        total_cash_balance: int
        total_time_deposit: int
        total_security_cash: int
        cash_balances: List["DatabaseModels.CashBalance"]
        time_deposits: List["DatabaseModels.TimeDeposit"]
        latest_bs_entry: Optional["DatabaseModels.BSTimeseries"]
        updated_at: datetime

        class Config:
            json_encoders = {datetime: lambda v: v.isoformat()}

    # 환율 관련 모델
    class CurrencyRate(BaseModel):
        currency: str
        exchange_rate: float
        updated_at: datetime

    class MarketSummary(BaseModel):
        domestic_value: float
        international_value: float
        domestic_pnl: float
        international_pnl: float
        domestic_return_rate: float
        international_return_rate: float
