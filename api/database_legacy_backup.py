import os
import json
from datetime import date, datetime, timedelta
from typing import List, Optional

import requests
from dotenv import load_dotenv
from supabase import Client, create_client

# .env 파일 로드
load_dotenv()
import sys

from .models import (
    AssetAllocation,
    AssetAllocationResponse,
    CashBalance,
    CashManagementSummary,
    CashUpdateRequest,
    CurrencyRate,
    HoldingDetail,
    HoldingResponse,
    MarketSummary,
    PerformanceData,
    PortfolioOverview,
    StockInfo,
    TimeDeposit,
    UnmatchedProduct,
    UnmatchedProductsResponse,
    BSTimeseries,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import get_api_logger

db_logger = get_api_logger("Database")


class DateTimeEncoder(json.JSONEncoder):
    """date/datetime 객체를 JSON 직렬화하기 위한 커스텀 인코더"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class SerializableClient(Client):
    """JSON 직렬화 문제를 해결한 Supabase 클라이언트 래퍼"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize_data(self, data):
        """데이터를 JSON 직렬화 가능한 형태로 변환"""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, (datetime, date)):
            return data.isoformat()
        else:
            return data

    def table(self, table_name):
        """테이블 작업을 직렬화와 함께 처리"""
        original_table = super().table(table_name)

        class SerializableTable:
            def __init__(self, table, serializer):
                self._table = table
                self._serialize = serializer

            def insert(self, data, *args, **kwargs):
                serialized_data = self._serialize(data)
                return self._table.insert(serialized_data, *args, **kwargs)

            def update(self, data, *args, **kwargs):
                serialized_data = self._serialize(data)
                return self._table.update(serialized_data, *args, **kwargs)

            def select(self, *args, **kwargs):
                return self._table.select(*args, **kwargs)

            def delete(self, *args, **kwargs):
                return self._table.delete(*args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._table, name)

        return SerializableTable(original_table, self._serialize_data)


class DatabaseManager:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY 환경변수가 필요합니다")

        # JSON 직렬화 문제를 해결하기 위해 커스텀 클라이언트 사용
        self.supabase: SerializableClient = SerializableClient(
            self.supabase_url, self.supabase_key
        )

    async def get_portfolio_overview(
        self, account: Optional[str] = None
    ) -> PortfolioOverview:
        """포트폴리오 전체 현황 조회"""
        try:
            # USD 환율 정보 가져오기
            currency_rates = await self.get_currency_rates(
                auto_update=True, currencies=["USD"]
            )
            usd_rate = currency_rates[0].exchange_rate if currency_rates else 1400.0
            db_logger.info(f"💱 USD 환율 적용: {usd_rate}")

            # get_asset_allocation 호출하여 투자자산 분배비율 가져오기
            asset_allocation_response = await self.get_asset_allocation(
                account, auto_add_unmatched=False
            )
            investment_allocations = asset_allocation_response.allocations
            total_investment_value = asset_allocation_response.total_portfolio_value

            # 현금성자산 계산 (cash_balance + time_deposit)
            # 1. cash_balance 조회
            cash_query = self.supabase.table("cash_balance").select("*")
            if account:
                cash_query = cash_query.eq("account", account)
            cash_response = cash_query.execute()
            cash_data = cash_response.data

            total_krw_cash = sum(float(item.get("krw", 0) or 0) for item in cash_data)
            total_usd_cash = sum(float(item.get("usd", 0) or 0) for item in cash_data)
            # USD를 KRW로 환산
            total_usd_cash_in_krw = total_usd_cash * usd_rate

            # 2. time_deposit 조회
            deposit_query = self.supabase.table("time_deposit").select("*")
            if account:
                deposit_query = deposit_query.eq("account", account)
            deposit_response = deposit_query.execute()
            deposit_data = deposit_response.data

            total_deposit_value = sum(
                float(item.get("market_value", 0) or 0) for item in deposit_data
            )

            # 현금성자산 총액
            cash_asset_value = (
                total_krw_cash + total_usd_cash_in_krw + total_deposit_value
            )

            # 전체 자산 = 투자자산 + 현금성자산
            total_value_krw = total_investment_value + cash_asset_value
            total_value_usd = total_value_krw / usd_rate

            # 비율 계산
            if total_value_krw > 0:
                cash_asset_ratio = (cash_asset_value / total_value_krw) * 100
                investment_asset_ratio = (
                    total_investment_value / total_value_krw
                ) * 100
            else:
                cash_asset_ratio = 0.0
                investment_asset_ratio = 0.0

            # 계좌 목록 (asset_allocation 결과에서 계좌 정보 가져오기)
            accounts = [account] if account else []

            # 총 평가손익 계산 (asset_allocation 결과에서 계산)
            total_pnl_krw = (
                0.0  # 이 정보는 asset_allocation에서 제공되지 않으므로 0으로 설정
            )
            total_pnl_usd = 0.0
            total_return_rate = 0.0

            return PortfolioOverview(
                total_value_krw=total_value_krw,
                total_value_usd=total_value_usd,
                total_pnl_krw=total_pnl_krw,
                total_pnl_usd=total_pnl_usd,
                total_return_rate=total_return_rate,
                accounts=accounts,
                cash_asset_value=cash_asset_value,
                investment_asset_value=total_investment_value,
                cash_asset_ratio=round(cash_asset_ratio, 2),
                investment_asset_ratio=round(investment_asset_ratio, 2),
                investment_allocations=investment_allocations,
                last_updated=datetime.now(),
            )

        except Exception as e:
            db_logger.error(f"포트폴리오 개요 조회 오류: {e}")
            raise

    async def get_holdings(
        self, account: Optional[str] = None, market: Optional[str] = None
    ) -> List[HoldingResponse]:
        """보유 종목 정보 조회"""
        try:
            query = self.supabase.table("overall_info").select("*")

            if account:
                query = query.eq("account", account)

            if market:
                query = query.eq("market", market)

            response = query.execute()
            data = response.data

            holdings = []
            for item in data:
                holding = HoldingResponse(
                    id=item.get("id"),
                    account=item.get("account"),
                    company=item.get("company"),
                    market=item.get("market"),
                    area=item.get("area"),
                    amount=item.get("amount", 0),
                    avg_price_krw=float(item.get("avg_price_krw", 0)),
                    current_price_krw=float(item.get("latest_close_krw", 0)),
                    principal=float(item.get("principal", 0)),
                    market_value=float(item.get("market_value", 0)),
                    unrealized_pnl=float(item.get("unrealized_G/L", 0)),
                    return_rate=float(item.get("rate_of_return", 0)),
                    avg_price_usd=(
                        float(item.get("avg_price_usd", 0))
                        if item.get("avg_price_usd")
                        else None
                    ),
                    current_price_usd=(
                        float(item.get("latest_close_usd", 0))
                        if item.get("latest_close_usd")
                        else None
                    ),
                    principal_usd=(
                        float(item.get("principal_usd", 0))
                        if item.get("principal_usd")
                        else None
                    ),
                    market_value_usd=(
                        float(item.get("market_value_usd", 0))
                        if item.get("market_value_usd")
                        else None
                    ),
                    unrealized_pnl_usd=(
                        float(item.get("unrealized_G/L_usd", 0))
                        if item.get("unrealized_G/L_usd")
                        else None
                    ),
                    return_rate_usd=(
                        float(item.get("rate_of_return_usd", 0))
                        if item.get("rate_of_return_usd")
                        else None
                    ),
                    first_buy_at=item.get("first_buy_at"),
                    last_buy_at=item.get("last_buy_at"),
                    last_sell_at=item.get("last_sell_at"),
                    total_realized_pnl=(
                        float(item.get("total_realized_G/L", 0))
                        if item.get("total_realized_G/L")
                        else None
                    ),
                )
                holdings.append(holding)

            return holdings

        except Exception as e:
            db_logger.error(f"보유 종목 조회 오류: {e}")
            raise

    async def get_all_stocks(self) -> List[StockInfo]:
        """모든 주식 정보 조회"""
        try:
            response = self.supabase.table("stock_info").select("*").execute()
            data = response.data
            db_logger.debug(f"data: {data}")

            stocks = []
            for item in data:
                stock = StockInfo(
                    id=item.get("id"),
                    company=item.get("company"),
                    symbol=item.get("symbol"),
                    exchange=item.get("exchange"),
                    sector=item.get("sector"),
                    industry=item.get("industry"),
                    area=item.get("area"),
                    latest_close=(
                        float(item.get("latest_close", 0))
                        if item.get("latest_close")
                        else None
                    ),
                    marketcap=(
                        float(item.get("marketcap", 0))
                        if item.get("marketcap")
                        else None
                    ),
                    updated_at=item.get("updated_at"),
                )
                stocks.append(stock)

            return stocks

        except Exception as e:
            db_logger.error(f"주식 정보 조회 오류: {e}")
            raise

    async def get_performance_data(self, account: str) -> Optional[PerformanceData]:
        """계좌별 성과 분석 데이터"""
        try:
            response = (
                self.supabase.table("overall_info")
                .select("*")
                .eq("account", account)
                .execute()
            )
            data = response.data

            if not data:
                return None

            total_investment = sum(float(item.get("principal", 0)) for item in data)
            total_value = sum(float(item.get("market_value", 0)) for item in data)
            total_return = total_value - total_investment
            return_rate = (
                (total_return / total_investment * 100) if total_investment > 0 else 0.0
            )

            # 섹터별 분배 (stock_info와 조인 필요)
            sector_allocation = {}
            region_allocation = {"국내": 0, "해외": 0}

            for item in data:
                market = item.get("market", "알수없음")
                value = float(item.get("market_value", 0))

                if market in region_allocation:
                    region_allocation[market] += value

                # 섹터 정보는 별도 조회 필요 (stock_info 테이블)

            return PerformanceData(
                account=account,
                total_investment=total_investment,
                total_value=total_value,
                total_return=total_return,
                return_rate=return_rate,
                sector_allocation=sector_allocation,
                region_allocation=region_allocation,
            )

        except Exception as e:
            db_logger.error(f"성과 데이터 조회 오류: {e}")
            raise

    async def get_currency_rates(
        self, auto_update: bool = True, currencies: Optional[List[str]] = None
    ) -> List[CurrencyRate]:
        """환율 정보 조회 (자동 업데이트 옵션 포함)

        Args:
            auto_update: 오래된 환율 자동 업데이트 여부
            currencies: 조회할 통화 리스트 (None이면 전체 조회)
        """
        try:
            db_logger.info(
                f"💱 환율 정보 조회 시작 - 통화: {currencies if currencies else '전체'}"
            )

            # 특정 통화만 조회할 경우 필터링
            query = self.supabase.table("currency").select("*")
            if currencies:
                query = query.in_("currency", currencies)
            response = query.execute()
            data = response.data

            # 가장 최근 영업일 계산
            latest_business_date = self._get_latest_business_date()
            db_logger.info(f"📅 최근 영업일: {latest_business_date}")

            rates = []
            outdated_currencies = []

            for item in data:
                # updated_at이 문자열인 경우 datetime으로 변환
                updated_at = item.get("updated_at")
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(
                            updated_at.replace("Z", "+00:00")
                        )
                    except:
                        updated_at = datetime.now()
                elif updated_at is None:
                    updated_at = datetime.now()

                # 날짜 비교 (최근 영업일과 다르면 오래된 것으로 간주)
                update_date = (
                    updated_at.date()
                    if hasattr(updated_at, "date")
                    else latest_business_date
                )
                is_outdated = update_date != latest_business_date

                if is_outdated:
                    outdated_currencies.append(item.get("currency"))
                    db_logger.warning(
                        f"⚠️ {item.get('currency')} 환율 정보가 오래됨 - "
                        f"마지막 업데이트: {update_date}, 최근 영업일: {latest_business_date}"
                    )

                rate = CurrencyRate(
                    currency=item.get("currency"),
                    exchange_rate=float(item.get("exchange_rate", 0)),
                    updated_at=updated_at,
                )
                rates.append(rate)

            # 오래된 환율이 있고 자동 업데이트가 활성화된 경우
            if outdated_currencies and auto_update:
                db_logger.info(
                    f"🔄 오래된 환율 정보 자동 업데이트 시작: {outdated_currencies}"
                )
                updated_rates = await self.update_currency_rates(outdated_currencies)

                # 업데이트된 환율로 교체
                for updated_rate in updated_rates:
                    for i, rate in enumerate(rates):
                        if rate.currency == updated_rate.currency:
                            rates[i] = updated_rate
                            break

            db_logger.info(f"✅ 환율 정보 조회 완료 - {len(rates)}개 통화")
            if outdated_currencies:
                db_logger.info(
                    f"📝 오래된 환율: {len(outdated_currencies)}개, 업데이트 완료"
                )

            return rates

        except Exception as e:
            db_logger.error(f"환율 정보 조회 오류: {e}")
            raise

    async def update_currency_rates(self, currencies: List[str]) -> List[CurrencyRate]:
        """특정 통화들의 환율 정보를 한국수출입은행 API로부터 업데이트"""
        updated_rates = []

        try:
            db_logger.info(f"🔄 환율 업데이트 시작: {currencies}")

            # 환경변수에서 API 키 가져오기
            api_key = os.environ.get("KOREAEXIM_API_KEY")
            if not api_key:
                db_logger.error("❌ KOREAEXIM_API_KEY 환경변수가 설정되지 않음")
                return updated_rates

            # 가장 최근 영업일 찾기
            latest_business_date = self._get_latest_business_date()
            search_date_str = latest_business_date.strftime("%Y%m%d")
            db_logger.info(f"📅 환율 조회 날짜: {search_date_str}")

            # 한국수출입은행 API 호출
            url = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
            params = {
                "authkey": api_key,
                "searchdate": search_date_str,
                "data": "AP01",  # 환율
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                db_logger.debug(f"✅ 환율 API 호출 response: {response}")
                if response.status_code == 200:
                    data = response.json()
                    db_logger.debug(f"✅ 환율 API 호출 성공: {data}")
                    # 통화코드 매핑 (API 응답 → DB 통화코드)
                    # API는 "USD", "EUR(유로)", "JPY(100엔)" 같은 형식 반환
                    currency_mapping = {}
                    for item in data:
                        cur_unit = item.get("cur_unit", "")
                        # 괄호 앞부분만 추출 (예: "EUR(유로)" → "EUR")
                        currency_code = cur_unit.split("(")[0].strip()
                        currency_mapping[currency_code] = item

                    # 요청된 통화들 처리
                    for currency in currencies:
                        if currency in currency_mapping:
                            item = currency_mapping[currency]
                            # deal_bas_r: 매매기준율 (쉼표 제거 후 float 변환)
                            rate_str = item.get("deal_bas_r", "")
                            if rate_str:
                                try:
                                    exchange_rate = float(rate_str.replace(",", ""))

                                    # 데이터베이스 업데이트
                                    update_result = (
                                        self.supabase.table("currency")
                                        .update(
                                            {
                                                "exchange_rate": exchange_rate,
                                                "updated_at": latest_business_date.isoformat(),
                                            }
                                        )
                                        .eq("currency", currency)
                                        .execute()
                                    )

                                    if update_result.data:
                                        updated_rate = CurrencyRate(
                                            currency=currency,
                                            exchange_rate=exchange_rate,
                                            updated_at=datetime.combine(
                                                latest_business_date,
                                                datetime.min.time(),
                                            ),
                                        )
                                        updated_rates.append(updated_rate)
                                        db_logger.info(
                                            f"✅ {currency} 환율 업데이트 성공: {exchange_rate}"
                                        )
                                    else:
                                        db_logger.error(
                                            f"❌ {currency} 환율 DB 업데이트 실패"
                                        )
                                except ValueError as e:
                                    db_logger.error(
                                        f"❌ {currency} 환율 변환 오류: {e}"
                                    )
                            else:
                                db_logger.error(f"❌ {currency} 환율 데이터 없음")
                        else:
                            db_logger.warning(f"⚠️ {currency} API 응답에 없음")

                else:
                    db_logger.error(f"❌ 환율 API 호출 실패: {response.status_code}")

            except requests.RequestException as e:
                db_logger.error(f"❌ 환율 API 호출 오류: {e}")
            except Exception as e:
                db_logger.error(f"❌ 환율 데이터 처리 오류: {e}")

            db_logger.info(f"🏁 환율 업데이트 완료: {len(updated_rates)}개 성공")
            return updated_rates

        except Exception as e:
            db_logger.error(f"환율 업데이트 전체 오류: {e}")
            return updated_rates

    def search_symbol_info(self, product_name: str) -> Optional[dict]:
        """종목명으로 심볼 정보 검색 (국내 + 해외)"""
        try:
            import FinanceDataReader as fdr
            import yfinance as yf

            # 1. 먼저 국내 주식/ETF 검색 (KRX)
            krx_stocks = fdr.StockListing("KRX")

            # ETF도 포함해서 검색 (regex=False로 문자열 그대로 검색)
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
                    market = stock.get("Market") or "KOSPI"  # ETF는 대부분 KOSPI
                    # code가 여전히 None이면 다른 필드 확인
                    if not code:
                        db_logger.error(f"ETF 코드를 찾을 수 없음: {stock.to_dict()}")
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
                    "exchange": market,  # KOSPI, KOSDAQ, KONEX
                    "sector": sector,
                    "industry": industry,
                    "asset_type": "equity",  # 일단 equity로 통일
                    "region_type": "domestic",
                    "latest_close": stock.get("Close", 0),
                    "marketcap": (
                        stock.get("Marcap", 0) / 10**9 if stock.get("Marcap") else None
                    ),
                }
                db_logger.info(
                    f"✅ 국내 심볼 발견: {product_name} -> {code} ({market}, sector: {sector})"
                )
                return symbol_info

            # 2. 해외 주식 검색 시도 (yfinance)
            # 일반적인 티커 패턴 시도
            potential_tickers = [
                product_name,  # 그대로
                product_name.upper(),  # 대문자
                product_name.replace(" ", ""),  # 공백 제거
            ]

            for ticker in potential_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info

                    # 유효한 티커인지 확인 (longName이나 shortName이 있으면)
                    if info.get("longName") or info.get("shortName"):
                        symbol_info = {
                            "symbol": ticker,
                            "exchange": info.get("exchange", "US"),
                            "sector": info.get("sector", None),
                            "industry": info.get("industry", None),
                            "asset_type": "equity",
                            "region_type": "global",
                        }
                        db_logger.info(
                            f"✅ 해외 심볼 발견: {product_name} -> {ticker} ({info.get('exchange', 'US')})"
                        )
                        return symbol_info
                except:
                    continue

            db_logger.warning(f"⚠️ 심볼 찾지 못함: {product_name}")
            return None

        except Exception as e:
            db_logger.error(f"심볼 검색 중 오류 ({product_name}): {e}")
            return None

    async def add_unmatched_to_symbol_table(
        self, unmatched_response: UnmatchedProductsResponse
    ) -> dict:
        """매칭되지 않는 상품들을 symbol_table에 추가"""
        added_count = 0
        failed_count = 0

        for product in unmatched_response.unmatched_products:
            try:
                # 종목명으로 심볼 정보 검색 (국내 + 해외)
                symbol_info = self.search_symbol_info(product.invest_prod_name)

                # 심볼을 찾지 못하면 추가하지 않음 (symbol은 NOT NULL 제약)
                if not symbol_info or not symbol_info.get("symbol"):
                    db_logger.warning(
                        f"⚠️ {product.invest_prod_name}: 심볼을 찾지 못해 추가 불가"
                    )
                    failed_count += 1
                    continue

                # symbol_table에 insert할 데이터 준비
                insert_data = {
                    "name": product.invest_prod_name,
                    "updated_at": datetime.now().isoformat(),
                }
                insert_data.update(symbol_info)

                result = (
                    self.supabase.table("symbol_table").insert(insert_data).execute()
                )

                if result.data:
                    added_count += 1
                    db_logger.info(
                        f"✅ Symbol table에 추가: {product.invest_prod_name}"
                    )
                else:
                    failed_count += 1
                    db_logger.warning(f"⚠️ 추가 실패: {product.invest_prod_name}")

            except Exception as e:
                failed_count += 1
                db_logger.error(f"❌ {product.invest_prod_name} 추가 중 오류: {e}")

        db_logger.info(
            f"📝 Symbol table 추가 완료 - 성공: {added_count}, 실패: {failed_count}"
        )

        return {"added": added_count, "failed": failed_count}

    def _get_latest_business_date(self) -> date:
        """가장 최근 영업일을 계산하여 반환

        Returns:
            date: 최근 영업일 (평일 20시 이전이면 전날, 주말이면 금요일)
        """
        now = datetime.now()
        latest_business_day = now

        # 평일 20시 이전이면 전날로
        if now.hour < 20:
            latest_business_day = now - timedelta(days=1)

        # 주말이면 가장 최근 금요일로
        while latest_business_day.weekday() >= 5:  # 5=토요일, 6=일요일
            latest_business_day = latest_business_day - timedelta(days=1)

        return latest_business_day.date()

    def _get_asset_category(
        self, asset_type: Optional[str], region_type: Optional[str]
    ) -> str:
        """자산 유형과 지역 유형으로 자산 카테고리를 결정"""
        if asset_type == "equity" and region_type == "domestic":
            return "국내주식"
        elif asset_type == "equity" and region_type == "global":
            return "해외주식"
        elif asset_type == "bond" and region_type == "domestic":
            return "국내채권"
        elif asset_type == "bond" and region_type == "global":
            return "해외채권"
        elif asset_type == "REITs" and region_type == "domestic":
            return "국내리츠"
        elif asset_type == "REITs" and region_type == "global":
            return "해외리츠"
        elif asset_type == "TDF":
            return "TDF"
        elif asset_type == "commodity":
            return "원자재"
        elif asset_type == "gold":
            return "금"
        elif asset_type == "cash":
            return "현금성자산"
        else:
            return "기타"

    async def get_asset_allocation(
        self, account: Optional[str] = None, auto_add_unmatched: bool = True
    ) -> AssetAllocationResponse:
        """자산 분배 정보 조회"""
        try:
            # USD 환율 정보 가져오기 (자동 업데이트 포함)
            currency_rates = await self.get_currency_rates(
                auto_update=True, currencies=["USD"]
            )
            usd_rate = currency_rates[0].exchange_rate if currency_rates else 1400.0
            db_logger.info(f"💱 USD 환율 적용: {usd_rate}")

            # Symbol table에 없는 종목 조회
            unmatched_products = await self.get_unmatched_products(account)
            stocks_added = False

            if unmatched_products.total_count > 0:
                db_logger.warning(
                    f"❌ 매칭되지 않는 종목 {unmatched_products.total_count}개 발견"
                )

                # 자동 추가 옵션이 활성화된 경우
                if auto_add_unmatched:
                    db_logger.info(
                        "🔄 매칭되지 않는 종목을 symbol_table에 자동 추가 시작"
                    )
                    add_result = await self.add_unmatched_to_symbol_table(
                        unmatched_products
                    )

                    if add_result["added"] > 0:
                        db_logger.info(f"✨ {add_result['added']}개 종목이 추가됨")
                        stocks_added = True

            # 종목이 추가되었으면 전체 업데이트, 아니면 가격만 업데이트
            if stocks_added:
                db_logger.info(
                    "📊 종목 추가됨 - 전체 업데이트 (가격 + sector/industry) 수행"
                )
                # 1. 가격 업데이트
                price_result = await self.update_symbol_table_prices()
                db_logger.info(
                    f"✅ 가격 업데이트 완료 - 성공: {price_result['success_count']}, "
                    f"실패: {price_result['fail_count']}, 스킵: {price_result['skip_count']}"
                )
                # 2. Sector/Industry 업데이트
                sector_result = await self.update_symbol_sector_info()
                db_logger.info(
                    f"✅ sector/industry 업데이트 완료 - 성공: {sector_result['success_count']}, "
                    f"실패: {sector_result['fail_count']}"
                )
            else:
                db_logger.info("📊 가격 정보만 업데이트 수행")
                price_result = await self.update_symbol_table_prices()
                db_logger.info(
                    f"✅ 가격 업데이트 완료 - 성공: {price_result['success_count']}, "
                    f"실패: {price_result['fail_count']}, 스킵: {price_result['skip_count']}"
                )

            # by_accounts 데이터 조회
            accounts_query = self.supabase.table("by_accounts").select("*")
            if account:
                accounts_query = accounts_query.eq("account", account)
            accounts_response = accounts_query.execute()
            accounts_data = accounts_response.data

            # funds 데이터 조회
            funds_query = self.supabase.table("funds").select("*")
            if account:
                funds_query = funds_query.eq("account", account)
            funds_response = funds_query.execute()
            funds_data = funds_response.data

            # symbol_table 데이터 조회
            symbols_response = self.supabase.table("symbol_table").select("*").execute()
            symbols_data = symbols_response.data

            # Python에서 조인 처리
            symbol_dict = {item["name"]: item for item in symbols_data}

            asset_allocation_data = {}
            total_value = 0.0

            # 1. by_accounts 처리
            for ba_item in accounts_data:
                if ba_item["amount"] <= 0:
                    continue

                company = ba_item["invest_prod_name"]
                symbol_info = symbol_dict.get(company)

                if not symbol_info:
                    continue

                # 평가금액 계산
                if symbol_info["exchange"] in ["KOSPI", "KOSDAQ"]:
                    market_value = ba_item["amount"] * symbol_info["latest_close"]
                else:
                    market_value = (
                        ba_item["amount"] * symbol_info["latest_close"] * usd_rate
                    )

                # 자산유형 매핑
                asset_category = self._get_asset_category(
                    symbol_info["asset_type"], symbol_info["region_type"]
                )

                # 자산 카테고리별 집계
                if asset_category not in asset_allocation_data:
                    asset_allocation_data[asset_category] = {
                        "holdings_count": 0,
                        "total_market_value": 0.0,
                        "holdings": [],
                    }

                # 종목 이름만 추가
                asset_allocation_data[asset_category]["holdings_count"] += 1
                asset_allocation_data[asset_category][
                    "total_market_value"
                ] += market_value
                asset_allocation_data[asset_category]["holdings"].append(company)
                total_value += market_value

            # 2. funds 처리
            for fund_item in funds_data:
                if not fund_item.get("market_value") or fund_item["market_value"] <= 0:
                    continue

                # 자산유형 매핑
                asset_category = self._get_asset_category(
                    fund_item.get("asset_type"), fund_item.get("region_type")
                )

                market_value = float(fund_item["market_value"])
                fund_name = fund_item["invest_prod_name"]

                # 자산 카테고리별 집계
                if asset_category not in asset_allocation_data:
                    asset_allocation_data[asset_category] = {
                        "holdings_count": 0,
                        "total_market_value": 0.0,
                        "holdings": [],
                    }

                # 펀드 이름만 추가
                asset_allocation_data[asset_category]["holdings_count"] += 1
                asset_allocation_data[asset_category][
                    "total_market_value"
                ] += market_value
                asset_allocation_data[asset_category]["holdings"].append(fund_name)
                total_value += market_value

            # # 3. time_deposit 처리
            # time_deposit_query = self.supabase.table("time_deposit").select("*")
            # if account:
            #     time_deposit_query = time_deposit_query.eq("account", account)
            # time_deposit_response = time_deposit_query.execute()
            # time_deposit_data = time_deposit_response.data

            # for td_item in time_deposit_data:
            #     if not td_item.get("market_value") or td_item["market_value"] <= 0:
            #         continue

            #     # 예금은 현금성자산으로 분류
            #     asset_category = "현금성자산"
            #     market_value = float(td_item["market_value"])
            #     deposit_name = td_item["invest_prod_name"]

            #     # 자산 카테고리별 집계
            #     if asset_category not in asset_allocation_data:
            #         asset_allocation_data[asset_category] = {
            #             "holdings_count": 0,
            #             "total_market_value": 0.0,
            #             "holdings": [],
            #         }

            #     # 예금 이름만 추가
            #     asset_allocation_data[asset_category]["holdings_count"] += 1
            #     asset_allocation_data[asset_category][
            #         "total_market_value"
            #     ] += market_value
            #     asset_allocation_data[asset_category]["holdings"].append(deposit_name)
            #     total_value += market_value

            # # 4. cash_balance 처리
            # cash_balance_query = self.supabase.table("cash_balance").select("*")
            # if account:
            #     cash_balance_query = cash_balance_query.eq("account", account)
            # cash_balance_response = cash_balance_query.execute()
            # cash_balance_data = cash_balance_response.data

            # # KRW, USD 합계 계산
            # total_krw_cash = sum(
            #     float(item.get("krw", 0) or 0) for item in cash_balance_data
            # )
            # total_usd_cash = sum(
            #     float(item.get("usd", 0) or 0) for item in cash_balance_data
            # )

            # # USD를 KRW로 환산
            # total_usd_cash_in_krw = total_usd_cash * usd_rate

            # # 예수금 총액 (KRW + USD 환산)
            # total_cash_value = total_krw_cash + total_usd_cash_in_krw

            # if total_cash_value > 0:
            #     asset_category = "현금성자산"

            #     # 자산 카테고리별 집계
            #     if asset_category not in asset_allocation_data:
            #         asset_allocation_data[asset_category] = {
            #             "holdings_count": 0,
            #             "total_market_value": 0.0,
            #             "holdings": [],
            #         }

            #     # 예수금 추가
            #     asset_allocation_data[asset_category]["holdings_count"] += 1
            #     asset_allocation_data[asset_category][
            #         "total_market_value"
            #     ] += total_cash_value
            #     asset_allocation_data[asset_category]["holdings"].append("예수금")
            #     total_value += total_cash_value

            # AssetAllocation 객체 생성
            allocations = []
            for category, data in asset_allocation_data.items():
                allocation_percentage = (
                    (data["total_market_value"] / total_value * 100)
                    if total_value > 0
                    else 0
                )
                allocation = AssetAllocation(
                    asset_category=category,
                    holdings_count=data["holdings_count"],
                    total_market_value=data["total_market_value"],
                    allocation_percentage=round(allocation_percentage, 2),
                    holdings=data["holdings"],
                )
                allocations.append(allocation)

            # 총 가치 기준으로 정렬
            allocations.sort(key=lambda x: x.total_market_value, reverse=True)

            return AssetAllocationResponse(
                total_portfolio_value=total_value,
                allocations=allocations,
                account=account,
                last_updated=datetime.now(),
            )

        except Exception as e:
            db_logger.error(f"자산 분배 조회 오류: {e}")
            # 에러 발생 시 빈 응답 반환
            return AssetAllocationResponse(
                total_portfolio_value=0.0,
                allocations=[],
                account=account,
                last_updated=datetime.now(),
            )

    async def get_unmatched_products(
        self, account: Optional[str] = None
    ) -> UnmatchedProductsResponse:
        """by_accounts 테이블에는 있지만 symbol_table에는 없는 상품 조회"""
        try:
            # by_accounts 데이터 조회
            accounts_query = self.supabase.table("by_accounts").select("*")
            if account:
                accounts_query = accounts_query.eq("account", account)
            accounts_response = accounts_query.execute()
            accounts_data = accounts_response.data

            # symbol_table 데이터 조회 (name 컬럼만)
            symbols_response = (
                self.supabase.table("symbol_table").select("name").execute()
            )
            symbols_data = symbols_response.data

            # symbol_table의 name들을 set으로 변환 (빠른 조회를 위해)
            symbol_names = {item["name"] for item in symbols_data}

            # 매칭되지 않는 상품들 찾기
            unmatched_products = []
            accounts_with_unmatched = set()

            for ba_item in accounts_data:
                invest_prod_name = ba_item["invest_prod_name"]

                # symbol_table에 없는 상품만 필터링
                if invest_prod_name not in symbol_names:
                    unmatched_product = UnmatchedProduct(
                        account=ba_item["account"],
                        invest_prod_name=invest_prod_name,
                        amount=ba_item["amount"],
                        avg_price_krw=ba_item.get("avg_price_krw"),
                        avg_price_usd=ba_item.get("avg_price_usd"),
                        first_buy_at=ba_item.get("first_buy_at"),
                        last_buy_at=ba_item.get("last_buy_at"),
                    )
                    unmatched_products.append(unmatched_product)
                    accounts_with_unmatched.add(ba_item["account"])

            return UnmatchedProductsResponse(
                unmatched_products=unmatched_products,
                total_count=len(unmatched_products),
                accounts_with_unmatched=list(accounts_with_unmatched),
                last_updated=datetime.now(),
            )

        except Exception as e:
            db_logger.error(f"매칭되지 않는 상품 조회 오류: {e}")
            raise

    def _get_korean_stock_data(
        self, symbol: str, exchange: str = "KOSPI"
    ) -> tuple[Optional[float], Optional[float], Optional[date]]:
        """국내 주식/ETF 가격 정보 조회 (FinanceDataReader + yfinance)

        Returns:
            (latest_close, marketcap, price_date): 최종가, 시가총액, 가격 날짜
        """
        import FinanceDataReader as fdr
        import yfinance as yf

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
                )  # 억원 -> 십억원 단위로 변환
                # ETF 리스트의 가격은 현재 날짜로 간주
                price_date_fdr = datetime.now().date()
                db_logger.info(
                    f"📊 ETF {symbol}: price={latest_close_fdr}, marketcap={marketcap_fdr}B KRW, date={price_date_fdr} (from ETF list)"
                )
                return latest_close_fdr, marketcap_fdr, price_date_fdr
        except Exception as e:
            db_logger.warning(f"⚠️ ETF 리스트 조회 실패 ({symbol}): {e}")

        # ETF가 아니면 일반 주식으로 처리
        try:
            df = fdr.DataReader(symbol, "2024-01-01")
            if not df.empty:
                latest_close_fdr = df["Close"].iloc[-1]
                # DataFrame의 마지막 인덱스가 날짜
                price_date_fdr = df.index[-1].date()
                db_logger.info(
                    f"📊 FinanceDataReader {symbol}: {latest_close_fdr}, date={price_date_fdr}"
                )
            else:
                db_logger.warning(f"⚠️ FinanceDataReader {symbol}: 데이터 없음")
        except Exception as e:
            db_logger.error(f"❌ FinanceDataReader {symbol} 오류: {e}")

        # yfinance로 백업 조회 및 marketcap
        # 거래소에 따라 적절한 suffix 사용 (KOSPI는 .KS, KOSDAQ는 .KQ)
        ticker_suffix = ".KS" if exchange == "KOSPI" else ".KQ"
        yf_ticker = f"{symbol}{ticker_suffix}"
        latest_close_yf, marketcap_yf, price_date_yf = self._get_stock_data_yfinance(
            yf_ticker
        )
        db_logger.info(
            f"📊 yfinance {yf_ticker}: close={latest_close_yf}, marketcap={marketcap_yf}, date={price_date_yf}"
        )

        latest_close = (
            latest_close_fdr if latest_close_fdr is not None else latest_close_yf
        )
        marketcap = marketcap_fdr if marketcap_fdr is not None else marketcap_yf
        price_date = price_date_fdr if price_date_fdr is not None else price_date_yf
        return latest_close, marketcap, price_date

    def _get_stock_data_yfinance(
        self, symbol: str
    ) -> tuple[Optional[float], Optional[float], Optional[date]]:
        """yfinance로 주식 정보 조회

        Returns:
            (latest_close, marketcap, price_date): 최종가, 시가총액, 가격 날짜
        """
        import yfinance as yf

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
            db_logger.error(f"❌ yfinance {symbol} 오류: {e}")
        return None, None, None

    def _check_if_etf(self, name: str, symbol: str, exchange: str) -> bool:
        """ETF 여부 확인"""
        import FinanceDataReader as fdr
        import yfinance as yf

        # 국내 ETF 체크
        if exchange in ["KOSPI", "KOSDAQ"]:
            try:
                etf_list = fdr.StockListing("ETF/KR")
                etf_info = etf_list[etf_list["Symbol"] == symbol]
                if not etf_info.empty:
                    return True
            except Exception as e:
                db_logger.debug(f"ETF 체크 실패 ({symbol}): {e}")

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

        # 해외 ETF 체크 - yfinance로 quoteType 확인
        try:
            yf_stock = yf.Ticker(symbol)
            yf_info = yf_stock.info
            quote_type = yf_info.get("quoteType")
            if quote_type == "ETF":
                db_logger.info(f"✅ {name} ({symbol}) ETF로 확인 (quoteType=ETF)")
                return True
        except Exception as e:
            db_logger.debug(f"해외 ETF 체크 실패 ({symbol}): {e}")

        return False

    def _extract_industry_from_name(self, name: str) -> str:
        """ETF 이름에서 industry 추출 (우선순위 기반)"""

        # 1순위: 구체적이고 긴 복합 키워드 (가장 먼저 매칭)
        high_priority_keywords = {
            "미국배당주": "US Dividend Stocks",
            "미국배당귀족": "US Dividend Aristocrats",
            "글로벌배당주": "Global Dividend Stocks",
            "미국S&P500": "S&P 500",
            "미국나스닥": "NASDAQ",
            "미국나스닥100": "NASDAQ 100",
            "미국부동산리츠": "US REITs",
            "미국달러단기채권": "US Short-Term Bonds",
            "미국30년국채": "US 30Y Treasury",
            "미국10년국채": "US 10Y Treasury",
            "미국투자등급회사채": "US Investment Grade Bonds",
            "타겟커버드콜": "Target Covered Call",
            "타겟데이트": "Target Date",
            "중국본토": "China A-Shares",
            "중국대형주": "China Large Cap",
        }

        # 2순위: 섹터/산업 키워드
        medium_priority_keywords = {
            "반도체": "Semiconductors",
            "2차전지": "Battery",
            "바이오": "Biotechnology",
            "헬스케어": "Healthcare",
            "제약": "Pharmaceuticals",
            "금융": "Financial",
            "은행": "Banking",
            "보험": "Insurance",
            "에너지": "Energy",
            "신재생에너지": "Renewable Energy",
            "소재": "Materials",
            "화학": "Chemicals",
            "철강": "Steel",
            "산업재": "Industrials",
            "건설": "Construction",
            "IT": "Information Technology",
            "소프트웨어": "Software",
            "인터넷": "Internet",
            "게임": "Gaming",
            "미디어": "Media",
            "통신": "Communication",
            "유틸리티": "Utilities",
            "전기가스": "Utilities",
            "필수소비재": "Consumer Staples",
            "식품": "Food & Beverage",
            "임의소비재": "Consumer Discretionary",
            "자동차": "Automotive",
            "전기차": "Electric Vehicles",
            "반려동물": "Pet Care",
            "AI": "Artificial Intelligence",
            "로봇": "Robotics",
            "우주항공": "Aerospace",
            "우주": "Space Exploration",
            "Space": "Space Exploration",
            "Innovation": "Innovation",
            "Exploration": "Space Exploration",
        }

        # 3순위: 자산 유형 및 일반 카테고리
        low_priority_keywords = {
            "배당": "Dividend",
            "고배당": "High Dividend",
            "국채": "Government Bond",
            "국고채": "Government Bond",
            "단기채권": "Short-Term Bond",
            "장기채권": "Long-Term Bond",
            "회사채": "Corporate Bond",
            "하이일드": "High Yield Bond",
            "금": "Gold",
            "골드": "Gold",
            "은": "Silver",
            "실버": "Silver",
            "원유": "Crude Oil",
            "천연가스": "Natural Gas",
            "구리": "Copper",
            "달러": "US Dollar",
            "유로": "Euro",
            "엔화": "Japanese Yen",
            "위안화": "Chinese Yuan",
            "리츠": "REITs",
            "부동산": "Real Estate",
            "농산물": "Agricultural Commodities",
            "곡물": "Grains",
            "대두": "Soybeans",
            "옥수수": "Corn",
            "밀": "Wheat",
            "S&P500": "S&P 500",
            "나스닥": "NASDAQ",
            "다우존스": "Dow Jones",
            "러셀2000": "Russell 2000",
            "코스피": "KOSPI",
            "코스닥": "KOSDAQ",
            "밸류": "Value",
            "그로스": "Growth",
            "모멘텀": "Momentum",
            "퀄리티": "Quality",
            "저변동성": "Low Volatility",
        }

        # 4순위: 전략 키워드 (조합용)
        strategy_keywords = {
            "레버리지": "Leveraged",
            "2X": "2X Leveraged",
            "3X": "3X Leveraged",
            "인버스": "Inverse",
            "인버스2X": "2X Inverse",
            "액티브": "Active",
            "커버드콜": "Covered Call",
            "합성": "Synthetic",
        }

        # 우선순위대로 검색
        result_industry = None
        result_strategy = None

        # 가장 구체적인 키워드부터 찾기
        for keywords_dict in [
            high_priority_keywords,
            medium_priority_keywords,
            low_priority_keywords,
        ]:
            if result_industry:
                break
            for keyword, industry in keywords_dict.items():
                if keyword in name:
                    result_industry = industry
                    break

        # 전략 키워드 찾기
        for keyword, strategy in strategy_keywords.items():
            if keyword in name:
                result_strategy = strategy
                break

        # 결과 조합
        if result_industry and result_strategy:
            return f"{result_industry} ({result_strategy})"
        elif result_industry:
            return result_industry
        elif result_strategy:
            return result_strategy

        return "ETF"  # 기본값

    def _get_etf_industry_alpha_vantage(self, symbol: str) -> Optional[str]:
        """Alpha Vantage로 해외 ETF industry 조회"""
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            db_logger.warning("⚠️ ALPHA_VANTAGE_API_KEY 환경변수 없음")
            return None

        try:
            url = "https://www.alphavantage.co/query"
            params = {"function": "OVERVIEW", "symbol": symbol, "apikey": api_key}

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Alpha Vantage는 "AssetType"과 "Industry" 제공
                asset_type = data.get("AssetType")
                industry = data.get("Industry")

                if asset_type == "ETF" and industry:
                    db_logger.info(f"✅ Alpha Vantage {symbol} industry: {industry}")
                    return industry
            else:
                db_logger.warning(f"⚠️ Alpha Vantage API 실패: {response.status_code}")
        except Exception as e:
            db_logger.error(f"❌ Alpha Vantage {symbol} 오류: {e}")

        return None

    async def update_symbol_sector_info(self) -> dict:
        """symbol_table에서 sector/industry가 None인 항목 업데이트"""
        try:
            db_logger.info("🔄 symbol_table sector/industry 정보 업데이트 시작")

            # sector나 industry가 None인 종목 조회
            response = (
                self.supabase.table("symbol_table")
                .select("name, symbol, exchange, sector, industry")
                .execute()
            )
            stocks = response.data

            # sector나 industry가 None인 종목 필터링
            stocks_to_update = [
                stock
                for stock in stocks
                if stock.get("sector") is None or stock.get("industry") is None
            ]

            db_logger.info(
                f"📋 sector/industry 정보가 없는 종목: {len(stocks_to_update)}개"
            )

            if len(stocks_to_update) == 0:
                db_logger.info("✅ 업데이트할 종목이 없습니다")
                return {
                    "success_count": 0,
                    "fail_count": 0,
                    "skip_count": len(stocks),
                    "total_count": len(stocks),
                }

            import yfinance as yf

            success_count = 0
            fail_count = 0
            failed_stocks = []

            for stock in stocks_to_update:
                name = stock["name"]
                symbol = stock["symbol"]
                exchange = stock["exchange"]

                db_logger.info(f"📈 처리 중: {name} ({symbol}) from {exchange}")

                sector = None
                industry = None

                # ETF 여부 먼저 확인
                is_etf = self._check_if_etf(name, symbol, exchange)

                if is_etf:
                    # ETF인 경우 sector는 "ETF"로 고정
                    sector = "ETF"
                    db_logger.info(f"🎯 {name} ({symbol}) ETF로 확인됨")

                    # industry 결정
                    # 해외 ETF인 경우 Alpha Vantage 시도
                    if exchange not in ["KOSPI", "KOSDAQ"]:
                        db_logger.info(
                            f"🌏 {name} ({symbol}) 해외 ETF - Alpha Vantage 조회 시도"
                        )
                        industry = self._get_etf_industry_alpha_vantage(symbol)

                    # industry가 여전히 없거나 국내 ETF인 경우 이름에서 추출
                    if industry is None:
                        db_logger.info(
                            f"📝 {name} ({symbol}) 이름에서 industry 추출 시도"
                        )
                        industry = self._extract_industry_from_name(name)

                    db_logger.info(
                        f"✨ ETF {name} ({symbol}) sector={sector}, industry={industry}"
                    )

                else:
                    # 일반 주식인 경우에만 yfinance로 정보 조회
                    try:
                        if exchange in ["KOSPI", "KOSDAQ"]:
                            # 국내 주식은 .KS/.KQ suffix 추가
                            ticker_suffix = ".KS" if exchange == "KOSPI" else ".KQ"
                            yf_ticker = f"{symbol}{ticker_suffix}"
                        else:
                            # 해외 주식은 그대로
                            yf_ticker = symbol

                        yf_stock = yf.Ticker(yf_ticker)
                        yf_info = yf_stock.info

                        sector = yf_info.get("sector")
                        industry = yf_info.get("industry")

                        db_logger.info(
                            f"📊 yfinance {name} ({symbol}) sector={sector}, industry={industry}"
                        )

                    except Exception as e:
                        db_logger.error(f"❌ yfinance {name} ({symbol}) 조회 오류: {e}")

                # sector 또는 industry가 있으면 업데이트
                if sector or industry:
                    try:
                        # 업데이트할 데이터 준비
                        update_data = {}
                        if sector:
                            update_data["sector"] = sector
                        if industry:
                            update_data["industry"] = industry

                        # DB 업데이트
                        update_result = (
                            self.supabase.table("symbol_table")
                            .update(update_data)
                            .eq("name", name)
                            .execute()
                        )

                        if update_result.data:
                            success_count += 1
                            db_logger.info(
                                f"✅ {name} ({symbol}) sector/industry 업데이트 완료: "
                                f"sector={sector}, industry={industry}"
                            )
                        else:
                            fail_count += 1
                            failed_stocks.append(
                                f"{name} ({symbol}) - DB 업데이트 실패"
                            )
                            db_logger.error(f"❌ {name} ({symbol}) DB 업데이트 실패")

                    except Exception as e:
                        fail_count += 1
                        failed_stocks.append(f"{name} ({symbol}) - 오류: {str(e)}")
                        db_logger.error(f"❌ {name} ({symbol}) 업데이트 오류: {e}")

                else:
                    fail_count += 1
                    failed_stocks.append(
                        f"{name} ({symbol}) - sector/industry 정보 없음"
                    )
                    db_logger.warning(f"⚠️ {name} ({symbol}) sector/industry 정보 없음")

            db_logger.info(
                f"🏁 sector/industry 업데이트 완료 - 성공: {success_count}, 실패: {fail_count}"
            )

            # 실패한 종목이 있으면 로깅
            if failed_stocks:
                db_logger.warning(f"❌ 실패한 종목 ({fail_count}개):")
                for failed in failed_stocks:
                    db_logger.warning(f"   - {failed}")

            return {
                "success_count": success_count,
                "fail_count": fail_count,
                "skip_count": 0,
                "total_count": len(stocks_to_update),
                "failed_stocks": failed_stocks,
            }

        except Exception as e:
            db_logger.error(f"❌ symbol_table sector/industry 업데이트 전체 오류: {e}")
            raise

    async def update_symbol_table_prices(self) -> dict:
        """symbol_table의 모든 종목 최신 가격 업데이트"""
        try:
            db_logger.info("🔄 symbol_table 가격 업데이트 시작")

            # 가장 최근 영업일 계산
            latest_business_date = self._get_latest_business_date()
            db_logger.info(f"📅 최근 영업일: {latest_business_date}")

            # symbol_table에서 모든 종목 조회 (name이 primary key)
            response = (
                self.supabase.table("symbol_table")
                .select("name, symbol, exchange, updated_at")
                .execute()
            )
            stocks = response.data

            success_count = 0
            fail_count = 0
            skip_count = 0
            failed_stocks = []  # 실패한 종목 리스트

            for stock in stocks:
                name = stock["name"]
                symbol = stock["symbol"]
                exchange = stock["exchange"]
                updated_at = stock.get("updated_at")

                # updated_at이 이미 최근 영업일이면 스킵
                if updated_at:
                    # updated_at을 datetime으로 변환
                    if isinstance(updated_at, str):
                        try:
                            updated_at_dt = datetime.fromisoformat(
                                updated_at.replace("Z", "+00:00")
                            )
                            updated_date = updated_at_dt.date()
                        except:
                            updated_date = None
                    elif hasattr(updated_at, "date"):
                        updated_date = updated_at.date()
                    else:
                        updated_date = None

                    # 이미 최근 영업일에 업데이트되었으면 스킵
                    if updated_date == latest_business_date:
                        skip_count += 1
                        db_logger.info(
                            f"⏭️ 스킵: {name} ({symbol}) - 이미 최근 영업일({latest_business_date})에 업데이트됨"
                        )
                        continue

                db_logger.info(f"📈 처리 중: {name} ({symbol}) from {exchange}")

                latest_close = None
                marketcap = None
                price_date = None

                # 거래소에 따라 다른 데이터 소스 사용
                if exchange in ["KOSPI", "KOSDAQ"]:
                    latest_close, marketcap, price_date = self._get_korean_stock_data(
                        symbol, exchange
                    )
                else:
                    # 해외 주식은 yfinance 사용
                    latest_close, marketcap, price_date = self._get_stock_data_yfinance(
                        symbol
                    )

                # 가격 정보가 있으면 업데이트
                if latest_close is not None:
                    # updated_at은 최근 영업일로 설정
                    updated_at_datetime = datetime.combine(
                        latest_business_date, datetime.min.time()
                    )

                    update_data = {
                        "latest_close": float(latest_close),
                        "updated_at": updated_at_datetime.isoformat(),
                    }
                    if marketcap is not None:
                        update_data["marketcap"] = float(marketcap)

                    update_result = (
                        self.supabase.table("symbol_table")
                        .update(update_data)
                        .eq("name", name)  # name으로 업데이트
                        .execute()
                    )

                    if update_result.data:
                        success_count += 1
                        db_logger.info(
                            f"✅ {name} ({symbol}) 업데이트 완료: {latest_close}"
                        )
                    else:
                        fail_count += 1
                        failed_stocks.append(f"{name} ({symbol}) - DB 업데이트 실패")
                        db_logger.error(f"❌ {name} ({symbol}) DB 업데이트 실패")
                else:
                    fail_count += 1
                    failed_stocks.append(f"{name} ({symbol}) - 가격 정보 없음")
                    db_logger.warning(f"⚠️ {name} ({symbol}) 가격 정보 없음")

            db_logger.info(
                f"🏁 가격 업데이트 완료 - 성공: {success_count}, 실패: {fail_count}, 스킵: {skip_count}"
            )

            # 실패한 종목이 있으면 로깅
            if failed_stocks:
                db_logger.warning(f"❌ 실패한 종목 ({fail_count}개):")
                for failed in failed_stocks:
                    db_logger.warning(f"   - {failed}")

            return {
                "success_count": success_count,
                "fail_count": fail_count,
                "skip_count": skip_count,
                "total_count": len(stocks),
                "failed_stocks": failed_stocks,
            }

        except Exception as e:
            db_logger.error(f"❌ symbol_table 가격 업데이트 전체 오류: {e}")
            raise

    # ============ 현금 관리 관련 메서드 ============

    async def get_cash_balances(
        self, account: Optional[str] = None
    ) -> List[CashBalance]:
        """증권사별 예수금 정보 조회"""
        try:
            query = self.supabase.table("cash_balance").select("*")
            if account:
                query = query.eq("account", account)

            response = query.execute()
            data = response.data

            cash_balances = []
            for item in data:
                cash_balance = CashBalance(
                    account=item.get("account"),
                    krw=float(item.get("krw", 0)),
                    usd=float(item.get("usd", 0)),
                    updated_at=datetime.now(),
                )
                cash_balances.append(cash_balance)

            return cash_balances

        except Exception as e:
            db_logger.error(f"현금 잔액 조회 오류: {e}")
            raise

    async def update_cash_balance(
        self, account: str, krw: Optional[float] = None, usd: Optional[float] = None
    ) -> bool:
        """증권사별 예수금 업데이트"""
        try:
            update_data = {}
            if krw is not None:
                update_data["krw"] = int(krw) if isinstance(krw, (int, float)) else krw
            if usd is not None:
                update_data["usd"] = (
                    float(usd) if isinstance(usd, (int, float)) else usd
                )

            if not update_data:
                db_logger.warning(f"⚠️ {account}: 업데이트할 데이터가 없음")
                return False

            db_logger.info(f"🔄 {account} 현금 잔액 업데이트 시도: {update_data}")

            # 먼저 해당 계좌가 존재하는지 확인
            existing = (
                self.supabase.table("cash_balance")
                .select("*")
                .eq("account", account)
                .execute()
            )
            if not existing.data:
                db_logger.error(f"❌ {account} 계좌를 찾을 수 없음")
                return False

            result = (
                self.supabase.table("cash_balance")
                .update(update_data)
                .eq("account", account)
                .execute()
            )

            db_logger.info(f"📊 Supabase 응답: {result}")

            if result.data:
                db_logger.info(f"✅ {account} 현금 잔액 업데이트 성공: {update_data}")

                # bs_timeseries 테이블에 security_cash_balance 동기화
                await self._sync_bs_timeseries_from_cash_balances()

                return True
            else:
                db_logger.error(f"❌ {account} 현금 잔액 업데이트 실패 - 데이터 없음")
                return False

        except Exception as e:
            db_logger.error(f"현금 잔액 업데이트 오류: {e}")
            import traceback

            db_logger.error(f"상세 에러: {traceback.format_exc()}")
            raise

    async def _sync_bs_timeseries_from_cash_balances(self) -> None:
        """cash_balance 테이블의 데이터를 기반으로 bs_timeseries 테이블의 security_cash_balance 필드 동기화"""
        try:
            # 1. cash_balance 테이블에서 모든 계좌의 krw 잔액 합계 계산
            cash_balances_response = (
                self.supabase.table("cash_balance").select("krw").execute()
            )
            cash_balances_data = cash_balances_response.data

            # 모든 증권사 예수금의 총합 계산
            total_security_cash = sum(
                float(item.get("krw", 0) or 0) for item in cash_balances_data
            )

            db_logger.info(
                f"💰 cash_balance 테이블 기반 총 증권사 예수금 계산: {total_security_cash:,}원"
            )

            # 2. 오늘 날짜의 bs_timeseries 항목 업데이트
            today = date.today()

            # 오늘 날짜의 기존 항목이 있는지 확인
            existing_bs = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .eq("date", today.isoformat())
                .execute()
            )

            if existing_bs.data:
                # 기존 항목 업데이트
                update_result = (
                    self.supabase.table("bs_timeseries")
                    .update({"security_cash_balance": int(total_security_cash)})
                    .eq("date", today.isoformat())
                    .execute()
                )

                if update_result.data:
                    db_logger.info(
                        f"✅ bs_timeseries 테이블의 security_cash_balance 업데이트 성공: {int(total_security_cash):,}원"
                    )
                else:
                    db_logger.error(f"❌ bs_timeseries 테이블 업데이트 실패")
            else:
                # 새 항목 생성
                new_bs_data = {
                    "date": today.isoformat(),
                    "security_cash_balance": int(total_security_cash),
                    "cash": 0,  # 기본값
                    "time_deposit": 0,  # 기본값
                }

                create_result = (
                    self.supabase.table("bs_timeseries").insert(new_bs_data).execute()
                )

                if create_result.data:
                    db_logger.info(
                        f"✅ bs_timeseries 테이블에 새 항목 생성 성공: {int(total_security_cash):,}원"
                    )
                else:
                    db_logger.error(f"❌ bs_timeseries 테이블 신규 항목 생성 실패")

        except Exception as e:
            db_logger.error(f"bs_timeseries 동기화 중 오류 발생: {e}")
            raise

    async def get_time_deposits(
        self, account: Optional[str] = None
    ) -> List[TimeDeposit]:
        """예적금 정보 조회"""
        try:
            query = self.supabase.table("time_deposit").select("*")
            if account:
                query = query.eq("account", account)

            response = query.execute()
            data = response.data

            time_deposits = []
            for item in data:
                time_deposit = TimeDeposit(
                    account=item.get("account"),
                    invest_prod_name=item.get("invest_prod_name"),
                    market_value=item.get("market_value", 0),
                    invested_principal=item.get("invested_principal", 0),
                    maturity_date=item.get("maturity_date"),
                    interest_rate=item.get("interest_rate"),
                    updated_at=datetime.now(),
                )
                time_deposits.append(time_deposit)

            return time_deposits

        except Exception as e:
            db_logger.error(f"예적금 정보 조회 오류: {e}")
            raise

    async def create_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: int,
        invested_principal: int,
        maturity_date: Optional[datetime] = None,
        interest_rate: Optional[float] = None,
    ) -> bool:
        """예적금 생성"""
        try:
            insert_data = {
                "account": account,
                "invest_prod_name": invest_prod_name,
                "market_value": market_value,
                "invested_principal": invested_principal,
                "updated_at": datetime.now(),
            }

            if maturity_date:
                insert_data["maturity_date"] = maturity_date
            if interest_rate:
                insert_data["interest_rate"] = interest_rate

            db_logger.debug(f"Insert data: {insert_data}")
            # 커스텀 클라이언트가 자동으로 JSON 직렬화 처리
            result = self.supabase.table("time_deposit").insert(insert_data).execute()

            if result.data:
                db_logger.info(f"✅ 예적금 생성 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self._sync_bs_timeseries_from_time_deposits()

                return True
            else:
                db_logger.error(f"❌ 예적금 생성 실패: {invest_prod_name}")
                return False

        except Exception as e:
            db_logger.error(f"예적금 생성 오류: {e}")
            raise

    async def update_time_deposit(
        self,
        account: str,
        invest_prod_name: str,
        market_value: Optional[int] = None,
        invested_principal: Optional[int] = None,
        maturity_date: Optional[datetime] = None,
        interest_rate: Optional[float] = None,
    ) -> bool:
        """예적금 수정"""
        try:
            update_data = {}
            if market_value is not None:
                update_data["market_value"] = market_value
            if invested_principal is not None:
                update_data["invested_principal"] = invested_principal
            if maturity_date is not None:
                update_data["maturity_date"] = maturity_date
            if interest_rate is not None:
                update_data["interest_rate"] = interest_rate

            if not update_data:
                return False

            db_logger.debug(f"Update data: {update_data}")
            # 커스텀 클라이언트가 자동으로 JSON 직렬화 처리
            result = (
                self.supabase.table("time_deposit")
                .update(update_data)
                .eq("account", account)
                .eq("invest_prod_name", invest_prod_name)
                .execute()
            )

            if result.data:
                db_logger.info(f"✅ 예적금 수정 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self._sync_bs_timeseries_from_time_deposits()

                return True
            else:
                db_logger.error(f"❌ 예적금 수정 실패: {invest_prod_name}")
                return False

        except Exception as e:
            db_logger.error(f"예적금 수정 오류: {e}")
            raise

    async def delete_time_deposit(self, account: str, invest_prod_name: str) -> bool:
        """예적금 삭제"""
        try:
            result = (
                self.supabase.table("time_deposit")
                .delete()
                .eq("account", account)
                .eq("invest_prod_name", invest_prod_name)
                .execute()
            )

            if result.data:
                db_logger.info(f"✅ 예적금 삭제 성공: {invest_prod_name}")

                # bs_timeseries 테이블 동기화
                await self._sync_bs_timeseries_from_time_deposits()

                return True
            else:
                db_logger.error(f"❌ 예적금 삭제 실패: {invest_prod_name}")
                return False

        except Exception as e:
            db_logger.error(f"예적금 삭제 오류: {e}")
            raise

    async def get_latest_bs_entry(self) -> Optional[dict]:
        """가장 최신 bs_timeseries 항목 조회"""
        try:
            response = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .order("date", desc=True)
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]
            else:
                return None

        except Exception as e:
            db_logger.error(f"최신 bs_timeseries 조회 오류: {e}")
            raise

    async def update_current_cash(
        self,
        cash: Optional[int] = None,
        time_deposit: Optional[int] = None,
        security_cash_balance: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """현재 현금 정보 선택적 업데이트 (bs_timeseries)

        Args:
            cash: 현금 (입출금계좌 합, 현금성 자산 총합 아님)
            time_deposit: 예적금
            security_cash_balance: 증권사 예수금
            reason: 업데이트 사유
        """
        try:
            today = date.today()

            # 업데이트할 컬럼 결정
            update_fields = {}
            if cash is not None:
                update_fields["cash"] = int(cash)
            if time_deposit is not None:
                update_fields["time_deposit"] = int(time_deposit)
            if security_cash_balance is not None:
                update_fields["security_cash_balance"] = int(security_cash_balance)

            if not update_fields:
                db_logger.warning("❌ 업데이트할 필드가 없습니다")
                return False

            # 오늘 데이터가 있는지 확인
            existing_response = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .eq("date", today.isoformat())
                .execute()
            )

            if existing_response.data:
                # 기존 데이터가 있으면 선택적 컬럼만 업데이트
                result = (
                    self.supabase.table("bs_timeseries")
                    .update(update_fields)
                    .eq("date", today.isoformat())
                    .execute()
                )
                db_logger.info(f"✅ 기존 데이터 업데이트: {list(update_fields.keys())}")
            else:
                # 새 데이터인 경우, 가장 최신 데이터에서 기존 값 가져오기
                latest_response = (
                    self.supabase.table("bs_timeseries")
                    .select("*")
                    .order("date", desc=True)
                    .limit(1)
                    .execute()
                )

                # 기본값 설정
                new_data = {"date": today.isoformat()}

                if latest_response.data:
                    latest = latest_response.data[0]
                    # 업데이트하지 않을 필드는 최신 데이터에서 가져오기
                    new_data["cash"] = (
                        int(cash) if cash is not None else latest.get("cash", 0)
                    )
                    new_data["time_deposit"] = (
                        int(time_deposit)
                        if time_deposit is not None
                        else latest.get("time_deposit", 0)
                    )
                    new_data["security_cash_balance"] = (
                        int(security_cash_balance)
                        if security_cash_balance is not None
                        else latest.get("security_cash_balance", 0)
                    )
                else:
                    # 이전 데이터가 없는 경우 기본값 사용
                    new_data["cash"] = int(cash) if cash is not None else 0
                    new_data["time_deposit"] = (
                        int(time_deposit) if time_deposit is not None else 0
                    )
                    new_data["security_cash_balance"] = (
                        int(security_cash_balance)
                        if security_cash_balance is not None
                        else 0
                    )

                result = self.supabase.table("bs_timeseries").insert(new_data).execute()
                db_logger.info(
                    f"✅ 새 데이터 생성: cash={new_data['cash']:,}, time_deposit={new_data['time_deposit']:,}, security={new_data['security_cash_balance']:,}"
                )

            if result.data:
                # 업데이트된 정보 요약
                updated_fields = ", ".join(
                    [f"{k}: {v:,}원" for k, v in update_fields.items()]
                )
                db_logger.info(
                    f"✅ 현금 정보 업데이트 성공 - {updated_fields} (사유: {reason or '수동 업데이트'})"
                )
                return True
            else:
                db_logger.error(f"❌ 현금 정보 업데이트 실패")
                return False

        except Exception as e:
            db_logger.error(f"현금 정보 업데이트 오류: {e}")
            raise

    async def get_cash_management_summary(self) -> CashManagementSummary:
        """현금 관리 요약 정보 조회"""
        try:
            # 1. 현금 잔액 조회
            cash_balances = await self.get_cash_balances()

            # 2. 예적금 조회
            time_deposits = await self.get_time_deposits()

            # 3. 최신 bs_timeseries 조회
            latest_bs = await self.get_latest_bs_entry()

            if latest_bs:
                # date 필드를 datetime으로 변환하여 JSON 직렬화 문제 해결
                bs_data = latest_bs.copy()
                if "date" in bs_data:
                    date_value = bs_data["date"]
                    if isinstance(date_value, str):
                        bs_data["date"] = datetime.fromisoformat(
                            date_value.replace("Z", "+00:00")
                        )
                    elif isinstance(date_value, date):
                        bs_data["date"] = datetime.combine(
                            date_value, datetime.min.time()
                        )
                    else:
                        bs_data["date"] = date_value

                return CashManagementSummary(
                    total_cash=latest_bs["cash"]
                    + latest_bs["time_deposit"]
                    + latest_bs["security_cash_balance"],
                    total_cash_balance=latest_bs["cash"],
                    total_time_deposit=latest_bs["time_deposit"],
                    total_security_cash=latest_bs["security_cash_balance"],
                    cash_balances=cash_balances,
                    time_deposits=time_deposits,
                    latest_bs_entry=BSTimeseries(**bs_data),
                    updated_at=datetime.now(),
                )
            else:
                return CashManagementSummary(
                    total_cash=0,
                    total_cash_balance=0,
                    total_time_deposit=0,
                    total_security_cash=0,
                    cash_balances=[],
                    time_deposits=[],
                    latest_bs_entry=None,
                    updated_at=datetime.now(),
                )

        except Exception as e:
            db_logger.error(f"현금 관리 요약 조회 오류: {e}")
            raise

    async def _sync_bs_timeseries_from_time_deposits(self) -> None:
        """time_deposit 테이블의 데이터를 기반으로 bs_timeseries 테이블의 time_deposit 필드 동기화"""
        try:
            # 1. time_deposit 테이블에서 모든 예적금의 market_value 합계 계산
            time_deposits_response = (
                self.supabase.table("time_deposit").select("market_value").execute()
            )
            time_deposits_data = time_deposits_response.data

            # 모든 예적금의 현재 평가액 합계 계산
            total_time_deposit = sum(
                float(item.get("market_value", 0) or 0) for item in time_deposits_data
            )

            db_logger.info(
                f"💰 time_deposit 테이블 기반 총 예적금 계산: {total_time_deposit:,}원"
            )

            # 2. 오늘 날짜의 bs_timeseries 항목 업데이트
            today = date.today()

            # 오늘 데이터가 있는지 확인
            existing_response = (
                self.supabase.table("bs_timeseries")
                .select("*")
                .eq("date", today.isoformat())
                .execute()
            )

            update_data = {"time_deposit": int(total_time_deposit)}

            if existing_response.data:
                # 기존 데이터가 있으면 time_deposit 필드만 업데이트
                result = (
                    self.supabase.table("bs_timeseries")
                    .update(update_data)
                    .eq("date", today.isoformat())
                    .execute()
                )
                db_logger.info(
                    f"✅ bs_timeseries 기존 데이터 동기화 완료: time_deposit={total_time_deposit:,}원"
                )
            else:
                # 오늘 데이터가 없으면 가장 최신 데이터에서 다른 필드 값을 가져와서 새로 생성
                latest_response = (
                    self.supabase.table("bs_timeseries")
                    .select("*")
                    .order("date", desc=True)
                    .limit(1)
                    .execute()
                )

                new_data = {"date": today.isoformat()}

                if latest_response.data:
                    latest = latest_response.data[0]
                    # 기존 필드 값 유지
                    new_data["cash"] = latest.get("cash", 0)
                    new_data["time_deposit"] = int(total_time_deposit)  # 새로 계산된 값
                    new_data["security_cash_balance"] = latest.get(
                        "security_cash_balance", 0
                    )
                else:
                    # 이전 데이터가 없는 경우
                    new_data["cash"] = 0
                    new_data["time_deposit"] = int(total_time_deposit)
                    new_data["security_cash_balance"] = 0

                result = self.supabase.table("bs_timeseries").insert(new_data).execute()
                db_logger.info(
                    f"✅ bs_timeseries 새 데이터 생성 완료: time_deposit={total_time_deposit:,}원"
                )

            if result.data:
                db_logger.info(
                    f"🎯 bs_timeseries 동기화 성공: time_deposit={total_time_deposit:,}원"
                )
            else:
                db_logger.error(f"❌ bs_timeseries 동기화 실패")

        except Exception as e:
            db_logger.error(f"❌ bs_timeseries 동기화 중 오류 발생: {e}")
            # 동기화 실패하더라도 예적금 수정/생성/삭제는 성공한 것으로 처리 (에러를 다시 발생시키지 않음)
