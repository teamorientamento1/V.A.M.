"""
Schema del database per l'archivio di conoscenze multidisciplinare
"""

SCHEMA_VERSION = "1.0.0"

# Schema SQL per SQLite
DATABASE_SCHEMA = """
-- Versione dello schema
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Discipline scientifiche
CREATE TABLE IF NOT EXISTS disciplines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pattern generali (formule, diagrammi, strutture)
CREATE TABLE IF NOT EXISTS content_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discipline_id INTEGER,
    pattern_type TEXT NOT NULL,  -- 'formula', 'diagram', 'table', 'notation', etc.
    visual_signature TEXT,       -- Hash o descrittore visivo
    latex_representation TEXT,
    mathml_representation TEXT,
    content_description TEXT,
    context_words TEXT,          -- JSON array di parole chiave
    frequency INTEGER DEFAULT 1,
    confidence_score REAL DEFAULT 0.5,
    variations TEXT,             -- JSON con varianti
    tts_rule TEXT,              -- Regola per sintesi vocale
    created_from TEXT,          -- 'word_analysis' o 'pdf_recognition' o 'user_input'
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
);

-- Simboli e notazioni
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    unicode_code TEXT,
    latex_code TEXT,
    category TEXT,               -- 'greek', 'operator', 'relation', 'unit', etc.
    discipline_id INTEGER,
    default_pronunciation TEXT,
    user_pronunciations TEXT,    -- JSON con preferenze personalizzate
    context_variants TEXT,       -- JSON: pronuncia diversa in contesti diversi
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
);

-- Componenti di formule/strutture
CREATE TABLE IF NOT EXISTS formula_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,
    component_type TEXT,         -- 'superscript', 'subscript', 'numerator', 'denominator', etc.
    content TEXT,
    position_index INTEGER,
    parent_component_id INTEGER, -- Per strutture annidate
    FOREIGN KEY (pattern_id) REFERENCES content_patterns(id),
    FOREIGN KEY (parent_component_id) REFERENCES formula_components(id)
);

-- Contesti di apprendimento
CREATE TABLE IF NOT EXISTS learned_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,
    surrounding_text TEXT,
    figure_references TEXT,      -- JSON array di riferimenti (Fig.X.Y)
    chapter_section TEXT,
    document_type TEXT,          -- 'textbook', 'paper', 'slides', etc.
    confidence REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES content_patterns(id)
);

-- Relazioni tra pattern (es: "questa formula è una variante di...")
CREATE TABLE IF NOT EXISTS pattern_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id_1 INTEGER,
    pattern_id_2 INTEGER,
    relationship_type TEXT,      -- 'variant', 'simplification', 'generalization', etc.
    similarity_score REAL,
    FOREIGN KEY (pattern_id_1) REFERENCES content_patterns(id),
    FOREIGN KEY (pattern_id_2) REFERENCES content_patterns(id)
);

-- Documenti analizzati (per tracciabilità)
CREATE TABLE IF NOT EXISTS analyzed_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_hash TEXT UNIQUE,       -- Hash del file per evitare duplicati
    document_type TEXT,          -- 'docx', 'pdf'
    discipline_id INTEGER,
    patterns_extracted INTEGER DEFAULT 0,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
);

-- Log delle modifiche (per audit e backup incrementali)
CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    record_id INTEGER,
    operation TEXT,              -- 'INSERT', 'UPDATE', 'DELETE'
    old_data TEXT,               -- JSON
    new_data TEXT,               -- JSON
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_action BOOLEAN DEFAULT 0 -- True se modificato dall'utente
);

-- Backup metadata
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_type TEXT,            -- 'full', 'incremental'
    records_count INTEGER,
    file_size_bytes INTEGER,
    checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_patterns_discipline ON content_patterns(discipline_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON content_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_frequency ON content_patterns(frequency);
CREATE INDEX IF NOT EXISTS idx_symbols_category ON symbols(category);
CREATE INDEX IF NOT EXISTS idx_symbols_discipline ON symbols(discipline_id);
CREATE INDEX IF NOT EXISTS idx_contexts_pattern ON learned_contexts(pattern_id);
CREATE INDEX IF NOT EXISTS idx_change_log_table ON change_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_backup_created ON backup_history(created_at);
"""

# Discipline predefinite
INITIAL_DISCIPLINES = [
    ("mathematics", "Matematica - formule, teoremi, dimostrazioni"),
    ("physics", "Fisica - leggi, costanti, unità di misura"),
    ("chemistry", "Chimica - formule molecolari, reazioni, stechiometria"),
    ("biology", "Biologia - nomenclatura, processi, classificazioni"),
    ("engineering", "Ingegneria - calcoli, schemi, progetti"),
    ("computer_science", "Informatica - algoritmi, pseudocodice, notazioni"),
    ("statistics", "Statistica - formule, distribuzioni, test"),
    ("generic", "Contenuti generici o multidisciplinari")
]
