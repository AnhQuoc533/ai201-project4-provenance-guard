import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel


def perplexity_calculation(text):
    """
    Evaluate text using language-model perplexity.
    
    Args:
        text (str): Normalized text to evaluate.
    
    Returns:
        dict: Score (0.0-1.0, or -100.0 for error), raw perplexity, and reasoning.
    """
    if not text or not isinstance(text, str):
        return {
            'score': -100.0,
            'raw_perplexity': None,
            'reasoning': 'Invalid input text for perplexity analysis',
        }
    
    try:
        text = text.strip()
        if not text:
            return {
                'score': -100.0,
                'raw_perplexity': None,
                'reasoning': 'Insufficient text content for perplexity analysis',
            }
        
        raw_perplexity = _calculate_gpt2_perplexity(text)
        normalized_score = _normalize_perplexity(raw_perplexity)
        
        reasoning = f'Normalized perplexity {normalized_score:.2f} (raw: {raw_perplexity:.1f})'
        
        return {
            'score': normalized_score,
            'raw_perplexity': raw_perplexity,
            'reasoning': reasoning,
        }
    except Exception as e:
        return {
            'score': -100.0,
            'raw_perplexity': None,
            'reasoning': f'Perplexity analysis error: {str(e)}',
        }


def tokenize(text, is_readable=False):
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    tokens = tokenizer.encode(text, return_tensors='pt')
    if is_readable:
        return tokenizer.convert_ids_to_tokens(tokens.squeeze().tolist())
    else:
        return tokens


def _calculate_gpt2_perplexity(text):
    """Calculate perplexity using GPT-2 language model."""
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    model.eval()    
    tokens = tokenize(text)
    
    if tokens.shape[1] < 20:
        raise ValueError("The submitted text contains fewer than 20 tokens.")
    
    with torch.no_grad():
        outputs = model(tokens, labels=tokens)
        loss = outputs.loss
        perplexity = torch.exp(loss).item()
    
    return perplexity


def _normalize_perplexity(raw_perplexity):
    """
    Normalize perplexity to 0.0-1.0 scale using min-max normalization. 
    0.0 indicates "very high perplexity (human-written)" and 1.0 indicates "very low perplexity (AI-generated).
    """
    min_perplexity = 10.0   # well below AI range
    max_perplexity = 50.0  # typical human upper range
    
    if raw_perplexity <= min_perplexity:
        return 1.0
    if raw_perplexity >= max_perplexity:
        return 0.0
    
    normalized = (raw_perplexity - min_perplexity) / (max_perplexity - min_perplexity)
    return 1 - min(1.0, max(0.0, normalized))
    