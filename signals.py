import json
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL


def _get_groq_client():
    """Initialize Groq client with API key from environment."""
    if not GROQ_API_KEY:
        raise ValueError('GROQ_API_KEY environment variable not set')
    return Groq(api_key=GROQ_API_KEY)


def _extract_json(response_text):
    """Extract JSON object from response text."""
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def llm_judgment(text):
    """
    Evaluate text using LLM semantic analysis.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -1.0 for error) and reasoning.
    """
    if not text or not isinstance(text, str):
        return {
            'score': -1.0,
            'reasoning': 'Invalid input text for analysis',
        }
    
    try:
        client = _get_groq_client()
        
        prompt = (
            "Analyze whether this text is human-written or AI-generated. "
            "Consider these factors:\n"
            "- Semantic coherence and reasoning patterns\n"
            "- Contextual consistency and narrative flow\n"
            "- Logical argumentation structure\n"
            "- Stylistic authenticity and genuine voice\n"
            "- Unexpected tangents or authentic curiosity\n"
            "- Emotional genuineness and originality\n\n"
            f"Text to analyze:\n{text}\n\n"
            "Respond with JSON only: "
            "{\"score\": <number 0.0 to 1.0>, \"reasoning\": \"<explanation>\"}\n"
            "Where: 0.0 = very likely human-written, 1.0 = very likely AI-generated"
        )
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0,
        )
        
        response_text = response.choices[0].message.content
        parsed = _extract_json(response_text)
        
        if parsed and isinstance(parsed, dict) and 'score' in parsed:
            score = float(parsed['score'])
            score = max(0.0, min(1.0, score))
            reasoning = str(parsed.get('reasoning', 'Analysis complete'))
            return {
                'score': score,
                'reasoning': reasoning,
            }
        
        return {
            'score': -1.0,
            'reasoning': 'Could not parse LLM response format',
        }
        
    except ValueError as e:
        return {
            'score': -1.0,
            'reasoning': f'Configuration error: {str(e)}',
        }
    except Exception as e:
        return {
            'score': -1.0,
            'reasoning': f'LLM analysis error: {str(e)}',
        }


def stylometric_heuristics(text):
    """
    Evaluate text using stylometric features.
    
    Placeholder: Returns 0.5 with generic reasoning.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -1.0 for error), subscores, and reasoning.
    """
    return {
        'score': 0.5,
        'subscores': {
            'entropy': 0.5,
            'lexical_diversity': 0.5,
            'sentence_variance': 0.5,
            'rare_word_ratio': 0.5,
            'function_word_ratio': 0.5,
            'ngram_deviation': 0.5,
        },
        'reasoning': 'Stylometry placeholder - implementation pending.',
    }


def perplexity_calculation(text):
    """
    Evaluate text using perplexity measurement.
    
    Placeholder: Returns 0.5 with generic reasoning.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -1.0 for error), raw perplexity, and reasoning.
    """
    return {
        'score': 0.5,
        'raw_perplexity': 100.0,
        'reasoning': 'Perplexity placeholder - implementation pending.',
    }