import json
import os
import uuid
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


def _generate_id(prefix: str):
    """
    Generate unique ID for submitted text (content ID), submitted appeal form (appeal ID),
    or reviewer decision (decision ID).
    
    Format: AAA-YYYY-MM-DD-XXXX 
            XXXX is a random hex string and 
            AAA is CTN, APP, or DEC.
    Args:
        prefix (str): Three-letter prefix for the identifier. 
                      CTN for content ID, APP for appeal ID, and DEC for decision ID
    Returns:
        str: Generated content ID.
    """
    if prefix not in {'CTN', 'APP', 'DEC'}:
        raise ValueError("Prefix must be one of 'CTN', 'APP', or 'DEC'")
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f'{prefix}-{today}-{random_suffix}'


def log_classification(text, confidence, label, signals):
    """
    Log a classification decision to audit log.
    
    Args:
        content_id (str): Unique content identifier.
        text (str): Original text submitted.
        confidence (float): Final confidence score (0.0-1.0).
        label (str): Classification label.
        signals (dict): Signal scores and reasoning.
    
    Returns:
        bool: Unique content identifier, or an empty string otherwise.
    """
    try:
        log_entry = {
            'content_id': _generate_id('CTN'),
            'created_at': _get_iso_timestamp(),
            'content': text,
            'classification': {
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
        return log_entry['content_id']
    except Exception as e:
        print(f'Error logging classification: {str(e)}')
        return ''
