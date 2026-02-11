"""
Workday API Client for Talent Intelligence

Provides access to:
- Human Capital Management (HCM) data
- Recruiting (ATS)
- Learning Management
- Compensation
- Talent Management
- Workforce Analytics
"""

import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class WorkerType(Enum):
    EMPLOYEE = "employee"
    CONTINGENT = "contingent"
    INTERN = "intern"


class RequisitionStatus(Enum):
    OPEN = "open"
    FILLED = "filled"
    CLOSED = "closed"
    ON_HOLD = "on_hold"


@dataclass
class WorkdayConfig:
    """Configuration for Workday API connection."""
    tenant_url: str  # e.g., https://impl.workday.com/acme
    client_id: str
    client_secret: str
    refresh_token: Optional[str] = None

    @property
    def base_url(self) -> str:
        return f"{self.tenant_url}/api/v1"

    @property
    def token_url(self) -> str:
        return f"{self.tenant_url}/oauth2/token"


@dataclass
class Worker:
    """Represents a Workday worker (employee or contingent)."""
    id: str
    worker_id: str  # Employee ID
    first_name: str
    last_name: str
    email: str
    worker_type: WorkerType
    supervisory_organization: Optional[str] = None
    job_profile: Optional[str] = None
    business_title: Optional[str] = None
    location: Optional[str] = None
    hire_date: Optional[datetime] = None
    termination_date: Optional[datetime] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    cost_center: Optional[str] = None
    pay_group: Optional[str] = None
    compensation_grade: Optional[str] = None
    annual_salary: Optional[float] = None
    is_active: bool = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def tenure_years(self) -> Optional[float]:
        if self.hire_date:
            days = (datetime.now() - self.hire_date).days
            return round(days / 365.25, 1)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'worker_id': self.worker_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'worker_type': self.worker_type.value,
            'supervisory_organization': self.supervisory_organization,
            'job_profile': self.job_profile,
            'business_title': self.business_title,
            'location': self.location,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'manager_name': self.manager_name,
            'cost_center': self.cost_center,
            'tenure_years': self.tenure_years,
            'is_active': self.is_active
        }


@dataclass
class JobRequisition:
    """Represents a job requisition."""
    id: str
    requisition_id: str
    job_title: str
    supervisory_organization: str
    status: RequisitionStatus
    target_hire_date: Optional[datetime] = None
    open_date: Optional[datetime] = None
    hiring_manager: Optional[str] = None
    location: Optional[str] = None
    job_family: Optional[str] = None
    candidates_count: int = 0
    interviews_scheduled: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'requisition_id': self.requisition_id,
            'job_title': self.job_title,
            'supervisory_organization': self.supervisory_organization,
            'status': self.status.value,
            'target_hire_date': self.target_hire_date.isoformat() if self.target_hire_date else None,
            'open_date': self.open_date.isoformat() if self.open_date else None,
            'hiring_manager': self.hiring_manager,
            'location': self.location,
            'candidates_count': self.candidates_count
        }


@dataclass
class LearningEnrollment:
    """Represents a learning enrollment."""
    id: str
    worker_id: str
    worker_name: str
    course_name: str
    course_type: str  # required, recommended, elective
    status: str  # enrolled, in_progress, completed, overdue
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'worker_id': self.worker_id,
            'worker_name': self.worker_name,
            'course_name': self.course_name,
            'course_type': self.course_type,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'score': self.score
        }


@dataclass
class GoalProgress:
    """Represents goal tracking."""
    id: str
    worker_id: str
    worker_name: str
    goal_title: str
    category: str  # performance, development, career
    status: str  # not_started, in_progress, completed, cancelled
    progress_percent: int
    due_date: Optional[datetime] = None
    created_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'worker_id': self.worker_id,
            'worker_name': self.worker_name,
            'goal_title': self.goal_title,
            'category': self.category,
            'status': self.status,
            'progress_percent': self.progress_percent,
            'due_date': self.due_date.isoformat() if self.due_date else None
        }


@dataclass
class WorkforceAnalytics:
    """Workforce analytics summary."""
    date: datetime
    total_headcount: int
    fte_count: float
    contractor_count: int
    voluntary_turnover_rate: float
    involuntary_turnover_rate: float
    time_to_fill_avg_days: float
    offer_acceptance_rate: float
    diversity_metrics: Dict[str, float]
    headcount_by_org: Dict[str, int]
    headcount_by_location: Dict[str, int]
    tenure_distribution: Dict[str, int]
    open_positions: int
    positions_filled_ytd: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'total_headcount': self.total_headcount,
            'fte_count': self.fte_count,
            'contractor_count': self.contractor_count,
            'voluntary_turnover_rate': self.voluntary_turnover_rate,
            'involuntary_turnover_rate': self.involuntary_turnover_rate,
            'total_turnover_rate': self.voluntary_turnover_rate + self.involuntary_turnover_rate,
            'time_to_fill_avg_days': self.time_to_fill_avg_days,
            'offer_acceptance_rate': self.offer_acceptance_rate,
            'diversity_metrics': self.diversity_metrics,
            'headcount_by_org': self.headcount_by_org,
            'headcount_by_location': self.headcount_by_location,
            'tenure_distribution': self.tenure_distribution,
            'open_positions': self.open_positions,
            'positions_filled_ytd': self.positions_filled_ytd
        }


@dataclass
class CompensationReport:
    """Compensation analysis."""
    date: datetime
    total_payroll: float
    avg_salary: float
    median_salary: float
    salary_by_org: Dict[str, float]
    salary_by_grade: Dict[str, float]
    compa_ratio_avg: float  # Ratio of actual pay to midpoint
    pay_equity_gap: float  # Percent difference
    bonus_pool_used: float
    merit_increase_avg: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'total_payroll': self.total_payroll,
            'avg_salary': self.avg_salary,
            'median_salary': self.median_salary,
            'salary_by_org': self.salary_by_org,
            'salary_by_grade': self.salary_by_grade,
            'compa_ratio_avg': self.compa_ratio_avg,
            'pay_equity_gap': self.pay_equity_gap,
            'bonus_pool_used': self.bonus_pool_used,
            'merit_increase_avg': self.merit_increase_avg
        }


class WorkdayClient:
    """Client for Workday REST API."""

    def __init__(self, config: WorkdayConfig):
        self.config = config
        self._access_token = None
        self._token_expiry = None
        self._session = None

    def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        import requests

        data = {
            'grant_type': 'refresh_token',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'refresh_token': self.config.refresh_token
        }

        response = requests.post(self.config.token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data['access_token']
        self._token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600) - 60)

        return self._access_token

    def _get_session(self):
        """Get requests session with auth."""
        if self._session is None:
            import requests
            self._session = requests.Session()

        token = self._get_access_token()
        self._session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return self._session

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        session = self._get_session()
        url = f"{self.config.base_url}{endpoint}"

        response = session.request(method, url, **kwargs)
        response.raise_for_status()

        if response.content:
            return response.json()
        return {}

    def get_workers(self, include_terminated: bool = False) -> List[Worker]:
        """Get worker data."""
        params = {'includeTerminated': str(include_terminated).lower()}
        data = self._request('GET', '/workers', params=params)
        workers = []

        for w in data.get('data', []):
            hire_date = None
            if w.get('hireDate'):
                try:
                    hire_date = datetime.fromisoformat(w['hireDate'].replace('Z', '+00:00'))
                except:
                    pass

            workers.append(Worker(
                id=w.get('id', ''),
                worker_id=w.get('employeeId', ''),
                first_name=w.get('firstName', ''),
                last_name=w.get('lastName', ''),
                email=w.get('workEmail', ''),
                worker_type=WorkerType.EMPLOYEE,
                supervisory_organization=w.get('supervisoryOrganization'),
                job_profile=w.get('jobProfile'),
                business_title=w.get('businessTitle'),
                location=w.get('location'),
                hire_date=hire_date,
                manager_name=w.get('manager'),
                cost_center=w.get('costCenter'),
                is_active=w.get('isActive', True)
            ))

        return workers

    def get_job_requisitions(self, status: Optional[RequisitionStatus] = None) -> List[JobRequisition]:
        """Get job requisitions."""
        params = {}
        if status:
            params['status'] = status.value

        data = self._request('GET', '/recruiting/requisitions', params=params)
        requisitions = []

        for r in data.get('data', []):
            open_date = None
            if r.get('openDate'):
                try:
                    open_date = datetime.fromisoformat(r['openDate'].replace('Z', '+00:00'))
                except:
                    pass

            requisitions.append(JobRequisition(
                id=r.get('id', ''),
                requisition_id=r.get('requisitionId', ''),
                job_title=r.get('jobTitle', ''),
                supervisory_organization=r.get('supervisoryOrganization', ''),
                status=RequisitionStatus(r.get('status', 'open')),
                open_date=open_date,
                hiring_manager=r.get('hiringManager'),
                location=r.get('location'),
                candidates_count=r.get('candidatesCount', 0)
            ))

        return requisitions

    def get_workforce_analytics(self) -> WorkforceAnalytics:
        """Get workforce analytics."""
        data = self._request('GET', '/analytics/workforce')

        return WorkforceAnalytics(
            date=datetime.now(),
            total_headcount=data.get('totalHeadcount', 0),
            fte_count=data.get('fteCount', 0),
            contractor_count=data.get('contractorCount', 0),
            voluntary_turnover_rate=data.get('voluntaryTurnoverRate', 0),
            involuntary_turnover_rate=data.get('involuntaryTurnoverRate', 0),
            time_to_fill_avg_days=data.get('timeToFillAvgDays', 0),
            offer_acceptance_rate=data.get('offerAcceptanceRate', 0),
            diversity_metrics=data.get('diversityMetrics', {}),
            headcount_by_org=data.get('headcountByOrg', {}),
            headcount_by_location=data.get('headcountByLocation', {}),
            tenure_distribution=data.get('tenureDistribution', {}),
            open_positions=data.get('openPositions', 0),
            positions_filled_ytd=data.get('positionsFilledYTD', 0)
        )


class WorkdayDemoClient:
    """Demo client with realistic mock data."""

    def __init__(self):
        self._workers = self._generate_mock_workers()
        self._requisitions = self._generate_mock_requisitions()

    def _generate_mock_workers(self) -> List[Worker]:
        """Generate realistic worker data."""
        workers = [
            Worker(
                id='WD001', worker_id='EMP001', first_name='Alexandra', last_name='Patel',
                email='apatel@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Engineering', job_profile='Senior Software Engineer',
                business_title='Senior Software Engineer', location='San Francisco',
                hire_date=datetime(2019, 6, 15), manager_name='John Smith',
                cost_center='CC001', compensation_grade='L5', annual_salary=165000, is_active=True
            ),
            Worker(
                id='WD002', worker_id='EMP002', first_name='Marcus', last_name='Johnson',
                email='mjohnson@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Sales', job_profile='Account Executive',
                business_title='Senior Account Executive', location='New York',
                hire_date=datetime(2020, 3, 1), manager_name='Emily Williams',
                cost_center='CC002', compensation_grade='L4', annual_salary=120000, is_active=True
            ),
            Worker(
                id='WD003', worker_id='EMP003', first_name='Priya', last_name='Sharma',
                email='psharma@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Product', job_profile='Product Manager',
                business_title='Senior Product Manager', location='Seattle',
                hire_date=datetime(2018, 9, 20), manager_name='Sarah Chen',
                cost_center='CC003', compensation_grade='L5', annual_salary=155000, is_active=True
            ),
            Worker(
                id='WD004', worker_id='EMP004', first_name='James', last_name='O\'Brien',
                email='jobrien@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Engineering', job_profile='Engineering Manager',
                business_title='Engineering Manager', location='Austin',
                hire_date=datetime(2017, 4, 10), manager_name='John Smith',
                cost_center='CC001', compensation_grade='L6', annual_salary=195000, is_active=True
            ),
            Worker(
                id='WD005', worker_id='EMP005', first_name='Yuki', last_name='Tanaka',
                email='ytanaka@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Finance', job_profile='Financial Analyst',
                business_title='Senior Financial Analyst', location='New York',
                hire_date=datetime(2021, 1, 18), manager_name='Robert Taylor',
                cost_center='CC004', compensation_grade='L4', annual_salary=105000, is_active=True
            ),
            Worker(
                id='WD006', worker_id='EMP006', first_name='Carlos', last_name='Rivera',
                email='crivera@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Marketing', job_profile='Marketing Manager',
                business_title='Marketing Manager', location='Miami',
                hire_date=datetime(2020, 7, 6), manager_name='Lisa Anderson',
                cost_center='CC005', compensation_grade='L5', annual_salary=125000, is_active=True
            ),
            Worker(
                id='WD007', worker_id='CTG001', first_name='Alex', last_name='Morgan',
                email='amorgan@contractor.com', worker_type=WorkerType.CONTINGENT,
                supervisory_organization='Engineering', job_profile='Software Consultant',
                business_title='Software Consultant', location='Remote',
                hire_date=datetime(2024, 1, 2), manager_name='James O\'Brien',
                cost_center='CC001', is_active=True
            ),
            Worker(
                id='WD008', worker_id='EMP007', first_name='Fatima', last_name='Hassan',
                email='fhassan@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='HR', job_profile='HR Business Partner',
                business_title='Senior HR Business Partner', location='Chicago',
                hire_date=datetime(2019, 11, 11), manager_name='Jennifer Martinez',
                cost_center='CC006', compensation_grade='L5', annual_salary=115000, is_active=True
            ),
            Worker(
                id='WD009', worker_id='EMP008', first_name='David', last_name='Lee',
                email='dlee@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Operations', job_profile='Operations Analyst',
                business_title='Operations Analyst', location='Austin',
                hire_date=datetime(2022, 5, 23), manager_name='Christopher Lee',
                cost_center='CC007', compensation_grade='L3', annual_salary=85000, is_active=True
            ),
            Worker(
                id='WD010', worker_id='INT001', first_name='Jordan', last_name='Williams',
                email='jwilliams@company.com', worker_type=WorkerType.INTERN,
                supervisory_organization='Engineering', job_profile='Software Engineering Intern',
                business_title='Software Engineering Intern', location='San Francisco',
                hire_date=datetime(2024, 6, 1), manager_name='Alexandra Patel',
                cost_center='CC001', is_active=True
            ),
            Worker(
                id='WD011', worker_id='EMP009', first_name='Michelle', last_name='Kim',
                email='mkim@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Engineering', job_profile='Data Scientist',
                business_title='Senior Data Scientist', location='Seattle',
                hire_date=datetime(2021, 8, 16), manager_name='James O\'Brien',
                cost_center='CC001', compensation_grade='L5', annual_salary=170000, is_active=True
            ),
            Worker(
                id='WD012', worker_id='EMP010', first_name='Thomas', last_name='Anderson',
                email='tanderson@company.com', worker_type=WorkerType.EMPLOYEE,
                supervisory_organization='Sales', job_profile='Sales Development Rep',
                business_title='Sales Development Representative', location='Denver',
                hire_date=datetime(2023, 9, 5), manager_name='Marcus Johnson',
                cost_center='CC002', compensation_grade='L2', annual_salary=65000, is_active=True
            ),
        ]
        return workers

    def _generate_mock_requisitions(self) -> List[JobRequisition]:
        """Generate mock job requisitions."""
        now = datetime.now()
        return [
            JobRequisition(
                id='REQ001', requisition_id='R-2024-001', job_title='Staff Software Engineer',
                supervisory_organization='Engineering', status=RequisitionStatus.OPEN,
                target_hire_date=now + timedelta(days=45), open_date=now - timedelta(days=20),
                hiring_manager='James O\'Brien', location='San Francisco',
                job_family='Engineering', candidates_count=24, interviews_scheduled=5
            ),
            JobRequisition(
                id='REQ002', requisition_id='R-2024-002', job_title='Product Designer',
                supervisory_organization='Product', status=RequisitionStatus.OPEN,
                target_hire_date=now + timedelta(days=30), open_date=now - timedelta(days=15),
                hiring_manager='Sarah Chen', location='Remote',
                job_family='Design', candidates_count=42, interviews_scheduled=8
            ),
            JobRequisition(
                id='REQ003', requisition_id='R-2024-003', job_title='Enterprise Account Executive',
                supervisory_organization='Sales', status=RequisitionStatus.OPEN,
                target_hire_date=now + timedelta(days=60), open_date=now - timedelta(days=10),
                hiring_manager='Emily Williams', location='New York',
                job_family='Sales', candidates_count=18, interviews_scheduled=3
            ),
            JobRequisition(
                id='REQ004', requisition_id='R-2024-004', job_title='DevOps Engineer',
                supervisory_organization='Engineering', status=RequisitionStatus.OPEN,
                target_hire_date=now + timedelta(days=40), open_date=now - timedelta(days=25),
                hiring_manager='John Smith', location='Austin',
                job_family='Engineering', candidates_count=15, interviews_scheduled=4
            ),
            JobRequisition(
                id='REQ005', requisition_id='R-2023-089', job_title='Marketing Analyst',
                supervisory_organization='Marketing', status=RequisitionStatus.FILLED,
                open_date=now - timedelta(days=60), hiring_manager='Lisa Anderson',
                location='Miami', job_family='Marketing', candidates_count=30
            ),
        ]

    def get_workers(self, include_terminated: bool = False) -> List[Worker]:
        if include_terminated:
            return self._workers
        return [w for w in self._workers if w.is_active]

    def get_job_requisitions(self, status: Optional[RequisitionStatus] = None) -> List[JobRequisition]:
        if status:
            return [r for r in self._requisitions if r.status == status]
        return self._requisitions

    def get_learning_enrollments(self, status: Optional[str] = None) -> List[LearningEnrollment]:
        """Get mock learning enrollments."""
        now = datetime.now()
        enrollments = [
            LearningEnrollment(
                id='LE001', worker_id='WD001', worker_name='Alexandra Patel',
                course_name='Leadership Essentials', course_type='required',
                status='completed', completion_date=now - timedelta(days=30), score=95
            ),
            LearningEnrollment(
                id='LE002', worker_id='WD002', worker_name='Marcus Johnson',
                course_name='Sales Negotiation Mastery', course_type='required',
                status='in_progress', due_date=now + timedelta(days=14)
            ),
            LearningEnrollment(
                id='LE003', worker_id='WD004', worker_name='James O\'Brien',
                course_name='Management 301: Advanced People Leadership', course_type='required',
                status='completed', completion_date=now - timedelta(days=60), score=88
            ),
            LearningEnrollment(
                id='LE004', worker_id='WD005', worker_name='Yuki Tanaka',
                course_name='Security Awareness Training', course_type='required',
                status='overdue', due_date=now - timedelta(days=7)
            ),
            LearningEnrollment(
                id='LE005', worker_id='WD006', worker_name='Carlos Rivera',
                course_name='Digital Marketing Trends 2024', course_type='elective',
                status='completed', completion_date=now - timedelta(days=15), score=92
            ),
            LearningEnrollment(
                id='LE006', worker_id='WD009', worker_name='David Lee',
                course_name='Data Analysis Fundamentals', course_type='recommended',
                status='enrolled', due_date=now + timedelta(days=30)
            ),
        ]
        if status:
            return [e for e in enrollments if e.status == status]
        return enrollments

    def get_goal_progress(self) -> List[GoalProgress]:
        """Get mock goal progress."""
        now = datetime.now()
        return [
            GoalProgress(
                id='G001', worker_id='WD001', worker_name='Alexandra Patel',
                goal_title='Lead cloud migration project', category='performance',
                status='in_progress', progress_percent=75, due_date=now + timedelta(days=60)
            ),
            GoalProgress(
                id='G002', worker_id='WD002', worker_name='Marcus Johnson',
                goal_title='Achieve $2M in new bookings', category='performance',
                status='in_progress', progress_percent=82, due_date=now + timedelta(days=90)
            ),
            GoalProgress(
                id='G003', worker_id='WD003', worker_name='Priya Sharma',
                goal_title='Launch new mobile app features', category='performance',
                status='completed', progress_percent=100, due_date=now - timedelta(days=10)
            ),
            GoalProgress(
                id='G004', worker_id='WD004', worker_name='James O\'Brien',
                goal_title='Hire 5 senior engineers', category='performance',
                status='in_progress', progress_percent=60, due_date=now + timedelta(days=45)
            ),
            GoalProgress(
                id='G005', worker_id='WD006', worker_name='Carlos Rivera',
                goal_title='Complete product marketing certification', category='development',
                status='in_progress', progress_percent=40, due_date=now + timedelta(days=120)
            ),
        ]

    def get_workforce_analytics(self) -> WorkforceAnalytics:
        """Get mock workforce analytics."""
        employees = [w for w in self._workers if w.worker_type == WorkerType.EMPLOYEE]
        contractors = [w for w in self._workers if w.worker_type == WorkerType.CONTINGENT]
        interns = [w for w in self._workers if w.worker_type == WorkerType.INTERN]

        # Calculate headcount by org
        by_org = {}
        for w in self._workers:
            org = w.supervisory_organization or 'Unknown'
            by_org[org] = by_org.get(org, 0) + 1

        # Calculate headcount by location
        by_location = {}
        for w in self._workers:
            loc = w.location or 'Unknown'
            by_location[loc] = by_location.get(loc, 0) + 1

        # Calculate tenure distribution
        tenure_dist = {'< 1 year': 0, '1-2 years': 0, '2-5 years': 0, '5+ years': 0}
        for w in employees:
            years = w.tenure_years or 0
            if years < 1:
                tenure_dist['< 1 year'] += 1
            elif years < 2:
                tenure_dist['1-2 years'] += 1
            elif years < 5:
                tenure_dist['2-5 years'] += 1
            else:
                tenure_dist['5+ years'] += 1

        open_reqs = len([r for r in self._requisitions if r.status == RequisitionStatus.OPEN])

        return WorkforceAnalytics(
            date=datetime.now(),
            total_headcount=len(self._workers),
            fte_count=len(employees) + 0.5 * len(interns),
            contractor_count=len(contractors),
            voluntary_turnover_rate=8.5,
            involuntary_turnover_rate=2.1,
            time_to_fill_avg_days=42,
            offer_acceptance_rate=87.5,
            diversity_metrics={
                'gender_female': 42.0,
                'gender_male': 56.0,
                'gender_non_binary': 2.0,
                'ethnicity_white': 45.0,
                'ethnicity_asian': 28.0,
                'ethnicity_hispanic': 15.0,
                'ethnicity_black': 8.0,
                'ethnicity_other': 4.0
            },
            headcount_by_org=by_org,
            headcount_by_location=by_location,
            tenure_distribution=tenure_dist,
            open_positions=open_reqs,
            positions_filled_ytd=23
        )

    def get_compensation_report(self) -> CompensationReport:
        """Get mock compensation report."""
        employees = [w for w in self._workers if w.worker_type == WorkerType.EMPLOYEE and w.annual_salary]
        salaries = [w.annual_salary for w in employees if w.annual_salary]

        salary_by_org = {}
        for w in employees:
            if w.annual_salary:
                org = w.supervisory_organization or 'Unknown'
                if org not in salary_by_org:
                    salary_by_org[org] = []
                salary_by_org[org].append(w.annual_salary)

        # Calculate averages by org
        for org in salary_by_org:
            salary_by_org[org] = round(sum(salary_by_org[org]) / len(salary_by_org[org]))

        return CompensationReport(
            date=datetime.now(),
            total_payroll=sum(salaries) if salaries else 0,
            avg_salary=round(sum(salaries) / len(salaries)) if salaries else 0,
            median_salary=sorted(salaries)[len(salaries) // 2] if salaries else 0,
            salary_by_org=salary_by_org,
            salary_by_grade={
                'L2': 65000,
                'L3': 85000,
                'L4': 112500,
                'L5': 152500,
                'L6': 195000
            },
            compa_ratio_avg=1.02,
            pay_equity_gap=3.2,
            bonus_pool_used=78.5,
            merit_increase_avg=4.2
        )


def create_workday_client(demo_mode: bool = False) -> WorkdayClient:
    """Factory function to create Workday client."""
    if demo_mode:
        return WorkdayDemoClient()

    tenant_url = os.getenv('WORKDAY_TENANT_URL')
    client_id = os.getenv('WORKDAY_CLIENT_ID')
    client_secret = os.getenv('WORKDAY_CLIENT_SECRET')
    refresh_token = os.getenv('WORKDAY_REFRESH_TOKEN')

    if not all([tenant_url, client_id, client_secret]):
        raise ValueError("WORKDAY_TENANT_URL, WORKDAY_CLIENT_ID, and WORKDAY_CLIENT_SECRET must be set")

    config = WorkdayConfig(
        tenant_url=tenant_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token
    )
    return WorkdayClient(config)
