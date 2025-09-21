from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal


class PortfolioOverview(BaseModel):
    total_value_krw: float
    total_value_usd: float
    total_pnl_krw: float
    total_pnl_usd: float
    total_return_rate: float
    accounts: List[str]
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
