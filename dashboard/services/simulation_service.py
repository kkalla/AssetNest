"""
시뮬레이션 서비스
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from dashboard.models import AssetAllocation
from dashboard.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """시뮬레이션 결과 모델"""
    simulation_type: str
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    adjustments: Dict[str, float]
    total_value: float
    adjustment_amount: float
    is_valid: bool
    recommendations: List[str]


class SimulationService:
    """자산 분배 시뮬레이션 서비스"""

    def __init__(self):
        pass

    def simulate_cash_vs_investment(
        self,
        current_cash: float,
        current_investment: float,
        target_cash_ratio: float
    ) -> SimulationResult:
        """
        현금 vs 투자자산 시뮬레이션

        Args:
            current_cash (float): 현재 현금
            current_investment (float): 현재 투자자산
            target_cash_ratio (float): 목표 현금 비율

        Returns:
            SimulationResult: 시뮬레이션 결과
        """
        try:
            total_assets = current_cash + current_investment

            if total_assets <= 0:
                return SimulationResult(
                    simulation_type="cash_vs_investment",
                    current_allocation={"현금": 0, "투자": 0},
                    target_allocation={"현금": 0, "투자": 0},
                    adjustments={"현금": 0, "투자": 0},
                    total_value=0,
                    adjustment_amount=0,
                    is_valid=False,
                    recommendations=["자산 데이터가 없습니다."]
                )

            current_cash_ratio = (current_cash / total_assets) * 100
            current_investment_ratio = (current_investment / total_assets) * 100
            target_investment_ratio = 100 - target_cash_ratio

            # 목표 금액 계산
            target_cash = total_assets * (target_cash_ratio / 100)
            target_investment = total_assets * (target_investment_ratio / 100)

            # 조정 금액 계산
            cash_adjustment = target_cash - current_cash
            investment_adjustment = target_investment - current_investment

            # 추천사항 생성
            recommendations = []

            if abs(cash_adjustment) < 1000:  # 1만원 미만
                recommendations.append("✅ 현재 비율이 목표 비율과 유사합니다. 조정이 필요하지 않습니다.")
            else:
                if cash_adjustment > 0:
                    recommendations.append(
                        f"📉 **투자자산 매도**: {self._format_currency(abs(cash_adjustment))} 상당의 주식/펀드를 매도하여 현금 비중을 높이세요."
                    )
                else:
                    recommendations.append(
                        f"📈 **투자자산 매수**: {self._format_currency(abs(investment_adjustment))} 상당의 주식/펀드를 매수하여 투자 비중을 높이세요."
                    )

            # 비율 건강성 체크
            if target_cash_ratio < 5:
                recommendations.append("⚠️ 목표 현금 비율이 너무 낮습니다. 비상 자금을 고려해보세요.")
            elif target_cash_ratio > 30:
                recommendations.append("⚠️ 목표 현금 비율이 너무 높습니다. 투자 기회를 놓치고 있을 수 있습니다.")

            result = SimulationResult(
                simulation_type="cash_vs_investment",
                current_allocation={
                    "현금": current_cash_ratio,
                    "투자": current_investment_ratio
                },
                target_allocation={
                    "현금": target_cash_ratio,
                    "투자": target_investment_ratio
                },
                adjustments={
                    "현금": cash_adjustment,
                    "투자": investment_adjustment
                },
                total_value=total_assets,
                adjustment_amount=abs(cash_adjustment) + abs(investment_adjustment),
                is_valid=True,
                recommendations=recommendations
            )

            logger.info(f"✅ 현금 vs 투자 시뮬레이션 완료 - 조정 필요: {result.adjustment_amount:,.0f}원")
            return result

        except Exception as e:
            logger.error(f"💥 현금 vs 투자 시뮬레이션 오류: {str(e)}")
            return SimulationResult(
                simulation_type="cash_vs_investment",
                current_allocation={},
                target_allocation={},
                adjustments={},
                total_value=0,
                adjustment_amount=0,
                is_valid=False,
                recommendations=["시뮬레이션 중 오류가 발생했습니다."]
            )

    def simulate_investment_allocation(
        self,
        current_investment: float,
        current_allocations: List[AssetAllocation],
        target_ratios: Dict[str, float]
    ) -> SimulationResult:
        """
        투자자산 분배 시뮬레이션

        Args:
            current_investment (float): 현재 투자자산 총액
            current_allocations (List[AssetAllocation]): 현재 자산 분배
            target_ratios (Dict[str, float]): 목표 비율

        Returns:
            SimulationResult: 시뮬레이션 결과
        """
        try:
            if not current_allocations or current_investment <= 0:
                return SimulationResult(
                    simulation_type="investment_allocation",
                    current_allocation={},
                    target_allocation={},
                    adjustments={},
                    total_value=0,
                    adjustment_amount=0,
                    is_valid=False,
                    recommendations=["투자자산 데이터가 없습니다."]
                )

            # 현재 분배 정보 준비
            current_allocation_ratios = {}
            adjustments = {}
            recommendations = []

            for alloc in current_allocations:
                asset_category = alloc.asset_category
                current_ratio = alloc.allocation_percentage
                current_value = alloc.total_market_value

                current_allocation_ratios[asset_category] = current_ratio

                # 목표 비율과 비교
                target_ratio = target_ratios.get(asset_category, 0)
                target_value = current_investment * (target_ratio / 100)
                adjustment = target_value - current_value

                adjustments[asset_category] = adjustment

            # 추천사항 생성
            total_adjustment = sum(abs(adj) for adj in adjustments.values())
            if total_adjustment < 10000:  # 10만원 미만
                recommendations.append("✅ 현재 분배가 목표와 유사합니다. 큰 조정이 필요하지 않습니다.")
            else:
                significant_adjustments = [(asset, adj) for asset, adj in adjustments.items() if abs(adj) >= 100000]
                if significant_adjustments:
                    for asset, adj in sorted(significant_adjustments, key=lambda x: abs(x[1]), reverse=True)[:3]:
                        if adj > 0:
                            recommendations.append(
                                f"📈 **{asset} 증가**: {self._format_currency(adj)} 추가 매수 필요"
                            )
                        else:
                            recommendations.append(
                                f"📉 **{asset} 감소**: {self._format_currency(abs(adj)) 매도 필요"
                            )

            # 목표 비율 합계 검증
            target_total = sum(target_ratios.values())
            if abs(target_total - 100) > 0.1:
                recommendations.append(f"⚠️ 목표 비율 합계가 {target_total:.1f}%입니다. 100%가 되도록 조정해주세요.")

            result = SimulationResult(
                simulation_type="investment_allocation",
                current_allocation=current_allocation_ratios,
                target_allocation=target_ratios,
                adjustments=adjustments,
                total_value=current_investment,
                adjustment_amount=total_adjustment,
                is_valid=abs(target_total - 100) < 0.1,
                recommendations=recommendations
            )

            logger.info(f"✅ 투자자산 분배 시뮬레이션 완료 - 총 조정액: {total_adjustment:,.0f}원")
            return result

        except Exception as e:
            logger.error(f"💥 투자자산 분배 시뮬레이션 오류: {str(e)}")
            return SimulationResult(
                simulation_type="investment_allocation",
                current_allocation={},
                target_allocation={},
                adjustments={},
                total_value=0,
                adjustment_amount=0,
                is_valid=False,
                recommendations=["시뮬레이션 중 오류가 발생했습니다."]
            )

    def generate_optimal_allocation(
        self,
        risk_profile: str = "balanced"
    ) -> Dict[str, float]:
        """
        최적 자산 분배 제안 생성

        Args:
            risk_profile (str): 위험 프로필 ("conservative", "balanced", "aggressive")

        Returns:
            Dict[str, float]: 제안된 자산 분배 비율
        """
        try:
            allocation_templates = {
                "conservative": {
                    "현금": 20,
                    "국내채권": 30,
                    "해외채권": 20,
                    "국내주식": 15,
                    "해외주식": 10,
                    "리츠": 5,
                    "TDF": 0,
                    "원자재": 0,
                    "금": 0,
                    "기타": 0
                },
                "balanced": settings.DEFAULT_ASSET_ALLOCATION,
                "aggressive": {
                    "현금": 5,
                    "국내채권": 10,
                    "해외채권": 5,
                    "국내주식": 25,
                    "해외주식": 30,
                    "리츠": 10,
                    "TDF": 5,
                    "원자재": 5,
                    "금": 5,
                    "기타": 0
                }
            }

            allocation = allocation_templates.get(risk_profile, allocation_templates["balanced"])

            logger.info(f"✅ 최적 자산 분배 생성 완료 - 프로필: {risk_profile}")
            return allocation

        except Exception as e:
            logger.error(f"💥 최적 자산 분배 생성 오류: {str(e)}")
            return settings.DEFAULT_ASSET_ALLOCATION

    def calculate_rebalancing_impact(
        self,
        current_allocations: List[AssetAllocation],
        target_allocation: Dict[str, float],
        total_value: float
    ) -> Dict[str, Any]:
        """
        리밸런싱 영향 분석

        Args:
            current_allocations (List[AssetAllocation]): 현재 분배
            target_allocation (Dict[str, float]): 목표 분배
            total_value (float): 총 자산

        Returns:
            Dict[str, Any]: 리밸런싱 영향 분석 결과
        """
        try:
            # 현재 분배 맵 생성
            current_map = {alloc.asset_category: alloc for alloc in current_allocations}

            # 리밸런싱 필요 자산 계산
            rebalancing_needed = []
            total_trading_value = 0

            for asset_type, target_ratio in target_allocation.items():
                current_value = current_map.get(asset_type, AssetAllocation(
                    asset_category=asset_type,
                    holdings_count=0,
                    total_market_value=0,
                    allocation_percentage=0
                )).total_market_value

                target_value = total_value * (target_ratio / 100)
                difference = target_value - current_value

                if abs(difference) > 50000:  # 50만원 이상 차이
                    rebalancing_needed.append({
                        "asset_type": asset_type,
                        "current_value": current_value,
                        "target_value": target_value,
                        "difference": difference,
                        "action": "매수" if difference > 0 else "매도"
                    })
                    total_trading_value += abs(difference)

            # 리밸런싱 비용 추정 (거래 수수료 등)
            estimated_trading_cost = total_trading_value * 0.001  # 0.1% 가정

            # 리밸런싱 후 예상 수익률 변화
            current_weighted_return = sum(
                alloc.allocation_percentage * 0.05  # 가정된 수익률
                for alloc in current_allocations
            ) / 100 if current_allocations else 0

            # 리밸런싱 효과성 평가
            if total_trading_value < total_value * 0.1:  # 총자산의 10% 미만
                efficiency_score = "높음"
                recommendation = "리밸런싱을 권장합니다."
            elif total_trading_value < total_value * 0.2:  # 총자산의 20% 미만
                efficiency_score = "보통"
                recommendation = "리밸런싱을 고려해볼 만합니다."
            else:
                efficiency_score = "낮음"
                recommendation = "리밸런싱 비용이 높습니다. 점진적 조정을 권장합니다."

            analysis_result = {
                "rebalancing_needed": rebalancing_needed,
                "total_trading_value": total_trading_value,
                "estimated_trading_cost": estimated_trading_cost,
                "current_weighted_return": current_weighted_return,
                "efficiency_score": efficiency_score,
                "recommendation": recommendation,
                "assets_to_rebalance": len(rebalancing_needed)
            }

            logger.info(f"✅ 리밸런싱 영향 분석 완료 - 필요 자산: {len(rebalancing_needed)}개")
            return analysis_result

        except Exception as e:
            logger.error(f"💥 리밸런싱 영향 분석 오류: {str(e)}")
            return {
                "rebalancing_needed": [],
                "total_trading_value": 0,
                "estimated_trading_cost": 0,
                "current_weighted_return": 0,
                "efficiency_score": "분석 불가",
                "recommendation": "분석 중 오류 발생",
                "assets_to_rebalance": 0
            }

    def _format_currency(self, amount: float) -> str:
        """통화 포맷팅"""
        return f"₩{amount:,.0f}"