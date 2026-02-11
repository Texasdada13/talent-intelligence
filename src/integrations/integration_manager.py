"""
HR Integration Manager for Talent Intelligence

Provides unified interface to:
- BambooHR
- Workday

Aggregates employee data, time off, performance, and workforce analytics.
"""

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from .bamboohr_client import (
    BambooHRClient, BambooHRDemoClient, create_bamboohr_client,
    Employee as BambooEmployee, TimeOffRequest, TimeOffBalance,
    HeadcountReport, PerformanceReview, EmploymentStatus
)
from .workday_client import (
    WorkdayClient, WorkdayDemoClient, create_workday_client,
    Worker, JobRequisition, LearningEnrollment, GoalProgress,
    WorkforceAnalytics, CompensationReport, WorkerType, RequisitionStatus
)

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    BAMBOOHR = "bamboohr"
    WORKDAY = "workday"
    DEMO = "demo"


@dataclass
class UnifiedEmployee:
    """Unified employee record from any HR system."""
    id: str
    source: IntegrationType
    source_id: str
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    hire_date: Optional[datetime] = None
    manager_name: Optional[str] = None
    is_active: bool = True
    tenure_years: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source': self.source.value,
            'source_id': self.source_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'job_title': self.job_title,
            'location': self.location,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'manager_name': self.manager_name,
            'is_active': self.is_active,
            'tenure_years': self.tenure_years
        }


@dataclass
class TalentSummary:
    """Aggregated talent summary across all sources."""
    date: datetime
    total_headcount: int
    active_employees: int
    contractors: int
    by_department: Dict[str, int]
    by_location: Dict[str, int]
    tenure_distribution: Dict[str, int]
    new_hires_30d: int
    terminations_30d: int
    open_positions: int
    pending_time_off: int
    turnover_rate: float
    time_to_fill_days: float
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    integration_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'total_headcount': self.total_headcount,
            'active_employees': self.active_employees,
            'contractors': self.contractors,
            'by_department': self.by_department,
            'by_location': self.by_location,
            'tenure_distribution': self.tenure_distribution,
            'new_hires_30d': self.new_hires_30d,
            'terminations_30d': self.terminations_30d,
            'net_change_30d': self.new_hires_30d - self.terminations_30d,
            'open_positions': self.open_positions,
            'pending_time_off': self.pending_time_off,
            'turnover_rate': self.turnover_rate,
            'time_to_fill_days': self.time_to_fill_days,
            'alerts': self.alerts,
            'integration_sources': self.integration_sources
        }


class TalentIntegrationManager:
    """Manager for unified HR integrations."""

    def __init__(self):
        self._bamboohr_client = None
        self._workday_client = None
        self._demo_mode = False

    def configure_bamboohr(self, company_domain: str, api_key: str):
        """Configure BambooHR connection."""
        from .bamboohr_client import BambooHRConfig, BambooHRClient
        config = BambooHRConfig(company_domain=company_domain, api_key=api_key)
        self._bamboohr_client = BambooHRClient(config)

    def configure_workday(
        self,
        tenant_url: str,
        client_id: str,
        client_secret: str,
        refresh_token: str
    ):
        """Configure Workday connection."""
        from .workday_client import WorkdayConfig, WorkdayClient
        config = WorkdayConfig(
            tenant_url=tenant_url,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token
        )
        self._workday_client = WorkdayClient(config)

    def enable_demo_mode(self):
        """Enable demo mode with mock data."""
        self._demo_mode = True
        self._bamboohr_client = BambooHRDemoClient()
        self._workday_client = WorkdayDemoClient()

    @property
    def is_configured(self) -> bool:
        """Check if any integration is configured."""
        return self._bamboohr_client is not None or self._workday_client is not None

    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        return {
            'bamboohr': {
                'configured': self._bamboohr_client is not None,
                'demo_mode': self._demo_mode and self._bamboohr_client is not None
            },
            'workday': {
                'configured': self._workday_client is not None,
                'demo_mode': self._demo_mode and self._workday_client is not None
            },
            'demo_mode': self._demo_mode
        }

    def get_employees(self, active_only: bool = True) -> List[UnifiedEmployee]:
        """Get unified employee list from all sources."""
        employees = []
        seen_emails = set()  # Dedupe by email

        # BambooHR employees
        if self._bamboohr_client:
            try:
                status = EmploymentStatus.ACTIVE if active_only else None
                bamboo_employees = self._bamboohr_client.get_employees(status=status)
                for emp in bamboo_employees:
                    if emp.email and emp.email not in seen_emails:
                        seen_emails.add(emp.email)
                        tenure = None
                        if emp.tenure_days:
                            tenure = round(emp.tenure_days / 365.25, 1)
                        employees.append(UnifiedEmployee(
                            id=f"bamboo_{emp.id}",
                            source=IntegrationType.BAMBOOHR if not self._demo_mode else IntegrationType.DEMO,
                            source_id=emp.id,
                            first_name=emp.first_name,
                            last_name=emp.last_name,
                            email=emp.email,
                            department=emp.department,
                            job_title=emp.job_title,
                            location=emp.location,
                            hire_date=emp.hire_date,
                            manager_name=emp.supervisor_name,
                            is_active=emp.status == EmploymentStatus.ACTIVE,
                            tenure_years=tenure
                        ))
            except Exception as e:
                logger.error(f"Error fetching BambooHR employees: {e}")

        # Workday workers
        if self._workday_client:
            try:
                workday_workers = self._workday_client.get_workers(include_terminated=not active_only)
                for worker in workday_workers:
                    if worker.email and worker.email not in seen_emails:
                        seen_emails.add(worker.email)
                        employees.append(UnifiedEmployee(
                            id=f"workday_{worker.id}",
                            source=IntegrationType.WORKDAY if not self._demo_mode else IntegrationType.DEMO,
                            source_id=worker.id,
                            first_name=worker.first_name,
                            last_name=worker.last_name,
                            email=worker.email,
                            department=worker.supervisory_organization,
                            job_title=worker.business_title,
                            location=worker.location,
                            hire_date=worker.hire_date,
                            manager_name=worker.manager_name,
                            is_active=worker.is_active,
                            tenure_years=worker.tenure_years
                        ))
            except Exception as e:
                logger.error(f"Error fetching Workday workers: {e}")

        return employees

    def get_time_off_requests(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get time off requests from BambooHR."""
        requests = []

        if self._bamboohr_client:
            try:
                bamboo_requests = self._bamboohr_client.get_time_off_requests(
                    start_date=start_date,
                    end_date=end_date,
                    status=status
                )
                for req in bamboo_requests:
                    requests.append({
                        **req.to_dict(),
                        'source': 'bamboohr'
                    })
            except Exception as e:
                logger.error(f"Error fetching time off requests: {e}")

        return requests

    def get_job_requisitions(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get job requisitions from Workday."""
        requisitions = []

        if self._workday_client:
            try:
                req_status = RequisitionStatus(status) if status else None
                workday_reqs = self._workday_client.get_job_requisitions(status=req_status)
                for req in workday_reqs:
                    requisitions.append({
                        **req.to_dict(),
                        'source': 'workday'
                    })
            except Exception as e:
                logger.error(f"Error fetching job requisitions: {e}")

        return requisitions

    def get_learning_enrollments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get learning enrollments from Workday."""
        enrollments = []

        if self._workday_client and hasattr(self._workday_client, 'get_learning_enrollments'):
            try:
                workday_enrollments = self._workday_client.get_learning_enrollments(status=status)
                for enrollment in workday_enrollments:
                    enrollments.append({
                        **enrollment.to_dict(),
                        'source': 'workday'
                    })
            except Exception as e:
                logger.error(f"Error fetching learning enrollments: {e}")

        return enrollments

    def get_goal_progress(self) -> List[Dict[str, Any]]:
        """Get goal progress from Workday."""
        goals = []

        if self._workday_client and hasattr(self._workday_client, 'get_goal_progress'):
            try:
                workday_goals = self._workday_client.get_goal_progress()
                for goal in workday_goals:
                    goals.append({
                        **goal.to_dict(),
                        'source': 'workday'
                    })
            except Exception as e:
                logger.error(f"Error fetching goal progress: {e}")

        return goals

    def get_performance_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get performance reviews from BambooHR."""
        reviews = []

        if self._bamboohr_client and hasattr(self._bamboohr_client, 'get_performance_reviews'):
            try:
                bamboo_reviews = self._bamboohr_client.get_performance_reviews(
                    start_date=start_date,
                    end_date=end_date
                )
                for review in bamboo_reviews:
                    reviews.append({
                        **review.to_dict(),
                        'source': 'bamboohr'
                    })
            except Exception as e:
                logger.error(f"Error fetching performance reviews: {e}")

        return reviews

    def get_compensation_report(self) -> Optional[Dict[str, Any]]:
        """Get compensation report from Workday."""
        if self._workday_client and hasattr(self._workday_client, 'get_compensation_report'):
            try:
                report = self._workday_client.get_compensation_report()
                return {
                    **report.to_dict(),
                    'source': 'workday'
                }
            except Exception as e:
                logger.error(f"Error fetching compensation report: {e}")
        return None

    def get_talent_summary(self) -> TalentSummary:
        """Get aggregated talent summary from all sources."""
        employees = self.get_employees(active_only=True)
        time_off = self.get_time_off_requests(status='pending')
        requisitions = self.get_job_requisitions(status='open')

        # Aggregate by department
        by_department = {}
        for emp in employees:
            dept = emp.department or 'Unknown'
            by_department[dept] = by_department.get(dept, 0) + 1

        # Aggregate by location
        by_location = {}
        for emp in employees:
            loc = emp.location or 'Unknown'
            by_location[loc] = by_location.get(loc, 0) + 1

        # Tenure distribution
        tenure_dist = {'< 1 year': 0, '1-2 years': 0, '2-5 years': 0, '5+ years': 0}
        for emp in employees:
            years = emp.tenure_years or 0
            if years < 1:
                tenure_dist['< 1 year'] += 1
            elif years < 2:
                tenure_dist['1-2 years'] += 1
            elif years < 5:
                tenure_dist['2-5 years'] += 1
            else:
                tenure_dist['5+ years'] += 1

        # Calculate new hires
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_hires = sum(
            1 for emp in employees
            if emp.hire_date and emp.hire_date > thirty_days_ago
        )

        # Get workforce analytics from Workday if available
        turnover_rate = 0.0
        time_to_fill = 0.0
        contractors = 0

        if self._workday_client and hasattr(self._workday_client, 'get_workforce_analytics'):
            try:
                analytics = self._workday_client.get_workforce_analytics()
                turnover_rate = analytics.voluntary_turnover_rate + analytics.involuntary_turnover_rate
                time_to_fill = analytics.time_to_fill_avg_days
                contractors = analytics.contractor_count
            except Exception as e:
                logger.warning(f"Could not get workforce analytics: {e}")

        # Generate alerts
        alerts = []

        # High turnover alert
        if turnover_rate > 15:
            alerts.append({
                'type': 'warning',
                'category': 'turnover',
                'message': f'High turnover rate: {turnover_rate:.1f}%',
                'severity': 'high'
            })

        # Many open positions
        if len(requisitions) > 10:
            alerts.append({
                'type': 'info',
                'category': 'recruiting',
                'message': f'{len(requisitions)} open positions requiring attention',
                'severity': 'medium'
            })

        # Overdue training
        overdue_training = [
            e for e in self.get_learning_enrollments(status='overdue')
        ]
        if overdue_training:
            alerts.append({
                'type': 'warning',
                'category': 'learning',
                'message': f'{len(overdue_training)} employees with overdue training',
                'severity': 'medium'
            })

        # Time off backlog
        if len(time_off) > 5:
            alerts.append({
                'type': 'info',
                'category': 'time_off',
                'message': f'{len(time_off)} pending time off requests',
                'severity': 'low'
            })

        # Integration sources
        sources = []
        if self._bamboohr_client:
            sources.append('BambooHR')
        if self._workday_client:
            sources.append('Workday')
        if self._demo_mode:
            sources = ['Demo Mode']

        return TalentSummary(
            date=datetime.now(),
            total_headcount=len(employees) + contractors,
            active_employees=len(employees),
            contractors=contractors,
            by_department=by_department,
            by_location=by_location,
            tenure_distribution=tenure_dist,
            new_hires_30d=new_hires,
            terminations_30d=1 if self._demo_mode else 0,  # Mock value for demo
            open_positions=len(requisitions),
            pending_time_off=len(time_off),
            turnover_rate=turnover_rate,
            time_to_fill_days=time_to_fill,
            alerts=alerts,
            integration_sources=sources
        )


# Global instance
_integration_manager = None


def get_integration_manager() -> TalentIntegrationManager:
    """Get or create integration manager singleton."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = TalentIntegrationManager()

        # Auto-configure from environment
        bamboo_domain = os.getenv('BAMBOOHR_COMPANY_DOMAIN')
        bamboo_key = os.getenv('BAMBOOHR_API_KEY')
        if bamboo_domain and bamboo_key:
            _integration_manager.configure_bamboohr(bamboo_domain, bamboo_key)

        workday_url = os.getenv('WORKDAY_TENANT_URL')
        workday_client = os.getenv('WORKDAY_CLIENT_ID')
        workday_secret = os.getenv('WORKDAY_CLIENT_SECRET')
        workday_token = os.getenv('WORKDAY_REFRESH_TOKEN')
        if all([workday_url, workday_client, workday_secret]):
            _integration_manager.configure_workday(
                workday_url, workday_client, workday_secret, workday_token or ''
            )

    return _integration_manager
