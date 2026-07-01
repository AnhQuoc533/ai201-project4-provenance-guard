import json
import os
from datetime import datetime, timezone

APPEALS_LOG_PATH = 'appeals_log.json'


def _load_appeals_log():
    """Load existing appeals log or create empty log."""
    if os.path.exists(APPEALS_LOG_PATH):
        try:
            with open(APPEALS_LOG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def get_pending_appeals(reviewer_email=None):
    """
    Get all pending appeals.
    
    Args:
        reviewer_email (str): Filter appeals assigned to specific reviewer.
    
    Returns:
        list: List of pending appeals with signal breakdowns.
    """
    appeals_log = _load_appeals_log()
    pending = []
    
    for appeal in appeals_log:
        if appeal['status'] != 'pending':
            continue
        
        if reviewer_email and appeal.get('assigned_reviewer') != reviewer_email:
            continue
        
        appeal_summary = {
            'appeal_id': appeal['appeal_id'],
            'content_id': appeal['content_id'],
            'created_at': appeal['created_at'],
            'creator_email': appeal['creator_email'],
            'status': appeal['status'],
            'assigned_reviewer': appeal.get('assigned_reviewer'),
            'original_classification': {
                'label': appeal['original_classification'].get('label'),
                'confidence': appeal['original_classification'].get('confidence'),
            },
            'signals': {
                'llm_judgment': appeal['original_classification']['signals'].get('llm_judgment', {}).get('score'),
                'stylometry': appeal['original_classification']['signals'].get('stylometry', {}).get('score'),
                'perplexity': appeal['original_classification']['signals'].get('perplexity', {}).get('score'),
            },
            'appeal_summary': {
                'reasoning_preview': appeal['appeal_details']['reasoning'][:100] + '...',
                'ai_assisted': appeal['appeal_details']['ai_assisted'],
                'writing_process': appeal['appeal_details']['writing_process'],
                'supporting_files_count': len(appeal['appeal_details'].get('supporting_files', [])),
            }
        }
        
        pending.append(appeal_summary)
    
    return pending


def get_appeal_detail(appeal_id):
    """
    Get full details of a specific appeal.
    
    Args:
        appeal_id (str): Appeal identifier.
    
    Returns:
        dict: Complete appeal data.
    """
    appeals_log = _load_appeals_log()
    
    for appeal in appeals_log:
        if appeal['appeal_id'] == appeal_id:
            return appeal
    
    return None


def assign_appeal_to_reviewer(appeal_id, reviewer_email):
    """
    Assign an appeal to a reviewer.
    
    Args:
        appeal_id (str): Appeal identifier.
        reviewer_email (str): Reviewer's email address.
    
    Returns:
        bool: True if successful.
    """
    try:
        appeals_log = _load_appeals_log()
        
        for appeal in appeals_log:
            if appeal['appeal_id'] == appeal_id:
                appeal['assigned_reviewer'] = reviewer_email
                appeal['assigned_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                with open(APPEALS_LOG_PATH, 'w') as f:
                    json.dump(appeals_log, f, indent=2)
                
                return True
        
        return False
    
    except Exception as e:
        print(f'Error assigning appeal: {str(e)}')
        return False


def get_appeals_count_by_status():
    """
    Get count of appeals by status.
    
    Returns:
        dict: Count of appeals in each status.
    """
    appeals_log = _load_appeals_log()
    counts = {
        'pending': 0,
        'under_review': 0,
        'resolved': 0,
        'reopened': 0,
    }
    
    for appeal in appeals_log:
        status = appeal['status']
        if status in counts:
            counts[status] += 1
    
    return counts


def format_appeal_for_reviewer(appeal):
    """
    Format appeal data for reviewer dashboard display.
    
    Args:
        appeal (dict): Appeal data.
    
    Returns:
        dict: Formatted appeal data.
    """
    if not appeal:
        return None
    
    signals = appeal['original_classification']['signals']
    
    return {
        'appeal_id': appeal['appeal_id'],
        'content_id': appeal['content_id'],
        'creator_email': appeal['creator_email'],
        'created_at': appeal['created_at'],
        'status': appeal['status'],
        'assigned_reviewer': appeal.get('assigned_reviewer'),
        'review_deadline': appeal.get('review_deadline'),
        
        'original_classification': {
            'result': appeal['original_classification'].get('label'),
            'confidence': appeal['original_classification'].get('confidence'),
        },
        
        'signal_breakdown': {
            'llm_judgment': {
                'score': signals.get('llm_judgment', {}).get('score'),
                'reasoning': signals.get('llm_judgment', {}).get('reasoning'),
            },
            'stylometry': {
                'score': signals.get('stylometry', {}).get('score'),
                'reasoning': signals.get('stylometry', {}).get('reasoning'),
                'subscores': signals.get('stylometry', {}).get('subscores', {}),
            },
            'perplexity': {
                'score': signals.get('perplexity', {}).get('score'),
                'reasoning': signals.get('perplexity', {}).get('reasoning'),
                'raw_perplexity': signals.get('perplexity', {}).get('raw_perplexity'),
            },
        },
        
        'appeal_details': {
            'reasoning': appeal['appeal_details']['reasoning'],
            'writing_date': appeal['appeal_details']['writing_date'],
            'process_duration_hours': appeal['appeal_details']['process_duration_hours'],
            'writing_process': appeal['appeal_details']['writing_process'],
            'native_language': appeal['appeal_details']['native_language'],
            'ai_assisted': appeal['appeal_details']['ai_assisted'],
            'ai_tools_detail': appeal['appeal_details']['ai_tools_detail'],
            'additional_context': appeal['appeal_details'].get('additional_context', ''),
            'supporting_files': appeal['appeal_details'].get('supporting_files', []),
        }
    }