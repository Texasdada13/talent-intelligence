"""
Diversity Analyzer - Talent Intelligence

Diversity metrics, representation analysis, and inclusion insights.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RepresentationStatus(Enum):
    EXCEEDS = "Exceeds Target"
    MEETS = "Meets Target"
    APPROACHING = "Approaching Target"
    BELOW = "Below Target"
    SIGNIFICANTLY_BELOW = "Significantly Below"


@dataclass
class DemographicBreakdown:
    """Breakdown of demographics for a group."""
    total_count: int
    gender: Dict[str, int]
    ethnicity: Dict[str, int]
    age_groups: Dict[str, int]
    tenure_groups: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepresentationMetrics:
    """Representation metrics for a demographic group."""
    group_name: str
    current_percentage: float
    target_percentage: float
    gap: float
    status: RepresentationStatus
    trend: str  # Improving, Stable, Declining
    year_over_year_change: float
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_name": self.group_name,
            "current_percentage": round(self.current_percentage, 1),
            "target_percentage": self.target_percentage,
            "gap": round(self.gap, 1),
            "status": self.status.value,
            "trend": self.trend,
            "year_over_year_change": round(self.year_over_year_change, 1)
        }


@dataclass
class PayEquityAnalysis:
    """Pay equity analysis results."""
    group_comparison: str
    avg_pay_gap: float
    gap_percentage: float
    statistical_significance: bool
    affected_employees: int
    remediation_cost: float
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_comparison": self.group_comparison,
            "avg_pay_gap": round(self.avg_pay_gap, 2),
            "gap_percentage": round(self.gap_percentage, 1),
            "statistical_significance": self.statistical_significance,
            "affected_employees": self.affected_employees,
            "remediation_cost": round(self.remediation_cost, 2)
        }


@dataclass
class DiversityReport:
    """Complete diversity analysis report."""
    report_id: str
    organization_id: str
    overall_diversity_score: float
    representation_metrics: List[RepresentationMetrics]
    leadership_diversity: Dict[str, float]
    pay_equity: List[PayEquityAnalysis]
    hiring_diversity: Dict[str, float]
    promotion_equity: Dict[str, float]
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "overall_diversity_score": round(self.overall_diversity_score, 1),
            "representation_metrics": [m.to_dict() for m in self.representation_metrics],
            "leadership_diversity": {k: round(v, 1) for k, v in self.leadership_diversity.items()},
            "pay_equity": [p.to_dict() for p in self.pay_equity],
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "recommendations": self.recommendations
        }


class DiversityAnalyzer:
    """Analyzes workforce diversity and inclusion metrics."""

    DEFAULT_TARGETS = {
        "women": 50.0,
        "underrepresented_minorities": 30.0,
        "veterans": 5.0,
        "disabilities": 7.0,
        "lgbtq": 5.0
    }

    LEADERSHIP_TARGETS = {
        "women_in_leadership": 40.0,
        "minorities_in_leadership": 25.0
    }

    def __init__(self, custom_targets: Optional[Dict[str, float]] = None):
        self.targets = {**self.DEFAULT_TARGETS, **(custom_targets or {})}

    def analyze_representation(
        self,
        group_name: str,
        current_count: int,
        total_count: int,
        target_percentage: Optional[float] = None,
        previous_percentage: Optional[float] = None
    ) -> RepresentationMetrics:
        """Analyze representation for a demographic group."""
        if total_count == 0:
            return RepresentationMetrics(
                group_name=group_name,
                current_percentage=0,
                target_percentage=target_percentage or self.targets.get(group_name.lower(), 30),
                gap=0,
                status=RepresentationStatus.SIGNIFICANTLY_BELOW,
                trend="Unknown",
                year_over_year_change=0,
                recommendations=["Insufficient data for analysis"]
            )

        current_pct = (current_count / total_count) * 100
        target = target_percentage or self.targets.get(group_name.lower(), 30)
        gap = current_pct - target

        # Determine status
        if gap >= 5:
            status = RepresentationStatus.EXCEEDS
        elif gap >= 0:
            status = RepresentationStatus.MEETS
        elif gap >= -5:
            status = RepresentationStatus.APPROACHING
        elif gap >= -15:
            status = RepresentationStatus.BELOW
        else:
            status = RepresentationStatus.SIGNIFICANTLY_BELOW

        # Determine trend
        yoy_change = 0
        if previous_percentage is not None:
            yoy_change = current_pct - previous_percentage
            if yoy_change > 1:
                trend = "Improving"
            elif yoy_change < -1:
                trend = "Declining"
            else:
                trend = "Stable"
        else:
            trend = "Unknown"

        # Recommendations
        recommendations = self._get_representation_recommendations(group_name, status, gap)

        return RepresentationMetrics(
            group_name=group_name,
            current_percentage=current_pct,
            target_percentage=target,
            gap=gap,
            status=status,
            trend=trend,
            year_over_year_change=yoy_change,
            recommendations=recommendations
        )

    def analyze_pay_equity(
        self,
        group_a_name: str,
        group_b_name: str,
        group_a_avg_pay: float,
        group_b_avg_pay: float,
        group_b_count: int,
        significance_threshold: float = 0.03
    ) -> PayEquityAnalysis:
        """Analyze pay equity between two groups."""
        if group_a_avg_pay == 0:
            return PayEquityAnalysis(
                group_comparison=f"{group_b_name} vs {group_a_name}",
                avg_pay_gap=0,
                gap_percentage=0,
                statistical_significance=False,
                affected_employees=0,
                remediation_cost=0,
                recommendations=["Insufficient data"]
            )

        gap = group_a_avg_pay - group_b_avg_pay
        gap_pct = (gap / group_a_avg_pay) * 100
        significant = abs(gap_pct / 100) > significance_threshold

        # Estimate remediation
        if gap > 0 and significant:
            remediation = gap * group_b_count
            affected = int(group_b_count * 0.3)  # Estimate 30% affected
        else:
            remediation = 0
            affected = 0

        recommendations = []
        if significant and gap > 0:
            recommendations.append(f"Conduct detailed pay equity analysis for {group_b_name}")
            recommendations.append("Review compensation policies and practices")
            recommendations.append("Consider pay adjustments for affected employees")
        else:
            recommendations.append("Continue monitoring pay equity metrics")

        return PayEquityAnalysis(
            group_comparison=f"{group_b_name} vs {group_a_name}",
            avg_pay_gap=gap,
            gap_percentage=gap_pct,
            statistical_significance=significant,
            affected_employees=affected,
            remediation_cost=remediation,
            recommendations=recommendations
        )

    def create_diversity_report(
        self,
        report_id: str,
        organization_id: str,
        demographics: DemographicBreakdown,
        leadership_demographics: Optional[DemographicBreakdown] = None,
        hiring_demographics: Optional[Dict[str, float]] = None,
        pay_data: Optional[Dict[str, Dict[str, float]]] = None
    ) -> DiversityReport:
        """Create comprehensive diversity report."""
        total = demographics.total_count

        # Analyze representation
        representation_metrics = []

        # Gender representation
        women_count = demographics.gender.get("Female", 0) + demographics.gender.get("Woman", 0)
        representation_metrics.append(
            self.analyze_representation("Women", women_count, total, self.targets.get("women"))
        )

        # Ethnic representation
        minority_count = sum(
            count for ethnicity, count in demographics.ethnicity.items()
            if ethnicity.lower() not in ["white", "caucasian"]
        )
        representation_metrics.append(
            self.analyze_representation("Underrepresented Minorities", minority_count, total)
        )

        # Leadership diversity
        leadership_diversity = {}
        if leadership_demographics:
            leader_total = leadership_demographics.total_count
            women_leaders = leadership_demographics.gender.get("Female", 0)
            leadership_diversity["women_in_leadership"] = (women_leaders / leader_total * 100) if leader_total > 0 else 0

            minority_leaders = sum(
                count for ethnicity, count in leadership_demographics.ethnicity.items()
                if ethnicity.lower() not in ["white", "caucasian"]
            )
            leadership_diversity["minorities_in_leadership"] = (minority_leaders / leader_total * 100) if leader_total > 0 else 0

        # Pay equity analysis
        pay_equity = []
        if pay_data:
            male_pay = pay_data.get("male", {}).get("avg", 0)
            female_pay = pay_data.get("female", {}).get("avg", 0)
            female_count = demographics.gender.get("Female", 0)

            if male_pay > 0 and female_pay > 0:
                pay_equity.append(self.analyze_pay_equity(
                    "Men", "Women", male_pay, female_pay, female_count
                ))

        # Calculate overall score
        overall_score = self._calculate_diversity_score(representation_metrics, leadership_diversity)

        # Identify strengths and areas for improvement
        strengths = [m.group_name for m in representation_metrics if m.status in [RepresentationStatus.EXCEEDS, RepresentationStatus.MEETS]]
        improvement_areas = [m.group_name for m in representation_metrics if m.status in [RepresentationStatus.BELOW, RepresentationStatus.SIGNIFICANTLY_BELOW]]

        # Generate recommendations
        recommendations = self._generate_diversity_recommendations(
            representation_metrics, leadership_diversity, pay_equity
        )

        return DiversityReport(
            report_id=report_id,
            organization_id=organization_id,
            overall_diversity_score=overall_score,
            representation_metrics=representation_metrics,
            leadership_diversity=leadership_diversity,
            pay_equity=pay_equity,
            hiring_diversity=hiring_demographics or {},
            promotion_equity={},
            strengths=strengths,
            improvement_areas=improvement_areas,
            recommendations=recommendations
        )

    def _calculate_diversity_score(
        self,
        metrics: List[RepresentationMetrics],
        leadership: Dict[str, float]
    ) -> float:
        """Calculate overall diversity score."""
        if not metrics:
            return 0

        # Score based on representation status
        status_scores = {
            RepresentationStatus.EXCEEDS: 100,
            RepresentationStatus.MEETS: 85,
            RepresentationStatus.APPROACHING: 70,
            RepresentationStatus.BELOW: 50,
            RepresentationStatus.SIGNIFICANTLY_BELOW: 25
        }

        rep_score = sum(status_scores[m.status] for m in metrics) / len(metrics)

        # Adjust for leadership diversity
        if leadership:
            leadership_score = sum(min(100, v / t * 100) for v, t in zip(
                leadership.values(),
                [self.LEADERSHIP_TARGETS.get(k, 30) for k in leadership.keys()]
            )) / len(leadership)
            return rep_score * 0.7 + leadership_score * 0.3

        return rep_score

    def _get_representation_recommendations(
        self,
        group: str,
        status: RepresentationStatus,
        gap: float
    ) -> List[str]:
        """Get recommendations for representation improvement."""
        if status in [RepresentationStatus.EXCEEDS, RepresentationStatus.MEETS]:
            return [f"Maintain current {group} representation", "Share best practices"]

        recommendations = []
        if status == RepresentationStatus.SIGNIFICANTLY_BELOW:
            recommendations.append(f"Develop targeted {group} recruitment strategy")
            recommendations.append(f"Partner with {group}-focused organizations")

        recommendations.append(f"Review hiring funnel for {group} candidates")
        recommendations.append(f"Establish {group} employee resource group")

        return recommendations[:3]

    def _generate_diversity_recommendations(
        self,
        metrics: List[RepresentationMetrics],
        leadership: Dict[str, float],
        pay_equity: List[PayEquityAnalysis]
    ) -> List[str]:
        """Generate overall diversity recommendations."""
        recommendations = []

        # Check for low representation
        low_rep = [m for m in metrics if m.status in [RepresentationStatus.BELOW, RepresentationStatus.SIGNIFICANTLY_BELOW]]
        if low_rep:
            recommendations.append(f"Focus on improving representation: {', '.join(m.group_name for m in low_rep[:2])}")

        # Check leadership diversity
        for metric, target in self.LEADERSHIP_TARGETS.items():
            actual = leadership.get(metric, 0)
            if actual < target * 0.7:
                recommendations.append(f"Develop pipeline for {metric.replace('_', ' ')}")

        # Check pay equity
        significant_gaps = [p for p in pay_equity if p.statistical_significance and p.gap_percentage > 3]
        if significant_gaps:
            recommendations.append("Address pay equity gaps identified in analysis")

        recommendations.append("Implement inclusive hiring practices")
        recommendations.append("Conduct regular diversity training")

        return recommendations[:5]
