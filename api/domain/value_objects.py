"""Value objects for domain concepts."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Union


class AssetCategory:
    """자산 카테고리 값 객체."""

    def __init__(self, value: str):
        valid_categories = {
            "국내주식",
            "해외주식",
            "국내채권",
            "해외채권",
            "국내리츠",
            "해외리츠",
            "TDF",
            "원자재",
            "금",
            "현금성자산",
            "기타",
        }
        if value not in valid_categories:
            raise ValueError(f"Invalid asset category: {value}")
        self.value = value

    def __eq__(self, other) -> bool:
        return isinstance(other, AssetCategory) and self.value == other.value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"AssetCategory('{self.value}')"


class MarketType:
    """시장 타입 값 객체."""

    def __init__(self, value: str):
        valid_markets = {"KOSPI", "KOSDAQ", "KONEX", "US", "NASDAQ", "NYSE"}
        if value not in valid_markets:
            raise ValueError(f"Invalid market type: {value}")
        self.value = value

    def is_domestic(self) -> bool:
        """국내 시장 여부"""
        return self.value in ["KOSPI", "KOSDAQ", "KONEX"]

    def is_us_market(self) -> bool:
        """미국 시장 여부"""
        return self.value in ["US", "NASDAQ", "NYSE"]

    def __eq__(self, other) -> bool:
        return isinstance(other, MarketType) and self.value == other.value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"MarketType('{self.value}')"


class Currency:
    """통화 값 객체."""

    def __init__(self, code: str):
        valid_currencies = {"KRW", "USD", "EUR", "JPY", "CNY", "GBP"}
        if code not in valid_currencies:
            raise ValueError(f"Invalid currency code: {code}")
        self.code = code

    def is_korean_won(self) -> bool:
        """원화 여부"""
        return self.code == "KRW"

    def is_us_dollar(self) -> bool:
        """미국 달러 여부"""
        return self.code == "USD"

    def __eq__(self, other) -> bool:
        return isinstance(other, Currency) and self.code == other.code

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"Currency('{self.code}')"


class BusinessDate:
    """영업일 값 객체."""

    def __init__(self, date: Union[date, str, datetime]):
        if isinstance(date, str):
            self.date = datetime.fromisoformat(date).date()
        elif isinstance(date, datetime):
            self.date = date.date()
        else:
            self.date = date

        if not self._is_valid_business_day(self.date):
            raise ValueError(f"Invalid business date: {self.date}")

    def _is_valid_business_day(self, date: date) -> bool:
        """유효한 영업일인지 확인 (평일만 영업일로 가정)"""
        return date.weekday() < 5  # 0-4는 월-금

    def is_today(self) -> bool:
        """오늘인지 확인"""
        return self.date == date.today()

    def days_until_today(self) -> int:
        """오늘까지 남은 일수"""
        return (date.today() - self.date).days

    def __eq__(self, other) -> bool:
        return isinstance(other, BusinessDate) and self.date == other.date

    def __str__(self) -> str:
        return self.date.isoformat()

    def __repr__(self) -> str:
        return f"BusinessDate('{self.date}')"


class Money:
    """금액 값 객체."""

    def __init__(self, amount: Union[float, int, Decimal], currency: Currency):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.amount = Decimal(str(amount))
        self.currency = currency

    def add(self, other: "Money") -> "Money":
        """금액 더하기"""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        """금액 빼기"""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        if self.amount < other.amount:
            raise ValueError("Insufficient funds")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Union[float, int, Decimal]) -> "Money":
        """금액 곱하기"""
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def convert_to(self, target_currency: Currency, exchange_rate: float) -> "Money":
        """다른 통화로 변환"""
        if exchange_rate <= 0:
            raise ValueError("Exchange rate must be positive")
        converted_amount = float(self.amount) * exchange_rate
        return Money(converted_amount, target_currency)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Money)
            and self.amount == other.amount
            and self.currency == other.currency
        )

    def __str__(self) -> str:
        return f"{self.amount:,.2f} {self.currency.code}"

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency})"
