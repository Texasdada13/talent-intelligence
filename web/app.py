"""Flask Application - Talent Intelligence (Fractional CHRO)"""
import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

database_url = os.getenv('DATABASE_URL', 'sqlite:///talent_intelligence.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

from src.database.models import db
db.init_app(app)

from src.database.repository import TalentRepository
repo = TalentRepository()

from src.ai_core.chat_engine import create_chat_engine
from src.patterns.benchmark_engine import create_hr_benchmarks
from src.integrations import get_integration_manager
from patriot_ui import init_ui
from patriot_ui.config import NavItem, NavSection

APP_NAME = "Talent Intelligence"
APP_VERSION = "1.0.0"

init_ui(app,
    product_name="Talent Intelligence",
    product_icon="bi-people",
    show_org_selector=True,
    nav_sections=[
        NavSection("Overview", [
            NavItem("Dashboard", "bi-speedometer2", "/dashboard"),
            NavItem("AI Consultant", "bi-chat-dots", "/chat"),
        ]),
        NavSection("Tools", [
            NavItem("Talent Assessment", "bi-person-check", "/talent-assessment"),
            NavItem("Retention", "bi-arrow-repeat", "/retention"),
            NavItem("Workforce Planning", "bi-diagram-3", "/workforce-planning"),
            NavItem("Succession Planning", "bi-ladder", "/succession-planning"),
            NavItem("Diversity & Inclusion", "bi-globe", "/diversity"),
        ]),
        NavSection("Connect", [
            NavItem("Integrations", "bi-plug", "/integrations"),
        ]),
    ]
)

@app.context_processor
def inject_globals():
    return {'app_name': APP_NAME, 'current_year': datetime.now().year}

@app.before_request
def create_tables():
    if not hasattr(app, '_tables_created'):
        db.create_all()
        app._tables_created = True

# Web Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    organizations = repo.get_all_organizations()
    return render_template('dashboard.html', organizations=organizations)

@app.route('/organization/<org_id>')
def organization_detail(org_id):
    org = repo.get_organization(org_id)
    if not org:
        return render_template('404.html'), 404
    departments = repo.get_departments(org_id)
    employees = repo.get_employees(org_id)
    metrics = repo.get_hr_metrics(org_id, limit=12)
    talent_dist = repo.get_talent_distribution(org_id)
    flight_risk = repo.get_flight_risk_summary(org_id)
    return render_template('organization.html', organization=org, departments=departments,
                          employees=employees, metrics=metrics, talent_distribution=talent_dist,
                          flight_risk=flight_risk)

@app.route('/talent-assessment')
def talent_assessment():
    organizations = repo.get_all_organizations()
    return render_template('talent_assessment.html', organizations=organizations)

@app.route('/retention')
def retention_analytics():
    organizations = repo.get_all_organizations()
    return render_template('retention.html', organizations=organizations)

@app.route('/workforce-planning')
def workforce_planning():
    organizations = repo.get_all_organizations()
    return render_template('workforce_planning.html', organizations=organizations)

@app.route('/succession-planning')
def succession_planning():
    organizations = repo.get_all_organizations()
    return render_template('succession_planning.html', organizations=organizations)

@app.route('/diversity')
def diversity_inclusion():
    organizations = repo.get_all_organizations()
    return render_template('diversity.html', organizations=organizations)

@app.route('/chat')
@app.route('/chat/<org_id>')
def chat_view(org_id=None):
    organizations = repo.get_all_organizations()
    org = repo.get_organization(org_id) if org_id else None
    return render_template('chat.html', organization=org, organizations=organizations)

# API Routes
@app.route('/api/organizations', methods=['GET'])
def api_list_organizations():
    return jsonify({'success': True, 'organizations': [o.to_dict() for o in repo.get_all_organizations()]})

@app.route('/api/organizations', methods=['POST'])
@limiter.limit("10 per hour")
def api_create_organization():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'success': False, 'error': 'Name required'}), 400
    org = repo.create_organization(data)
    return jsonify({'success': True, 'organization': org.to_dict()})

@app.route('/api/organizations/<org_id>/metrics', methods=['POST'])
@limiter.limit("30 per hour")
def api_add_metrics(org_id):
    data = request.get_json()
    if not data.get('period_date'):
        return jsonify({'success': False, 'error': 'Period date required'}), 400
    metrics = repo.create_hr_metrics(org_id, data)
    return jsonify({'success': True, 'metrics': metrics.to_dict()})

@app.route('/api/organizations/<org_id>/employees', methods=['GET'])
def api_get_employees(org_id):
    employees = repo.get_employees(org_id)
    return jsonify({'success': True, 'employees': [e.to_dict() for e in employees]})

@app.route('/api/organizations/<org_id>/employees', methods=['POST'])
@limiter.limit("50 per hour")
def api_create_employee(org_id):
    data = request.get_json()
    emp = repo.create_employee(org_id, data)
    return jsonify({'success': True, 'employee': emp.to_dict()})

@app.route('/api/organizations/<org_id>/benchmark', methods=['POST'])
@limiter.limit("10 per hour")
def api_run_benchmark(org_id):
    latest = repo.get_latest_hr_metrics(org_id)
    if not latest:
        return jsonify({'success': False, 'error': 'No HR metrics available'}), 400
    engine = create_hr_benchmarks()
    values = {k: v for k, v in latest.get_kpi_values().items() if v is not None}
    if not values:
        return jsonify({'success': False, 'error': 'No valid metrics'}), 400
    report = engine.analyze(values, entity_id=org_id)
    return jsonify({'success': True, 'benchmark': report.to_dict()})

# Integration Routes
@app.route('/integrations')
def integrations_view():
    """HR integrations page."""
    integration_manager = get_integration_manager()
    status = integration_manager.get_integration_status()
    return render_template('integrations.html', integration_status=status)

@app.route('/api/integrations/status', methods=['GET'])
def api_integration_status():
    """Get integration connection status."""
    integration_manager = get_integration_manager()
    return jsonify({
        'success': True,
        'status': integration_manager.get_integration_status()
    })

@app.route('/api/integrations/demo/enable', methods=['POST'])
def api_enable_demo_mode():
    """Enable demo mode for integrations."""
    integration_manager = get_integration_manager()
    integration_manager.enable_demo_mode()
    return jsonify({
        'success': True,
        'message': 'Demo mode enabled',
        'status': integration_manager.get_integration_status()
    })

@app.route('/api/integrations/employees', methods=['GET'])
def api_get_integration_employees():
    """Get unified employee list from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    active_only = request.args.get('active_only', 'true').lower() == 'true'
    employees = integration_manager.get_employees(active_only=active_only)
    return jsonify({
        'success': True,
        'employees': [emp.to_dict() for emp in employees],
        'count': len(employees)
    })

@app.route('/api/integrations/time-off', methods=['GET'])
def api_get_time_off_requests():
    """Get time off requests from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    status = request.args.get('status')
    requests_list = integration_manager.get_time_off_requests(status=status)
    return jsonify({
        'success': True,
        'time_off_requests': requests_list,
        'count': len(requests_list)
    })

@app.route('/api/integrations/requisitions', methods=['GET'])
def api_get_job_requisitions():
    """Get job requisitions from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    status = request.args.get('status')
    requisitions = integration_manager.get_job_requisitions(status=status)
    return jsonify({
        'success': True,
        'requisitions': requisitions,
        'count': len(requisitions)
    })

@app.route('/api/integrations/learning', methods=['GET'])
def api_get_learning_enrollments():
    """Get learning enrollments from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    status = request.args.get('status')
    enrollments = integration_manager.get_learning_enrollments(status=status)
    return jsonify({
        'success': True,
        'enrollments': enrollments,
        'count': len(enrollments)
    })

@app.route('/api/integrations/goals', methods=['GET'])
def api_get_goal_progress():
    """Get goal progress from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    goals = integration_manager.get_goal_progress()
    return jsonify({
        'success': True,
        'goals': goals,
        'count': len(goals)
    })

@app.route('/api/integrations/performance-reviews', methods=['GET'])
def api_get_performance_reviews():
    """Get performance reviews from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    reviews = integration_manager.get_performance_reviews()
    return jsonify({
        'success': True,
        'reviews': reviews,
        'count': len(reviews)
    })

@app.route('/api/integrations/compensation', methods=['GET'])
def api_get_compensation_report():
    """Get compensation report from integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    report = integration_manager.get_compensation_report()
    if not report:
        return jsonify({'success': False, 'error': 'Compensation data not available'}), 400

    return jsonify({
        'success': True,
        'compensation': report
    })

@app.route('/api/integrations/talent-summary', methods=['GET'])
def api_get_talent_summary():
    """Get aggregated talent summary from all integrations."""
    integration_manager = get_integration_manager()
    if not integration_manager.is_configured:
        return jsonify({'success': False, 'error': 'No integrations configured'}), 400

    summary = integration_manager.get_talent_summary()
    return jsonify({
        'success': True,
        'summary': summary.to_dict()
    })

# Chat API
chat_sessions = {}

@app.route('/api/chat/session', methods=['POST'])
@limiter.limit("20 per hour")
def api_create_chat_session():
    data = request.get_json() or {}
    org_id = data.get('organization_id')
    session = repo.create_chat_session(org_id)
    chat_engine = create_chat_engine()
    if org_id:
        org = repo.get_organization(org_id)
        latest = repo.get_latest_hr_metrics(org_id)
        context = {'organization': org.to_dict() if org else {},
                   'metrics': latest.get_kpi_values() if latest else {},
                   'talent_distribution': repo.get_talent_distribution(org_id),
                   'flight_risk': repo.get_flight_risk_summary(org_id)}
        chat_engine.set_context(context)
    chat_sessions[session.id] = chat_engine
    return jsonify({'success': True, 'session_id': session.id, 'suggested_prompts': chat_engine.get_suggested_prompts()})

@app.route('/api/chat/stream', methods=['POST'])
@limiter.limit("50 per hour")
def api_chat_stream():
    data = request.get_json()
    session_id, message = data.get('session_id'), data.get('message')
    if not session_id or not message:
        return jsonify({'success': False, 'error': 'session_id and message required'}), 400
    chat_engine = chat_sessions.get(session_id) or create_chat_engine()
    chat_sessions[session_id] = chat_engine
    repo.add_chat_message(session_id, 'user', message)

    def generate():
        full = ""
        for token in chat_engine.stream_chat(message):
            full += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        repo.add_chat_message(session_id, 'assistant', full)
        yield f"data: {json.dumps({'type': 'done', 'suggested_prompts': chat_engine.get_suggested_prompts()})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/health')
@limiter.exempt
def health():
    return jsonify({'status': 'healthy', 'app': APP_NAME})

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html') if not request.path.startswith('/api/') else jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5107)), debug=os.getenv('FLASK_ENV') != 'production')
