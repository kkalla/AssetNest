"""Holdings service for stock and portfolio holdings management."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

from .interfaces import IHoldingsService
from ..database_modules.repositories import HoldingsRepository
from ..adapters.market_data_adapter import MarketDataAdapter
from ..database_modules.models import DatabaseModels

logger = logging.getLogger(__name__)


class HoldingsService(IHoldingsService):
    """보유 종목 관리 서비스."""

    def __init__(
        self,
        holdings_repository: HoldingsRepository,
        market_data_adapter: MarketDataAdapter,
    ):
        self.holdings_repository = holdings_repository
        self.market_data_adapter = market_data_adapter

    async def get_holdings(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.HoldingDetail]:
        """보유 종목 정보 조회"""
        try:
            logger.info(f"📊 보유 종목 정보 조회 - 계좌: {account or '전체'}")

            holdings_data = self.holdings_repository.get_holdings(account)

            holdings = []
            for item in holdings_data:
                holding = DatabaseModels.HoldingDetail(
                    account=item.get("account"),
                    name=item.get("company"),
                    symbol=item.get("symbol"),
                    quantity=int(item.get("amount", 0)),
                    average_price=float(item.get("avg_price_krw", 0)),
                    current_price=float(item.get("current_price_krw", 0)),
                    valuation_amount=float(item.get("market_value", 0)),
                    profit_loss=float(item.get("unrealized_pnl", 0)),
                    profit_loss_rate=float(item.get("return_rate", 0)),
                    currency="KRW",
                    sector=item.get("sector"),
                    asset_type=item.get("asset_type"),
                    region_type=item.get("region_type"),
                    updated_at=datetime.now(),
                )
                holdings.append(holding)

            logger.info(f"✅ 보유 종목 정보 조회 완료 - {len(holdings)}개 종목")
            return holdings

        except Exception as e:
            logger.error(f"보유 종목 정보 조회 오류: {e}")
            raise

    async def update_holding(
        self,
        account: str,
        company: str,
        quantity: Optional[int] = None,
        average_price: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> bool:
        """보유 종목 정보 업데이트"""
        try:
            logger.info(f"🔄 보유 종목 정보 업데이트 - {account}/{company}")

            update_data = {}
            if quantity is not None:
                update_data["amount"] = quantity
            if average_price is not None:
                update_data["avg_price_krw"] = average_price
            if current_price is not None:
                update_data["current_price_krw"] = current_price

            if not update_data:
                logger.warning("⚠️ 업데이트할 데이터가 없음")
                return False

            result = self.holdings_repository.update_holding(
                account, company, update_data
            )

            if result:
                logger.info(f"✅ 보유 종목 정보 업데이트 성공: {company}")
            else:
                logger.error(f"❌ 보유 종목 정보 업데이트 실패: {company}")

            return result

        except Exception as e:
            logger.error(f"보유 종목 정보 업데이트 오류: {e}")
            raise

    async def get_stock_info(self, symbol: str) -> Optional[DatabaseModels.StockInfo]:
        """특정 주식 정보 조회"""
        try:
            logger.info(f"📊 주식 정보 조회 - {symbol}")

            stock_data = self.holdings_repository.get_stock_info(symbol)

            if stock_data:
                stock_info = DatabaseModels.StockInfo(
                    symbol=stock_data.get("symbol"),
                    name=stock_data.get("company"),
                    sector=stock_data.get("sector"),
                    industry=stock_data.get("industry"),
                    asset_type=stock_data.get("asset_type"),
                    region_type=stock_data.get("region_type"),
                    latest_close=stock_data.get("latest_close"),
                    marketcap=stock_data.get("marketcap"),
                    updated_at=stock_data.get("updated_at"),
                )
                logger.info(f"✅ 주식 정보 조회 성공: {symbol}")
                return stock_info
            else:
                logger.warning(f"⚠️ 주식 정보 없음: {symbol}")
                return None

        except Exception as e:
            logger.error(f"주식 정보 조회 오류: {e}")
            raise

    async def update_symbol_prices(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """symbol_table의 가격 정보 업데이트"""
        try:
            logger.info(
                f"🔄 symbol 가격 정보 업데이트 시작 - {symbols if symbols else '전체'}"
            )

            # 가장 최근 영업일 계산
            latest_business_date = self._get_latest_business_date()
            logger.info(f"📅 최근 영업일: {latest_business_date}")

            # symbol_table 데이터 조회
            symbol_data = self.holdings_repository.get_symbol_table(symbols)
            logger.info(f"📊 대상 심볼 수: {len(symbol_data)}")

            updated_symbols = []
            failed_symbols = []

            # 종목별 가격 업데이트
            for symbol_info in symbol_data:
                symbol = symbol_info.get("symbol")
                region_type = symbol_info.get("region_type", "domestic")

                try:
                    # 시장 데이터 어댑터로 가격 조회
                    price_data = await self.market_data_adapter.get_stock_price(
                        symbol, region_type, latest_business_date
                    )

                    if price_data and price_data.get("latest_close"):
                        # symbol_table 업데이트
                        update_result = self.holdings_repository.update_symbol_price(
                            symbol,
                            price_data["latest_close"],
                            price_data.get("marketcap"),
                            price_data.get("updated_at", datetime.now()),
                        )

                        if update_result:
                            updated_symbols.append(symbol)
                            logger.debug(
                                f"✅ {symbol} 가격 업데이트 성공: {price_data['latest_close']}"
                            )
                        else:
                            failed_symbols.append(symbol)
                            logger.error(f"❌ {symbol} 가격 DB 업데이트 실패")
                    else:
                        failed_symbols.append(symbol)
                        logger.warning(f"⚠️ {symbol} 가격 정보 없음")

                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.error(f"❌ {symbol} 가격 업데이트 오류: {e}")

            # 결과 요약
            total_symbols = len(symbol_data)
            success_count = len(updated_symbols)
            failed_count = len(failed_symbols)
            success_rate = (
                (success_count / total_symbols * 100) if total_symbols > 0 else 0
            )

            result = {
                "total_symbols": total_symbols,
                "updated_symbols": updated_symbols,
                "failed_symbols": failed_symbols,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": round(success_rate, 2),
                "target_date": latest_business_date.isoformat(),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"🏁 symbol 가격 업데이트 완료 - 성공: {success_count}/{total_symbols} ({success_rate:.1f}%)"
            )
            return result

        except Exception as e:
            logger.error(f"symbol 가격 업데이트 전체 오류: {e}")
            raise

    async def get_all_stocks(self) -> List[DatabaseModels.StockInfo]:
        """모든 주식 정보 조회"""
        try:
            logger.info("📊 모든 주식 정보 조회 시작")

            stock_data = self.holdings_repository.get_all_stocks()

            stocks = []
            for item in stock_data:
                stock = DatabaseModels.StockInfo(
                    symbol=item.get("symbol"),
                    name=item.get("company"),
                    sector=item.get("sector"),
                    industry=item.get("industry"),
                    asset_type=item.get("asset_type"),
                    region_type=item.get("region_type"),
                    latest_close=item.get("latest_close"),
                    marketcap=item.get("marketcap"),
                    updated_at=item.get("updated_at"),
                )
                stocks.append(stock)

            logger.info(f"✅ 모든 주식 정보 조회 완료 - {len(stocks)}개 종목")
            return stocks

        except Exception as e:
            logger.error(f"모든 주식 정보 조회 오류: {e}")
            raise

    async def get_performance_data(
        self, account: str
    ) -> DatabaseModels.PerformanceData:
        """성과 데이터 조회"""
        try:
            logger.info(f"📊 성과 데이터 조회 - 계좌: {account}")

            # 기본 성과 데이터 생성 (추후 확장 가능)
            performance_data = DatabaseModels.PerformanceData(
                account=account,
                total_investment=0.0,
                total_value=0.0,
                total_return=0.0,
                return_rate=0.0,
                sector_allocation={},
                region_allocation={},
                daily_returns=[],
                cumulative_returns=[],
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                updated_at=datetime.now(),
            )

            logger.info(f"✅ 성과 데이터 조회 완료 - 계좌: {account}")
            return performance_data

        except Exception as e:
            logger.error(f"성과 데이터 조회 오류: {e}")
            raise

    async def update_symbol_table_prices(self) -> Dict[str, Any]:
        """symbol_table의 모든 종목 최신 가격 업데이트"""
        return await self.update_symbol_prices()

    async def update_symbol_sector_info(self) -> Dict[str, Any]:
        """symbol_table에서 sector/industry가 None인 항목 업데이트"""
        try:
            logger.info("🔄 symbol sector 정보 업데이트 시작")

            # sector가 None인 심볼 조회
            symbols_to_update = self.holdings_repository.get_symbols_without_sector()
            logger.info(f"📊 sector 업데이트 대상: {len(symbols_to_update)}개 종목")

            updated_symbols = []
            failed_symbols = []

            for symbol_info in symbols_to_update:
                symbol = symbol_info.get("symbol")
                try:
                    # 기본적인 sector 정보 추출 (단순화된 버전)
                    company_name = symbol_info.get("company", "")
                    sector = self._extract_sector_from_name(company_name)

                    # sector 정보 업데이트
                    result = self.holdings_repository.update_symbol_sector(
                        symbol, sector
                    )

                    if result:
                        updated_symbols.append(symbol)
                        logger.debug(f"✅ {symbol} sector 업데이트 성공: {sector}")
                    else:
                        failed_symbols.append(symbol)
                        logger.error(f"❌ {symbol} sector DB 업데이트 실패")

                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.error(f"❌ {symbol} sector 업데이트 오류: {e}")

            # 결과 요약
            total_symbols = len(symbols_to_update)
            success_count = len(updated_symbols)
            failed_count = len(failed_symbols)

            result = {
                "total_symbols": total_symbols,
                "updated_symbols": updated_symbols,
                "failed_symbols": failed_symbols,
                "success_count": success_count,
                "failed_count": failed_count,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"🏁 symbol sector 업데이트 완료 - 성공: {success_count}/{total_symbols}"
            )
            return result

        except Exception as e:
            logger.error(f"symbol sector 업데이트 전체 오류: {e}")
            raise

    def _extract_sector_from_name(self, company_name: str) -> str:
        """회사 이름에서 sector 정보 추출 (단순화된 버전)"""
        if not company_name:
            return "기타"

        # 기본적인 sector 키워드 매칭
        sector_keywords = {
            "IT": ["반도체", "소프트웨어", "IT", "컴퓨터", "인터넷", "게임"],
            "금융": ["은행", "증권", "보험", "카드", "금융"],
            "바이오": ["바이오", "제약", "의약", "헬스케어", "의료"],
            "제조": ["제조", "자동차", "조선", "기계", "화학"],
            "유통": ["유통", "백화점", "리테일", "상사"],
            "통신": ["통신", "방송", "미디어"],
            "건설": ["건설", "부동산", "건축"],
            "에너지": ["에너지", "전력", "가스", "석유"],
        }

        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in company_name:
                    return sector

        return "기타"

    def _get_latest_business_date(self) -> date:
        """가장 최근 영업일을 계산하여 반환"""
        now = datetime.now()
        latest_business_day = now

        # 평일 20시 이전이면 전날로
        if now.hour < 20:
            latest_business_day = now - timedelta(days=1)

        # 주말이면 가장 최근 금요일로
        while latest_business_day.weekday() >= 5:  # 5=토요일, 6=일요일
            latest_business_day = latest_business_day - timedelta(days=1)

        return latest_business_day.date()
