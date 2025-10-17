"""Configuration and constants for the Gemini QA System."""

# Model Names
MODEL_PRO = "gemini-2.5-pro"
MODEL_FLASH = "gemini-2.5-flash"

# Agent Settings
DEFAULT_MAX_REFINEMENTS = 3
WORD_COUNT_TOLERANCE = 0.10  # 10% tolerance

# File Settings
SUPPORTED_EXTENSIONS = ['txt', 'pdf', 'md', 'py', 'json', 'csv', 'm']
TEXT_ENCODINGS = ['utf-8', 'latin-1', 'cp1252']

# UI Settings
PAGE_TITLE = "Gemini Multi-Agent QA System"
PAGE_ICON = "🤖"