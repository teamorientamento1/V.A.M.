"""
Knowledge Base - Archivio multidisciplinare con backup automatico
"""
import sqlite3
import json
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import threading
import time

from config.settings import *
from core.database_schema import DATABASE_SCHEMA, INITIAL_DISCIPLINES, SCHEMA_VERSION


class KnowledgeBase:
    """
    Gestisce l'archivio di conoscenze multidisciplinare con backup automatico
    """
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.connection = None
        self.backup_thread = None
        self.backup_running = False
        self._initialize_database()
        self._start_auto_backup()
    
    def _initialize_database(self):
        """Inizializza il database se non esiste"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # Crea schema
        cursor = self.connection.cursor()
        cursor.executescript(DATABASE_SCHEMA)
        
        # Inserisci versione schema
        cursor.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,)
        )
        
        # Inserisci discipline iniziali
        for name, description in INITIAL_DISCIPLINES:
            cursor.execute(
                "INSERT OR IGNORE INTO disciplines (name, description) VALUES (?, ?)",
                (name, description)
            )
        
        self.connection.commit()
        print(f"Database inizializzato: {self.db_path}")
    
    # ============= PATTERN MANAGEMENT =============
    
    def add_pattern(self, discipline: str, pattern_type: str, **kwargs) -> int:
        """
        Aggiunge un nuovo pattern all'archivio
        
        Args:
            discipline: Nome della disciplina
            pattern_type: Tipo di pattern ('formula', 'diagram', etc.)
            **kwargs: Altri attributi del pattern
        
        Returns:
            ID del pattern inserito
        """
        discipline_id = self._get_discipline_id(discipline)
        
        cursor = self.connection.cursor()
        
        # Prepara i campi
        fields = ['discipline_id', 'pattern_type']
        values = [discipline_id, pattern_type]
        placeholders = ['?', '?']
        
        # Campi opzionali
        optional_fields = [
            'visual_signature', 'latex_representation', 'mathml_representation',
            'content_description', 'context_words', 'confidence_score',
            'variations', 'tts_rule', 'created_from'
        ]
        
        for field in optional_fields:
            if field in kwargs:
                fields.append(field)
                # Converti liste/dict in JSON
                value = kwargs[field]
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                values.append(value)
                placeholders.append('?')
        
        query = f"""
            INSERT INTO content_patterns ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(query, values)
        pattern_id = cursor.lastrowid
        
        # Log cambiamento
        self._log_change('content_patterns', pattern_id, 'INSERT', None, kwargs)
        
        self.connection.commit()
        return pattern_id
    
    def find_similar_patterns(self, 
                             latex: Optional[str] = None,
                             visual_signature: Optional[str] = None,
                             context: Optional[str] = None,
                             discipline: Optional[str] = None,
                             limit: int = 10) -> List[Dict]:
        """
        Trova pattern simili nell'archivio
        
        TODO: Implementare similarity search avanzato (vector embeddings)
        Per ora usa matching esatto o LIKE
        """
        cursor = self.connection.cursor()
        
        query = """
            SELECT cp.*, d.name as discipline_name
            FROM content_patterns cp
            JOIN disciplines d ON cp.discipline_id = d.id
            WHERE 1=1
        """
        params = []
        
        if latex:
            query += " AND latex_representation LIKE ?"
            params.append(f"%{latex}%")
        
        if visual_signature:
            query += " AND visual_signature = ?"
            params.append(visual_signature)
        
        if discipline:
            query += " AND d.name = ?"
            params.append(discipline)
        
        query += " ORDER BY confidence_score DESC, frequency DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update_pattern_frequency(self, pattern_id: int, increment: int = 1):
        """Aggiorna la frequenza di un pattern (rinforzo)"""
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE content_patterns SET frequency = frequency + ?, last_seen = ? WHERE id = ?",
            (increment, datetime.now(), pattern_id)
        )
        self._log_change('content_patterns', pattern_id, 'UPDATE', None, {'frequency': f'+{increment}'})
        self.connection.commit()
    
    # ============= SYMBOL MANAGEMENT =============
    
    def add_symbol(self, symbol: str, discipline: str, **kwargs) -> int:
        """Aggiunge un simbolo all'archivio"""
        discipline_id = self._get_discipline_id(discipline)
        
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO symbols (symbol, discipline_id, unicode_code, latex_code, 
                               category, default_pronunciation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            discipline_id,
            kwargs.get('unicode_code'),
            kwargs.get('latex_code'),
            kwargs.get('category'),
            kwargs.get('default_pronunciation')
        ))
        
        symbol_id = cursor.lastrowid
        self._log_change('symbols', symbol_id, 'INSERT', None, kwargs)
        self.connection.commit()
        return symbol_id
    
    def get_symbol_pronunciation(self, symbol: str, context: Optional[str] = None) -> Optional[str]:
        """
        Ottiene la pronuncia di un simbolo
        TODO: Implementare pronuncia context-aware
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT default_pronunciation, user_pronunciations, context_variants FROM symbols WHERE symbol = ?",
            (symbol,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # TODO: Se c'è context, cerca in context_variants
        # Per ora ritorna default
        return row['default_pronunciation']
    
    def update_symbol_pronunciation(self, symbol: str, pronunciation: str, 
                                   context: Optional[str] = None, user_preference: bool = True):
        """
        Aggiorna la pronuncia di un simbolo
        """
        # TODO: Implementare aggiornamento context-aware e user preferences
        cursor = self.connection.cursor()
        
        if user_preference:
            # Aggiungi a user_pronunciations JSON
            pass
        else:
            cursor.execute(
                "UPDATE symbols SET default_pronunciation = ? WHERE symbol = ?",
                (pronunciation, symbol)
            )
        
        self.connection.commit()
    
    # ============= CONTEXT MANAGEMENT =============
    
    def add_context(self, pattern_id: int, surrounding_text: str, **kwargs):
        """Aggiunge contesto di apprendimento per un pattern"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO learned_contexts 
            (pattern_id, surrounding_text, figure_references, chapter_section, 
             document_type, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pattern_id,
            surrounding_text,
            json.dumps(kwargs.get('figure_references', [])),
            kwargs.get('chapter_section'),
            kwargs.get('document_type'),
            kwargs.get('confidence', 0.5)
        ))
        self.connection.commit()
    
    # ============= DOCUMENT TRACKING =============
    
    def register_document(self, filename: str, file_content: bytes, 
                         document_type: str, discipline: str) -> Optional[int]:
        """
        Registra un documento analizzato
        Returns None se già analizzato (stesso hash)
        """
        file_hash = hashlib.sha256(file_content).hexdigest()
        discipline_id = self._get_discipline_id(discipline)
        
        cursor = self.connection.cursor()
        
        # Verifica se già analizzato
        cursor.execute("SELECT id FROM analyzed_documents WHERE file_hash = ?", (file_hash,))
        if cursor.fetchone():
            print(f"Documento già analizzato: {filename}")
            return None
        
        cursor.execute("""
            INSERT INTO analyzed_documents (filename, file_hash, document_type, discipline_id)
            VALUES (?, ?, ?, ?)
        """, (filename, file_hash, document_type, discipline_id))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def update_document_patterns_count(self, document_id: int, count: int):
        """Aggiorna il conteggio pattern estratti da un documento"""
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE analyzed_documents SET patterns_extracted = ? WHERE id = ?",
            (count, document_id)
        )
        self.connection.commit()
    
    # ============= STATISTICS & QUERIES =============
    
    def get_statistics(self) -> Dict:
        """Ottiene statistiche sull'archivio"""
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Pattern per disciplina
        cursor.execute("""
            SELECT d.name, COUNT(cp.id) as count
            FROM disciplines d
            LEFT JOIN content_patterns cp ON d.id = cp.discipline_id
            GROUP BY d.id
        """)
        stats['patterns_by_discipline'] = {row['name']: row['count'] for row in cursor.fetchall()}
        
        # Simboli totali
        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        stats['total_symbols'] = cursor.fetchone()['count']
        
        # Documenti analizzati
        cursor.execute("SELECT COUNT(*) as count FROM analyzed_documents")
        stats['documents_analyzed'] = cursor.fetchone()['count']
        
        # Pattern più frequenti
        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count
            FROM content_patterns
            GROUP BY pattern_type
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_pattern_types'] = {row['pattern_type']: row['count'] for row in cursor.fetchall()}
        
        return stats
    
    # ============= BACKUP SYSTEM =============
    
    def _start_auto_backup(self):
        """Avvia thread per backup automatici"""
        if AUTO_BACKUP_INTERVAL > 0:
            self.backup_running = True
            self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
            self.backup_thread.start()
            print("Sistema di backup automatico avviato")
    
    def _backup_loop(self):
        """Loop per backup automatici periodici"""
        while self.backup_running:
            time.sleep(AUTO_BACKUP_INTERVAL)
            try:
                self.create_backup(backup_type='incremental')
            except Exception as e:
                print(f"Errore durante backup automatico: {e}")
    
    def create_backup(self, backup_type: str = 'full') -> Path:
        """
        Crea un backup del database
        
        Args:
            backup_type: 'full' o 'incremental'
        
        Returns:
            Path del file di backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"kb_backup_{backup_type}_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        if backup_type == 'full':
            # Copia completa del database
            shutil.copy2(self.db_path, backup_path)
        else:
            # Backup incrementale (solo i cambiamenti recenti)
            # TODO: Implementare backup incrementale usando change_log
            # Per ora fa backup completo
            shutil.copy2(self.db_path, backup_path)
        
        # Calcola checksum
        with open(backup_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        file_size = backup_path.stat().st_size
        
        # Registra backup
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO backup_history 
            (backup_path, backup_type, file_size_bytes, checksum, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(backup_path),
            backup_type,
            file_size,
            checksum,
            datetime.now() + timedelta(days=BACKUP_RETENTION_DAYS)
        ))
        self.connection.commit()
        
        print(f"Backup creato: {backup_path} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Cleanup vecchi backup
        self._cleanup_old_backups()
        
        return backup_path
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Ripristina un backup
        """
        if not backup_path.exists():
            print(f"Backup non trovato: {backup_path}")
            return False
        
        # Verifica checksum
        cursor = self.connection.cursor()
        cursor.execute("SELECT checksum FROM backup_history WHERE backup_path = ?", (str(backup_path),))
        row = cursor.fetchone()
        
        if row:
            with open(backup_path, 'rb') as f:
                current_checksum = hashlib.sha256(f.read()).hexdigest()
            
            if current_checksum != row['checksum']:
                print("ERRORE: Checksum non corrisponde! Backup corrotto.")
                return False
        
        # Chiudi connessione attuale
        self.connection.close()
        
        # Crea backup del database corrente prima di sovrascriverlo
        current_backup = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(self.db_path, current_backup)
        
        # Ripristina
        shutil.copy2(backup_path, self.db_path)
        
        # Riconnetti
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        print(f"Backup ripristinato da: {backup_path}")
        return True
    
    def _cleanup_old_backups(self):
        """Elimina backup scaduti"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT backup_path FROM backup_history WHERE expires_at < ?", (datetime.now(),))
        
        for row in cursor.fetchall():
            backup_path = Path(row['backup_path'])
            if backup_path.exists():
                backup_path.unlink()
                print(f"Backup scaduto eliminato: {backup_path}")
        
        cursor.execute("DELETE FROM backup_history WHERE expires_at < ?", (datetime.now(),))
        self.connection.commit()
    
    def list_backups(self) -> List[Dict]:
        """Elenca tutti i backup disponibili"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM backup_history 
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    # ============= UTILITY METHODS =============
    
    def _get_discipline_id(self, discipline_name: str) -> int:
        """Ottiene l'ID di una disciplina"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM disciplines WHERE name = ?", (discipline_name,))
        row = cursor.fetchone()
        
        if not row:
            # Se non esiste, creala come 'generic'
            cursor.execute("SELECT id FROM disciplines WHERE name = 'generic'")
            row = cursor.fetchone()
        
        return row['id']
    
    def _log_change(self, table_name: str, record_id: int, operation: str, 
                   old_data: Any, new_data: Any):
        """Registra un cambiamento nel change_log"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO change_log (table_name, record_id, operation, old_data, new_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            table_name,
            record_id,
            operation,
            json.dumps(old_data, ensure_ascii=False) if old_data else None,
            json.dumps(new_data, ensure_ascii=False) if new_data else None
        ))
    
    def close(self):
        """Chiude connessione e ferma backup automatici"""
        self.backup_running = False
        if self.backup_thread:
            self.backup_thread.join(timeout=2)
        
        if self.connection:
            self.connection.close()
        
        print("Knowledge Base chiusa")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
