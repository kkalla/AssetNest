from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class PortfolioOverview(BaseModel):
    total_value_krw: float
    total_value_usd: float
    total_pnl_krw: float
    total_pnl_usd: float
    total_return_rate: float
    accounts: List[str]
    # 현금성자산 vs 투자자산 분류
    cash_asset_value: float = 0.0  # 현금성자산 가치 (KRW)
    investment_asset_value: float = 0.0  # 투자자산 가치 (KRW)
    cash_asset_ratio: float = 0.0  # 현금성자산 비율 (%)
    investment_asset_ratio: float = 0.0  # 투자자산 비율 (%)
    investment_allocations: List["AssetAllocation"] = []  # 투자자산 분배비율
    last_updated: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class HoldingResponse(BaseModel):
    id: int
    account: str
    company: str
    market: str  # "국내" or "해외"
    area: Optional[str] = None
    amount: int
    avg_price_krw: float
    current_price_krw: float
    principal: float
    market_value: float
    unrealized_pnl: float  # "unrealized_G/L"
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
    total_realized_pnl: Optional[float] = None  # "total_realized_G/L"


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
    sector_allocation: dict
    region_allocation: dict


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


class HoldingDetail(BaseModel):
    """자산 분배 내 개별 종목 상세 정보"""

    name: str
    symbol: str
    amount: int
    market_value: float
    account: str


class AssetAllocation(BaseModel):
    asset_category: str
    holdings_count: int
    total_market_value: float
    allocation_percentage: float
    holdings: List[str] = []  # 종목 이름 리스트


class AssetAllocationResponse(BaseModel):
    total_portfolio_value: float
    allocations: List[AssetAllocation]
    account: Optional[str] = None
    last_updated: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UnmatchedProduct(BaseModel):
    """by_accounts 테이블에는 있지만 symbol_table에는 없는 상품"""

    account: str
    invest_prod_name: str
    amount: int
    avg_price_krw: Optional[float] = None
    avg_price_usd: Optional[float] = None
    first_buy_at: Optional[date] = None
    last_buy_at: Optional[date] = None


class UnmatchedProductsResponse(BaseModel):
    """매칭되지 않는 상품들의 응답"""

    unmatched_products: List[UnmatchedProduct]
    total_count: int
    accounts_with_unmatched: List[str]
    last_updated: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CashBalance(BaseModel):
    """증권사별 예수금 정보"""

    account: str
    krw: float
    usd: float
    updated_at: datetime


class TimeDeposit(BaseModel):
    """예적금 정보"""

    account: str
    invest_prod_name: str
    market_value: int
    invested_principal: int
    maturity_date: Optional[datetime] = None
    interest_rate: Optional[float] = None
    updated_at: datetime


class BSTimeseries(BaseModel):
    """일별 현금 흐름 정보"""

    date: datetime
    cash: int
    time_deposit: int
    security_cash_balance: int


class CashBalanceUpdate(BaseModel):
    """현금 잔액 업데이트 요청"""

    krw: Optional[float] = None
    usd: Optional[float] = None


class TimeDepositCreate(BaseModel):
    """예적금 생성 요청"""

    account: str
    invest_prod_name: str
    market_value: int
    invested_principal: int
    maturity_date: Optional[datetime] = None
    interest_rate: Optional[float] = None


class TimeDepositUpdate(BaseModel):
    """예적금 수정 요청"""

    market_value: Optional[int] = None
    invested_principal: Optional[int] = None
    maturity_date: Optional[datetime] = None
    interest_rate: Optional[float] = None


class TimeDepositUpdateWithAccount(BaseModel):
    """예적금 수정 요청 (계정 포함)"""

    invest_prod_name: str
    market_value: Optional[int] = None
    invested_principal: Optional[int] = None
    maturity_date: Optional[datetime] = None
    interest_rate: Optional[float] = None


class CashUpdateRequest(BaseModel):
    """현금 업데이트 요청 (bs_timeseries)"""

    cash: int
    reason: Optional[str] = None


class CashManagementSummary(BaseModel):
    """현금 관리 요약 정보"""

    total_cash: int  # 총 현금 잔액
    total_cash_balance: int  # 총 현금 잔액
    total_time_deposit: int  # 총 예적금
    total_security_cash: int  # 총 증권사 예수금
    cash_balances: List[CashBalance]
    time_deposits: List[TimeDeposit]
    latest_bs_entry: Optional[BSTimeseries]
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
