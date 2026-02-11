"""
External Data Integrations for Talent Intelligence

Provides connections to:
- BambooHR (HRIS)
- Workday (HCM)
"""

from .bamboohr_client import (
    BambooHRClient,
    BambooHRDemoClient,
    BambooHRConfig,
    Employee,
    TimeOffRequest,
    TimeOffBalance,
    PerformanceReview,
    HeadcountReport,
    EmploymentStatus,
    create_bamboohr_client
)

from .workday_client import (
    WorkdayClient,
    WorkdayDemoClient,
    WorkdayConfig,
    Worker,
    JobRequisition,
    LearningEnrollment,
    GoalProgress,
    WorkforceAnalytics,
    CompensationReport,
    WorkerType,
    RequisitionStatus,
    create_workday_client
)

from .integration_manager import (
    TalentIntegrationManager,
    UnifiedEmployee,
    TalentSummary,
    IntegrationType,
    get_integration_manager
)

__all__ = [
    # BambooHR
    'BambooHRClient',
    'BambooHRDemoClient',
    'BambooHRConfig',
    'Employee',
    'TimeOffRequest',
    'TimeOffBalance',
    'PerformanceReview',
    'HeadcountReport',
    'EmploymentStatus',
    'create_bamboohr_client',

    # Workday
    'WorkdayClient',
    'WorkdayDemoClient',
    'WorkdayConfig',
    'Worker',
    'JobRequisition',
    'LearningEnrollment',
    'GoalProgress',
    'WorkforceAnalytics',
    'CompensationReport',
    'WorkerType',
    'RequisitionStatus',
    'create_workday_client',

    # Integration Manager
    'TalentIntegrationManager',
    'UnifiedEmployee',
    'TalentSummary',
    'IntegrationType',
    'get_integration_manager'
]
