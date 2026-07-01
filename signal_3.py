def perplexity_calculation(text):
    """
    Evaluate text using perplexity measurement.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -1.0 for error), raw perplexity, and reasoning.
    """
    if not text or not isinstance(text, str):
        return {
            'score': -1.0,
            'raw_perplexity': None,
            'reasoning': 'Invalid input text for perplexity analysis',
        }
    
    try:
        words = text.lower().split()
        
        if not words:
            return {
                'score': -1.0,
                'raw_perplexity': None,
                'reasoning': 'Insufficient text content for perplexity analysis',
            }
        
        raw_perplexity = _calculate_perplexity(words)
        normalized_score = _normalize_perplexity(raw_perplexity)
        
        reasoning = f'Normalized perplexity {normalized_score:.2f} (raw: {raw_perplexity:.1f})'
        
        return {
            'score': normalized_score,
            'raw_perplexity': raw_perplexity,
            'reasoning': reasoning,
        }
    except Exception as e:
        return {
            'score': -1.0,
            'raw_perplexity': None,
            'reasoning': f'Perplexity analysis error: {str(e)}',
        }
    
def _calculate_perplexity(words):
    """Calculate perplexity based on word frequency."""
    from collections import Counter
    import math
    
    if not words:
        return 100.0
    
    word_freq = Counter(words)
    total_words = len(words)
    cross_entropy = 0.0
    
    for word in words:
        probability = word_freq[word] / total_words
        if probability > 0:
            cross_entropy -= math.log2(probability)
    
    cross_entropy /= total_words
    perplexity = 2 ** cross_entropy
    
    return perplexity


def _normalize_perplexity(raw_perplexity):
    """Normalize perplexity to 0.0-1.0 scale."""
    min_perplexity = 10.0
    max_perplexity = 300.0
    
    normalized = (raw_perplexity - min_perplexity) / (max_perplexity - min_perplexity)
    return min(1.0, max(0.0, normalized))