def stylometric_heuristics(text):
    """
    Evaluate text using stylometric features.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -1.0 for error), subscores, and reasoning.
    """
    if not text or not isinstance(text, str):
        return {
            'score': -1.0,
            'subscores': {},
            'reasoning': 'Invalid input text for stylometry analysis',
        }
    
    try:
        words = text.lower().split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not words or not sentences:
            return {
                'score': -1.0,
                'subscores': {},
                'reasoning': 'Insufficient text content for stylometry analysis',
            }
        
        entropy_score = _calculate_entropy(words)
        lexical_diversity = _calculate_lexical_diversity(words)
        sentence_variance = _calculate_sentence_variance(sentences)
        rare_word_ratio = _calculate_rare_word_ratio(words)
        function_word_ratio = _calculate_function_word_ratio(words)
        ngram_deviation = _calculate_ngram_deviation(words)
        
        subscores = {
            'entropy': entropy_score,
            'lexical_diversity': lexical_diversity,
            'sentence_variance': sentence_variance,
            'rare_word_ratio': rare_word_ratio,
            'function_word_ratio': function_word_ratio,
            'ngram_deviation': ngram_deviation,
        }
        
        avg_score = sum(subscores.values()) / len(subscores)
        
        reasoning = (
            f'Entropy: {entropy_score:.2f}, '
            f'Lexical diversity: {lexical_diversity:.2f}, '
            f'Sentence variance: {sentence_variance:.2f}, '
            f'Rare word ratio: {rare_word_ratio:.2f}, '
            f'Function word ratio: {function_word_ratio:.2f}, '
            f'N-gram deviation: {ngram_deviation:.2f}'
        )
        
        return {
            'score': round(avg_score, 4),
            'subscores': subscores,
            'reasoning': reasoning,
        }
    except Exception as e:
        return {
            'score': -1.0,
            'subscores': {},
            'reasoning': f'Stylometry analysis error: {str(e)}',
        }


def _calculate_entropy(words):
    """Calculate Shannon entropy of word distribution."""
    from collections import Counter
    import math
    
    if not words:
        return 0.0
    
    word_freq = Counter(words)
    total_words = len(words)
    entropy = 0.0
    
    for count in word_freq.values():
        probability = count / total_words
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    max_entropy = math.log2(min(len(word_freq), total_words))
    if max_entropy == 0:
        return 0.0
    
    normalized_entropy = entropy / max_entropy
    return min(1.0, max(0.0, normalized_entropy))


def _calculate_lexical_diversity(words):
    """Calculate lexical diversity using type-token ratio."""
    if not words:
        return 0.0
    
    unique_words = len(set(words))
    total_words = len(words)
    ttr = unique_words / total_words
    
    return min(1.0, max(0.0, ttr))


def _calculate_sentence_variance(sentences):
    """Calculate variance in sentence lengths."""
    if len(sentences) < 2:
        return 0.5
    
    sentence_lengths = [len(s.split()) for s in sentences]
    mean_length = sum(sentence_lengths) / len(sentence_lengths)
    
    if mean_length == 0:
        return 0.5
    
    variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    std_dev = variance ** 0.5
    coefficient_of_variation = std_dev / mean_length
    
    normalized_variance = min(1.0, max(0.0, coefficient_of_variation / 2))
    return normalized_variance


def _calculate_rare_word_ratio(words):
    """Calculate ratio of words that appear only once."""
    from collections import Counter
    
    if not words:
        return 0.0
    
    word_freq = Counter(words)
    rare_words = sum(1 for count in word_freq.values() if count == 1)
    ratio = rare_words / len(word_freq) if word_freq else 0.0
    
    return min(1.0, max(0.0, ratio))


def _calculate_function_word_ratio(words):
    """Calculate ratio of common function words."""
    function_words = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'is', 'was', 'are', 'been',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
    }
    
    if not words:
        return 0.0
    
    function_word_count = sum(1 for word in words if word in function_words)
    ratio = function_word_count / len(words)
    
    return min(1.0, max(0.0, ratio))


def _calculate_ngram_deviation(words):
    """Calculate n-gram diversity."""
    if len(words) < 2:
        return 0.5
    
    bigrams = [f'{words[i]} {words[i+1]}' for i in range(len(words)-1)]
    unique_bigrams = len(set(bigrams))
    total_bigrams = len(bigrams)
    
    diversity = unique_bigrams / total_bigrams if total_bigrams > 0 else 0.0
    return min(1.0, max(0.0, diversity))
