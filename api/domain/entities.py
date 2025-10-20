"""Domain entities representing core business concepts."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass

from .value_objects import AssetCategory, MarketType, Currency


@dataclass
class Asset:
    """자산 엔티티."""

    id: Optional[int] = None
    name: str = ""
    symbol: str = ""
    exchange: str = ""
    sector: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    asset_type: str = "equity"
    region_type: str = "domestic"
    latest_close: Optional[float] = None
    marketcap: Optional[float] = None
    updated_at: Optional[datetime] = None

    def is_etf(self) -> bool:
        """ETF 여부 확인"""
        etf_keywords = [
            "ETF",
            "KODEX",
            "TIGER",
            "ARIRANG",
            "KBSTAR",
            "ACE",
            "PLUS",
            "ARK",
        ]
        return any(keyword in self.name.upper() for keyword in etf_keywords)

    def get_asset_category(self) -> AssetCategory:
        """자산 카테고리 결정"""
        if self.asset_type == "equity" and self.region_type == "domestic":
            return AssetCategory("국내주식")
        elif self.asset_type == "equity" and self.region_type == "global":
            return AssetCategory("해외주식")
        elif self.asset_type == "bond" and self.region_type == "domestic":
            return AssetCategory("국내채권")
        elif self.asset_type == "bond" and self.region_type == "global":
            return AssetCategory("해외채권")
        elif self.asset_type == "REITs" and self.region_type == "domestic":
            return AssetCategory("국내리츠")
        elif self.asset_type == "REITs" and self.region_type == "global":
            return AssetCategory("해외리츠")
        elif self.asset_type == "TDF":
            return AssetCategory("TDF")
        elif self.asset_type == "commodity":
            return AssetCategory("원자재")
        elif self.asset_type == "gold":
            return AssetCategory("금")
        elif self.asset_type == "cash":
            return AssetCategory("현금성자산")
        else:
            return AssetCategory("기타")


@dataclass
class Portfolio:
    """포트폴리오 엔티티."""

    account: str
    assets: List[Asset]
    cash_balance: float = 0.0
    time_deposits: float = 0.0
    updated_at: datetime = datetime.now()

    def total_value_krw(self, usd_rate: float = 1400.0) -> float:
        """총 평가금액 (KRW) 계산"""
        asset_value = sum(
            asset.latest_close or 0
            for asset in self.assets
            if asset.exchange in ["KOSPI", "KOSDAQ"]
        )
        usd_assets = [
            asset for asset in self.assets if asset.exchange not in ["KOSPI", "KOSDAQ"]
        ]
        usd_value = sum((asset.latest_close or 0) * usd_rate for asset in usd_assets)
        return asset_value + usd_value + self.cash_balance + self.time_deposits

    def total_value_usd(self, usd_rate: float = 1400.0) -> float:
        """총 평가금액 (USD) 계산"""
        return self.total_value_krw(usd_rate) / usd_rate

    def asset_allocation(self, usd_rate: float = 1400.0) -> dict:
        """자산 분배 계산"""
        total = self.total_value_krw(usd_rate)
        if total == 0:
            return {}

        allocation = {}
        for asset in self.assets:
            category = asset.get_asset_category()
            value = asset.latest_close or 0
            if asset.exchange not in ["KOSPI", "KOSDAQ"]:
                value *= usd_rate

            if category.value not in allocation:
                allocation[category.value] = 0
            allocation[category.value] += value

        # 현금성자산 추가
        cash_total = self.cash_balance + self.time_deposits
        if cash_total > 0:
            if "현금성자산" not in allocation:
                allocation["현금성자산"] = 0
            allocation["현금성자산"] += cash_total

        # 비율로 변환
        for category in allocation:
            allocation[category] = (allocation[category] / total) * 100

        return allocation


@dataclass
class CashPosition:
    """현금 포지션 엔티티."""

    account: str
    krw: float = 0.0
    usd: float = 0.0
    updated_at: datetime = datetime.now()

    def total_krw(self, usd_rate: float = 1400.0) -> float:
        """KRW 총액 계산"""
        return self.krw + (self.usd * usd_rate)

    def total_usd(self, usd_rate: float = 1400.0) -> float:
        """USD 총액 계산"""
        return self.total_krw(usd_rate) / usd_rate


@dataclass
class TimeDeposit:
    """예적금 엔티티."""

    account: str
    invest_prod_name: str
    market_value: int
    invested_principal: int
    maturity_date: Optional[datetime] = None
    interest_rate: Optional[float] = None
    updated_at: datetime = datetime.now()

    def is_matured(self) -> bool:
        """만기 도래 여부"""
        if not self.maturity_date:
            return False
        return datetime.now() >= self.maturity_date

    def expected_return(self) -> float:
        """예상 수익률 계산"""
        if not self.interest_rate or self.invested_principal == 0:
            return 0.0
        return (
            (self.market_value - self.invested_principal) / self.invested_principal
        ) * 100
