"""Market data adapter for external API integrations."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, Tuple, List
import time

try:
    import FinanceDataReader as fdr
    import yfinance as yf
except ImportError as e:
    logging.warning(f"Market data libraries not available: {e}")
    fdr = None
    yf = None

logger = logging.getLogger(__name__)


class IMarketDataProvider(ABC):
    """시장 데이터 제공자 인터페이스."""

    @abstractmethod
    async def get_korean_stock_data(
        self, symbol: str, exchange: str = "KOSPI"
    ) -> Tuple[Optional[float], Optional[float], Optional[date]]:
        """국내 주식/ETF 가격 정보 조회"""
        pass

    @abstractmethod
    async def get_stock_data_yfinance(
        self, symbol: str
    ) -> Tuple[Optional[float], Optional[float], Optional[date]]:
        """yfinance로 주식 정보 조회"""
        pass

    @abstractmethod
    def search_symbol_info(self, product_name: str) -> Optional[dict]:
        """종목명으로 심볼 정보 검색"""
        pass


class MarketDataAdapter(IMarketDataProvider):
    """시장 데이터 어댑터."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def _retry_async_call(self, func, *args, **kwargs):
        """비동기 함수 재시도 래퍼"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}, retrying in {self.retry_delay}s..."
                )
                await asyncio.sleep(self.retry_delay)
                self.retry_delay *= 2  # Exponential backoff

    def _retry_sync_call(self, func, *args, **kwargs):
        """동기 함수 재시도 래퍼"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}, retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)
                self.retry_delay *= 2  # Exponential backoff

    async def get_korean_stock_data(
        self, symbol: str, exchange: str = "KOSPI"
    ) -> Tuple[Optional[float], Optional[float], Optional[date]]:
        """국내 주식/ETF 가격 정보 조회 (FinanceDataReader + yfinance)"""
        if not fdr or not yf:
            logger.error("FinanceDataReader or yfinance not available")
            return None, None, None

        def _get_data():
            latest_close_fdr = None
            marketcap_fdr = None
            price_date_fdr = None

            # 먼저 ETF 리스트에서 확인
            try:
                etf_list = fdr.StockListing("ETF/KR")
                etf_info = etf_list[etf_list["Symbol"] == symbol]

                if not etf_info.empty:
                    # ETF인 경우
                    etf_data = etf_info.iloc[0]
                    latest_close_fdr = float(etf_data["Price"])
                    marketcap_fdr = (
                        float(etf_data["MarCap"]) / 100
                    )  # 억원 -> 십억원 단위
                    price_date_fdr = datetime.now().date()
                    logger.info(
                        f"📊 ETF {symbol}: price={latest_close_fdr}, "
                        f"marketcap={marketcap_fdr}B KRW, date={price_date_fdr}"
                    )
                    return latest_close_fdr, marketcap_fdr, price_date_fdr
            except Exception as e:
                logger.warning(f"ETF 리스트 조회 실패 ({symbol}): {e}")

            # ETF가 아니면 일반 주식으로 처리
            try:
                df = fdr.DataReader(symbol, "2024-01-01")
                if not df.empty:
                    latest_close_fdr = df["Close"].iloc[-1]
                    price_date_fdr = df.index[-1].date()
                    logger.info(
                        f"📊 FinanceDataReader {symbol}: {latest_close_fdr}, date={price_date_fdr}"
                    )
                else:
                    logger.warning(f"⚠️ FinanceDataReader {symbol}: 데이터 없음")
            except Exception as e:
                logger.error(f"❌ FinanceDataReader {symbol} 오류: {e}")

            # yfinance로 백업 조회 및 marketcap
            ticker_suffix = ".KS" if exchange == "KOSPI" else ".KQ"
            yf_ticker = f"{symbol}{ticker_suffix}"
            latest_close_yf, marketcap_yf, price_date_yf = (
                self._get_stock_data_yfinance_sync(yf_ticker)
            )

            latest_close = (
                latest_close_fdr if latest_close_fdr is not None else latest_close_yf
            )
            marketcap = marketcap_fdr if marketcap_fdr is not None else marketcap_yf
            price_date = price_date_fdr if price_date_fdr is not None else price_date_yf

            return latest_close, marketcap, price_date

        return await self._retry_async_call(asyncio.to_thread, _get_data)

    def _get_stock_data_yfinance_sync(
        self, symbol: str
    ) -> Tuple[Optional[float], Optional[float], Optional[date]]:
        """yfinance로 주식 정보 조회 (동기)"""
        if not yf:
            return None, None, None

        try:
            ticker = yf.Ticker(symbol)

            # 최근 1일 데이터 조회하여 날짜 확보
            hist = ticker.history(period="1d")

            latest_close = None
            price_date = None

            if not hist.empty:
                latest_close = hist["Close"].iloc[-1]
                price_date = hist.index[-1].date()
            else:
                # history가 비어있으면 info에서 가져오기
                info = ticker.info
                latest_close = info.get("currentPrice") or info.get(
                    "regularMarketPrice"
                )
                # regularMarketTime은 epoch timestamp (초 단위)
                market_time = info.get("regularMarketTime")
                if market_time:
                    price_date = datetime.fromtimestamp(market_time).date()
                else:
                    # 날짜 정보가 없으면 현재 날짜 사용
                    price_date = datetime.now().date()

            # 시가총액
            info = ticker.info
            marketcap = info.get("marketCap")
            if marketcap:
                marketcap = marketcap / 1_000_000_000  # 십억 단위로 변환

            return latest_close, marketcap, price_date
        except Exception as e:
            logger.error(f"❌ yfinance {symbol} 오류: {e}")
            return None, None, None

    async def get_stock_data_yfinance(
        self, symbol: str
    ) -> Tuple[Optional[float], Optional[float], Optional[date]]:
        """yfinance로 주식 정보 조회 (비동기)"""
        return await self._retry_async_call(
            asyncio.to_thread, self._get_stock_data_yfinance_sync, symbol
        )

    def search_symbol_info(self, product_name: str) -> Optional[dict]:
        """종목명으로 심볼 정보 검색 (국내 + 해외)"""
        if not fdr or not yf:
            logger.error("FinanceDataReader or yfinance not available")
            return None

        def _search():
            # 1. 먼저 국내 주식/ETF 검색 (KRX)
            krx_stocks = fdr.StockListing("KRX")

            # ETF도 포함해서 검색
            matched = krx_stocks[
                krx_stocks["Name"].str.contains(product_name, na=False, regex=False)
            ]

            # ETF 리스트도 별도로 검색
            is_etf = False
            if len(matched) == 0:
                try:
                    etf_list = fdr.StockListing("ETF/KR")
                    matched = etf_list[
                        etf_list["Name"].str.contains(
                            product_name, na=False, regex=False
                        )
                    ]
                    is_etf = True
                except:
                    pass

            if len(matched) > 0:
                stock = matched.iloc[0]

                # ETF와 일반 주식의 컬럼명이 다를 수 있음
                if is_etf:
                    code = (
                        stock.get("Code")
                        or stock.get("Symbol")
                        or stock.get("종목코드")
                    )
                    market = stock.get("Market") or "KOSPI"
                    if not code:
                        logger.error(f"ETF 코드를 찾을 수 없음: {stock.to_dict()}")
                        return None
                else:
                    code = stock["Code"]
                    market = stock["Market"]

                # yfinance로 sector/industry 정보 가져오기
                ticker_suffix = ".KS" if market == "KOSPI" else ".KQ"
                yf_ticker = f"{code}{ticker_suffix}"

                sector = None
                industry = None
                try:
                    yf_stock = yf.Ticker(yf_ticker)
                    yf_info = yf_stock.info
                    sector = yf_info.get("sector")
                    industry = yf_info.get("industry")
                except:
                    pass

                symbol_info = {
                    "symbol": code,
                    "exchange": market,
                    "sector": sector,
                    "industry": industry,
                    "asset_type": "equity",
                    "region_type": "domestic",
                    "latest_close": stock.get("Close", 0),
                    "marketcap": (
                        stock.get("Marcap", 0) / 10**9 if stock.get("Marcap") else None
                    ),
                }
                logger.info(
                    f"✅ 국내 심볼 발견: {product_name} -> {code} ({market}, sector: {sector})"
                )
                return symbol_info

            # 2. 해외 주식 검색 시도 (yfinance)
            potential_tickers = [
                product_name,  # 그대로
                product_name.upper(),  # 대문자
                product_name.replace(" ", ""),  # 공백 제거
            ]

            for ticker in potential_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info

                    # 유효한 티커인지 확인
                    if info.get("longName") or info.get("shortName"):
                        symbol_info = {
                            "symbol": ticker,
                            "exchange": info.get("exchange", "US"),
                            "sector": info.get("sector", None),
                            "industry": info.get("industry", None),
                            "asset_type": "equity",
                            "region_type": "global",
                        }
                        logger.info(
                            f"✅ 해외 심볼 발견: {product_name} -> {ticker} ({info.get('exchange', 'US')})"
                        )
                        return symbol_info
                except:
                    continue

            logger.warning(f"⚠️ 심볼 찾지 못함: {product_name}")
            return None

        return self._retry_sync_call(_search)

    def check_if_etf(self, name: str, symbol: str, exchange: str) -> bool:
        """ETF 여부 확인"""
        if not fdr or not yf:
            return False

        # 국내 ETF 체크
        if exchange in ["KOSPI", "KOSDAQ"]:
            try:
                etf_list = fdr.StockListing("ETF/KR")
                etf_info = etf_list[etf_list["Symbol"] == symbol]
                if not etf_info.empty:
                    return True
            except Exception as e:
                logger.debug(f"ETF 체크 실패 ({symbol}): {e}")

        # 이름에 ETF 키워드 포함 여부 체크
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
        if any(keyword in name.upper() for keyword in etf_keywords):
            return True

        # 해외 ETF 체크
        try:
            yf_stock = yf.Ticker(symbol)
            yf_info = yf_stock.info
            quote_type = yf_info.get("quoteType")
            if quote_type == "ETF":
                logger.info(f"✅ {name} ({symbol}) ETF로 확인 (quoteType=ETF)")
                return True
        except Exception as e:
            logger.debug(f"해외 ETF 체크 실패 ({symbol}): {e}")

        return False
