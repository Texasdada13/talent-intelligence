"""
Succession Analyzer - Talent Intelligence

Succession planning and leadership pipeline analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReadinessLevel(Enum):
    READY_NOW = "Ready Now"
    READY_1_YEAR = "Ready in 1 Year"
    READY_2_YEARS = "Ready in 2+ Years"
    DEVELOPING = "Developing"
    NOT_READY = "Not Ready"


class RoleRisk(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class CriticalRole:
    """Definition of a critical role."""
    role_id: str
    title: str
    department: str
    incumbent_id: Optional[str]
    incumbent_name: Optional[str]
    vacancy_risk: float  # 0-100
    business_impact: str
    successor_count: int = 0
    ready_now_count: int = 0
    risk_level: RoleRisk = RoleRisk.MEDIUM


@dataclass
class SuccessorCandidate:
    """Potential successor for a role."""
    employee_id: str
    employee_name: str
    current_role: str
    readiness_level: ReadinessLevel
    performance_rating: str
    potential_rating: str
    development_gaps: List[str]
    development_actions: List[str]
    time_in_role: int  # months
    flight_risk: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReadinessAssessment:
    """Assessment of candidate readiness."""
    employee_id: str
    employee_name: str
    target_role: str
    overall_readiness: float  # 0-100
    readiness_level: ReadinessLevel
    competency_scores: Dict[str, float]
    experience_gaps: List[str]
    development_plan: List[str]
    estimated_ready_date: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "target_role": self.target_role,
            "overall_readiness": round(self.overall_readiness, 1),
            "readiness_level": self.readiness_level.value,
            "competency_scores": {k: round(v, 1) for k, v in self.competency_scores.items()},
            "experience_gaps": self.experience_gaps,
            "development_plan": self.development_plan
        }


@dataclass
class SuccessionPlan:
    """Complete succession plan."""
    plan_id: str
    organization_id: str
    critical_roles: List[CriticalRole]
    succession_coverage: float  # % of roles with successors
    ready_now_coverage: float  # % with ready-now successors
    role_assessments: Dict[str, List[SuccessorCandidate]]
    high_risk_roles: List[str]
    bench_strength: str
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "critical_role_count": len(self.critical_roles),
            "succession_coverage": round(self.succession_coverage, 1),
            "ready_now_coverage": round(self.ready_now_coverage, 1),
            "high_risk_roles": self.high_risk_roles,
            "bench_strength": self.bench_strength,
            "recommendations": self.recommendations
        }


class SuccessionAnalyzer:
    """Analyzes succession planning and bench strength."""

    READINESS_THRESHOLDS = {
        90: ReadinessLevel.READY_NOW,
        75: ReadinessLevel.READY_1_YEAR,
        60: ReadinessLevel.READY_2_YEARS,
        40: ReadinessLevel.DEVELOPING,
        0: ReadinessLevel.NOT_READY
    }

    def __init__(self):
        self.role_competencies: Dict[str, List[str]] = {}

    def set_role_competencies(self, role_id: str, competencies: List[str]):
        """Define competencies required for a role."""
        self.role_competencies[role_id] = competencies

    def assess_readiness(
        self,
        employee_id: str,
        employee_name: str,
        target_role: str,
        competency_scores: Dict[str, float],
        experience_years: float,
        required_experience: float = 5
    ) -> ReadinessAssessment:
        """Assess an employee's readiness for a role."""
        # Calculate overall readiness
        if competency_scores:
            avg_competency = sum(competency_scores.values()) / len(competency_scores)
        else:
            avg_competency = 50

        experience_score = min(100, (experience_years / required_experience) * 100)
        overall_readiness = (avg_competency * 0.7) + (experience_score * 0.3)

        # Determine readiness level
        readiness_level = self._determine_readiness(overall_readiness)

        # Identify gaps
        experience_gaps = []
        if experience_years < required_experience:
            experience_gaps.append(f"Need {required_experience - experience_years:.1f} more years experience")

        low_competencies = [c for c, s in competency_scores.items() if s < 70]
        if low_competencies:
            experience_gaps.extend([f"Develop {c}" for c in low_competencies[:3]])

        # Development plan
        development_plan = self._create_development_plan(
            readiness_level, low_competencies, experience_gaps
        )

        # Estimate ready date
        if readiness_level == ReadinessLevel.READY_NOW:
            ready_date = "Now"
        elif readiness_level == ReadinessLevel.READY_1_YEAR:
            ready_date = "Within 12 months"
        elif readiness_level == ReadinessLevel.READY_2_YEARS:
            ready_date = "12-24 months"
        else:
            ready_date = "24+ months"

        return ReadinessAssessment(
            employee_id=employee_id,
            employee_name=employee_name,
            target_role=target_role,
            overall_readiness=overall_readiness,
            readiness_level=readiness_level,
            competency_scores=competency_scores,
            experience_gaps=experience_gaps,
            development_plan=development_plan,
            estimated_ready_date=ready_date
        )

    def create_succession_plan(
        self,
        plan_id: str,
        organization_id: str,
        critical_roles: List[CriticalRole],
        role_successors: Dict[str, List[SuccessorCandidate]]
    ) -> SuccessionPlan:
        """Create a comprehensive succession plan."""
        # Calculate coverage metrics
        roles_with_successors = sum(1 for r in critical_roles if role_successors.get(r.role_id))
        succession_coverage = (roles_with_successors / len(critical_roles) * 100) if critical_roles else 0

        ready_now_roles = sum(
            1 for r in critical_roles
            if any(s.readiness_level == ReadinessLevel.READY_NOW for s in role_successors.get(r.role_id, []))
        )
        ready_now_coverage = (ready_now_roles / len(critical_roles) * 100) if critical_roles else 0

        # Identify high-risk roles
        high_risk_roles = []
        for role in critical_roles:
            successors = role_successors.get(role.role_id, [])
            if not successors or role.vacancy_risk > 70:
                high_risk_roles.append(role.title)
            elif not any(s.readiness_level in [ReadinessLevel.READY_NOW, ReadinessLevel.READY_1_YEAR] for s in successors):
                high_risk_roles.append(role.title)

        # Assess bench strength
        bench_strength = self._assess_bench_strength(succession_coverage, ready_now_coverage)

        # Generate recommendations
        recommendations = self._generate_succession_recommendations(
            critical_roles, role_successors, high_risk_roles, succession_coverage
        )

        return SuccessionPlan(
            plan_id=plan_id,
            organization_id=organization_id,
            critical_roles=critical_roles,
            succession_coverage=succession_coverage,
            ready_now_coverage=ready_now_coverage,
            role_assessments=role_successors,
            high_risk_roles=high_risk_roles[:10],
            bench_strength=bench_strength,
            recommendations=recommendations
        )

    def _determine_readiness(self, score: float) -> ReadinessLevel:
        """Determine readiness level from score."""
        for threshold, level in sorted(self.READINESS_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return level
        return ReadinessLevel.NOT_READY

    def _create_development_plan(
        self,
        readiness: ReadinessLevel,
        low_competencies: List[str],
        gaps: List[str]
    ) -> List[str]:
        """Create development plan based on gaps."""
        plan = []

        if readiness == ReadinessLevel.READY_NOW:
            plan.append("Provide stretch assignments to maintain engagement")
            plan.append("Include in leadership meetings and strategic discussions")

        elif readiness == ReadinessLevel.READY_1_YEAR:
            plan.append("Assign to high-visibility project")
            if low_competencies:
                plan.append(f"Focus development on: {', '.join(low_competencies[:2])}")

        elif readiness == ReadinessLevel.READY_2_YEARS:
            plan.append("Create structured development plan")
            plan.append("Assign executive mentor")
            if low_competencies:
                plan.append(f"Training needed: {', '.join(low_competencies[:3])}")

        else:
            plan.append("Assess long-term potential")
            plan.append("Consider alternative career paths")

        return plan[:4]

    def _assess_bench_strength(self, coverage: float, ready_now: float) -> str:
        """Assess overall bench strength."""
        if coverage >= 90 and ready_now >= 70:
            return "Strong - Well-prepared succession pipeline"
        elif coverage >= 75 and ready_now >= 50:
            return "Good - Most roles covered, some development needed"
        elif coverage >= 50:
            return "Moderate - Gaps exist, accelerate development"
        else:
            return "Weak - Significant succession risk, immediate action needed"

    def _generate_succession_recommendations(
        self,
        roles: List[CriticalRole],
        successors: Dict[str, List[SuccessorCandidate]],
        high_risk: List[str],
        coverage: float
    ) -> List[str]:
        """Generate succession planning recommendations."""
        recommendations = []

        if high_risk:
            recommendations.append(f"Address {len(high_risk)} high-risk roles: {', '.join(high_risk[:3])}")

        if coverage < 80:
            recommendations.append("Identify additional succession candidates for coverage")

        # Check for single points of failure
        single_successor_roles = [r for r in roles if len(successors.get(r.role_id, [])) == 1]
        if single_successor_roles:
            recommendations.append(f"Develop backup successors for {len(single_successor_roles)} roles")

        recommendations.append("Conduct annual succession review with leadership")

        return recommendations[:5]
