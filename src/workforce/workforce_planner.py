"""
Workforce Planner - Talent Intelligence

Headcount planning, workforce forecasting, and capacity analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, date
import logging
import math

logger = logging.getLogger(__name__)


class PlanningScenario(Enum):
    BASELINE = "Baseline"
    GROWTH = "Growth"
    CONSERVATIVE = "Conservative"
    AGGRESSIVE = "Aggressive"
    RECESSION = "Recession"


class GapSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = "None"


@dataclass
class DepartmentProfile:
    """Profile of a department for workforce planning."""
    department_id: str
    name: str
    current_headcount: int
    target_headcount: int
    avg_attrition_rate: float  # Annual %
    avg_time_to_fill: int  # Days
    avg_cost_per_hire: float
    critical_roles: int = 0
    contractors: int = 0
    open_positions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HeadcountForecast:
    """Headcount forecast for a period."""
    period: str
    starting_headcount: int
    projected_attrition: int
    projected_hires: int
    ending_headcount: int
    target_headcount: int
    gap: int
    gap_percentage: float
    hiring_need: int
    cost_projection: float
    risk_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "starting_headcount": self.starting_headcount,
            "projected_attrition": self.projected_attrition,
            "projected_hires": self.projected_hires,
            "ending_headcount": self.ending_headcount,
            "target_headcount": self.target_headcount,
            "gap": self.gap,
            "gap_percentage": round(self.gap_percentage, 1),
            "hiring_need": self.hiring_need,
            "cost_projection": round(self.cost_projection, 2),
            "risk_level": self.risk_level
        }


@dataclass
class SkillGap:
    """Identified skill gap in the workforce."""
    skill_name: str
    current_capacity: int  # Number of people with skill
    required_capacity: int
    gap: int
    gap_severity: GapSeverity
    impact_areas: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "current_capacity": self.current_capacity,
            "required_capacity": self.required_capacity,
            "gap": self.gap,
            "gap_severity": self.gap_severity.value,
            "impact_areas": self.impact_areas,
            "recommendations": self.recommendations
        }


@dataclass
class WorkforcePlan:
    """Complete workforce plan."""
    plan_id: str
    organization_id: str
    scenario: PlanningScenario
    planning_horizon: int  # months
    period_forecasts: List[HeadcountForecast]
    department_plans: Dict[str, List[HeadcountForecast]]
    total_hiring_need: int
    total_cost_projection: float
    skill_gaps: List[SkillGap]
    risk_assessment: str
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "scenario": self.scenario.value,
            "planning_horizon": self.planning_horizon,
            "total_hiring_need": self.total_hiring_need,
            "total_cost_projection": round(self.total_cost_projection, 2),
            "skill_gaps": [g.to_dict() for g in self.skill_gaps],
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations,
            "period_forecasts": [p.to_dict() for p in self.period_forecasts]
        }


class WorkforcePlanner:
    """Plans workforce needs and forecasts headcount."""

    SCENARIO_MODIFIERS = {
        PlanningScenario.BASELINE: {"growth": 1.0, "attrition": 1.0},
        PlanningScenario.GROWTH: {"growth": 1.2, "attrition": 0.9},
        PlanningScenario.CONSERVATIVE: {"growth": 0.8, "attrition": 1.1},
        PlanningScenario.AGGRESSIVE: {"growth": 1.5, "attrition": 0.85},
        PlanningScenario.RECESSION: {"growth": 0.5, "attrition": 1.3}
    }

    def __init__(
        self,
        default_attrition_rate: float = 15.0,  # Annual %
        default_time_to_fill: int = 45,
        default_cost_per_hire: float = 4000
    ):
        self.default_attrition_rate = default_attrition_rate
        self.default_time_to_fill = default_time_to_fill
        self.default_cost_per_hire = default_cost_per_hire

    def create_workforce_plan(
        self,
        plan_id: str,
        organization_id: str,
        current_headcount: int,
        target_headcount: int,
        departments: Optional[List[DepartmentProfile]] = None,
        skill_requirements: Optional[Dict[str, int]] = None,
        current_skills: Optional[Dict[str, int]] = None,
        scenario: PlanningScenario = PlanningScenario.BASELINE,
        planning_horizon: int = 12,  # months
        growth_rate: float = 0  # Monthly growth rate for target
    ) -> WorkforcePlan:
        """Create a comprehensive workforce plan."""
        modifiers = self.SCENARIO_MODIFIERS[scenario]

        # Generate period forecasts
        period_forecasts = self._generate_forecasts(
            current_headcount=current_headcount,
            target_headcount=target_headcount,
            attrition_rate=self.default_attrition_rate * modifiers["attrition"],
            growth_rate=growth_rate * modifiers["growth"],
            cost_per_hire=self.default_cost_per_hire,
            periods=planning_horizon
        )

        # Generate department-level plans
        department_plans = {}
        if departments:
            for dept in departments:
                dept_forecasts = self._generate_forecasts(
                    current_headcount=dept.current_headcount,
                    target_headcount=dept.target_headcount,
                    attrition_rate=dept.avg_attrition_rate * modifiers["attrition"],
                    growth_rate=growth_rate * modifiers["growth"],
                    cost_per_hire=dept.avg_cost_per_hire,
                    periods=planning_horizon
                )
                department_plans[dept.department_id] = dept_forecasts

        # Calculate totals
        total_hiring = sum(p.hiring_need for p in period_forecasts)
        total_cost = sum(p.cost_projection for p in period_forecasts)

        # Analyze skill gaps
        skill_gaps = []
        if skill_requirements and current_skills:
            skill_gaps = self._analyze_skill_gaps(skill_requirements, current_skills)

        # Risk assessment
        risk_assessment = self._assess_workforce_risk(
            period_forecasts, skill_gaps, departments or []
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            period_forecasts, skill_gaps, scenario, departments or []
        )

        return WorkforcePlan(
            plan_id=plan_id,
            organization_id=organization_id,
            scenario=scenario,
            planning_horizon=planning_horizon,
            period_forecasts=period_forecasts,
            department_plans=department_plans,
            total_hiring_need=total_hiring,
            total_cost_projection=total_cost,
            skill_gaps=skill_gaps,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )

    def _generate_forecasts(
        self,
        current_headcount: int,
        target_headcount: int,
        attrition_rate: float,
        growth_rate: float,
        cost_per_hire: float,
        periods: int
    ) -> List[HeadcountForecast]:
        """Generate period-by-period headcount forecasts."""
        forecasts = []
        headcount = current_headcount
        monthly_attrition_rate = attrition_rate / 12 / 100

        for i in range(periods):
            period_name = f"Month {i + 1}"

            # Calculate attrition for period
            projected_attrition = max(1, int(headcount * monthly_attrition_rate))

            # Calculate target for this period (with growth)
            period_target = int(target_headcount * (1 + growth_rate * (i + 1) / 100))

            # Calculate hiring need
            after_attrition = headcount - projected_attrition
            hiring_need = max(0, period_target - after_attrition)

            # Assume we can hire some portion
            projected_hires = min(hiring_need, max(3, int(hiring_need * 0.7)))
            ending_headcount = after_attrition + projected_hires

            # Calculate gap
            gap = ending_headcount - period_target
            gap_pct = (gap / period_target * 100) if period_target > 0 else 0

            # Cost projection
            cost = projected_hires * cost_per_hire

            # Risk level
            if gap_pct < -15:
                risk = "Critical"
            elif gap_pct < -10:
                risk = "High"
            elif gap_pct < -5:
                risk = "Medium"
            elif gap_pct < 0:
                risk = "Low"
            else:
                risk = "None"

            forecasts.append(HeadcountForecast(
                period=period_name,
                starting_headcount=headcount,
                projected_attrition=projected_attrition,
                projected_hires=projected_hires,
                ending_headcount=ending_headcount,
                target_headcount=period_target,
                gap=gap,
                gap_percentage=gap_pct,
                hiring_need=hiring_need,
                cost_projection=cost,
                risk_level=risk
            ))

            headcount = ending_headcount

        return forecasts

    def _analyze_skill_gaps(
        self,
        required: Dict[str, int],
        current: Dict[str, int]
    ) -> List[SkillGap]:
        """Analyze skill gaps in the workforce."""
        gaps = []

        for skill, required_count in required.items():
            current_count = current.get(skill, 0)
            gap = required_count - current_count

            if gap > 0:
                # Determine severity
                gap_ratio = gap / required_count if required_count > 0 else 1
                if gap_ratio >= 0.5:
                    severity = GapSeverity.CRITICAL
                elif gap_ratio >= 0.3:
                    severity = GapSeverity.HIGH
                elif gap_ratio >= 0.15:
                    severity = GapSeverity.MEDIUM
                else:
                    severity = GapSeverity.LOW

                recommendations = self._get_skill_gap_recommendations(skill, gap, severity)

                gaps.append(SkillGap(
                    skill_name=skill,
                    current_capacity=current_count,
                    required_capacity=required_count,
                    gap=gap,
                    gap_severity=severity,
                    impact_areas=[f"Projects requiring {skill}"],
                    recommendations=recommendations
                ))

        # Sort by severity
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
            GapSeverity.NONE: 4
        }
        gaps.sort(key=lambda g: severity_order[g.gap_severity])

        return gaps

    def _get_skill_gap_recommendations(
        self,
        skill: str,
        gap: int,
        severity: GapSeverity
    ) -> List[str]:
        """Generate recommendations for skill gap."""
        recs = []

        if severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]:
            recs.append(f"Prioritize hiring for {skill} ({gap} positions)")
            recs.append(f"Consider contractors or consultants for immediate {skill} needs")

        recs.append(f"Develop internal training program for {skill}")

        if gap > 3:
            recs.append(f"Create {skill} career path to attract talent")

        return recs[:3]

    def _assess_workforce_risk(
        self,
        forecasts: List[HeadcountForecast],
        skill_gaps: List[SkillGap],
        departments: List[DepartmentProfile]
    ) -> str:
        """Assess overall workforce risk."""
        risk_factors = []

        # Check headcount gaps
        critical_periods = [f for f in forecasts if f.risk_level == "Critical"]
        high_risk_periods = [f for f in forecasts if f.risk_level == "High"]

        if critical_periods:
            risk_factors.append(f"{len(critical_periods)} critical staffing gaps")

        if high_risk_periods:
            risk_factors.append(f"{len(high_risk_periods)} high-risk periods")

        # Check skill gaps
        critical_skills = [g for g in skill_gaps if g.gap_severity == GapSeverity.CRITICAL]
        if critical_skills:
            risk_factors.append(f"{len(critical_skills)} critical skill gaps")

        # Check departments
        understaffed = [d for d in departments if d.current_headcount < d.target_headcount * 0.85]
        if understaffed:
            risk_factors.append(f"{len(understaffed)} understaffed departments")

        if len(risk_factors) >= 3:
            return f"Critical - Multiple workforce risks: {'; '.join(risk_factors)}"
        elif len(risk_factors) >= 2:
            return f"High - Significant risks: {'; '.join(risk_factors)}"
        elif len(risk_factors) >= 1:
            return f"Medium - Monitor: {'; '.join(risk_factors)}"
        else:
            return "Low - Workforce planning on track"

    def _generate_recommendations(
        self,
        forecasts: List[HeadcountForecast],
        skill_gaps: List[SkillGap],
        scenario: PlanningScenario,
        departments: List[DepartmentProfile]
    ) -> List[str]:
        """Generate workforce planning recommendations."""
        recommendations = []

        # Hiring recommendations
        total_hiring = sum(f.hiring_need for f in forecasts)
        if total_hiring > 0:
            recommendations.append(f"Plan to hire {total_hiring} employees over planning horizon")

        # Skill gap recommendations
        critical_gaps = [g for g in skill_gaps if g.gap_severity == GapSeverity.CRITICAL]
        if critical_gaps:
            skills = ", ".join(g.skill_name for g in critical_gaps[:3])
            recommendations.append(f"Address critical skill gaps: {skills}")

        # Retention focus
        if scenario == PlanningScenario.RECESSION:
            recommendations.append("Focus on retaining key talent during uncertainty")
        elif scenario == PlanningScenario.GROWTH:
            recommendations.append("Build recruiting capacity for growth phase")

        # Department-specific
        for dept in departments:
            if dept.open_positions > dept.current_headcount * 0.2:
                recommendations.append(f"Accelerate hiring in {dept.name}")

        # Cost management
        total_cost = sum(f.cost_projection for f in forecasts)
        if total_cost > 100000:
            recommendations.append(f"Budget ${total_cost:,.0f} for recruiting costs")

        return recommendations[:5]

    def calculate_attrition_impact(
        self,
        current_headcount: int,
        attrition_rate: float,
        months: int = 12
    ) -> Dict[str, Any]:
        """Calculate impact of attrition over time."""
        monthly_rate = attrition_rate / 12 / 100
        remaining = current_headcount

        monthly_losses = []
        for m in range(months):
            loss = int(remaining * monthly_rate)
            monthly_losses.append(loss)
            remaining -= loss

        total_loss = current_headcount - remaining
        replacement_cost = total_loss * self.default_cost_per_hire

        return {
            "current_headcount": current_headcount,
            "attrition_rate": attrition_rate,
            "months": months,
            "projected_departures": total_loss,
            "ending_headcount": remaining,
            "monthly_losses": monthly_losses,
            "replacement_cost": replacement_cost,
            "productivity_loss_estimate": total_loss * 0.25 * 3  # 3 months ramp time
        }
