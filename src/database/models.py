"""Database Models - Talent Intelligence"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from typing import Dict, Any, List
import uuid
import json

db = SQLAlchemy()

def generate_uuid() -> str:
    return str(uuid.uuid4())


class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    size_category = db.Column(db.String(50))
    total_headcount = db.Column(db.Integer)

    # HR Metrics
    turnover_rate = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    diversity_score = db.Column(db.Float)
    bench_strength = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employees = db.relationship('Employee', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    departments = db.relationship('Department', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    hr_metrics = db.relationship('HRMetrics', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='organization', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'name': self.name, 'industry': self.industry,
            'total_headcount': self.total_headcount, 'turnover_rate': self.turnover_rate,
            'engagement_score': self.engagement_score, 'diversity_score': self.diversity_score,
            'bench_strength': self.bench_strength
        }


class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    organization_id = db.Column(db.String(36), db.ForeignKey('organization.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    manager_id = db.Column(db.String(36))
    headcount = db.Column(db.Integer)
    budget = db.Column(db.Float)
    turnover_rate = db.Column(db.Float)
    engagement_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employees = db.relationship('Employee', backref='department', lazy='dynamic')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'name': self.name, 'headcount': self.headcount,
            'turnover_rate': self.turnover_rate, 'engagement_score': self.engagement_score
        }


class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    organization_id = db.Column(db.String(36), db.ForeignKey('organization.id'), nullable=False)
    department_id = db.Column(db.String(36), db.ForeignKey('department.id'))

    # Basic Info
    employee_number = db.Column(db.String(50))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(200))
    job_title = db.Column(db.String(200))
    job_level = db.Column(db.String(50))
    manager_id = db.Column(db.String(36))

    # Employment
    hire_date = db.Column(db.Date)
    termination_date = db.Column(db.Date)
    employment_status = db.Column(db.String(20), default='Active')
    employment_type = db.Column(db.String(20))  # Full-time, Part-time, Contractor

    # Compensation
    base_salary = db.Column(db.Float)
    target_bonus = db.Column(db.Float)
    compa_ratio = db.Column(db.Float)

    # Demographics
    gender = db.Column(db.String(50))
    ethnicity = db.Column(db.String(100))
    age_group = db.Column(db.String(20))

    # Performance & Potential
    performance_rating = db.Column(db.String(50))
    potential_rating = db.Column(db.String(50))
    talent_category = db.Column(db.String(50))
    flight_risk = db.Column(db.String(20))

    # Engagement
    engagement_score = db.Column(db.Float)
    last_survey_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reviews = db.relationship('PerformanceReview', backref='employee', lazy='dynamic')

    @property
    def tenure_months(self) -> int:
        if not self.hire_date:
            return 0
        end = self.termination_date or date.today()
        return (end.year - self.hire_date.year) * 12 + (end.month - self.hire_date.month)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'first_name': self.first_name, 'last_name': self.last_name,
            'job_title': self.job_title, 'department_id': self.department_id,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'employment_status': self.employment_status, 'performance_rating': self.performance_rating,
            'potential_rating': self.potential_rating, 'talent_category': self.talent_category,
            'flight_risk': self.flight_risk, 'engagement_score': self.engagement_score,
            'tenure_months': self.tenure_months
        }


class PerformanceReview(db.Model):
    __tablename__ = 'performance_review'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    employee_id = db.Column(db.String(36), db.ForeignKey('employee.id'), nullable=False)
    review_period = db.Column(db.String(50))
    review_date = db.Column(db.Date)

    overall_rating = db.Column(db.String(50))
    goal_achievement = db.Column(db.Float)
    competency_scores = db.Column(db.Text)  # JSON
    strengths = db.Column(db.Text)  # JSON array
    development_areas = db.Column(db.Text)  # JSON array
    manager_comments = db.Column(db.Text)

    def set_competencies(self, scores: Dict[str, float]):
        self.competency_scores = json.dumps(scores)

    def get_competencies(self) -> Dict[str, float]:
        return json.loads(self.competency_scores) if self.competency_scores else {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'employee_id': self.employee_id, 'review_period': self.review_period,
            'overall_rating': self.overall_rating, 'goal_achievement': self.goal_achievement,
            'competency_scores': self.get_competencies()
        }


class HRMetrics(db.Model):
    __tablename__ = 'hr_metrics'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    organization_id = db.Column(db.String(36), db.ForeignKey('organization.id'), nullable=False)
    period_date = db.Column(db.Date, nullable=False)
    period_label = db.Column(db.String(50))

    # Headcount
    total_headcount = db.Column(db.Integer)
    new_hires = db.Column(db.Integer)
    terminations = db.Column(db.Integer)

    # Turnover
    turnover_rate = db.Column(db.Float)
    voluntary_turnover = db.Column(db.Float)
    involuntary_turnover = db.Column(db.Float)
    high_performer_retention = db.Column(db.Float)

    # Recruitment
    time_to_fill = db.Column(db.Float)
    cost_per_hire = db.Column(db.Float)
    offer_acceptance_rate = db.Column(db.Float)

    # Engagement
    engagement_score = db.Column(db.Float)
    enps = db.Column(db.Float)

    # Performance
    goal_achievement_rate = db.Column(db.Float)

    # Compensation
    compa_ratio_avg = db.Column(db.Float)
    pay_equity_gap = db.Column(db.Float)

    # Diversity
    diversity_representation = db.Column(db.Float)
    diversity_leadership = db.Column(db.Float)

    # Development
    training_hours_avg = db.Column(db.Float)
    internal_promotion_rate = db.Column(db.Float)
    succession_coverage = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'period_date': self.period_date.isoformat() if self.period_date else None,
            'period_label': self.period_label, 'total_headcount': self.total_headcount,
            'turnover_rate': self.turnover_rate, 'engagement_score': self.engagement_score,
            'time_to_fill': self.time_to_fill, 'diversity_representation': self.diversity_representation
        }

    def get_kpi_values(self) -> Dict[str, float]:
        return {
            'turnover_rate': self.turnover_rate, 'voluntary_turnover': self.voluntary_turnover,
            'high_performer_retention': self.high_performer_retention, 'time_to_fill': self.time_to_fill,
            'cost_per_hire': self.cost_per_hire, 'offer_acceptance_rate': self.offer_acceptance_rate,
            'engagement_score': self.engagement_score, 'enps': self.enps,
            'goal_achievement': self.goal_achievement_rate, 'compa_ratio': self.compa_ratio_avg,
            'pay_equity_gap': self.pay_equity_gap, 'diversity_representation': self.diversity_representation,
            'diversity_leadership': self.diversity_leadership, 'training_hours': self.training_hours_avg,
            'internal_promotion_rate': self.internal_promotion_rate, 'succession_coverage': self.succession_coverage
        }


class ChatSession(db.Model):
    __tablename__ = 'chat_session'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    organization_id = db.Column(db.String(36), db.ForeignKey('organization.id'))
    conversation_mode = db.Column(db.String(50), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
