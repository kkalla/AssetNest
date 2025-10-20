"""Portfolio service for portfolio overview and asset allocation management."""

import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional

from .interfaces import IPortfolioService, ISyncService
from ..database_modules.repositories import PortfolioRepository
from ..database_modules.models import DatabaseModels

logger = logging.getLogger(__name__)


class PortfolioService(IPortfolioService):
    """포트폴리오 관리 서비스."""

    def __init__(
        self, portfolio_repository: PortfolioRepository, sync_service: ISyncService
    ):
        self.portfolio_repository = portfolio_repository
        self.sync_service = sync_service

    async def get_portfolio_overview(self) -> DatabaseModels.PortfolioOverview:
        """포트폴리오 전체 현황 조회"""
        try:
            logger.info("📊 포트폴리오 전체 현황 조회 시작")

            # 1. overall_info 뷰에서 데이터 조회
            overview_data = self.portfolio_repository.get_portfolio_overview()

            if not overview_data:
                logger.warning("⚠️ 포트폴리오 데이터가 없습니다")
                return self._create_empty_overview()

            # 2. 데이터 변환 및 계산
            total_assets = 0
            total_valuation_amount = 0
            total_profit_loss = 0
            total_profit_loss_rate = 0
            krw_assets = 0
            usd_assets = 0
            total_equity = 0
            total_bond = 0
            total_reit = 0
            total_commodity = 0
            total_cash = 0

            for item in overview_data:
                # 통화별 자산 계산
                if item.get("currency") == "KRW":
                    krw_assets += float(item.get("valuation_amount", 0))
                elif item.get("currency") == "USD":
                    usd_assets += float(item.get("valuation_amount", 0))

                # 자산유형별 계산
                asset_type = item.get("asset_type", "").lower()
                valuation = float(item.get("valuation_amount", 0))

                if asset_type == "equity":
                    total_equity += valuation
                elif asset_type == "bond":
                    total_bond += valuation
                elif asset_type == "reit":
                    total_reit += valuation
                elif asset_type == "commodity":
                    total_commodity += valuation
                elif asset_type == "cash":
                    total_cash += valuation

                # 총계 계산
                total_valuation_amount += valuation
                total_profit_loss += float(item.get("profit_loss", 0))

            # 평가손익률 계산 (가중 평균)
            if total_valuation_amount > 0:
                total_profit_loss_rate = (
                    total_profit_loss / total_valuation_amount
                ) * 100

            # 총자산 = 총평가금액 (bs_timeseries의 현금 포함)
            total_assets = total_valuation_amount

            # 최신 bs_timeseries 데이터 조회
            latest_bs = self._get_latest_bs_data()

            # PortfolioOverview 객체 생성
            overview = DatabaseModels.PortfolioOverview(
                total_assets=int(total_assets),
                total_valuation_amount=int(total_valuation_amount),
                total_profit_loss=int(total_profit_loss),
                total_profit_loss_rate=round(total_profit_loss_rate, 2),
                krw_assets=int(krw_assets),
                usd_assets=int(usd_assets),
                total_equity=int(total_equity),
                total_bond=int(total_bond),
                total_reit=int(total_reit),
                total_commodity=int(total_commodity),
                total_cash=int(total_cash),
                updated_at=datetime.now(),
            )

            logger.info(
                f"✅ 포트폴리오 전체 현황 조회 완료 - 총자산: {total_assets:,.0f}원"
            )
            return overview

        except Exception as e:
            logger.error(f"포트폴리오 전체 현황 조회 오류: {e}")
            raise

    async def get_portfolio_summary(
        self, account: Optional[str] = None
    ) -> List[DatabaseModels.PortfolioSummary]:
        """계좌별 포트폴리오 요약 정보 조회"""
        try:
            logger.info(f"📊 포트폴리오 요약 정보 조회 - 계좌: {account or '전체'}")

            summary_data = self.portfolio_repository.get_portfolio_summary(account)

            summaries = []
            for item in summary_data:
                summary = DatabaseModels.PortfolioSummary(
                    account=item.get("account"),
                    valuation_amount=int(item.get("valuation_amount", 0)),
                    profit_loss=int(item.get("profit_loss", 0)),
                    profit_loss_rate=float(item.get("profit_loss_rate", 0)),
                    updated_at=datetime.now(),
                )
                summaries.append(summary)

            logger.info(f"✅ 포트폴리오 요약 정보 조회 완료 - {len(summaries)}개 계좌")
            return summaries

        except Exception as e:
            logger.error(f"포트폴리오 요약 정보 조회 오류: {e}")
            raise

    async def get_asset_allocation(self) -> DatabaseModels.AssetAllocation:
        """자산 배분 현황 조회"""
        try:
            logger.info("📊 자산 배분 현황 조회 시작")

            # 자산유형별 배분 조회
            allocation_data = self.portfolio_repository.get_asset_allocation_by_type()

            # 지역별 배분 조회
            region_data = self.portfolio_repository.get_asset_allocation_by_region()

            # 통화별 배분 조회
            currency_data = self.portfolio_repository.get_asset_allocation_by_currency()

            # 자산유형별 데이터 처리
            asset_type_allocation = {}
            for item in allocation_data:
                asset_type = item.get("asset_type", "기타")
                amount = float(item.get("valuation_amount", 0))
                asset_type_allocation[asset_type] = amount

            # 지역별 데이터 처리
            region_allocation = {}
            for item in region_data:
                region = item.get("region_type", "기타")
                amount = float(item.get("valuation_amount", 0))
                region_allocation[region] = amount

            # 통화별 데이터 처리
            currency_allocation = {}
            for item in currency_data:
                currency = item.get("currency", "기타")
                amount = float(item.get("valuation_amount", 0))
                currency_allocation[currency] = amount

            # 총자산 계산
            total_assets = sum(asset_type_allocation.values())

            # 비율 계산
            asset_type_ratios = {
                asset_type: (amount / total_assets * 100) if total_assets > 0 else 0
                for asset_type, amount in asset_type_allocation.items()
            }

            region_ratios = {
                region: (amount / total_assets * 100) if total_assets > 0 else 0
                for region, amount in region_allocation.items()
            }

            currency_ratios = {
                currency: (amount / total_assets * 100) if total_assets > 0 else 0
                for currency, amount in currency_allocation.items()
            }

            allocation = DatabaseModels.AssetAllocation(
                by_asset_type=asset_type_ratios,
                by_region=region_ratios,
                by_currency=currency_ratios,
                total_assets=int(total_assets),
                updated_at=datetime.now(),
            )

            logger.info(f"✅ 자산 배분 현황 조회 완료 - 총자산: {total_assets:,.0f}원")
            return allocation

        except Exception as e:
            logger.error(f"자산 배분 현황 조회 오류: {e}")
            raise

    async def get_unmatched_products(self) -> List[DatabaseModels.UnmatchedProduct]:
        """symbol_table에 없는 종목 조회"""
        try:
            logger.info("🔍 미매칭 종목 조회 시작")

            unmatched_data = self.portfolio_repository.get_unmatched_products()

            unmatched_products = []
            for item in unmatched_data:
                product = DatabaseModels.UnmatchedProduct(
                    company=item.get("company"),
                    valuation_amount=int(item.get("valuation_amount", 0)),
                    profit_loss=int(item.get("profit_loss", 0)),
                    profit_loss_rate=float(item.get("profit_loss_rate", 0)),
                    account=item.get("account"),
                    updated_at=datetime.now(),
                )
                unmatched_products.append(product)

            logger.info(f"✅ 미매칭 종목 조회 완료 - {len(unmatched_products)}개 종목")
            return unmatched_products

        except Exception as e:
            logger.error(f"미매칭 종목 조회 오류: {e}")
            raise

    async def get_top_holdings(
        self, limit: int = 10
    ) -> List[DatabaseModels.TopHolding]:
        """TOP 보유 종목 조회"""
        try:
            logger.info(f"📊 TOP 보유 종목 조회 - 상위 {limit}개")

            top_holdings_data = self.portfolio_repository.get_top_holdings(limit)

            top_holdings = []
            for item in top_holdings_data:
                holding = DatabaseModels.TopHolding(
                    name=item.get("name"),
                    symbol=item.get("symbol"),
                    valuation_amount=int(item.get("valuation_amount", 0)),
                    profit_loss=int(item.get("profit_loss", 0)),
                    profit_loss_rate=float(item.get("profit_loss_rate", 0)),
                    account=item.get("account"),
                    sector=item.get("sector"),
                    updated_at=datetime.now(),
                )
                top_holdings.append(holding)

            logger.info(f"✅ TOP 보유 종목 조회 완료 - {len(top_holdings)}개 종목")
            return top_holdings

        except Exception as e:
            logger.error(f"TOP 보유 종목 조회 오류: {e}")
            raise

    async def refresh_portfolio_data(self) -> Dict[str, Any]:
        """포트폴리오 데이터 새로고침 (전체 동기화 작업 오케스트레이션)"""
        try:
            logger.info("🔄 포트폴리오 데이터 전체 새로고침 시작")

            # sync_service를 통한 전체 동기화 작업 실행
            sync_results = await self.sync_service.orchestrate_sync_operations()

            logger.info("✅ 포트폴리오 데이터 새로고침 완료")
            return sync_results

        except Exception as e:
            logger.error(f"포트폴리오 데이터 새로고침 오류: {e}")
            raise

    def _create_empty_overview(self) -> DatabaseModels.PortfolioOverview:
        """빈 포트폴리오 개요 생성"""
        return DatabaseModels.PortfolioOverview(
            total_assets=0,
            total_valuation_amount=0,
            total_profit_loss=0,
            total_profit_loss_rate=0.0,
            krw_assets=0,
            usd_assets=0,
            total_equity=0,
            total_bond=0,
            total_reit=0,
            total_commodity=0,
            total_cash=0,
            updated_at=datetime.now(),
        )

    async def add_unmatched_to_symbol_table(
        self, unmatched_response: DatabaseModels.UnmatchedProductsResponse
    ) -> Dict[str, int]:
        """매칭되지 않는 상품들을 symbol_table에 추가"""
        try:
            logger.info(
                f"🔄 미매칭 종목 symbol_table 추가 시작 - {len(unmatched_response.unmatched_products)}개"
            )

            added_count = 0
            failed_count = 0

            for product in unmatched_response.unmatched_products:
                try:
                    # 기본 symbol 생성 (단순화된 버전)
                    symbol = self._generate_symbol_from_name(product.company)

                    # symbol_table에 추가
                    result = self.portfolio_repository.add_to_symbol_table(
                        symbol=symbol,
                        company=product.company,
                        asset_type="equity",
                        region_type="domestic",
                    )

                    if result:
                        added_count += 1
                        logger.debug(f"✅ {product.company} symbol_table 추가 성공")
                    else:
                        failed_count += 1
                        logger.error(f"❌ {product.company} symbol_table 추가 실패")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ {product.company} symbol_table 추가 오류: {e}")

            result = {
                "total_products": len(unmatched_response.unmatched_products),
                "added_count": added_count,
                "failed_count": failed_count,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"🏁 미매칭 종목 symbol_table 추가 완료 - 성공: {added_count}/{len(unmatched_response.unmatched_products)}"
            )
            return result

        except Exception as e:
            logger.error(f"미매칭 종목 symbol_table 추가 전체 오류: {e}")
            raise

    def _generate_symbol_from_name(self, company_name: str) -> str:
        """회사 이름에서 기본 symbol 생성"""
        if not company_name:
            return "UNKNOWN"

        # 간단한 symbol 생성 로직 (실제로는 더 정교한 로직 필요)
        import re

        # 한글 이름은 기본 패턴 사용
        if re.search(r"[가-힣]", company_name):
            return f"KR_{company_name[:8]}"

        # 영문 이름은 정리해서 사용
        clean_name = re.sub(r"[^A-Za-z0-9]", "", company_name)
        symbol = clean_name[:10].upper()

        return symbol if symbol else "UNKNOWN"

    def _get_latest_bs_data(self) -> Optional[Dict[str, Any]]:
        """최신 bs_timeseries 데이터 조회"""
        try:
            return self.portfolio_repository.get_latest_bs_entry()
        except Exception as e:
            logger.error(f"최신 bs_timeseries 조회 오류: {e}")
            return None
