from collections import Counter
from signal_3 import tokenize
import math


def stylometric_heuristics(text):
    """
    Evaluate text using stylometric features.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -100.0 for error), subscores, and reasoning.
    """
    if not text or not isinstance(text, str):
        return {
            'score': -100.0,
            'subscores': {},
            'reasoning': 'Invalid input text for stylometry analysis',
        }
    
    try:
        tokens = tokenize(text.lower(), is_readable=True)
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not tokens or not sentences:
            return {
                'score': -100.0,
                'subscores': {},
                'reasoning': 'Insufficient text content for stylometry analysis',
            }
        
        entropy_score = _calculate_entropy(tokens)
        lexical_diversity = _calculate_lexical_diversity(tokens)
        sentence_variance = _calculate_sentence_variance(sentences)
        function_word_ratio = _calculate_function_word_ratio(tokens)
        
        subscores = {
            'entropy': entropy_score,
            'lexical_diversity': lexical_diversity,
            'sentence_variance': sentence_variance,
            'function_word_ratio': function_word_ratio,
        }
        reasoning = (
            f'Entropy: {entropy_score:.2f}, '
            f'Lexical diversity: {lexical_diversity:.2f}, '
            f'Sentence variance: {sentence_variance:.2f}, '
            f'Function word ratio: {function_word_ratio:.2f}'
        )

        if len(tokens) > 200:
            subscores['rare_word_ratio'] = _calculate_rare_word_ratio(tokens)
            subscores['ngram_deviation'] = _calculate_ngram_deviation(tokens)
            reasoning += f', Rare word ratio: {subscores['rare_word_ratio']}, N-gram deviation: {subscores['ngram_deviation']}'
        
        return {
            'score': sum(subscores.values()) / len(subscores),
            'subscores': subscores,
            'reasoning': reasoning,
        }
    except Exception as e:
        return {
            'score': -100.0,
            'subscores': {},
            'reasoning': f'Stylometry analysis error: {str(e)}',
        }


def _calculate_entropy(words):
    """Calculate Shannon entropy of word distribution."""    
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
    return 1.0 - min(1.0, max(0.0, normalized_entropy))


def _calculate_lexical_diversity(words):
    """Calculate lexical diversity using type-token ratio."""
    if not words:
        return 0.0
    
    unique_words = len(set(words))
    total_words = len(words)
    ttr = unique_words / total_words
    
    return 1.0 - min(1.0, max(0.0, ttr))


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
    return 1.0 - min(1.0, max(0.0, coefficient_of_variation / 2))


def _calculate_rare_word_ratio(words):
    """Calculate ratio of observed rare words to expected rare words."""    
    if not words:
        return 0.0
    
    word_freq = Counter(words)
    observed_rare_words = sum(1 for count in word_freq.values() if count == 1)
    unique_words = len(word_freq)
    
    expected_rare_ratio = 0.25
    expected_rare_words = unique_words * expected_rare_ratio
    
    if expected_rare_words == 0:
        return 0.0
    
    ratio = observed_rare_words / expected_rare_words    
    return 1.0 - min(1.0, max(0.0, ratio))


def _calculate_function_word_ratio(words):
    """Calculate deviation of function word ratio from baseline."""
    function_words = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'is', 'was', 'are', 'been',
        'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
    }
    
    if not words:
        return 0.0
    
    function_word_count = sum(1 for word in words if word in function_words)
    observed_ratio = function_word_count / len(words)
    
    baseline_ratio = 0.38
    deviation = abs(observed_ratio - baseline_ratio) / baseline_ratio
    return 1.0 - min(1.0, max(0.0, deviation))


def _calculate_ngram_deviation(words):
    """Calculate n-gram deviation using chi-squared test."""
    if len(words) < 2:
        return 0.5
    
    bigrams = [f'{words[i]} {words[i+1]}' for i in range(len(words)-1)]
    
    if not bigrams:
        return 0.5
    
    observed_freq = Counter(bigrams)
    total_bigrams = len(bigrams)
    unique_bigrams = len(observed_freq)
    
    expected_freq = total_bigrams / unique_bigrams if unique_bigrams > 0 else total_bigrams    
    chi_squared = sum((obs - expected_freq) ** 2 / expected_freq for obs in observed_freq.values() if expected_freq > 0)
    
    max_chi_squared = total_bigrams * (unique_bigrams - 1)
    if max_chi_squared == 0:
        return 0.5
    
    return 1.0 - min(1.0, chi_squared / max_chi_squared)