"""
HR Benchmark Engine - Talent Intelligence

KPI benchmarking for HR metrics against industry standards.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KPIDirection(Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class KPICategory(Enum):
    RETENTION = "Retention"
    RECRUITMENT = "Recruitment"
    ENGAGEMENT = "Engagement"
    PERFORMANCE = "Performance"
    COMPENSATION = "Compensation"
    DEVELOPMENT = "Development"
    DIVERSITY = "Diversity"
    PRODUCTIVITY = "Productivity"
    CUSTOM = "Custom"


@dataclass
class KPIDefinition:
    kpi_id: str
    name: str
    benchmark_value: float
    direction: KPIDirection = KPIDirection.HIGHER_IS_BETTER
    category: KPICategory = KPICategory.CUSTOM
    unit: str = ""
    description: str = ""
    weight: float = 1.0


@dataclass
class KPIScore:
    kpi_id: str
    kpi_name: str
    actual_value: float
    benchmark_value: float
    score: float
    gap: float
    gap_percent: float
    direction: KPIDirection
    rating: str
    unit: str = ""
    recommendation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "kpi_name": self.kpi_name,
            "actual_value": self.actual_value,
            "benchmark_value": self.benchmark_value,
            "score": self.score,
            "gap": self.gap,
            "gap_percent": self.gap_percent,
            "rating": self.rating,
            "recommendation": self.recommendation
        }


@dataclass
class CategoryScore:
    category: str
    score: float
    kpi_count: int
    kpi_scores: List[KPIScore]
    strengths: List[str]
    improvements: List[str]


@dataclass
class BenchmarkReport:
    entity_id: str
    overall_score: float
    overall_rating: str
    grade: str
    category_scores: Dict[str, CategoryScore]
    kpi_scores: List[KPIScore]
    top_strengths: List[str]
    top_improvements: List[str]
    recommendations: List[str]
    percentile: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "overall_score": self.overall_score,
            "overall_rating": self.overall_rating,
            "grade": self.grade,
            "category_scores": {
                cat: {"score": cs.score, "kpi_count": cs.kpi_count}
                for cat, cs in self.category_scores.items()
            },
            "kpi_count": len(self.kpi_scores),
            "top_strengths": self.top_strengths,
            "top_improvements": self.top_improvements,
            "recommendations": self.recommendations
        }


class BenchmarkEngine:
    """HR KPI benchmarking engine."""

    RATING_THRESHOLDS = {90: "Excellent", 75: "Good", 60: "Fair", 40: "Poor", 0: "Critical"}
    GRADE_THRESHOLDS = {90: "A", 80: "B", 70: "C", 60: "D", 0: "F"}

    def __init__(
        self,
        kpis: List[KPIDefinition],
        category_weights: Optional[Dict[str, float]] = None
    ):
        self.kpis = {kpi.kpi_id: kpi for kpi in kpis}
        self.category_weights = category_weights or {}

        self.kpis_by_category: Dict[str, List[KPIDefinition]] = {}
        for kpi in kpis:
            cat = kpi.category.value
            if cat not in self.kpis_by_category:
                self.kpis_by_category[cat] = []
            self.kpis_by_category[cat].append(kpi)

    def score_kpi(self, kpi: KPIDefinition, actual_value: float) -> KPIScore:
        benchmark = kpi.benchmark_value
        gap = actual_value - benchmark

        if benchmark != 0:
            gap_percent = (gap / abs(benchmark)) * 100
        else:
            gap_percent = 100 if actual_value > 0 else 0

        score = self._calculate_score(actual_value, benchmark, kpi.direction)
        rating = self._determine_rating(score)
        recommendation = self._generate_recommendation(kpi, actual_value, benchmark, rating)

        return KPIScore(
            kpi_id=kpi.kpi_id,
            kpi_name=kpi.name,
            actual_value=round(actual_value, 2),
            benchmark_value=benchmark,
            score=round(score, 1),
            gap=round(gap, 2),
            gap_percent=round(gap_percent, 1),
            direction=kpi.direction,
            rating=rating,
            unit=kpi.unit,
            recommendation=recommendation,
            metadata={"category": kpi.category.value, "weight": kpi.weight}
        )

    def _calculate_score(self, actual: float, benchmark: float, direction: KPIDirection) -> float:
        if benchmark == 0:
            return 100 if actual >= 0 else 0

        if direction == KPIDirection.HIGHER_IS_BETTER:
            if actual >= benchmark:
                bonus = min(20, ((actual - benchmark) / benchmark) * 20)
                return min(120, 100 + bonus)
            else:
                return max(0, (actual / benchmark) * 100)
        else:
            if actual <= benchmark:
                if actual == 0:
                    return 120
                bonus = min(20, ((benchmark - actual) / benchmark) * 20)
                return min(120, 100 + bonus)
            else:
                excess_ratio = actual / benchmark
                return max(0, 100 - ((excess_ratio - 1) * 100))

    def _determine_rating(self, score: float) -> str:
        for threshold, rating in sorted(self.RATING_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return rating
        return "Critical"

    def _determine_grade(self, score: float) -> str:
        for threshold, grade in sorted(self.GRADE_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return grade
        return "F"

    def _generate_recommendation(self, kpi: KPIDefinition, actual: float, benchmark: float, rating: str) -> str:
        if rating in ["Excellent", "Good"]:
            return f"Maintain strong performance in {kpi.name}"

        direction_text = "increase" if kpi.direction == KPIDirection.HIGHER_IS_BETTER else "reduce"
        gap = abs(actual - benchmark)

        if rating == "Fair":
            return f"Minor improvement needed: {direction_text} {kpi.name} by {gap:.1f}{kpi.unit}"
        elif rating == "Poor":
            return f"Priority action: {direction_text} {kpi.name} significantly"
        else:
            return f"CRITICAL: Immediate intervention required for {kpi.name}"

    def analyze(
        self,
        actual_values: Dict[str, float],
        entity_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> BenchmarkReport:
        kpi_scores = []
        category_kpis: Dict[str, List[KPIScore]] = {}

        for kpi_id, kpi in self.kpis.items():
            actual = actual_values.get(kpi_id)
            if actual is None:
                continue

            score = self.score_kpi(kpi, actual)
            kpi_scores.append(score)

            cat = kpi.category.value
            if cat not in category_kpis:
                category_kpis[cat] = []
            category_kpis[cat].append(score)

        category_scores = {}
        for cat, scores in category_kpis.items():
            cat_score = self._calculate_category_score(cat, scores)
            category_scores[cat] = cat_score

        overall_score = self._calculate_overall_score(category_scores)
        overall_rating = self._determine_rating(overall_score)
        grade = self._determine_grade(overall_score)

        sorted_kpis = sorted(kpi_scores, key=lambda k: k.score, reverse=True)
        top_strengths = [f"{k.kpi_name}: {k.actual_value}{k.unit} ({k.rating})" for k in sorted_kpis[:3] if k.rating in ["Excellent", "Good"]]
        top_improvements = [f"{k.kpi_name}: {k.actual_value}{k.unit} vs benchmark {k.benchmark_value}{k.unit}" for k in sorted_kpis[-3:] if k.rating in ["Poor", "Critical"]]
        recommendations = [k.recommendation for k in kpi_scores if k.rating in ["Poor", "Critical"]]

        return BenchmarkReport(
            entity_id=entity_id,
            overall_score=round(overall_score, 1),
            overall_rating=overall_rating,
            grade=grade,
            category_scores=category_scores,
            kpi_scores=kpi_scores,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            recommendations=recommendations[:5],
            metadata=metadata or {}
        )

    def _calculate_category_score(self, category: str, kpi_scores: List[KPIScore]) -> CategoryScore:
        if not kpi_scores:
            return CategoryScore(category=category, score=0, kpi_count=0, kpi_scores=[], strengths=[], improvements=[])

        total_weight = sum(k.metadata.get("weight", 1) for k in kpi_scores)
        weighted_sum = sum(k.score * k.metadata.get("weight", 1) for k in kpi_scores)
        avg_score = weighted_sum / total_weight if total_weight > 0 else 0

        strengths = [k.kpi_name for k in kpi_scores if k.rating in ["Excellent", "Good"]]
        improvements = [k.kpi_name for k in kpi_scores if k.rating in ["Poor", "Critical"]]

        return CategoryScore(
            category=category,
            score=round(avg_score, 1),
            kpi_count=len(kpi_scores),
            kpi_scores=kpi_scores,
            strengths=strengths,
            improvements=improvements
        )

    def _calculate_overall_score(self, category_scores: Dict[str, CategoryScore]) -> float:
        if not category_scores:
            return 0

        total_weight = 0
        weighted_sum = 0

        for cat, cat_score in category_scores.items():
            weight = self.category_weights.get(cat, 1.0)
            weighted_sum += cat_score.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0


# Factory Functions

def create_hr_benchmarks() -> BenchmarkEngine:
    """Create comprehensive HR benchmark engine."""
    kpis = [
        # Retention KPIs
        KPIDefinition("turnover_rate", "Annual Turnover Rate", 15.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RETENTION, "%", "Total employee turnover"),
        KPIDefinition("voluntary_turnover", "Voluntary Turnover Rate", 10.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RETENTION, "%", "Employee-initiated departures"),
        KPIDefinition("high_performer_retention", "High Performer Retention", 90.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RETENTION, "%", "Retention of top performers"),
        KPIDefinition("first_year_turnover", "First Year Turnover", 20.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RETENTION, "%", "New hire turnover in first year"),

        # Recruitment KPIs
        KPIDefinition("time_to_fill", "Time to Fill", 45.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RECRUITMENT, "days", "Average days to fill position"),
        KPIDefinition("cost_per_hire", "Cost per Hire", 4000.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RECRUITMENT, "$", "Average recruiting cost"),
        KPIDefinition("offer_acceptance_rate", "Offer Acceptance Rate", 85.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%", "Accepted offers / total offers"),
        KPIDefinition("quality_of_hire", "Quality of Hire", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%", "New hire performance rating"),

        # Engagement KPIs
        KPIDefinition("engagement_score", "Employee Engagement Score", 75.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%", "Overall engagement"),
        KPIDefinition("enps", "Employee Net Promoter Score", 30.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "", "eNPS score"),
        KPIDefinition("survey_participation", "Survey Participation Rate", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%", "Engagement survey response rate"),

        # Performance KPIs
        KPIDefinition("performance_review_completion", "Review Completion Rate", 95.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.PERFORMANCE, "%", "On-time review completion"),
        KPIDefinition("goal_achievement", "Goal Achievement Rate", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.PERFORMANCE, "%", "Goals met or exceeded"),
        KPIDefinition("pip_success_rate", "PIP Success Rate", 50.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.PERFORMANCE, "%", "PIP employees improved"),

        # Compensation KPIs
        KPIDefinition("compa_ratio", "Compa-Ratio", 100.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.COMPENSATION, "%", "Salary vs. market midpoint"),
        KPIDefinition("pay_equity_gap", "Pay Equity Gap", 3.0, KPIDirection.LOWER_IS_BETTER, KPICategory.COMPENSATION, "%", "Gender/race pay gap"),

        # Development KPIs
        KPIDefinition("training_hours", "Training Hours per Employee", 40.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DEVELOPMENT, "hrs", "Annual training hours"),
        KPIDefinition("internal_promotion_rate", "Internal Promotion Rate", 60.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DEVELOPMENT, "%", "Positions filled internally"),
        KPIDefinition("succession_coverage", "Succession Coverage", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DEVELOPMENT, "%", "Critical roles with successors"),

        # Diversity KPIs
        KPIDefinition("diversity_representation", "Diversity Representation", 40.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DIVERSITY, "%", "Underrepresented groups"),
        KPIDefinition("diversity_leadership", "Diversity in Leadership", 30.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DIVERSITY, "%", "Diverse leaders"),
    ]

    return BenchmarkEngine(kpis, category_weights={
        "Retention": 1.2,
        "Engagement": 1.2,
        "Recruitment": 1.0,
        "Performance": 1.0,
        "Development": 1.0,
        "Compensation": 0.9,
        "Diversity": 0.9
    })


def create_engagement_benchmarks() -> BenchmarkEngine:
    """Create employee engagement-focused benchmark engine."""
    kpis = [
        KPIDefinition("overall_engagement", "Overall Engagement", 75.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("job_satisfaction", "Job Satisfaction", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("manager_effectiveness", "Manager Effectiveness", 75.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("career_development", "Career Development Satisfaction", 70.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DEVELOPMENT, "%"),
        KPIDefinition("work_life_balance", "Work-Life Balance", 70.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("recognition", "Recognition & Appreciation", 75.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("company_confidence", "Confidence in Company", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("team_collaboration", "Team Collaboration", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("communication", "Communication Effectiveness", 70.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.ENGAGEMENT, "%"),
        KPIDefinition("resources_tools", "Resources & Tools", 75.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.PRODUCTIVITY, "%"),
    ]

    return BenchmarkEngine(kpis)


def create_recruitment_benchmarks() -> BenchmarkEngine:
    """Create recruitment-focused benchmark engine."""
    kpis = [
        KPIDefinition("time_to_fill", "Time to Fill", 45.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RECRUITMENT, "days"),
        KPIDefinition("time_to_hire", "Time to Hire", 30.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RECRUITMENT, "days"),
        KPIDefinition("cost_per_hire", "Cost per Hire", 4000.0, KPIDirection.LOWER_IS_BETTER, KPICategory.RECRUITMENT, "$"),
        KPIDefinition("source_of_hire", "Internal Source Rate", 30.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%"),
        KPIDefinition("applicants_per_opening", "Applicants per Opening", 50.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, ""),
        KPIDefinition("offer_acceptance", "Offer Acceptance Rate", 85.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%"),
        KPIDefinition("quality_of_hire", "Quality of Hire Score", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%"),
        KPIDefinition("hiring_manager_satisfaction", "Hiring Manager Satisfaction", 85.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%"),
        KPIDefinition("candidate_experience", "Candidate Experience Score", 80.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.RECRUITMENT, "%"),
        KPIDefinition("diversity_of_hires", "Diversity of Hires", 40.0, KPIDirection.HIGHER_IS_BETTER, KPICategory.DIVERSITY, "%"),
    ]

    return BenchmarkEngine(kpis)
