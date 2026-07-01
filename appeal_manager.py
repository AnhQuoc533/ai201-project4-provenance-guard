import json
import os
from datetime import datetime, timezone, timedelta
from audit_logger import _get_iso_timestamp, _generate_id

APPEALS_LOG_PATH = 'appeals_log.json'
CONTENT_STATUS_PATH = 'content_status.json'


def _load_appeals_log():
    """Load existing appeals log or create empty log."""
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


def _load_content_status():
    """Load content status or create empty status file."""
    if os.path.exists(CONTENT_STATUS_PATH):
        try:
            with open(CONTENT_STATUS_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_content_status(status_data):
    """Save content status to file."""
    with open(CONTENT_STATUS_PATH, 'w') as f:
        json.dump(status_data, f, indent=2)


def _get_review_deadline():
    """Get review deadline (14 days from now)."""
    deadline = datetime.now(timezone.utc) + timedelta(days=14)
    return deadline.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_content_status(content_id):
    """
    Get status of a content submission.
    
    Args:
        content_id (str): Content identifier.
    
    Returns:
        dict: Status information or None if not found.
    """
    status_data = _load_content_status()
    return status_data.get(content_id)


def check_appeal_eligibility(content_id):
    """
    Check if a content is eligible for appeal.
    
    Args:
        content_id (str): Content identifier.
    
    Returns:
        tuple: (is_eligible, reason)
    """
    status = get_content_status(content_id)
    
    if not status:
        return False, 'Content not found'
    
    if status.get('status') == 'under review':
        return False, 'Content is already under review'
    
    if status.get('status') == 'resolved':
        return False, 'Appeal already processed for this content'
    
    created_at = datetime.fromisoformat(status['created_at'].replace('Z', '+00:00'))
    appeal_deadline = created_at + timedelta(days=30)
    
    if datetime.now(timezone.utc) > appeal_deadline:
        return False, 'Appeal period (30 days) has expired'
    
    return True, None


def create_appeal(content_id, creator_email, appeal_form_data, original_classification):
    """
    Create and log an appeal.
    
    Args:
        content_id (str): Content identifier.
        creator_email (str): Creator's email address.
        appeal_form_data (dict): Form submission data.
        original_classification (dict): Original classification data.
    
    Returns:
        str: Appeal ID if successful, empty string otherwise.
    """
    try:
        appeal_id = _generate_id('APP')
        
        appeal_entry = {
            'appeal_id': appeal_id,
            'content_id': content_id,
            'creator_email': creator_email,
            'created_at': _get_iso_timestamp(),
            'status': 'pending',
            'assigned_reviewer': None,
            'assigned_at': None,
            'review_deadline': _get_review_deadline(),
            
            'appeal_details': {
                'reasoning': appeal_form_data.get('reasoning', ''),
                'writing_date': appeal_form_data.get('writing_date', ''),
                'process_duration_hours': appeal_form_data.get('process_duration_hours'),
                'writing_process': appeal_form_data.get('writing_process', ''),
                'native_language': appeal_form_data.get('native_language', ''),
                'ai_assisted': appeal_form_data.get('ai_assisted', False),
                'ai_tools_detail': appeal_form_data.get('ai_tools_detail', ''),
                'additional_context': appeal_form_data.get('additional_context', ''),
                'supporting_files': appeal_form_data.get('supporting_files', []),
            },
            
            'original_classification': original_classification,
        }
        
        appeals_log = _load_appeals_log()
        appeals_log.append(appeal_entry)
        _save_appeals_log(appeals_log)
        
        status_data = _load_content_status()
        if content_id in status_data:
            status_data[content_id]['status'] = 'under review'
            status_data[content_id]['appeal_id'] = appeal_id
            _save_content_status(status_data)
        
        return appeal_id
    
    except Exception as e:
        print(f'Error creating appeal: {str(e)}')
        return ''


def update_content_status(content_id, classification_result):
    """
    Update content status after classification.
    
    Args:
        content_id (str): Content identifier.
        classification_result (dict): Classification result with label and confidence.
    
    Returns:
        bool: True if successful.
    """
    try:
        status_data = _load_content_status()
        
        status_data[content_id] = {
            'status': 'classified',
            'created_at': _get_iso_timestamp(),
            'label': classification_result.get('label'),
            'confidence': classification_result.get('confidence'),
            'appeal_id': None,
        }
        
        _save_content_status(status_data)
        return True
    except Exception as e:
        print(f'Error updating content status: {str(e)}')
        return False


def get_appeal_by_id(appeal_id):
    """
    Retrieve appeal details by appeal ID.
    
    Args:
        appeal_id (str): Appeal identifier.
    
    Returns:
        dict: Appeal data or None if not found.
    """
    appeals_log = _load_appeals_log()
    for appeal in appeals_log:
        if appeal['appeal_id'] == appeal_id:
            return appeal
    return None


def get_appeals_by_content_id(content_id):
    """
    Retrieve all appeals for a specific content.
    
    Args:
        content_id (str): Content identifier.
    
    Returns:
        list: List of appeals for the content.
    """
    appeals_log = _load_appeals_log()
    return [a for a in appeals_log if a['content_id'] == content_id]