import json
import os
from datetime import datetime, timezone, timedelta

APPEALS_LOG_PATH = 'appeals_log.json'
DECISIONS_LOG_PATH = 'decisions_log.json'


def _get_iso_timestamp():
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _generate_decision_id():
    """Generate unique decision ID."""
    import uuid
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f'DEC-{today}-{random_suffix}'


def _load_appeals_log():
    """Load existing appeals log."""
    if os.path.exists(APPEALS_LOG_PATH):
        try:
            with open(APPEALS_LOG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_appeals_log(log_data):
    """Save appeals log to file."""
    with open(APPEALS_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)


def _load_decisions_log():
    """Load existing decisions log or create empty log."""
    if os.path.exists(DECISIONS_LOG_PATH):
        try:
            with open(DECISIONS_LOG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_decisions_log(log_data):
    """Save decisions log to file."""
    with open(DECISIONS_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)


def submit_decision(appeal_id, reviewer_email, decision_type, reasoning, recommended_changes=None):
    """
    Submit a reviewer decision on an appeal.
    
    Args:
        appeal_id (str): Appeal identifier.
        reviewer_email (str): Reviewer's email address.
        decision_type (str): Decision type (approve, deny, inconclusive).
        reasoning (str): Explanation for the decision.
        recommended_changes (str): Recommended system changes (optional).
    
    Returns:
        tuple: (success, decision_id_or_error_message)
    """
    if decision_type not in {'approve', 'deny', 'inconclusive'}:
        return False, 'Invalid decision type'
    
    if not reasoning or len(reasoning.strip()) < 10:
        return False, 'Reasoning must be at least 10 words'
    
    try:
        appeals_log = _load_appeals_log()
        appeal_found = False
        
        for appeal in appeals_log:
            if appeal['appeal_id'] == appeal_id:
                appeal_found = True
                
                if appeal['status'] != 'pending':
                    return False, 'Appeal is not in pending status'
                
                decision_id = _generate_decision_id()
                decision_entry = {
                    'decision_id': decision_id,
                    'appeal_id': appeal_id,
                    'content_id': appeal['content_id'],
                    'reviewer_email': reviewer_email,
                    'decision_type': decision_type,
                    'reasoning': reasoning,
                    'recommended_changes': recommended_changes or '',
                    'submitted_at': _get_iso_timestamp(),
                }
                
                decisions_log = _load_decisions_log()
                decisions_log.append(decision_entry)
                _save_decisions_log(decisions_log)
                
                if decision_type == 'inconclusive':
                    appeal['status'] = 'pending'
                    appeal['review_deadline'] = (
                        datetime.now(timezone.utc) + timedelta(days=14)
                    ).strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    appeal['status'] = 'resolved'
                    appeal['decision_id'] = decision_id
                
                _save_appeals_log(appeals_log)
                
                return True, decision_id
        
        if not appeal_found:
            return False, 'Appeal not found'
    
    except Exception as e:
        return False, f'Error processing decision: {str(e)}'


def get_decision_by_id(decision_id):
    """
    Retrieve a decision by ID.
    
    Args:
        decision_id (str): Decision identifier.
    
    Returns:
        dict: Decision data or None if not found.
    """
    decisions_log = _load_decisions_log()
    for decision in decisions_log:
        if decision['decision_id'] == decision_id:
            return decision
    return None


def get_decisions_by_appeal_id(appeal_id):
    """
    Get all decisions for an appeal.
    
    Args:
        appeal_id (str): Appeal identifier.
    
    Returns:
        list: List of decisions.
    """
    decisions_log = _load_decisions_log()
    return [d for d in decisions_log if d['appeal_id'] == appeal_id]


def get_reviewer_decision_history(reviewer_email):
    """
    Get decision history for a reviewer.
    
    Args:
        reviewer_email (str): Reviewer's email address.
    
    Returns:
        list: List of decisions made by the reviewer.
    """
    decisions_log = _load_decisions_log()
    return [d for d in decisions_log if d['reviewer_email'] == reviewer_email]


def request_more_information(appeal_id, questions):
    """
    Request additional information from creator for inconclusive appeals.
    
    Args:
        appeal_id (str): Appeal identifier.
        questions (list): List of questions for creator.
    
    Returns:
        bool: True if successful.
    """
    try:
        appeals_log = _load_appeals_log()
        
        for appeal in appeals_log:
            if appeal['appeal_id'] == appeal_id:
                appeal['pending_questions'] = questions
                appeal['questions_sent_at'] = _get_iso_timestamp()
                appeal['response_deadline'] = (
                    datetime.now(timezone.utc) + timedelta(days=14)
                ).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                _save_appeals_log(appeals_log)
                return True
        
        return False
    
    except Exception as e:
        print(f'Error requesting information: {str(e)}')
        return False


def get_appeal_statistics():
    """
    Get statistics about appeals.
    
    Returns:
        dict: Appeal statistics.
    """
    appeals_log = _load_appeals_log()
    decisions_log = _load_decisions_log()
    
    total_appeals = len(appeals_log)
    pending = sum(1 for a in appeals_log if a['status'] == 'pending')
    resolved = sum(1 for a in appeals_log if a['status'] == 'resolved')
    
    total_decisions = len(decisions_log)
    approved = sum(1 for d in decisions_log if d['decision_type'] == 'approve')
    denied = sum(1 for d in decisions_log if d['decision_type'] == 'deny')
    inconclusive = sum(1 for d in decisions_log if d['decision_type'] == 'inconclusive')
    
    return {
        'total_appeals': total_appeals,
        'pending_appeals': pending,
        'resolved_appeals': resolved,
        'total_decisions': total_decisions,
        'approved_decisions': approved,
        'denied_decisions': denied,
        'inconclusive_decisions': inconclusive,
    }