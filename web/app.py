"""Flask Application - Talent Intelligence (Fractional CHRO)"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
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

APP_NAME = "Talent Intelligence"
APP_VERSION = "1.0.0"

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
def health():
    return jsonify({'status': 'healthy', 'app': APP_NAME})

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html') if not request.path.startswith('/api/') else jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5107)), debug=os.getenv('FLASK_ENV') != 'production')
