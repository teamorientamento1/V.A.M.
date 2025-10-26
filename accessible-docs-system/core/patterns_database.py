"""
Patterns Database - Database SQLite per pattern configurabili
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional


class PatternsDatabase:
    """Gestisce database pattern per riconoscimento elementi"""
    
    def __init__(self, db_path: str = "data/patterns.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Inizializza database con schema"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Tabella pattern keyword
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_type TEXT NOT NULL,
                keyword TEXT NOT NULL,
                language TEXT DEFAULT 'it',
                is_abbreviation BOOLEAN DEFAULT 0,
                is_plural BOOLEAN DEFAULT 0,
                enabled BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                UNIQUE(element_type, keyword, language)
            )
        ''')
        
        # Tabella categorie elementi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS element_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                parent_category TEXT,
                description TEXT,
                color TEXT DEFAULT '#3498db',
                enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabella esempi trovati (per machine learning futuro)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                document_name TEXT,
                context TEXT,
                matched_text TEXT,
                paragraph_index INTEGER,
                confidence REAL DEFAULT 1.0,
                verified BOOLEAN DEFAULT 0,
                found_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES patterns(id)
            )
        ''')
        
        # Tabella regex custom
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_regex (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_type TEXT NOT NULL,
                regex_pattern TEXT NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                test_cases TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indici per performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(element_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_enabled ON patterns(enabled)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_examples_pattern ON pattern_examples(pattern_id)')
        
        self.conn.commit()
        
        # Popola dati default se vuoto
        if self.get_pattern_count() == 0:
            self._populate_default_patterns()
    
    def _populate_default_patterns(self):
        """Popola pattern di default"""
        default_patterns = [
            # Figure
            ('figure', 'figura', 'it', False, False, 1, 10),
            ('figure', 'figure', 'it', False, True, 1, 10),
            ('figure', 'fig', 'it', True, False, 1, 10),
            ('figure', 'fig.', 'it', True, False, 1, 10),
            ('figure', 'figure', 'en', False, False, 1, 10),
            ('figure', 'figures', 'en', False, True, 1, 10),
            ('figure', 'fig', 'en', True, False, 1, 10),
            ('figure', 'fig.', 'en', True, False, 1, 10),
            
            # Esempi
            ('figure', 'esempio', 'it', False, False, 1, 8),
            ('figure', 'esempi', 'it', False, True, 1, 8),
            ('figure', 'es.', 'it', True, False, 1, 8),
            ('figure', 'example', 'en', False, False, 1, 8),
            ('figure', 'ex.', 'en', True, False, 1, 8),
            
            # Grafici
            ('figure', 'grafico', 'it', False, False, 1, 9),
            ('figure', 'grafici', 'it', False, True, 1, 9),
            ('figure', 'graf.', 'it', True, False, 1, 9),
            ('figure', 'graph', 'en', False, False, 1, 9),
            
            # Immagini
            ('figure', 'immagine', 'it', False, False, 1, 7),
            ('figure', 'immagini', 'it', False, True, 1, 7),
            ('figure', 'img', 'it', True, False, 1, 7),
            ('figure', 'img.', 'it', True, False, 1, 7),
            ('figure', 'image', 'en', False, False, 1, 7),
            
            # Tabelle
            ('table', 'tabella', 'it', False, False, 1, 10),
            ('table', 'tabelle', 'it', False, True, 1, 10),
            ('table', 'tab', 'it', True, False, 1, 10),
            ('table', 'tab.', 'it', True, False, 1, 10),
            ('table', 'table', 'en', False, False, 1, 10),
            ('table', 'tables', 'en', False, True, 1, 10),
            
            # Equazioni
            ('equation', 'equazione', 'it', False, False, 1, 10),
            ('equation', 'equazioni', 'it', False, True, 1, 10),
            ('equation', 'eq', 'it', True, False, 1, 10),
            ('equation', 'eq.', 'it', True, False, 1, 10),
            ('equation', 'equation', 'en', False, False, 1, 10),
            ('equation', 'equations', 'en', False, True, 1, 10),
            
            # Schema/Diagrammi
            ('diagram', 'schema', 'it', False, False, 1, 8),
            ('diagram', 'schemi', 'it', False, True, 1, 8),
            ('diagram', 'sch.', 'it', True, False, 1, 8),
            ('diagram', 'diagram', 'en', False, False, 1, 8),
            ('diagram', 'diagramma', 'it', False, False, 1, 8),
        ]
        
        cursor = self.conn.cursor()
        for pattern in default_patterns:
            cursor.execute('''
                INSERT OR IGNORE INTO patterns 
                (element_type, keyword, language, is_abbreviation, is_plural, enabled, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', pattern)
        
        # Categorie default
        categories = [
            ('figure', None, 'Immagini e figure', '#3498db'),
            ('table', None, 'Tabelle e dati', '#2ecc71'),
            ('equation', None, 'Equazioni matematiche', '#e74c3c'),
            ('diagram', None, 'Schemi e diagrammi', '#f39c12'),
        ]
        
        for cat in categories:
            cursor.execute('''
                INSERT OR IGNORE INTO element_categories 
                (category_name, parent_category, description, color)
                VALUES (?, ?, ?, ?)
            ''', cat)
        
        self.conn.commit()
    
    def add_pattern(self, element_type: str, keyword: str, **kwargs) -> int:
        """Aggiunge nuovo pattern"""
        cursor = self.conn.cursor()
        
        language = kwargs.get('language', 'it')
        is_abbrev = kwargs.get('is_abbreviation', False)
        is_plural = kwargs.get('is_plural', False)
        enabled = kwargs.get('enabled', True)
        priority = kwargs.get('priority', 5)
        notes = kwargs.get('notes', '')
        
        try:
            cursor.execute('''
                INSERT INTO patterns 
                (element_type, keyword, language, is_abbreviation, is_plural, enabled, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (element_type, keyword, language, is_abbrev, is_plural, enabled, priority, notes))
            
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1  # Già esistente
    
    def get_patterns(self, element_type: str = None, enabled_only: bool = True) -> List[Dict]:
        """Ottiene pattern dal database"""
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM patterns WHERE 1=1'
        params = []
        
        if element_type:
            query += ' AND element_type = ?'
            params.append(element_type)
        
        if enabled_only:
            query += ' AND enabled = 1'
        
        query += ' ORDER BY priority DESC, keyword ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_all_keywords(self, element_type: str = None) -> List[str]:
        """Ottiene lista keyword per tipo"""
        patterns = self.get_patterns(element_type, enabled_only=True)
        return [p['keyword'] for p in patterns]
    
    def update_pattern(self, pattern_id: int, **kwargs):
        """Aggiorna pattern esistente"""
        cursor = self.conn.cursor()
        
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['keyword', 'language', 'is_abbreviation', 'is_plural', 'enabled', 'priority', 'notes']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return
        
        values.append(pattern_id)
        query = f"UPDATE patterns SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        self.conn.commit()
    
    def delete_pattern(self, pattern_id: int):
        """Elimina pattern"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM patterns WHERE id = ?', (pattern_id,))
        self.conn.commit()
    
    def add_example(self, pattern_id: int, document_name: str, context: str, 
                    matched_text: str, paragraph_index: int, confidence: float = 1.0):
        """Registra esempio trovato"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO pattern_examples 
            (pattern_id, document_name, context, matched_text, paragraph_index, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (pattern_id, document_name, context, matched_text, paragraph_index, confidence))
        self.conn.commit()
    
    def get_pattern_count(self) -> int:
        """Conta pattern totali"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patterns')
        return cursor.fetchone()[0]
    
    def get_statistics(self) -> Dict:
        """Ottiene statistiche database"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM patterns')
        total_patterns = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM patterns WHERE enabled = 1')
        enabled_patterns = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT element_type) FROM patterns')
        element_types = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM pattern_examples')
        total_examples = cursor.fetchone()[0]
        
        return {
            'total_patterns': total_patterns,
            'enabled_patterns': enabled_patterns,
            'element_types': element_types,
            'total_examples': total_examples
        }
    
    def search_patterns(self, search_term: str) -> List[Dict]:
        """Cerca pattern per keyword"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM patterns 
            WHERE keyword LIKE ? OR notes LIKE ?
            ORDER BY priority DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def export_patterns(self, file_path: str):
        """Esporta pattern in JSON"""
        patterns = self.get_patterns(enabled_only=False)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
    
    def import_patterns(self, file_path: str) -> int:
        """Importa pattern da JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        
        imported = 0
        for pattern in patterns:
            result = self.add_pattern(
                pattern['element_type'],
                pattern['keyword'],
                language=pattern.get('language', 'it'),
                is_abbreviation=pattern.get('is_abbreviation', False),
                is_plural=pattern.get('is_plural', False),
                enabled=pattern.get('enabled', True),
                priority=pattern.get('priority', 5),
                notes=pattern.get('notes', '')
            )
            if result > 0:
                imported += 1
        
        return imported
    
    def close(self):
        """Chiude connessione"""
        if self.conn:
            self.conn.close()
