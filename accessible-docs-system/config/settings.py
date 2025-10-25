"""
Configurazione globale del sistema
"""
import os
from pathlib import Path

# Percorsi base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
BACKUP_DIR = DATA_DIR / "backups"
USER_DATA_DIR = DATA_DIR / "user_data"

# Database
DATABASE_PATH = KNOWLEDGE_BASE_DIR / "knowledge_base.db"
BACKUP_RETENTION_DAYS = 30  # Mantieni backup per 30 giorni
AUTO_BACKUP_INTERVAL = 3600  # Backup automatico ogni ora (in secondi)

# Discipline supportate
SUPPORTED_DISCIPLINES = [
    "mathematics",
    "physics", 
    "chemistry",
    "biology",
    "engineering",
    "computer_science",
    "statistics",
    "generic"  # Per contenuti non specifici
]

# OCR e riconoscimento
OCR_CONFIDENCE_THRESHOLD = 0.7
MATHPIX_API_KEY = None  # Da configurare
USE_MATHPIX = False  # Se True usa Mathpix, altrimenti fallback

# Analisi documento
CONTEXT_RADIUS = 150  # Caratteri da leggere attorno agli elementi
MIN_PATTERN_FREQUENCY = 3  # Minimo occorrenze per considerare un pattern
SIMILARITY_THRESHOLD = 0.85  # Soglia per pattern simili

# Jump Manager
JUMP_PREFIX = "DESC_"  # Prefisso per gli ancoraggi delle descrizioni
RETURN_TEXT = "↑ Torna al testo"  # Testo per link di ritorno
BLOCK_TTS_TAG = "<!--TTS:SKIP-->"  # Tag per bloccare sintesi vocale

# UI
WINDOW_TITLE = "Accessible Docs System"
WINDOW_SIZE = (1200, 800)
THEME = "light"  # light o dark

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = BASE_DIR / "logs" / "system.log"

# Export
DEFAULT_EXPORT_FORMAT = "docx"
PRESERVE_FORMATTING = True

# Creazione directory se non esistono
for directory in [DATA_DIR, KNOWLEDGE_BASE_DIR, BACKUP_DIR, USER_DATA_DIR, BASE_DIR / "logs"]:
    directory.mkdir(parents=True, exist_ok=True)
