"""Text processing utilities."""

import re


def strip_markdown(text):
    """Remove markdown formatting for clean text output."""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'``````', '', text)
    text = re.sub(r'^[-*]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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