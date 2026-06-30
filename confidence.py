from config import CONFIDENCE_WEIGHTS, CONFIDENCE_THRESHOLDS


def aggregate_confidence(signals):
    """
    Aggregate three signal scores into unified confidence score.
    
    Placeholder: Uses weighted average formula from specification.
    
    Args:
        signals (dict): Scores for llm_judgment, stylometry, perplexity.
    
    Returns:
        float: Unified confidence score (0.0-1.0).
    """
    confidence = (
        signals['llm_judgment']['score'] * CONFIDENCE_WEIGHTS['llm_judgment'] +
        signals['stylometry']['score'] * CONFIDENCE_WEIGHTS['stylometry'] +
        signals['perplexity']['score'] * CONFIDENCE_WEIGHTS['perplexity']
    )
    return round(confidence, 4)


def get_label(confidence):
    """
    Map confidence score to classification label.
    
    Args:
        confidence (float): Unified confidence score (0.0-1.0).
    
    Returns:
        str: classification label.
    """
    for min_score, max_score, label in CONFIDENCE_THRESHOLDS:
        if min_score <= confidence <= max_score:
            return label
    return 'Invalid Result'
