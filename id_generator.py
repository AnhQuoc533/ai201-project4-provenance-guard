import uuid
from datetime import datetime, timezone


def generate_content_id():
    """
    Generate unique content ID.
    
    Format: CTN-YYYY-MM-DD-XXXX where XXXX is a random hex string.
    
    Returns:
        str: Generated content ID.
    """
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f'CTN-{today}-{random_suffix}'


def generate_decision_id():
    """
    Generate unique decision ID.
    
    Format: DEC-YYYY-MM-DD-XXXX where XXXX is a random hex string.
    
    Returns:
        str: Generated decision ID.
    """
    today = datetime.utcnow().strftime('%Y-%m-%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f'DEC-{today}-{random_suffix}'
