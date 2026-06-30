import json
import os
from datetime import datetime, timezone


AUDIT_LOG_PATH = 'audit_log.json'


def _get_iso_timestamp():
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _load_audit_log():
    """Load existing audit log or create empty log."""
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_audit_log(log_data):
    """Save audit log to file."""
    with open(AUDIT_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)


def log_classification(content_id, decision_id, text, confidence, label, signals):
    """
    Log a classification decision to audit log.
    
    Args:
        content_id (str): Unique content identifier.
        decision_id (str): Unique decision identifier.
        text (str): Original text submitted.
        confidence (float): Final confidence score (0.0-1.0).
        label (str): Classification label.
        signals (dict): Signal scores and reasoning.
    
    Returns:
        bool: True if logging successful, False otherwise.
    """
    try:
        log_entry = {
            'content_id': content_id,
            'decision_id': decision_id,
            'created_at': _get_iso_timestamp(),
            'text_length': len(text),
            'original_classification': {
                'result': label,
                'confidence': confidence,
                'signals': {
                    'llm_judgment': {
                        'score': signals['llm_judgment']['score'],
                        'reasoning': signals['llm_judgment']['reasoning'],
                    },
                    'stylometry': {
                        'score': signals['stylometry']['score'],
                        'reasoning': signals['stylometry']['reasoning'],
                        'subscores': signals['stylometry'].get('subscores', {}),
                    },
                    'perplexity': {
                        'score': signals['perplexity']['score'],
                        'reasoning': signals['perplexity']['reasoning'],
                        'raw_perplexity': signals['perplexity'].get('raw_perplexity', None),
                    },
                }
            }
        }
        
        log_data = _load_audit_log()
        log_data.append(log_entry)
        _save_audit_log(log_data)
        return True
    except Exception as e:
        print(f'Error logging classification: {str(e)}')
        return False
