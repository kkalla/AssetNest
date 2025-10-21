"""
포트폴리오 서비스
"""
from typing import Dict, Any, Optional, List
import logging

from dashboard.api import portfolio_api
from dashboard.models import PortfolioOverview, AssetAllocation, DataValidator, DataFrameConverter
from dashboard.utils import cache_with_ttl

logger = logging.getLogger(__name__)


class PortfolioService:
    """포트폴리오 비즈니스 로직 서비스"""

    def __init__(self):
        self.cache_ttl = 300  # 5분

    @cache_with_ttl(ttl_seconds=300)
    def get_portfolio_overview(self, account: Optional[str] = None) -> Optional[PortfolioOverview]:
        """
        포트폴리오 개요 정보 조회

        Args:
            account (Optional[str]): 계좌 필터

        Returns:
            Optional[PortfolioOverview]: 포트폴리오 개요 모델
        """
        try:
            logger.info(f"📊 포트폴리오 개요 서비스 호출 - 계정: {account or '전체'}")

            data = portfolio_api.get_overview(account)

            if data and DataValidator.validate_portfolio_data(data):
                overview = PortfolioOverview.from_dict(data)
                logger.info(f"✅ 포트폴리오 개요 조회 성공 - 총 자산: {overview.total_value_krw:,.0f}원")
                return overview
            else:
                logger.warning("⚠️ 포트폴리오 개요 데이터 검증 실패")
                return None

        except Exception as e:
            logger.error(f"💥 포트폴리오 개요 서비스 오류: {str(e)}")
            return None

    @cache_with_ttl(ttl_seconds=300)
    def get_portfolio_summary(self, account: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        포트폴리오 요약 정보 조회

        Args:
            account (Optional[str]): 계좌 필터

        Returns:
            Optional[List[Dict[str, Any]]]: 포트폴리오 요약 리스트
        """
        try:
            logger.info(f"📋 포트폴리오 요약 서비스 호출 - 계정: {account or '전체'}")

            summaries = portfolio_api.get_summary(account)

            if summaries:
                logger.info(f"✅ 포트폴리오 요약 조회 성공 - {len(summaries)}개 계좌")
            return summaries

        except Exception as e:
            logger.error(f"💥 포트폴리오 요약 서비스 오류: {str(e)}")
            return []

    @cache_with_ttl(ttl_seconds=300)
    def get_asset_allocation(self, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        자산 분배 정보 조회

        Args:
            account (Optional[str]): 계좌 필터

        Returns:
            Optional[Dict[str, Any]]: 자산 분배 데이터
        """
        try:
            logger.info(f"🥧 자산 분배 서비스 호출 - 계정: {account or '전체'}")

            data = portfolio_api.get_allocation(account)

            if data:
                logger.info("✅ 자산 분배 조회 성공")
            return data

        except Exception as e:
            logger.error(f"💥 자산 분배 서비스 오류: {str(e)}")
            return None

    def calculate_portfolio_metrics(self, overview: PortfolioOverview) -> Dict[str, Any]:
        """
        포트폴리오 지표 계산

        Args:
            overview (PortfolioOverview): 포트폴리오 개요 모델

        Returns:
            Dict[str, Any]: 계산된 지표들
        """
        try:
            metrics = {
                "total_assets_krw": overview.total_value_krw,
                "total_assets_usd": overview.total_value_usd,
                "total_pnl_krw": overview.total_pnl_krw,
                "total_pnl_usd": overview.total_pnl_usd,
                "total_return_rate": overview.total_return_rate,
                "cash_ratio": overview.cash_asset_ratio,
                "investment_ratio": overview.investment_asset_ratio,
                "cash_amount": overview.cash_asset_value,
                "investment_amount": overview.investment_asset_value,
                "updated_at": overview.updated_at
            }

            # 추가 지표 계산
            if overview.total_value_krw > 0:
                metrics["pnl_ratio"] = (overview.total_pnl_krw / overview.total_value_krw) * 100
            else:
                metrics["pnl_ratio"] = 0

            # 투자자산 내부 분배 분석
            if overview.investment_allocations:
                total_investment = sum(alloc.get("total_market_value", 0) for alloc in overview.investment_allocations)
                if total_investment > 0:
                    metrics["investment_details"] = []
                    for alloc in overview.investment_allocations:
                        weight = (alloc.get("total_market_value", 0) / total_investment) * 100
                        metrics["investment_details"].append({
                            "asset_category": alloc.get("asset_category", ""),
                            "weight": weight,
                            "market_value": alloc.get("total_market_value", 0),
                            "count": alloc.get("holdings_count", 0)
                        })

            logger.debug("✅ 포트폴리오 지표 계산 완료")
            return metrics

        except Exception as e:
            logger.error(f"💥 포트폴리오 지표 계산 오류: {str(e)}")
            return {}

    def analyze_portfolio_health(self, overview: PortfolioOverview) -> Dict[str, Any]:
        """
        포트폴리오 건강성 분석

        Args:
            overview (PortfolioOverview): 포트폴리오 개요 모델

        Returns:
            Dict[str, Any]: 건강성 분석 결과
        """
        try:
            health_score = 0
            recommendations = []

            # 현금 비율 분석
            cash_ratio = overview.cash_asset_ratio
            if 5 <= cash_ratio <= 20:  # 건강한 현금 비율
                health_score += 20
            elif cash_ratio < 5:
                recommendations.append("현금 비율이 너무 낮습니다. 비상 자금을 확보하세요.")
            elif cash_ratio > 20:
                recommendations.append("현금 비율이 너무 높습니다. 투자 비중을 늘려보세요.")

            # 수익률 분석
            return_rate = overview.total_return_rate
            if return_rate >= 0:
                health_score += 20
            else:
                recommendations.append("현재 손실 상태입니다. 포트폴리오 재검토가 필요합니다.")

            # 분산도 분석
            if overview.investment_allocations:
                unique_assets = len(overview.investment_allocations)
                if unique_assets >= 5:  # 다각화 잘됨
                    health_score += 20
                elif unique_assets < 3:
                    recommendations.append("자산 분산도가 낮습니다. 더 다양한 자산에 투자하세요.")

                # 특정 자산 비중 과다 여부 체크
                for alloc in overview.investment_allocations:
                    if alloc.get("allocation_percentage", 0) > 40:
                        recommendations.append(f"{alloc.get('asset_category', '')} 비중이 너무 높습니다. 분산을 고려하세요.")

            # 총자산 규모 분석
            if overview.total_value_krw >= 10000000:  # 1000만원 이상
                health_score += 20
            elif overview.total_value_krw < 1000000:  # 100만원 미만
                recommendations.append("총자산 규모가 작습니다. 꾸준적인 저축을 권장합니다.")

            # 데이터 최신성 분석
            from datetime import datetime, timedelta
            if (datetime.now() - overview.updated_at).days <= 1:
                health_score += 20
            else:
                recommendations.append("포트폴리오 데이터가 오래되었습니다. 새로고침이 필요합니다.")

            # 건강 등급 결정
            if health_score >= 80:
                health_grade = "매우 좋음"
                health_color = "🟢"
            elif health_score >= 60:
                health_grade = "좋음"
                health_color = "🟡"
            elif health_score >= 40:
                health_grade = "보통"
                health_color = "🟠"
            else:
                health_grade = "개선 필요"
                health_color = "🔴"

            analysis_result = {
                "health_score": health_score,
                "health_grade": health_grade,
                "health_color": health_color,
                "recommendations": recommendations,
                "analysis_summary": f"건강 점수: {health_score}/100 ({health_grade})"
            }

            logger.info(f"✅ 포트폴리오 건강성 분석 완료 - 점수: {health_score}")
            return analysis_result

        except Exception as e:
            logger.error(f"💥 포트폴리오 건강성 분석 오류: {str(e)}")
            return {
                "health_score": 0,
                "health_grade": "분석 불가",
                "health_color": "❌",
                "recommendations": ["데이터 분석 중 오류가 발생했습니다."],
                "analysis_summary": "분석 실패"
            }

    def generate_portfolio_report(self, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        포트폴리오 리포트 생성

        Args:
            account (Optional[str]): 계좌 필터

        Returns:
            Optional[Dict[str, Any]]: 포트폴리오 리포트
        """
        try:
            logger.info(f"📄 포트폴리오 리포트 생성 시작 - 계정: {account or '전체'}")

            # 기본 데이터 조회
            overview = self.get_portfolio_overview(account)
            if not overview:
                logger.error("❌ 포트폴리오 개요 데이터 없음 - 리포트 생성 중단")
                return None

            allocation = self.get_asset_allocation(account)
            summary = self.get_portfolio_summary(account)

            # 지표 계산
            metrics = self.calculate_portfolio_metrics(overview)
            health_analysis = self.analyze_portfolio_health(overview)

            # 리포트 생성
            report = {
                "generated_at": overview.updated_at.isoformat(),
                "account": account or "전체",
                "overview": {
                    "total_assets_krw": overview.total_value_krw,
                    "total_pnl_krw": overview.total_pnl_krw,
                    "total_return_rate": overview.total_return_rate,
                    "cash_ratio": overview.cash_asset_ratio,
                    "investment_ratio": overview.investment_asset_ratio
                },
                "metrics": metrics,
                "health_analysis": health_analysis,
                "allocation": allocation,
                "summary": summary
            }

            logger.info("✅ 포트폴리오 리포트 생성 완료")
            return report

        except Exception as e:
            logger.error(f"💥 포트폴리오 리포트 생성 오류: {str(e)}")
            return None