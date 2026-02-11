"""
BambooHR API Client for Talent Intelligence

Provides access to:
- Employee directory and profiles
- Time off requests and balances
- Performance reviews
- Compensation data
- Org chart and reporting relationships
"""

import os
import json
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class EmploymentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


@dataclass
class BambooHRConfig:
    """Configuration for BambooHR API connection."""
    company_domain: str  # Your company subdomain (e.g., 'acme' for acme.bamboohr.com)
    api_key: str

    @property
    def base_url(self) -> str:
        return f"https://api.bamboohr.com/api/gateway.php/{self.company_domain}/v1"


@dataclass
class Employee:
    """Represents a BambooHR employee."""
    id: str
    first_name: str
    last_name: str
    email: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    hire_date: Optional[datetime] = None
    status: EmploymentStatus = EmploymentStatus.ACTIVE
    supervisor_id: Optional[str] = None
    supervisor_name: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    salary: Optional[float] = None
    pay_rate: Optional[str] = None  # hourly, salary, etc.
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def tenure_days(self) -> Optional[int]:
        if self.hire_date:
            return (datetime.now() - self.hire_date).days
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'job_title': self.job_title,
            'location': self.location,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'status': self.status.value,
            'supervisor_id': self.supervisor_id,
            'supervisor_name': self.supervisor_name,
            'tenure_days': self.tenure_days,
            'custom_fields': self.custom_fields
        }


@dataclass
class TimeOffRequest:
    """Represents a time off request."""
    id: str
    employee_id: str
    employee_name: str
    type: str  # vacation, sick, personal, etc.
    start_date: datetime
    end_date: datetime
    amount: float  # days or hours
    status: str  # pending, approved, denied, cancelled
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'type': self.type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'amount': self.amount,
            'status': self.status,
            'notes': self.notes
        }


@dataclass
class TimeOffBalance:
    """Represents time off balance for an employee."""
    employee_id: str
    type: str
    balance: float
    used: float
    scheduled: float

    @property
    def available(self) -> float:
        return self.balance - self.used - self.scheduled

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_id': self.employee_id,
            'type': self.type,
            'balance': self.balance,
            'used': self.used,
            'scheduled': self.scheduled,
            'available': self.available
        }


@dataclass
class PerformanceReview:
    """Represents a performance review."""
    id: str
    employee_id: str
    employee_name: str
    reviewer_id: str
    reviewer_name: str
    review_date: datetime
    rating: Optional[float] = None  # e.g., 1-5 scale
    status: str = "completed"  # draft, pending, completed
    goals_met: Optional[int] = None
    total_goals: Optional[int] = None
    strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    comments: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'reviewer_name': self.reviewer_name,
            'review_date': self.review_date.isoformat(),
            'rating': self.rating,
            'status': self.status,
            'goals_met': self.goals_met,
            'total_goals': self.total_goals,
            'strengths': self.strengths,
            'areas_for_improvement': self.areas_for_improvement
        }


@dataclass
class HeadcountReport:
    """Headcount metrics by department/location."""
    date: datetime
    total_employees: int
    active_employees: int
    by_department: Dict[str, int]
    by_location: Dict[str, int]
    by_status: Dict[str, int]
    new_hires_30d: int = 0
    terminations_30d: int = 0

    @property
    def net_change_30d(self) -> int:
        return self.new_hires_30d - self.terminations_30d

    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date.isoformat(),
            'total_employees': self.total_employees,
            'active_employees': self.active_employees,
            'by_department': self.by_department,
            'by_location': self.by_location,
            'by_status': self.by_status,
            'new_hires_30d': self.new_hires_30d,
            'terminations_30d': self.terminations_30d,
            'net_change_30d': self.net_change_30d
        }


class BambooHRClient:
    """Client for BambooHR API."""

    def __init__(self, config: BambooHRConfig):
        self.config = config
        self._session = None

    def _get_session(self):
        """Get or create requests session with auth."""
        if self._session is None:
            import requests
            self._session = requests.Session()
            # BambooHR uses API key as username with 'x' as password
            auth_string = f"{self.config.api_key}:x"
            encoded = base64.b64encode(auth_string.encode()).decode()
            self._session.headers.update({
                'Authorization': f'Basic {encoded}',
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

    def get_employees(self, status: Optional[EmploymentStatus] = None) -> List[Employee]:
        """Get employee directory."""
        # BambooHR uses a report endpoint for employee data
        fields = [
            'id', 'firstName', 'lastName', 'displayName', 'email',
            'department', 'jobTitle', 'location', 'hireDate', 'status',
            'supervisorId', 'supervisor', 'workPhone', 'mobilePhone'
        ]

        data = self._request('GET', f"/employees/directory")
        employees = []

        for emp in data.get('employees', []):
            emp_status = EmploymentStatus.ACTIVE
            if emp.get('status') == 'Inactive':
                emp_status = EmploymentStatus.INACTIVE

            if status and emp_status != status:
                continue

            hire_date = None
            if emp.get('hireDate'):
                try:
                    hire_date = datetime.fromisoformat(emp['hireDate'])
                except:
                    pass

            employees.append(Employee(
                id=str(emp.get('id', '')),
                first_name=emp.get('firstName', ''),
                last_name=emp.get('lastName', ''),
                email=emp.get('workEmail', emp.get('email', '')),
                department=emp.get('department'),
                job_title=emp.get('jobTitle'),
                location=emp.get('location'),
                hire_date=hire_date,
                status=emp_status,
                supervisor_id=emp.get('supervisorId'),
                supervisor_name=emp.get('supervisor'),
                work_phone=emp.get('workPhone'),
                mobile_phone=emp.get('mobilePhone')
            ))

        return employees

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Get single employee details."""
        data = self._request('GET', f"/employees/{employee_id}?fields=all")

        if not data:
            return None

        hire_date = None
        if data.get('hireDate'):
            try:
                hire_date = datetime.fromisoformat(data['hireDate'])
            except:
                pass

        return Employee(
            id=str(data.get('id', '')),
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('workEmail', data.get('email', '')),
            department=data.get('department'),
            job_title=data.get('jobTitle'),
            location=data.get('location'),
            hire_date=hire_date,
            status=EmploymentStatus.ACTIVE,
            supervisor_id=data.get('supervisorId'),
            supervisor_name=data.get('supervisor'),
            salary=float(data['payRate']) if data.get('payRate') else None,
            custom_fields=data.get('customFields', {})
        )

    def get_time_off_requests(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[TimeOffRequest]:
        """Get time off requests."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now() + timedelta(days=90)

        params = {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
        if status:
            params['status'] = status

        data = self._request('GET', '/time_off/requests/', params=params)
        requests_list = []

        for req in data.get('requests', []):
            try:
                requests_list.append(TimeOffRequest(
                    id=str(req.get('id', '')),
                    employee_id=str(req.get('employeeId', '')),
                    employee_name=req.get('name', ''),
                    type=req.get('type', {}).get('name', 'Time Off'),
                    start_date=datetime.fromisoformat(req['start']),
                    end_date=datetime.fromisoformat(req['end']),
                    amount=float(req.get('amount', {}).get('amount', 0)),
                    status=req.get('status', {}).get('status', 'pending'),
                    notes=req.get('notes')
                ))
            except Exception as e:
                logger.warning(f"Error parsing time off request: {e}")

        return requests_list

    def get_time_off_balances(self, employee_id: str) -> List[TimeOffBalance]:
        """Get time off balances for an employee."""
        data = self._request('GET', f'/employees/{employee_id}/time_off/calculator')
        balances = []

        for balance in data.get('timeOffTypes', []):
            balances.append(TimeOffBalance(
                employee_id=employee_id,
                type=balance.get('name', 'Time Off'),
                balance=float(balance.get('balance', 0)),
                used=float(balance.get('usedBalance', 0)),
                scheduled=float(balance.get('scheduledBalance', 0))
            ))

        return balances

    def get_headcount_report(self) -> HeadcountReport:
        """Generate headcount report."""
        employees = self.get_employees()

        by_department = {}
        by_location = {}
        by_status = {}
        active_count = 0

        for emp in employees:
            # By department
            dept = emp.department or 'Unknown'
            by_department[dept] = by_department.get(dept, 0) + 1

            # By location
            loc = emp.location or 'Unknown'
            by_location[loc] = by_location.get(loc, 0) + 1

            # By status
            status = emp.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if emp.status == EmploymentStatus.ACTIVE:
                active_count += 1

        # Calculate 30-day changes
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_hires = sum(1 for e in employees if e.hire_date and e.hire_date > thirty_days_ago)

        return HeadcountReport(
            date=datetime.now(),
            total_employees=len(employees),
            active_employees=active_count,
            by_department=by_department,
            by_location=by_location,
            by_status=by_status,
            new_hires_30d=new_hires,
            terminations_30d=0  # Would need terminated employees report
        )


class BambooHRDemoClient:
    """Demo client with realistic mock data."""

    def __init__(self):
        self._employees = self._generate_mock_employees()
        self._time_off_requests = self._generate_mock_time_off()

    def _generate_mock_employees(self) -> List[Employee]:
        """Generate realistic employee data."""
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Product']
        locations = ['New York', 'San Francisco', 'Austin', 'Chicago', 'Remote']

        employees = [
            Employee(
                id='1', first_name='Sarah', last_name='Johnson', email='sjohnson@company.com',
                department='Engineering', job_title='VP of Engineering', location='San Francisco',
                hire_date=datetime(2019, 3, 15), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CEO'
            ),
            Employee(
                id='2', first_name='Michael', last_name='Chen', email='mchen@company.com',
                department='Engineering', job_title='Senior Software Engineer', location='San Francisco',
                hire_date=datetime(2020, 7, 1), status=EmploymentStatus.ACTIVE,
                supervisor_id='1', supervisor_name='Sarah Johnson'
            ),
            Employee(
                id='3', first_name='Emily', last_name='Williams', email='ewilliams@company.com',
                department='Sales', job_title='Sales Director', location='New York',
                hire_date=datetime(2018, 11, 20), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CEO'
            ),
            Employee(
                id='4', first_name='James', last_name='Rodriguez', email='jrodriguez@company.com',
                department='Sales', job_title='Account Executive', location='New York',
                hire_date=datetime(2022, 2, 14), status=EmploymentStatus.ACTIVE,
                supervisor_id='3', supervisor_name='Emily Williams'
            ),
            Employee(
                id='5', first_name='Lisa', last_name='Anderson', email='landerson@company.com',
                department='Marketing', job_title='Marketing Manager', location='Austin',
                hire_date=datetime(2021, 5, 3), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CMO'
            ),
            Employee(
                id='6', first_name='David', last_name='Kim', email='dkim@company.com',
                department='Engineering', job_title='Software Engineer', location='Remote',
                hire_date=datetime(2023, 8, 21), status=EmploymentStatus.ACTIVE,
                supervisor_id='1', supervisor_name='Sarah Johnson'
            ),
            Employee(
                id='7', first_name='Jennifer', last_name='Martinez', email='jmartinez@company.com',
                department='HR', job_title='HR Manager', location='Chicago',
                hire_date=datetime(2020, 1, 6), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CHRO'
            ),
            Employee(
                id='8', first_name='Robert', last_name='Taylor', email='rtaylor@company.com',
                department='Finance', job_title='Financial Analyst', location='New York',
                hire_date=datetime(2021, 9, 13), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CFO'
            ),
            Employee(
                id='9', first_name='Amanda', last_name='Brown', email='abrown@company.com',
                department='Product', job_title='Product Manager', location='San Francisco',
                hire_date=datetime(2022, 4, 18), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='CPO'
            ),
            Employee(
                id='10', first_name='Christopher', last_name='Lee', email='clee@company.com',
                department='Operations', job_title='Operations Lead', location='Austin',
                hire_date=datetime(2019, 8, 5), status=EmploymentStatus.ACTIVE,
                supervisor_id=None, supervisor_name='COO'
            ),
            Employee(
                id='11', first_name='Michelle', last_name='Davis', email='mdavis@company.com',
                department='Engineering', job_title='QA Engineer', location='Remote',
                hire_date=datetime(2023, 1, 9), status=EmploymentStatus.ACTIVE,
                supervisor_id='1', supervisor_name='Sarah Johnson'
            ),
            Employee(
                id='12', first_name='Kevin', last_name='Wilson', email='kwilson@company.com',
                department='Sales', job_title='Sales Representative', location='Chicago',
                hire_date=datetime(2023, 11, 1), status=EmploymentStatus.ACTIVE,
                supervisor_id='3', supervisor_name='Emily Williams'
            ),
            Employee(
                id='13', first_name='Rachel', last_name='Thomas', email='rthomas@company.com',
                department='Marketing', job_title='Content Specialist', location='Remote',
                hire_date=datetime(2024, 1, 15), status=EmploymentStatus.ACTIVE,
                supervisor_id='5', supervisor_name='Lisa Anderson'
            ),
            Employee(
                id='14', first_name='Brian', last_name='Jackson', email='bjackson@company.com',
                department='Engineering', job_title='DevOps Engineer', location='San Francisco',
                hire_date=datetime(2022, 6, 20), status=EmploymentStatus.ACTIVE,
                supervisor_id='1', supervisor_name='Sarah Johnson'
            ),
            Employee(
                id='15', first_name='Nicole', last_name='White', email='nwhite@company.com',
                department='HR', job_title='HR Coordinator', location='Chicago',
                hire_date=datetime(2023, 3, 27), status=EmploymentStatus.ACTIVE,
                supervisor_id='7', supervisor_name='Jennifer Martinez'
            ),
        ]
        return employees

    def _generate_mock_time_off(self) -> List[TimeOffRequest]:
        """Generate mock time off requests."""
        now = datetime.now()
        return [
            TimeOffRequest(
                id='TO1', employee_id='2', employee_name='Michael Chen',
                type='Vacation', start_date=now + timedelta(days=14),
                end_date=now + timedelta(days=21), amount=5, status='approved'
            ),
            TimeOffRequest(
                id='TO2', employee_id='4', employee_name='James Rodriguez',
                type='Sick Leave', start_date=now - timedelta(days=3),
                end_date=now - timedelta(days=2), amount=2, status='approved'
            ),
            TimeOffRequest(
                id='TO3', employee_id='6', employee_name='David Kim',
                type='Personal', start_date=now + timedelta(days=7),
                end_date=now + timedelta(days=7), amount=1, status='pending'
            ),
            TimeOffRequest(
                id='TO4', employee_id='9', employee_name='Amanda Brown',
                type='Vacation', start_date=now + timedelta(days=30),
                end_date=now + timedelta(days=37), amount=5, status='approved'
            ),
            TimeOffRequest(
                id='TO5', employee_id='12', employee_name='Kevin Wilson',
                type='Sick Leave', start_date=now - timedelta(days=1),
                end_date=now, amount=1, status='approved'
            ),
        ]

    def get_employees(self, status: Optional[EmploymentStatus] = None) -> List[Employee]:
        if status:
            return [e for e in self._employees if e.status == status]
        return self._employees

    def get_employee(self, employee_id: str) -> Optional[Employee]:
        for emp in self._employees:
            if emp.id == employee_id:
                return emp
        return None

    def get_time_off_requests(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[TimeOffRequest]:
        results = self._time_off_requests
        if status:
            results = [r for r in results if r.status == status]
        return results

    def get_time_off_balances(self, employee_id: str) -> List[TimeOffBalance]:
        return [
            TimeOffBalance(employee_id=employee_id, type='Vacation', balance=15, used=5, scheduled=3),
            TimeOffBalance(employee_id=employee_id, type='Sick Leave', balance=10, used=2, scheduled=0),
            TimeOffBalance(employee_id=employee_id, type='Personal', balance=3, used=1, scheduled=0),
        ]

    def get_headcount_report(self) -> HeadcountReport:
        employees = self._employees

        by_department = {}
        by_location = {}
        by_status = {}
        active_count = 0

        for emp in employees:
            dept = emp.department or 'Unknown'
            by_department[dept] = by_department.get(dept, 0) + 1

            loc = emp.location or 'Unknown'
            by_location[loc] = by_location.get(loc, 0) + 1

            status = emp.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if emp.status == EmploymentStatus.ACTIVE:
                active_count += 1

        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_hires = sum(1 for e in employees if e.hire_date and e.hire_date > thirty_days_ago)

        return HeadcountReport(
            date=datetime.now(),
            total_employees=len(employees),
            active_employees=active_count,
            by_department=by_department,
            by_location=by_location,
            by_status=by_status,
            new_hires_30d=new_hires,
            terminations_30d=1  # Mock termination
        )

    def get_performance_reviews(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PerformanceReview]:
        """Get mock performance reviews."""
        return [
            PerformanceReview(
                id='PR1', employee_id='2', employee_name='Michael Chen',
                reviewer_id='1', reviewer_name='Sarah Johnson',
                review_date=datetime(2024, 1, 15), rating=4.5, status='completed',
                goals_met=8, total_goals=10,
                strengths=['Technical expertise', 'Problem solving', 'Team collaboration'],
                areas_for_improvement=['Documentation', 'Presentation skills']
            ),
            PerformanceReview(
                id='PR2', employee_id='4', employee_name='James Rodriguez',
                reviewer_id='3', reviewer_name='Emily Williams',
                review_date=datetime(2024, 1, 20), rating=4.0, status='completed',
                goals_met=7, total_goals=8,
                strengths=['Client relationships', 'Quota achievement', 'Initiative'],
                areas_for_improvement=['CRM updates', 'Forecasting accuracy']
            ),
            PerformanceReview(
                id='PR3', employee_id='6', employee_name='David Kim',
                reviewer_id='1', reviewer_name='Sarah Johnson',
                review_date=datetime(2024, 2, 1), rating=3.8, status='completed',
                goals_met=5, total_goals=7,
                strengths=['Code quality', 'Learning agility'],
                areas_for_improvement=['Communication', 'Meeting attendance', 'Estimates']
            ),
        ]


def create_bamboohr_client(demo_mode: bool = False) -> BambooHRClient:
    """Factory function to create BambooHR client."""
    if demo_mode:
        return BambooHRDemoClient()

    company_domain = os.getenv('BAMBOOHR_COMPANY_DOMAIN')
    api_key = os.getenv('BAMBOOHR_API_KEY')

    if not company_domain or not api_key:
        raise ValueError("BAMBOOHR_COMPANY_DOMAIN and BAMBOOHR_API_KEY must be set")

    config = BambooHRConfig(
        company_domain=company_domain,
        api_key=api_key
    )
    return BambooHRClient(config)
