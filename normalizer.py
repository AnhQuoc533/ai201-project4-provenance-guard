import re
import html

def normalize_content(text):
    """
    Normalize text by handling whitespace, line breaks, and HTML entities.
    
    Args:
        text (str): Raw text to normalize.
    
    Returns:
        str: Normalized text.
    """
    if not isinstance(text, str):
        return ''
    
    text = html.unescape(text)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = text.strip()
    
    return text
