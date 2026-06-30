from config import Config


def aggregate_confidence(signals):
    """
    Aggregate three signal scores into unified confidence score.
    
    Placeholder: Uses weighted average formula from specification.
    
    Args:
        signals (dict): Scores for llm_judgment, stylometry, perplexity.
    
    Returns:
        float: Unified confidence score (0.0-1.0).
    """
    weights = Config.CONFIDENCE_WEIGHTS
    confidence = (
        signals['llm_judgment']['score'] * weights['llm_judgment'] +
        signals['stylometry']['score'] * weights['stylometry'] +
        signals['perplexity']['score'] * weights['perplexity']
    )
    return round(confidence, 4)


def get_label_for_confidence(confidence):
    """
    Map confidence score to transparency label.
    
    Args:
        confidence (float): Unified confidence score (0.0-1.0).
    
    Returns:
        str: Transparency label text.
    """
    for min_score, max_score, label in Config.CONFIDENCE_THRESHOLDS:
        if min_score <= confidence <= max_score:
            return label
    return 'Your text is AI-Generated'


def generate_label(confidence, signals):
    """
    Generate transparency label with confidence score and reasoning.
    
    Placeholder: Returns label template with placeholder reasoning.
    
    Args:
        confidence (float): Unified confidence score.
        signals (dict): All signal results.
    
    Returns:
        dict: Label text and reasoning.
    """
    label = get_label_for_confidence(confidence)
    confidence_percentage = int(confidence * 100)
    
    return {
        'label': label,
        'confidence_percentage': confidence_percentage,
        'reasoning': 'Transparency label placeholder - implementation pending.',
    }
