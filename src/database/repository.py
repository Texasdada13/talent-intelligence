"""Repository Pattern - Talent Intelligence"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy import desc
from .models import db, Organization, Employee, Department, HRMetrics, PerformanceReview, ChatSession, ChatMessage


class TalentRepository:
    """Repository for talent data access."""

    # Organization
    def create_organization(self, data: Dict[str, Any]) -> Organization:
        org = Organization(**{k: v for k, v in data.items() if hasattr(Organization, k)})
        db.session.add(org)
        db.session.commit()
        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        return Organization.query.get(org_id)

    def get_all_organizations(self) -> List[Organization]:
        return Organization.query.order_by(desc(Organization.created_at)).all()

    def update_organization(self, org_id: str, data: Dict[str, Any]) -> Optional[Organization]:
        org = Organization.query.get(org_id)
        if not org:
            return None
        for k, v in data.items():
            if hasattr(org, k) and k != 'id':
                setattr(org, k, v)
        db.session.commit()
        return org

    # Employee
    def create_employee(self, org_id: str, data: Dict[str, Any]) -> Employee:
        emp = Employee(organization_id=org_id, **{k: v for k, v in data.items() if hasattr(Employee, k) and k != 'organization_id'})
        db.session.add(emp)
        db.session.commit()
        return emp

    def get_employees(self, org_id: str, department_id: Optional[str] = None, status: str = 'Active') -> List[Employee]:
        query = Employee.query.filter_by(organization_id=org_id, employment_status=status)
        if department_id:
            query = query.filter_by(department_id=department_id)
        return query.order_by(Employee.last_name).all()

    def get_employee(self, emp_id: str) -> Optional[Employee]:
        return Employee.query.get(emp_id)

    def update_employee(self, emp_id: str, data: Dict[str, Any]) -> Optional[Employee]:
        emp = Employee.query.get(emp_id)
        if not emp:
            return None
        for k, v in data.items():
            if hasattr(emp, k) and k not in ['id', 'organization_id']:
                setattr(emp, k, v)
        db.session.commit()
        return emp

    # Department
    def create_department(self, org_id: str, data: Dict[str, Any]) -> Department:
        dept = Department(organization_id=org_id, **{k: v for k, v in data.items() if hasattr(Department, k) and k != 'organization_id'})
        db.session.add(dept)
        db.session.commit()
        return dept

    def get_departments(self, org_id: str) -> List[Department]:
        return Department.query.filter_by(organization_id=org_id).order_by(Department.name).all()

    # HR Metrics
    def create_hr_metrics(self, org_id: str, data: Dict[str, Any]) -> HRMetrics:
        if isinstance(data.get('period_date'), str):
            data['period_date'] = datetime.strptime(data['period_date'], '%Y-%m-%d').date()
        metrics = HRMetrics(organization_id=org_id, **{k: v for k, v in data.items() if hasattr(HRMetrics, k) and k != 'organization_id'})
        db.session.add(metrics)
        db.session.commit()
        return metrics

    def get_hr_metrics(self, org_id: str, limit: int = 12) -> List[HRMetrics]:
        return HRMetrics.query.filter_by(organization_id=org_id).order_by(desc(HRMetrics.period_date)).limit(limit).all()

    def get_latest_hr_metrics(self, org_id: str) -> Optional[HRMetrics]:
        return HRMetrics.query.filter_by(organization_id=org_id).order_by(desc(HRMetrics.period_date)).first()

    # Chat
    def create_chat_session(self, org_id: Optional[str] = None, mode: str = 'general') -> ChatSession:
        session = ChatSession(organization_id=org_id, conversation_mode=mode)
        db.session.add(session)
        db.session.commit()
        return session

    def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        return ChatSession.query.get(session_id)

    def add_chat_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.session.add(msg)
        db.session.commit()
        return msg

    def get_chat_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        return ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).limit(limit).all()

    # Analytics
    def get_headcount_by_department(self, org_id: str) -> Dict[str, int]:
        depts = self.get_departments(org_id)
        return {d.name: Employee.query.filter_by(department_id=d.id, employment_status='Active').count() for d in depts}

    def get_talent_distribution(self, org_id: str) -> Dict[str, int]:
        employees = self.get_employees(org_id)
        distribution = {}
        for emp in employees:
            cat = emp.talent_category or 'Unassessed'
            distribution[cat] = distribution.get(cat, 0) + 1
        return distribution

    def get_flight_risk_summary(self, org_id: str) -> Dict[str, int]:
        employees = self.get_employees(org_id)
        summary = {}
        for emp in employees:
            risk = emp.flight_risk or 'Unknown'
            summary[risk] = summary.get(risk, 0) + 1
        return summary
