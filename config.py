"""Configuration and constants for the Gemini QA System."""

# Model Names
MODEL_PRO = "gemini-2.5-pro"
MODEL_FLASH = "gemini-2.5-flash"

# Agent Settings
DEFAULT_MAX_REFINEMENTS = 3
WORD_COUNT_TOLERANCE = 0.10  # 10% tolerance

# File Settings
SUPPORTED_EXTENSIONS = [
    # Images
    "png", "jpg", "jpeg", "webp", "heic", "heif",
    
    # Documents
    "pdf", "txt", "md", "rtf",
    
    # Code files
    "py", "js", "java", "c", "cpp", "cs", "go", "rb", "php", "swift", "kt",
    "m", "r", "sql", "sh", "bash", "yml", "yaml", "json", "xml", "html", "css",
    
    # Data files
    "csv", "tsv", "xls", "xlsx",
    
    # Audio
    "mp3", "wav", "mpeg", "m4a", "ogg", "flac",
    
    # Video
    "mp4", "mov", "avi", "wmv", "flv", "mpg", "mpeg", "webm", "mkv",
    
    # Archives (if supported by your application)
    "zip", "tar", "gz",
    
    # Other
    "log", "cfg", "conf", "ini"
]
TEXT_ENCODINGS = ['utf-8', 'latin-1', 'cp1252']

# UI Settings
PAGE_TITLE = "Gemini Multi-Agent QA System"
PAGE_ICON = "🤖"