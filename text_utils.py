"""Text processing utilities."""

import re


def count_words(text):
    """Count words, sentences, and characters for essay writing."""
    if not text or not text.strip():
        return 0, 0, 0
    
    # Word count (split by whitespace)
    words = len(text.split())
    
    # Sentence count (rough estimate)
    sentences = text.count('.') + text.count('!') + text.count('?')
    
    # Character count (excluding whitespace)
    chars = len(text.replace(' ', '').replace('\n', ''))
    
    return words, sentences, chars


def contains_numbers(text):
    """Check if text contains any numbers (to determine if grading is relevant)."""
    return bool(re.search(r'\d', text))
