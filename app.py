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
        data = request.get_json(force=True, silent=True)
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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.route("/")
def home():
    return "Provenance Guard is running."


if __name__ == '__main__':
    app.run(debug=True, port=5000)
