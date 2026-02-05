"""
Workforce Scoring Engine - Talent Intelligence

Multi-dimensional scoring for employee performance, potential,
and talent assessment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScoreDirection(Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class TalentCategory(Enum):
    STAR = "Star"  # High performance, high potential
    HIGH_PERFORMER = "High Performer"  # High performance, moderate potential
    HIGH_POTENTIAL = "High Potential"  # Moderate performance, high potential
    CORE_CONTRIBUTOR = "Core Contributor"  # Solid performance, moderate potential
    DEVELOPING = "Developing"  # Growing, needs support
    UNDERPERFORMER = "Underperformer"  # Below expectations


@dataclass
class ScoringComponent:
    """Definition of a scoring component."""
    component_id: str
    name: str
    weight: float
    direction: ScoreDirection = ScoreDirection.HIGHER_IS_BETTER
    min_value: float = 0
    max_value: float = 100
    description: str = ""


@dataclass
class ComponentScore:
    """Score result for a single component."""
    component_id: str
    component_name: str
    raw_value: float
    normalized_score: float
    weighted_score: float
    weight: float
    rating: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "raw_value": round(self.raw_value, 2),
            "normalized_score": round(self.normalized_score, 1),
            "weighted_score": round(self.weighted_score, 1),
            "weight": self.weight,
            "rating": self.rating
        }


@dataclass
class WorkforceScore:
    """Complete workforce scoring result."""
    entity_id: str
    entity_name: str
    overall_score: float
    overall_rating: str
    talent_category: TalentCategory
    component_scores: List[ComponentScore]
    strengths: List[str]
    development_areas: List[str]
    recommendations: List[str]
    percentile: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "overall_score": round(self.overall_score, 1),
            "overall_rating": self.overall_rating,
            "talent_category": self.talent_category.value,
            "component_scores": [c.to_dict() for c in self.component_scores],
            "strengths": self.strengths,
            "development_areas": self.development_areas,
            "recommendations": self.recommendations,
            "percentile": self.percentile
        }


class WorkforceScoringEngine:
    """Multi-dimensional workforce scoring engine."""

    RATING_THRESHOLDS = {
        90: "Exceptional",
        80: "Exceeds Expectations",
        70: "Meets Expectations",
        60: "Needs Improvement",
        0: "Below Expectations"
    }

    def __init__(self, components: List[ScoringComponent]):
        """Initialize with scoring components."""
        self.components = {c.component_id: c for c in components}
        self.total_weight = sum(c.weight for c in components)

    def score(
        self,
        entity_id: str,
        entity_name: str,
        values: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkforceScore:
        """Calculate workforce score from component values."""
        component_scores = []
        total_weighted_score = 0
        total_weight_used = 0

        for comp_id, component in self.components.items():
            raw_value = values.get(comp_id)
            if raw_value is None:
                continue

            normalized = self._normalize_value(raw_value, component)
            weighted = normalized * (component.weight / self.total_weight)
            rating = self._determine_rating(normalized)

            component_scores.append(ComponentScore(
                component_id=comp_id,
                component_name=component.name,
                raw_value=raw_value,
                normalized_score=normalized,
                weighted_score=weighted * 100,
                weight=component.weight,
                rating=rating
            ))

            total_weighted_score += weighted
            total_weight_used += component.weight / self.total_weight

        if total_weight_used > 0:
            overall_score = (total_weighted_score / total_weight_used) * 100
        else:
            overall_score = 0

        overall_rating = self._determine_rating(overall_score)
        talent_category = self._determine_talent_category(overall_score, component_scores)

        # Identify strengths and development areas
        sorted_scores = sorted(component_scores, key=lambda x: x.normalized_score, reverse=True)
        strengths = [s.component_name for s in sorted_scores[:3] if s.normalized_score >= 70]
        development_areas = [s.component_name for s in sorted_scores[-3:] if s.normalized_score < 70]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, talent_category, component_scores
        )

        return WorkforceScore(
            entity_id=entity_id,
            entity_name=entity_name,
            overall_score=overall_score,
            overall_rating=overall_rating,
            talent_category=talent_category,
            component_scores=component_scores,
            strengths=strengths,
            development_areas=development_areas,
            recommendations=recommendations,
            metadata=metadata or {}
        )

    def _normalize_value(self, value: float, component: ScoringComponent) -> float:
        """Normalize value to 0-100 scale."""
        range_size = component.max_value - component.min_value
        if range_size == 0:
            return 50

        if component.direction == ScoreDirection.HIGHER_IS_BETTER:
            normalized = ((value - component.min_value) / range_size) * 100
        else:
            normalized = ((component.max_value - value) / range_size) * 100

        return max(0, min(100, normalized))

    def _determine_rating(self, score: float) -> str:
        """Determine rating from score."""
        for threshold, rating in sorted(self.RATING_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return rating
        return "Below Expectations"

    def _determine_talent_category(
        self,
        overall_score: float,
        component_scores: List[ComponentScore]
    ) -> TalentCategory:
        """Determine talent category based on performance and potential."""
        # Find performance and potential scores if available
        performance_score = None
        potential_score = None

        for cs in component_scores:
            if 'performance' in cs.component_id.lower():
                performance_score = cs.normalized_score
            elif 'potential' in cs.component_id.lower():
                potential_score = cs.normalized_score

        # If we don't have both, use overall score
        if performance_score is None:
            performance_score = overall_score
        if potential_score is None:
            potential_score = overall_score

        # 9-box grid logic
        if performance_score >= 80 and potential_score >= 80:
            return TalentCategory.STAR
        elif performance_score >= 80 and potential_score >= 60:
            return TalentCategory.HIGH_PERFORMER
        elif performance_score >= 60 and potential_score >= 80:
            return TalentCategory.HIGH_POTENTIAL
        elif performance_score >= 60 and potential_score >= 60:
            return TalentCategory.CORE_CONTRIBUTOR
        elif performance_score >= 40 or potential_score >= 40:
            return TalentCategory.DEVELOPING
        else:
            return TalentCategory.UNDERPERFORMER

    def _generate_recommendations(
        self,
        overall_score: float,
        talent_category: TalentCategory,
        component_scores: List[ComponentScore]
    ) -> List[str]:
        """Generate development recommendations."""
        recommendations = []

        if talent_category == TalentCategory.STAR:
            recommendations.append("Consider for leadership development program")
            recommendations.append("Assign high-visibility strategic projects")
            recommendations.append("Discuss career advancement opportunities")

        elif talent_category == TalentCategory.HIGH_PERFORMER:
            recommendations.append("Provide stretch assignments to develop potential")
            recommendations.append("Consider mentoring or coaching program")
            recommendations.append("Recognize and reward contributions")

        elif talent_category == TalentCategory.HIGH_POTENTIAL:
            recommendations.append("Focus on skill development and experience building")
            recommendations.append("Pair with high-performing mentor")
            recommendations.append("Provide performance coaching")

        elif talent_category == TalentCategory.CORE_CONTRIBUTOR:
            recommendations.append("Maintain engagement through meaningful work")
            recommendations.append("Offer professional development opportunities")
            recommendations.append("Regular feedback and recognition")

        elif talent_category == TalentCategory.DEVELOPING:
            recommendations.append("Create structured development plan")
            recommendations.append("Provide additional training and support")
            recommendations.append("Set clear expectations and milestones")

        else:
            recommendations.append("Conduct performance review discussion")
            recommendations.append("Create performance improvement plan")
            recommendations.append("Provide coaching and support resources")

        # Add component-specific recommendations
        weak_areas = [cs for cs in component_scores if cs.normalized_score < 60]
        for area in weak_areas[:2]:
            recommendations.append(f"Focus on improving {area.component_name}")

        return recommendations[:5]


# Factory Functions

def create_performance_engine() -> WorkforceScoringEngine:
    """Create employee performance scoring engine."""
    components = [
        ScoringComponent(
            "goal_achievement", "Goal Achievement", 25,
            description="Achievement of assigned goals and objectives"
        ),
        ScoringComponent(
            "quality_of_work", "Quality of Work", 20,
            description="Accuracy, thoroughness, and excellence of deliverables"
        ),
        ScoringComponent(
            "productivity", "Productivity", 15,
            description="Volume and efficiency of work output"
        ),
        ScoringComponent(
            "collaboration", "Collaboration", 15,
            description="Teamwork and cross-functional cooperation"
        ),
        ScoringComponent(
            "communication", "Communication", 10,
            description="Clarity and effectiveness of communication"
        ),
        ScoringComponent(
            "initiative", "Initiative", 10,
            description="Proactive problem-solving and improvement"
        ),
        ScoringComponent(
            "reliability", "Reliability", 5,
            description="Dependability and consistency"
        )
    ]
    return WorkforceScoringEngine(components)


def create_potential_engine() -> WorkforceScoringEngine:
    """Create employee potential assessment engine."""
    components = [
        ScoringComponent(
            "learning_agility", "Learning Agility", 25,
            description="Ability to learn quickly and adapt"
        ),
        ScoringComponent(
            "leadership_capability", "Leadership Capability", 20,
            description="Ability to lead and influence others"
        ),
        ScoringComponent(
            "strategic_thinking", "Strategic Thinking", 20,
            description="Big-picture perspective and planning ability"
        ),
        ScoringComponent(
            "emotional_intelligence", "Emotional Intelligence", 15,
            description="Self-awareness and relationship management"
        ),
        ScoringComponent(
            "drive_ambition", "Drive & Ambition", 10,
            description="Motivation and career aspiration"
        ),
        ScoringComponent(
            "adaptability", "Adaptability", 10,
            description="Flexibility in changing environments"
        )
    ]
    return WorkforceScoringEngine(components)


def create_engagement_scoring_engine() -> WorkforceScoringEngine:
    """Create employee engagement scoring engine."""
    components = [
        ScoringComponent(
            "job_satisfaction", "Job Satisfaction", 20,
            description="Satisfaction with role and responsibilities"
        ),
        ScoringComponent(
            "manager_relationship", "Manager Relationship", 20,
            description="Quality of relationship with direct manager"
        ),
        ScoringComponent(
            "growth_opportunity", "Growth Opportunity", 15,
            description="Perceived career growth opportunities"
        ),
        ScoringComponent(
            "work_life_balance", "Work-Life Balance", 15,
            description="Balance between work and personal life"
        ),
        ScoringComponent(
            "recognition", "Recognition", 10,
            description="Feeling valued and recognized"
        ),
        ScoringComponent(
            "company_alignment", "Company Alignment", 10,
            description="Alignment with company mission and values"
        ),
        ScoringComponent(
            "team_connection", "Team Connection", 10,
            description="Connection with colleagues and team"
        )
    ]
    return WorkforceScoringEngine(components)
