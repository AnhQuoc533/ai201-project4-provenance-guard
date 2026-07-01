import re


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, 'Email is required'
    
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, 'Email format is invalid'
    
    return True, None


def validate_reasoning(reasoning):
    """
    Validate appeal reasoning field.
    
    Args:
        reasoning (str): Creator's explanation for appeal.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not reasoning or not isinstance(reasoning, str):
        return False, 'Reasoning is required'
    
    word_count = len(reasoning.strip().split())
    
    if word_count < 10:
        return False, 'Reasoning must be at least 10 words'
    
    if word_count > 500:
        return False, 'Reasoning must not exceed 500 words'
    
    return True, None


def validate_writing_date(date_str):
    """
    Validate writing date format (YYYY-MM-DD).
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not date_str or not isinstance(date_str, str):
        return False, 'Writing date is required'
    
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False, 'Date must be in YYYY-MM-DD format'
    
    return True, None


def validate_process_duration(duration):
    """
    Validate process duration in hours.
    
    Args:
        duration (int or float): Duration in hours.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if duration is None:
        return False, 'Process duration is required'
    
    try:
        hours = float(duration)
        if hours < 0:
            return False, 'Duration cannot be negative'
        if hours > 10000:
            return False, 'Duration seems unreasonably long'
        return True, None
    except (ValueError, TypeError):
        return False, 'Duration must be a number'


def validate_writing_process(process):
    """
    Validate writing process selection.
    
    Args:
        process (str): Writing process type.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_processes = [
        'original composition',
        'revised from drafts',
        'research-based',
        'response to events',
        'others',
    ]
    
    if not process or not isinstance(process, str):
        return False, 'Writing process is required'
    
    if process.lower() not in valid_processes:
        return False, f'Writing process must be one of: {", ".join(valid_processes)}'
    
    return True, None


def validate_native_language(language):
    """
    Validate native language field.
    
    Args:
        language (str): Native language.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not language or not isinstance(language, str):
        return False, 'Native language is required'
    
    if len(language.strip()) < 2:
        return False, 'Language name must be at least 2 characters'
    
    return True, None


def validate_ai_tool_disclosure(ai_assisted, tools_detail=None):
    """
    Validate AI tool disclosure field.
    
    Args:
        ai_assisted (bool): Whether AI tools were used.
        tools_detail (str): Details about AI tools used.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(ai_assisted, bool):
        return False, 'AI tool disclosure must be boolean'
    
    if ai_assisted and tools_detail:
        word_count = len(tools_detail.strip().split())
        if word_count < 5:
            return False, 'AI tools detail must be at least 5 words'
        if word_count > 500:
            return False, 'AI tools detail must not exceed 500 words'
    
    return True, None


def validate_additional_context(context):
    """
    Validate additional context field (optional).
    
    Args:
        context (str): Additional context provided by creator.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if context is None or context == '':
        return True, None
    
    if not isinstance(context, str):
        return False, 'Additional context must be a string'
    
    word_count = len(context.strip().split())
    if word_count > 500:
        return False, 'Additional context must not exceed 500 words'
    
    return True, None


def validate_appeal_form(form_data):
    """
    Validate entire appeal form.
    
    Args:
        form_data (dict): Appeal form data from request.
    
    Returns:
        tuple: (is_valid, error_messages_dict)
    """
    errors = {}
    
    if 'email' not in form_data:
        errors['email'] = 'Email is required'
    else:
        is_valid, error = validate_email(form_data['email'])
        if not is_valid:
            errors['email'] = error
    
    if 'reasoning' not in form_data:
        errors['reasoning'] = 'Reasoning is required'
    else:
        is_valid, error = validate_reasoning(form_data['reasoning'])
        if not is_valid:
            errors['reasoning'] = error
    
    if 'writing_date' not in form_data:
        errors['writing_date'] = 'Writing date is required'
    else:
        is_valid, error = validate_writing_date(form_data['writing_date'])
        if not is_valid:
            errors['writing_date'] = error
    
    if 'process_duration_hours' not in form_data:
        errors['process_duration_hours'] = 'Process duration is required'
    else:
        is_valid, error = validate_process_duration(form_data['process_duration_hours'])
        if not is_valid:
            errors['process_duration_hours'] = error
    
    if 'writing_process' not in form_data:
        errors['writing_process'] = 'Writing process is required'
    else:
        is_valid, error = validate_writing_process(form_data['writing_process'])
        if not is_valid:
            errors['writing_process'] = error
    
    if 'native_language' not in form_data:
        errors['native_language'] = 'Native language is required'
    else:
        is_valid, error = validate_native_language(form_data['native_language'])
        if not is_valid:
            errors['native_language'] = error
    
    if 'ai_assisted' not in form_data:
        errors['ai_assisted'] = 'AI tool disclosure is required'
    else:
        tools_detail = form_data.get('ai_tools_detail')
        is_valid, error = validate_ai_tool_disclosure(form_data['ai_assisted'], tools_detail)
        if not is_valid:
            errors['ai_assisted'] = error
    
    if 'additional_context' in form_data:
        is_valid, error = validate_additional_context(form_data['additional_context'])
        if not is_valid:
            errors['additional_context'] = error
    
    return len(errors) == 0, errors