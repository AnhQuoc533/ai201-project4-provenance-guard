from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from signal_1 import llm_judgment
from signal_2 import stylometric_heuristics
from signal_3 import perplexity_calculation

from config import RATELIMIT_DEFAULT, RATELIMIT_STORAGE_URL, MAX_CONTENT_LENGTH, LABEL_REASONING
from normalizer import normalize_content
from confidence import aggregate_confidence, get_label
from audit_logger import log_classification

from appeal_validator import validate_appeal_form
from appeal_manager import (
    create_appeal,
    update_content_status,
    check_appeal_eligibility,
)
from reviewer_dashboard import (
    get_pending_appeals,
    get_appeal_detail,
    format_appeal_for_reviewer,
    get_appeals_count_by_status,
)
from decision_processor import (
    submit_decision,
    request_more_information,
    get_appeal_statistics,
)


app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[RATELIMIT_DEFAULT],
    storage_uri=RATELIMIT_STORAGE_URL,
)


@app.errorhandler(400)
def handle_bad_request(e):
    """Handle bad request errors."""
    return jsonify({
        'error': 'Bad request',
        'message': str(e.description),
        'status_code': 400,
    }), 400


@app.errorhandler(429)
def handle_rate_limit(e):
    """Handle rate limit exceeded errors."""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Maximum 10 requests per minute allowed. Please try again later.',
        'status_code': 429,
    }), 429


def validate_submission(data):
    """
    Validate submission request data.
    
    Args:
        data (dict): Request JSON data.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, 'Request body must be valid JSON.'
    
    if 'text' not in data:
        return False, 'Missing required field: text'
    
    text = data.get('text', '')
    
    if not isinstance(text, str):
        return False, 'Field text must be a string.'
    
    if len(text.strip()) == 0:
        return False, 'Field text cannot be empty.'
    
    if len(text) > MAX_CONTENT_LENGTH:
        return False, f'Text exceeds maximum length of {MAX_CONTENT_LENGTH:,} characters.'
    
    return True, None


@app.route('/submit', methods=['POST'])
def submit_text():
    """
    Submit text for AI detection analysis.
    
    Request body: {text: string}
    
    Returns:
        JSON response with confidence score and transparency label.
    """
    try:
        data = request.get_json()
    except Exception:
        return jsonify({
            'error': 'Invalid JSON',
            'message': 'Request body must be valid JSON.',
            'status_code': 400,
        }), 400
    
    is_valid, error_message = validate_submission(data)
    if not is_valid:
        return jsonify({
            'error': 'Validation error',
            'message': error_message,
            'status_code': 400,
        }), 400
    
    normalized_text = normalize_content(data['text'])    
    signals = {
        'llm_judgment': llm_judgment(normalized_text),
        'stylometry': stylometric_heuristics(normalized_text),
        'perplexity': perplexity_calculation(normalized_text),
    }
    confidence = aggregate_confidence(signals)
    label = get_label(confidence)    
    content_id = log_classification(data['text'], confidence, label, signals)
    
    classification_result = {
        'label': label,
        'confidence': confidence,
        'signals': signals,
    }
    update_content_status(content_id, classification_result)
    
    return jsonify({
        'success': True,
        'result': {
            'content_id': content_id,
            'label': label,
            'confidence': confidence,
            'reasoning': LABEL_REASONING[label],
        },
        'status_code': 200,
    }), 200


@app.route('/appeal', methods=['POST'])
def submit_appeal():
    """
    Submit an appeal for a classified content.
    
    Request body: {
        content_id: string,
        email: string,
        reasoning: string,
        writing_date: string (YYYY-MM-DD),
        process_duration_hours: number,
        writing_process: string,
        native_language: string,
        ai_assisted: boolean,
        ai_tools_detail: string (optional if ai_assisted is true),
        additional_context: string (optional),
        supporting_files: array (optional)
    }
    
    Returns:
        JSON response with appeal ID.
    """
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        return jsonify({
            'error': 'Invalid JSON',
            'message': 'Request body must be valid JSON.',
            'status_code': 400,
        }), 400
    
    content_id = data.get('content_id')
    if not content_id:
        return jsonify({
            'error': 'Validation error',
            'message': 'Missing required field: content_id',
            'status_code': 400,
        }), 400
    
    is_eligible, eligibility_error = check_appeal_eligibility(content_id)
    if not is_eligible:
        return jsonify({
            'error': 'Appeal not eligible',
            'message': eligibility_error,
            'status_code': 400,
        }), 400
    
    is_valid, errors = validate_appeal_form(data)
    if not is_valid:
        return jsonify({
            'error': 'Validation error',
            'message': 'Form validation failed',
            'errors': errors,
            'status_code': 400,
        }), 400
    
    from audit_logger import _load_audit_log
    audit_log = _load_audit_log()
    original_classification = None
    
    for entry in audit_log:
        if entry.get('content_id') == content_id:
            original_classification = {
                'label': entry['classification'].get('result'),
                'confidence': entry['classification'].get('confidence'),
                'signals': entry['classification'].get('signals', {}),
            }
            break
    
    if not original_classification:
        return jsonify({
            'error': 'Content not found',
            'message': 'Could not find original classification for this content.',
            'status_code': 404,
        }), 404
    
    appeal_id = create_appeal(
        content_id,
        data['email'],
        data,
        original_classification,
    )
    
    if not appeal_id:
        return jsonify({
            'error': 'Appeal creation failed',
            'message': 'Failed to create appeal. Please try again.',
            'status_code': 500,
        }), 500
    
    return jsonify({
        'success': True,
        'result': {
            'appeal_id': appeal_id,
            'content_id': content_id,
            'status': 'pending',
            'message': 'Appeal submitted successfully. You will receive updates via email.',
        },
        'status_code': 200,
    }), 200


@app.route('/appeals/pending', methods=['GET'])
def get_pending():
    """
    Get pending appeals for reviewer dashboard.
    
    Query params:
        reviewer_email (optional): Filter by assigned reviewer
    
    Returns:
        JSON response with list of pending appeals.
    """
    reviewer_email = request.args.get('reviewer_email')
    
    appeals = get_pending_appeals(reviewer_email)
    counts = get_appeals_count_by_status()
    
    return jsonify({
        'success': True,
        'result': {
            'pending_appeals': appeals,
            'statistics': counts,
        },
        'status_code': 200,
    }), 200


@app.route('/appeals/<appeal_id>', methods=['GET'])
def get_appeal(appeal_id):
    """
    Get detailed information about a specific appeal.
    
    Args:
        appeal_id (str): Appeal identifier.
    
    Returns:
        JSON response with appeal details.
    """
    appeal = get_appeal_detail(appeal_id)
    
    if not appeal:
        return jsonify({
            'error': 'Not found',
            'message': f'Appeal {appeal_id} not found.',
            'status_code': 404,
        }), 404
    
    formatted = format_appeal_for_reviewer(appeal)
    
    return jsonify({
        'success': True,
        'result': formatted,
        'status_code': 200,
    }), 200


@app.route('/appeals/<appeal_id>/decision', methods=['POST'])
def submit_appeal_decision(appeal_id):
    """
    Submit a reviewer decision on an appeal.
    
    Request body: {
        reviewer_email: string,
        decision_type: string (approve, deny, inconclusive),
        reasoning: string,
        recommended_changes: string (optional)
    }
    
    Returns:
        JSON response with decision ID.
    """
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        return jsonify({
            'error': 'Invalid JSON',
            'message': 'Request body must be valid JSON.',
            'status_code': 400,
        }), 400
    
    reviewer_email = data.get('reviewer_email')
    decision_type = data.get('decision_type', '').lower()
    reasoning = data.get('reasoning', '')
    recommended_changes = data.get('recommended_changes')
    
    if not reviewer_email:
        return jsonify({
            'error': 'Validation error',
            'message': 'Missing required field: reviewer_email',
            'status_code': 400,
        }), 400
    
    success, result = submit_decision(
        appeal_id,
        reviewer_email,
        decision_type,
        reasoning,
        recommended_changes,
    )
    
    if not success:
        return jsonify({
            'error': 'Decision submission failed',
            'message': result,
            'status_code': 400,
        }), 400
    
    decision_id = result
    
    if decision_type == 'inconclusive':
        questions = data.get('questions', [])
        request_more_information(appeal_id, questions)
    
    return jsonify({
        'success': True,
        'result': {
            'decision_id': decision_id,
            'appeal_id': appeal_id,
            'decision_type': decision_type,
            'status': 'submitted',
        },
        'status_code': 200,
    }), 200


@app.route('/appeals/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about appeals and decisions.
    
    Returns:
        JSON response with appeal statistics.
    """
    stats = get_appeal_statistics()
    
    return jsonify({
        'success': True,
        'result': stats,
        'status_code': 200,
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.route("/")
def home():
    return "Provenance Guard is running."


if __name__ == '__main__':
    app.run(debug=True, port=5000)