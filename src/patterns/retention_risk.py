"""
Retention Risk Classifier - Talent Intelligence

Flight risk analysis and attrition prediction for workforce planning.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


class RiskFactor(Enum):
    COMPENSATION = "Compensation"
    CAREER_GROWTH = "Career Growth"
    MANAGER_RELATIONSHIP = "Manager Relationship"
    WORK_ENVIRONMENT = "Work Environment"
    JOB_FIT = "Job Fit"
    TENURE = "Tenure"
    ENGAGEMENT = "Engagement"
    LIFE_EVENTS = "Life Events"
    MARKET_CONDITIONS = "Market Conditions"


@dataclass
class RiskIndicator:
    """Definition of a risk indicator."""
    indicator_id: str
    name: str
    weight: float
    risk_factor: RiskFactor
    threshold_low: float = 30  # Below this = low risk
    threshold_high: float = 70  # Above this = high risk
    description: str = ""


@dataclass
class IndicatorAssessment:
    """Assessment result for a single indicator."""
    indicator_id: str
    indicator_name: str
    value: float
    risk_contribution: float
    risk_level: RiskLevel
    risk_factor: RiskFactor
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "indicator_name": self.indicator_name,
            "value": round(self.value, 2),
            "risk_contribution": round(self.risk_contribution, 1),
            "risk_level": self.risk_level.value,
            "risk_factor": self.risk_factor.value,
            "explanation": self.explanation
        }


@dataclass
class RetentionRiskAssessment:
    """Complete retention risk assessment."""
    employee_id: str
    employee_name: str
    overall_risk_score: float
    risk_level: RiskLevel
    flight_probability: float  # 0-100%
    risk_factors: Dict[str, float]
    indicator_assessments: List[IndicatorAssessment]
    top_risk_drivers: List[str]
    retention_recommendations: List[str]
    urgency: str
    estimated_time_to_departure: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "overall_risk_score": round(self.overall_risk_score, 1),
            "risk_level": self.risk_level.value,
            "flight_probability": round(self.flight_probability, 1),
            "risk_factors": {k: round(v, 1) for k, v in self.risk_factors.items()},
            "top_risk_drivers": self.top_risk_drivers,
            "retention_recommendations": self.retention_recommendations,
            "urgency": self.urgency,
            "estimated_time_to_departure": self.estimated_time_to_departure
        }


class RetentionRiskClassifier:
    """Classifies employee retention/flight risk."""

    RISK_THRESHOLDS = {
        80: RiskLevel.CRITICAL,
        60: RiskLevel.HIGH,
        40: RiskLevel.MEDIUM,
        20: RiskLevel.LOW,
        0: RiskLevel.VERY_LOW
    }

    URGENCY_MAP = {
        RiskLevel.CRITICAL: "Immediate action required",
        RiskLevel.HIGH: "Action needed within 2 weeks",
        RiskLevel.MEDIUM: "Monitor closely, plan intervention",
        RiskLevel.LOW: "Regular check-ins sufficient",
        RiskLevel.VERY_LOW: "No immediate concern"
    }

    TIME_TO_DEPARTURE = {
        RiskLevel.CRITICAL: "0-3 months",
        RiskLevel.HIGH: "3-6 months",
        RiskLevel.MEDIUM: "6-12 months",
        RiskLevel.LOW: "12+ months",
        RiskLevel.VERY_LOW: "Not anticipated"
    }

    def __init__(self, indicators: List[RiskIndicator]):
        """Initialize with risk indicators."""
        self.indicators = {i.indicator_id: i for i in indicators}
        self.total_weight = sum(i.weight for i in indicators)

    def assess(
        self,
        employee_id: str,
        employee_name: str,
        indicator_values: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> RetentionRiskAssessment:
        """Assess retention risk for an employee."""
        assessments = []
        risk_factors: Dict[str, List[float]] = {}
        total_weighted_risk = 0
        total_weight_used = 0

        for ind_id, indicator in self.indicators.items():
            value = indicator_values.get(ind_id)
            if value is None:
                continue

            risk_contribution = self._calculate_risk_contribution(value, indicator)
            risk_level = self._determine_indicator_risk(risk_contribution)
            explanation = self._generate_explanation(indicator, value, risk_level)

            assessments.append(IndicatorAssessment(
                indicator_id=ind_id,
                indicator_name=indicator.name,
                value=value,
                risk_contribution=risk_contribution,
                risk_level=risk_level,
                risk_factor=indicator.risk_factor,
                explanation=explanation
            ))

            # Aggregate by risk factor
            factor_name = indicator.risk_factor.value
            if factor_name not in risk_factors:
                risk_factors[factor_name] = []
            risk_factors[factor_name].append(risk_contribution * indicator.weight)

            total_weighted_risk += risk_contribution * (indicator.weight / self.total_weight)
            total_weight_used += indicator.weight / self.total_weight

        # Calculate overall risk
        if total_weight_used > 0:
            overall_risk = total_weighted_risk / total_weight_used
        else:
            overall_risk = 0

        # Aggregate risk factors
        aggregated_factors = {
            factor: sum(scores) / len(scores) if scores else 0
            for factor, scores in risk_factors.items()
        }

        # Determine overall risk level
        risk_level = self._determine_risk_level(overall_risk)

        # Calculate flight probability (non-linear transformation)
        flight_probability = self._calculate_flight_probability(overall_risk)

        # Identify top risk drivers
        sorted_assessments = sorted(assessments, key=lambda x: x.risk_contribution, reverse=True)
        top_drivers = [
            f"{a.indicator_name}: {a.explanation}"
            for a in sorted_assessments[:3]
            if a.risk_contribution >= 50
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, sorted_assessments, aggregated_factors
        )

        return RetentionRiskAssessment(
            employee_id=employee_id,
            employee_name=employee_name,
            overall_risk_score=overall_risk,
            risk_level=risk_level,
            flight_probability=flight_probability,
            risk_factors=aggregated_factors,
            indicator_assessments=assessments,
            top_risk_drivers=top_drivers,
            retention_recommendations=recommendations,
            urgency=self.URGENCY_MAP[risk_level],
            estimated_time_to_departure=self.TIME_TO_DEPARTURE[risk_level],
            metadata=metadata or {}
        )

    def _calculate_risk_contribution(self, value: float, indicator: RiskIndicator) -> float:
        """Calculate risk contribution from indicator value."""
        # Value is expected to be a risk score (0-100, higher = more risk)
        return min(100, max(0, value))

    def _determine_indicator_risk(self, risk_contribution: float) -> RiskLevel:
        """Determine risk level from contribution score."""
        for threshold, level in sorted(self.RISK_THRESHOLDS.items(), reverse=True):
            if risk_contribution >= threshold:
                return level
        return RiskLevel.VERY_LOW

    def _determine_risk_level(self, overall_risk: float) -> RiskLevel:
        """Determine overall risk level."""
        for threshold, level in sorted(self.RISK_THRESHOLDS.items(), reverse=True):
            if overall_risk >= threshold:
                return level
        return RiskLevel.VERY_LOW

    def _calculate_flight_probability(self, risk_score: float) -> float:
        """Convert risk score to flight probability with non-linear scaling."""
        # Sigmoid-like transformation
        if risk_score <= 20:
            return risk_score * 0.5  # 0-10%
        elif risk_score <= 40:
            return 10 + (risk_score - 20) * 1.0  # 10-30%
        elif risk_score <= 60:
            return 30 + (risk_score - 40) * 1.5  # 30-60%
        elif risk_score <= 80:
            return 60 + (risk_score - 60) * 1.5  # 60-90%
        else:
            return min(95, 90 + (risk_score - 80) * 0.25)  # 90-95%

    def _generate_explanation(
        self,
        indicator: RiskIndicator,
        value: float,
        risk_level: RiskLevel
    ) -> str:
        """Generate explanation for indicator assessment."""
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return f"Significant concern in {indicator.name.lower()}"
        elif risk_level == RiskLevel.MEDIUM:
            return f"Moderate concern in {indicator.name.lower()}"
        else:
            return f"{indicator.name} is within acceptable range"

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        assessments: List[IndicatorAssessment],
        risk_factors: Dict[str, float]
    ) -> List[str]:
        """Generate retention recommendations."""
        recommendations = []

        # Find highest risk factors
        sorted_factors = sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)

        for factor, score in sorted_factors[:3]:
            if score < 40:
                continue

            if factor == RiskFactor.COMPENSATION.value:
                recommendations.append("Review compensation against market rates")
                if score >= 60:
                    recommendations.append("Consider retention bonus or salary adjustment")

            elif factor == RiskFactor.CAREER_GROWTH.value:
                recommendations.append("Discuss career development path and opportunities")
                recommendations.append("Identify stretch assignments or new responsibilities")

            elif factor == RiskFactor.MANAGER_RELATIONSHIP.value:
                recommendations.append("Facilitate conversation between employee and manager")
                recommendations.append("Consider manager coaching or team reassignment")

            elif factor == RiskFactor.WORK_ENVIRONMENT.value:
                recommendations.append("Address work environment concerns")
                recommendations.append("Explore flexible work arrangements")

            elif factor == RiskFactor.JOB_FIT.value:
                recommendations.append("Evaluate role alignment with skills and interests")
                recommendations.append("Consider internal mobility options")

            elif factor == RiskFactor.ENGAGEMENT.value:
                recommendations.append("Increase meaningful work and autonomy")
                recommendations.append("Strengthen team connections")

        # Add urgency-based recommendations
        if risk_level == RiskLevel.CRITICAL:
            recommendations.insert(0, "Schedule immediate stay interview")
        elif risk_level == RiskLevel.HIGH:
            recommendations.insert(0, "Conduct stay conversation within 1 week")

        return recommendations[:5]


def create_retention_risk_classifier() -> RetentionRiskClassifier:
    """Create standard retention risk classifier."""
    indicators = [
        RiskIndicator(
            "compensation_gap", "Compensation Gap", 15,
            RiskFactor.COMPENSATION,
            description="Gap between current and market compensation"
        ),
        RiskIndicator(
            "time_since_raise", "Time Since Last Raise", 10,
            RiskFactor.COMPENSATION,
            description="Months since last compensation increase"
        ),
        RiskIndicator(
            "promotion_timeline", "Promotion Timeline", 12,
            RiskFactor.CAREER_GROWTH,
            description="Time since last promotion vs. typical timeline"
        ),
        RiskIndicator(
            "skill_utilization", "Skill Utilization Gap", 10,
            RiskFactor.JOB_FIT,
            description="Gap between skills and role requirements"
        ),
        RiskIndicator(
            "manager_rating", "Manager Relationship Score", 15,
            RiskFactor.MANAGER_RELATIONSHIP,
            description="Inverted score - low rating = high risk"
        ),
        RiskIndicator(
            "engagement_score", "Engagement Level", 12,
            RiskFactor.ENGAGEMENT,
            description="Inverted engagement - low engagement = high risk"
        ),
        RiskIndicator(
            "work_life_balance", "Work-Life Balance Risk", 8,
            RiskFactor.WORK_ENVIRONMENT,
            description="Overtime hours and stress indicators"
        ),
        RiskIndicator(
            "tenure_risk", "Tenure Risk Window", 8,
            RiskFactor.TENURE,
            description="Risk based on typical departure timelines"
        ),
        RiskIndicator(
            "job_search_signals", "Job Search Signals", 10,
            RiskFactor.MARKET_CONDITIONS,
            description="LinkedIn activity, recruiter contacts, etc."
        )
    ]
    return RetentionRiskClassifier(indicators)


def create_high_performer_risk_classifier() -> RetentionRiskClassifier:
    """Create classifier focused on high performer retention."""
    indicators = [
        RiskIndicator(
            "recognition_gap", "Recognition Gap", 15,
            RiskFactor.ENGAGEMENT,
            description="Gap between contribution and recognition"
        ),
        RiskIndicator(
            "growth_opportunity", "Growth Opportunity Gap", 18,
            RiskFactor.CAREER_GROWTH,
            description="Perceived lack of advancement opportunities"
        ),
        RiskIndicator(
            "challenge_level", "Challenge Level", 12,
            RiskFactor.JOB_FIT,
            description="Lack of challenging work"
        ),
        RiskIndicator(
            "compensation_percentile", "Compensation Percentile", 15,
            RiskFactor.COMPENSATION,
            description="Position in compensation band"
        ),
        RiskIndicator(
            "project_visibility", "Project Visibility", 10,
            RiskFactor.CAREER_GROWTH,
            description="Visibility of current assignments"
        ),
        RiskIndicator(
            "leadership_access", "Leadership Access", 10,
            RiskFactor.CAREER_GROWTH,
            description="Access to senior leadership"
        ),
        RiskIndicator(
            "autonomy_level", "Autonomy Level", 10,
            RiskFactor.WORK_ENVIRONMENT,
            description="Decision-making authority"
        ),
        RiskIndicator(
            "market_demand", "Market Demand", 10,
            RiskFactor.MARKET_CONDITIONS,
            description="External demand for skills"
        )
    ]
    return RetentionRiskClassifier(indicators)
