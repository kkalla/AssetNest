"""
데이터 모델 정의
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import streamlit as st


@dataclass
class PortfolioOverview:
    """포트폴리오 개요 데이터 모델"""
    total_value_krw: float
    total_value_usd: float
    total_pnl_krw: float
    total_pnl_usd: float
    total_return_rate: float
    cash_asset_value: float
    investment_asset_value: float
    cash_asset_ratio: float
    investment_asset_ratio: float
    investment_allocations: List[Dict[str, Any]]
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioOverview":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            total_value_krw=data.get("total_value_krw", 0),
            total_value_usd=data.get("total_value_usd", 0),
            total_pnl_krw=data.get("total_pnl_krw", 0),
            total_pnl_usd=data.get("total_pnl_usd", 0),
            total_return_rate=data.get("total_return_rate", 0),
            cash_asset_value=data.get("cash_asset_value", 0),
            investment_asset_value=data.get("investment_asset_value", 0),
            cash_asset_ratio=data.get("cash_asset_ratio", 0),
            investment_asset_ratio=data.get("investment_asset_ratio", 0),
            investment_allocations=data.get("investment_allocations", []),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class HoldingData:
    """보유 종목 데이터 모델"""
    company: str
    account: str
    market: str
    amount: int
    avg_price_krw: float
    current_price_krw: float
    market_value: float
    unrealized_pnl: float
    return_rate: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoldingData":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            company=data.get("company", ""),
            account=data.get("account", ""),
            market=data.get("market", ""),
            amount=int(data.get("amount", 0)),
            avg_price_krw=float(data.get("avg_price_krw", 0)),
            current_price_krw=float(data.get("current_price_krw", 0)),
            market_value=float(data.get("market_value", 0)),
            unrealized_pnl=float(data.get("unrealized_pnl", 0)),
            return_rate=float(data.get("return_rate", 0))
        )


@dataclass
class CashBalance:
    """현금 잔고 데이터 모델"""
    account: str
    krw: float
    usd: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CashBalance":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            account=data.get("account", ""),
            krw=float(data.get("krw", 0)),
            usd=float(data.get("usd", 0))
        )

    @property
    def total_krw(self, usd_to_krw_rate: float = 1400) -> float:
        """총액 (KRW) 계산"""
        return self.krw + (self.usd * usd_to_krw_rate)


@dataclass
class TimeDeposit:
    """예적금 데이터 모델"""
    account: str
    invest_prod_name: str
    market_value: float
    invested_principal: float
    maturity_date: Optional[date] = None
    interest_rate: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeDeposit":
        """딕셔너리에서 인스턴스 생성"""
        maturity_date = data.get("maturity_date")
        if maturity_date:
            if isinstance(maturity_date, str):
                maturity_date = datetime.fromisoformat(maturity_date).date()
            elif isinstance(maturity_date, datetime):
                maturity_date = maturity_date.date()

        return cls(
            account=data.get("account", ""),
            invest_prod_name=data.get("invest_prod_name", ""),
            market_value=float(data.get("market_value", 0)),
            invested_principal=float(data.get("invested_principal", 0)),
            maturity_date=maturity_date,
            interest_rate=data.get("interest_rate")
        )

    @property
    def interest_amount(self) -> float:
        """이자 금액 계산"""
        return self.market_value - self.invested_principal

    @property
    def return_rate(self) -> float:
        """수익률 계산"""
        if self.invested_principal > 0:
            return (self.interest_amount / self.invested_principal) * 100
        return 0


@dataclass
class CurrencyRate:
    """환율 데이터 모델"""
    currency: str
    exchange_rate: float
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurrencyRate":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            currency=data.get("currency", ""),
            exchange_rate=float(data.get("exchange_rate", 0)),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class AssetAllocation:
    """자산 분배 데이터 모델"""
    asset_category: str
    holdings_count: int
    total_market_value: float
    allocation_percentage: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetAllocation":
        """딕셔너리에서 인스턴스 생성"""
        return cls(
            asset_category=data.get("asset_category", ""),
            holdings_count=int(data.get("holdings_count", 0)),
            total_market_value=float(data.get("total_market_value", 0)),
            allocation_percentage=float(data.get("allocation_percentage", 0))
        )


@dataclass
class BSTimeseriesEntry:
    """BS 시계열 데이터 모델"""
    date: date
    cash: float
    time_deposit: float
    security_cash_balance: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BSTimeseriesEntry":
        """딕셔너리에서 인스턴스 생성"""
        entry_date = data.get("date")
        if isinstance(entry_date, str):
            entry_date = datetime.fromisoformat(entry_date).date()
        elif isinstance(entry_date, datetime):
            entry_date = entry_date.date()

        return cls(
            date=entry_date or date.today(),
            cash=float(data.get("cash", 0)),
            time_deposit=float(data.get("time_deposit", 0)),
            security_cash_balance=float(data.get("security_cash_balance", 0))
        )

    @property
    def total_cash_assets(self) -> float:
        """총 현금성자산"""
        return self.cash + self.time_deposit + self.security_cash_balance


class DataValidator:
    """데이터 검증 유틸리티"""

    @staticmethod
    def validate_portfolio_data(data: Dict[str, Any]) -> bool:
        """포트폴리오 데이터 검증"""
        required_fields = ["total_value_krw", "total_pnl_krw", "total_return_rate"]
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_holding_data(data: Dict[str, Any]) -> bool:
        """보유 종목 데이터 검증"""
        required_fields = ["company", "account", "market_value", "return_rate"]
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_cash_balance(data: Dict[str, Any]) -> bool:
        """현금 잔고 데이터 검증"""
        required_fields = ["account", "krw"]
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_time_deposit(data: Dict[str, Any]) -> bool:
        """예적금 데이터 검증"""
        required_fields = ["account", "invest_prod_name", "market_value", "invested_principal"]
        return all(field in data for field in required_fields)


class DataFrameConverter:
    """데이터프레임 변환 유틸리티"""

    @staticmethod
    def holdings_to_dataframe(holdings: List[HoldingData]) -> pd.DataFrame:
        """보유 종목 리스트를 데이터프레임으로 변환"""
        if not holdings:
            return pd.DataFrame()

        data = [
            {
                "company": h.company,
                "account": h.account,
                "market": h.market,
                "amount": h.amount,
                "avg_price_krw": h.avg_price_krw,
                "current_price_krw": h.current_price_krw,
                "market_value": h.market_value,
                "unrealized_pnl": h.unrealized_pnl,
                "return_rate": h.return_rate
            }
            for h in holdings
        ]
        return pd.DataFrame(data)

    @staticmethod
    def cash_balances_to_dataframe(balances: List[CashBalance], usd_to_krw_rate: float = 1400) -> pd.DataFrame:
        """현금 잔고 리스트를 데이터프레임으로 변환"""
        if not balances:
            return pd.DataFrame()

        data = [
            {
                "account": b.account,
                "krw": b.krw,
                "usd": b.usd,
                "total_krw": b.total_krw(usd_to_krw_rate),
                "krw_formatted": f"₩{b.krw:,.0f}",
                "usd_formatted": f"${b.usd:,.2f}"
            }
            for b in balances
        ]
        return pd.DataFrame(data)

    @staticmethod
    def time_deposits_to_dataframe(deposits: List[TimeDeposit]) -> pd.DataFrame:
        """예적금 리스트를 데이터프레임으로 변환"""
        if not deposits:
            return pd.DataFrame()

        data = [
            {
                "account": d.account,
                "invest_prod_name": d.invest_prod_name,
                "market_value": d.market_value,
                "invested_principal": d.invested_principal,
                "maturity_date": d.maturity_date,
                "interest_rate": d.interest_rate,
                "interest_amount": d.interest_amount,
                "return_rate": d.return_rate,
                "market_value_formatted": f"₩{d.market_value:,.0f}",
                "invested_principal_formatted": f"₩{d.invested_principal:,.0f}",
                "maturity_date_formatted": d.maturity_date if d.maturity_date else "-",
                "interest_rate_formatted": f"{d.interest_rate:.2f}%" if d.interest_rate else "-"
            }
            for d in deposits
        ]
        return pd.DataFrame(data)

    @staticmethod
    def asset_allocations_to_dataframe(allocations: List[AssetAllocation]) -> pd.DataFrame:
        """자산 분배 리스트를 데이터프레임으로 변환"""
        if not allocations:
            return pd.DataFrame()

        data = [
            {
                "asset_category": a.asset_category,
                "holdings_count": a.holdings_count,
                "total_market_value": a.total_market_value,
                "allocation_percentage": a.allocation_percentage,
                "total_market_value_formatted": f"₩{a.total_market_value:,.0f}",
                "allocation_percentage_formatted": f"{a.allocation_percentage:.0f}%"
            }
            for a in allocations
        ]
        return pd.DataFrame(data)