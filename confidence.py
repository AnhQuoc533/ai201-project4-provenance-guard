from config import CONFIDENCE_WEIGHTS, CONFIDENCE_THRESHOLDS


def aggregate_confidence(signals):
    """
    Aggregate three signal scores into unified confidence score.
    
    Args:
        signals (dict): Scores for llm_judgment, stylometry, perplexity.
    
    Returns:
        float: Unified confidence score (0.0-1.0).
    """
    llm_score = signals['llm_judgment']['score']
    stylometry_score = signals['stylometry']['score']
    perplexity_score = signals['perplexity']['score']
    
    llm_score = 0.5 if llm_score < 0 else llm_score
    stylometry_score = 0.5 if stylometry_score < 0 else stylometry_score
    perplexity_score = 0.5 if perplexity_score < 0 else perplexity_score
    
    confidence = (
        llm_score * CONFIDENCE_WEIGHTS['llm_judgment'] +
        stylometry_score * CONFIDENCE_WEIGHTS['stylometry'] +
        perplexity_score * CONFIDENCE_WEIGHTS['perplexity']
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
