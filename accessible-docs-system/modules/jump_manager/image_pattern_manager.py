"""
Sistema di pattern configurabile per l'identificazione delle etichette delle immagini
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ImagePatternManager:
    """Gestisce pattern personalizzabili per identificare le etichette delle immagini"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inizializza il gestore dei pattern
        
        Args:
            db_path: Percorso al database SQLite. Se None, usa il database di default
        """
        if db_path is None:
            # Usa il database patterns.db nella cartella data
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "patterns.db"
        
        self.db_path = str(db_path)
        self._init_database()
        
        # Cache dei pattern per migliorare le performance
        self._pattern_cache = None
        self._load_default_patterns()
    
    def _init_database(self):
        """Inizializza le tabelle del database se non esistono"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella per i pattern di etichette
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_label_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT UNIQUE NOT NULL,
                regex_pattern TEXT NOT NULL,
                priority INTEGER DEFAULT 100,
                enabled INTEGER DEFAULT 1,
                case_sensitive INTEGER DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        """)
        
        # Tabella per tracciare le etichette trovate e gestire i duplicati
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS found_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_path TEXT,
                label TEXT NOT NULL,
                paragraph_index INTEGER,
                pattern_used TEXT,
                occurrence_number INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_path, label, paragraph_index)
            )
        """)
        
        # Indici per migliorare le performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_priority 
            ON image_label_patterns(priority DESC, enabled)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_found_labels_doc 
            ON found_labels(document_path, label)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_default_patterns(self):
        """Carica i pattern di default se il database è vuoto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM image_label_patterns")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Pattern aggiornati per supportare numerazione multi-livello (es: 5.2.2, 11.3.4.1)
            # (\d+(?:\.\d+)*[a-z]?) cattura: 5, 5.2, 5.2.2, 5.2.2.1, 11a, etc.
            default_patterns = [
                ("figura", r'Fig\.?\s*(\d+(?:\.\d+)*[a-z]?)', 100, "Figura standard (Fig, Fig.) - supporta multi-livello"),
                ("figura_estesa", r'Figura\.?\s*(\d+(?:\.\d+)*[a-z]?)', 95, "Figura scritta per esteso - supporta multi-livello"),
                ("figure_en", r'Figure\.?\s*(\d+(?:\.\d+)*[a-z]?)', 90, "Figure in inglese - supporta multi-livello"),
                ("immagine", r'Immagine\.?\s*(\d+(?:\.\d+)*[a-z]?)', 85, "Immagine - supporta multi-livello"),
                ("grafico", r'Grafico\.?\s*(\d+(?:\.\d+)*[a-z]?)', 80, "Grafico - supporta multi-livello"),
                ("tabella", r'Tab\.?\s*(\d+(?:\.\d+)*[a-z]?)', 75, "Tabella abbreviata - supporta multi-livello"),
                ("tabella_estesa", r'Tabella\.?\s*(\d+(?:\.\d+)*[a-z]?)', 70, "Tabella per esteso - supporta multi-livello"),
                ("esempio", r'Esempio\.?\s*(\d+(?:\.\d+)*[a-z]?)', 65, "Esempio - supporta multi-livello (es: 5.2.2)"),
                ("didascalia", r'Didascalia\.?\s*(\d+(?:\.\d+)*[a-z]?)', 60, "Didascalia - supporta multi-livello"),
                ("schema", r'Schema\.?\s*(\d+(?:\.\d+)*[a-z]?)', 55, "Schema - supporta multi-livello"),
                ("diagramma", r'Diagramma\.?\s*(\d+(?:\.\d+)*[a-z]?)', 50, "Diagramma - supporta multi-livello"),
            ]
            
            cursor.executemany("""
                INSERT INTO image_label_patterns 
                (pattern_name, regex_pattern, priority, description)
                VALUES (?, ?, ?, ?)
            """, default_patterns)
            
            conn.commit()
            print(f"✓ Caricati {len(default_patterns)} pattern di default (con supporto multi-livello)")
        
        conn.close()
    
    def add_pattern(self, pattern_name: str, regex_pattern: str, 
                   priority: int = 50, description: str = "",
                   case_sensitive: bool = False) -> bool:
        """
        Aggiunge un nuovo pattern per identificare le etichette
        
        Args:
            pattern_name: Nome identificativo del pattern
            regex_pattern: Espressione regolare per il matching
            priority: Priorità del pattern (più alto = cercato prima)
            description: Descrizione del pattern
            case_sensitive: Se True, il pattern è case-sensitive
            
        Returns:
            True se aggiunto con successo, False altrimenti
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO image_label_patterns 
                (pattern_name, regex_pattern, priority, description, case_sensitive)
                VALUES (?, ?, ?, ?, ?)
            """, (pattern_name, regex_pattern, priority, description, int(case_sensitive)))
            
            conn.commit()
            conn.close()
            
            # Invalida la cache
            self._pattern_cache = None
            print(f"✓ Pattern '{pattern_name}' aggiunto con successo")
            return True
            
        except sqlite3.IntegrityError:
            print(f"✗ Pattern '{pattern_name}' già esistente")
            return False
        except Exception as e:
            print(f"✗ Errore nell'aggiungere il pattern: {e}")
            return False
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """Rimuove un pattern"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM image_label_patterns WHERE pattern_name = ?
            """, (pattern_name,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if deleted:
                self._pattern_cache = None
                print(f"✓ Pattern '{pattern_name}' rimosso")
            else:
                print(f"✗ Pattern '{pattern_name}' non trovato")
            
            return deleted
            
        except Exception as e:
            print(f"✗ Errore nella rimozione del pattern: {e}")
            return False
    
    def update_pattern(self, pattern_name: str, **kwargs) -> bool:
        """
        Aggiorna un pattern esistente
        
        Args:
            pattern_name: Nome del pattern da aggiornare
            **kwargs: Campi da aggiornare (regex_pattern, priority, description, enabled, case_sensitive)
        """
        try:
            valid_fields = {'regex_pattern', 'priority', 'description', 'enabled', 'case_sensitive'}
            updates = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not updates:
                print("✗ Nessun campo valido da aggiornare")
                return False
            
            # Converti booleani in interi per SQLite
            if 'enabled' in updates:
                updates['enabled'] = int(updates['enabled'])
            if 'case_sensitive' in updates:
                updates['case_sensitive'] = int(updates['case_sensitive'])
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [pattern_name]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE image_label_patterns 
                SET {set_clause}
                WHERE pattern_name = ?
            """, values)
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if updated:
                self._pattern_cache = None
                print(f"✓ Pattern '{pattern_name}' aggiornato")
            else:
                print(f"✗ Pattern '{pattern_name}' non trovato")
            
            return updated
            
        except Exception as e:
            print(f"✗ Errore nell'aggiornare il pattern: {e}")
            return False
    
    def get_patterns(self, enabled_only: bool = True) -> List[Dict]:
        """
        Ottiene tutti i pattern, ordinati per priorità
        
        Args:
            enabled_only: Se True, restituisce solo i pattern abilitati
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute("""
                SELECT * FROM image_label_patterns 
                WHERE enabled = 1
                ORDER BY priority DESC, pattern_name
            """)
        else:
            cursor.execute("""
                SELECT * FROM image_label_patterns 
                ORDER BY priority DESC, pattern_name
            """)
        
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return patterns
    
    def _get_pattern_cache(self) -> List[Tuple[str, re.Pattern, str]]:
        """Ottiene i pattern compilati dalla cache o li ricarica"""
        if self._pattern_cache is None:
            patterns = self.get_patterns(enabled_only=True)
            self._pattern_cache = []
            
            for p in patterns:
                flags = 0 if p['case_sensitive'] else re.IGNORECASE
                try:
                    compiled_pattern = re.compile(p['regex_pattern'], flags)
                    self._pattern_cache.append((
                        p['pattern_name'],
                        compiled_pattern,
                        p['regex_pattern']
                    ))
                except re.error as e:
                    print(f"⚠ Pattern '{p['pattern_name']}' non valido: {e}")
        
        return self._pattern_cache
    
    def find_label_in_text(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Cerca un'etichetta nel testo usando i pattern configurati
        
        Args:
            text: Testo in cui cercare
            
        Returns:
            Tupla (label, pattern_name) se trovata, None altrimenti
        """
        if not text:
            return None
        
        patterns = self._get_pattern_cache()
        
        for pattern_name, compiled_pattern, _ in patterns:
            match = compiled_pattern.search(text)
            if match:
                # Aggiorna last_used
                self._update_last_used(pattern_name)
                return match.group(0), pattern_name
        
        return None
    
    def _update_last_used(self, pattern_name: str):
        """Aggiorna il timestamp last_used per un pattern"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE image_label_patterns 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE pattern_name = ?
            """, (pattern_name,))
            conn.commit()
            conn.close()
        except:
            pass  # Non critico se fallisce
    
    def find_label_with_duplicates(self, doc, para_index: int, search_range: int = 3,
                                   document_path: str = None) -> Tuple[str, int]:
        """
        Cerca la label nei paragrafi circostanti gestendo i duplicati
        
        Args:
            doc: Documento python-docx
            para_index: Indice del paragrafo con l'immagine
            search_range: Quanti paragrafi prima/dopo cercare
            document_path: Percorso del documento (per tracciare i duplicati)
            
        Returns:
            Tupla (label, occurrence_number) dove occurrence_number indica 
            quante volte questa label è apparsa nel documento
        """
        start = max(0, para_index - search_range)
        end = min(len(doc.paragraphs), para_index + search_range + 1)
        
        label = None
        pattern_used = None
        
        # Cerca la label nei paragrafi circostanti
        for i in range(start, end):
            text = doc.paragraphs[i].text
            result = self.find_label_in_text(text)
            
            if result:
                label, pattern_used = result
                break
        
        # Se non trovata, usa un ID generico
        if label is None:
            label = f"IMG_{para_index}"
            pattern_used = "default"
        
        # Gestisci i duplicati
        occurrence = 1
        if document_path:
            occurrence = self._track_label_occurrence(
                document_path, label, para_index, pattern_used
            )
            
            # Se è un duplicato, aggiungi un suffisso
            if occurrence > 1:
                label = f"{label}_{occurrence}"
        
        return label, occurrence
    
    def _track_label_occurrence(self, document_path: str, label: str, 
                               para_index: int, pattern_used: str) -> int:
        """
        Traccia l'occorrenza di una label nel documento e restituisce il numero di occorrenza
        
        Returns:
            Numero di occorrenza (1 per la prima volta, 2 per la seconda, ecc.)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Conta quante volte questa label è già apparsa
            cursor.execute("""
                SELECT COUNT(*) FROM found_labels 
                WHERE document_path = ? AND label = ?
            """, (document_path, label))
            
            count = cursor.fetchone()[0] + 1
            
            # Registra questa occorrenza
            try:
                cursor.execute("""
                    INSERT INTO found_labels 
                    (document_path, label, paragraph_index, pattern_used, occurrence_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (document_path, label, para_index, pattern_used, count))
                conn.commit()
            except sqlite3.IntegrityError:
                # Già presente, aggiorna
                cursor.execute("""
                    UPDATE found_labels 
                    SET occurrence_number = ?
                    WHERE document_path = ? AND label = ? AND paragraph_index = ?
                """, (count, document_path, label, para_index))
                conn.commit()
            
            conn.close()
            return count
            
        except Exception as e:
            print(f"⚠ Errore nel tracciare l'occorrenza: {e}")
            return 1
    
    def clear_document_labels(self, document_path: str):
        """Pulisce le etichette tracciate per un documento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM found_labels WHERE document_path = ?", (document_path,))
            conn.commit()
            conn.close()
            print(f"✓ Etichette del documento '{document_path}' pulite")
        except Exception as e:
            print(f"✗ Errore nella pulizia delle etichette: {e}")
    
    def get_label_statistics(self, document_path: Optional[str] = None) -> Dict:
        """
        Ottiene statistiche sull'uso delle etichette
        
        Args:
            document_path: Se specificato, statistiche per quel documento, altrimenti globali
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if document_path:
            cursor.execute("""
                SELECT pattern_used, COUNT(*) as count
                FROM found_labels
                WHERE document_path = ?
                GROUP BY pattern_used
                ORDER BY count DESC
            """, (document_path,))
        else:
            cursor.execute("""
                SELECT pattern_used, COUNT(*) as count
                FROM found_labels
                GROUP BY pattern_used
                ORDER BY count DESC
            """)
        
        pattern_usage = dict(cursor.fetchall())
        
        if document_path:
            cursor.execute("""
                SELECT label, occurrence_number
                FROM found_labels
                WHERE document_path = ? AND occurrence_number > 1
                ORDER BY label
            """, (document_path,))
        else:
            cursor.execute("""
                SELECT document_path, label, occurrence_number
                FROM found_labels
                WHERE occurrence_number > 1
                ORDER BY document_path, label
            """)
        
        duplicates = cursor.fetchall()
        conn.close()
        
        return {
            'pattern_usage': pattern_usage,
            'duplicates': duplicates,
            'total_labels': sum(pattern_usage.values())
        }
    
    def list_patterns(self):
        """Stampa tutti i pattern in modo leggibile"""
        patterns = self.get_patterns(enabled_only=False)
        
        if not patterns:
            print("Nessun pattern configurato")
            return
        
        print("\n" + "="*80)
        print("PATTERN DI ETICHETTE IMMAGINI")
        print("="*80)
        
        for p in patterns:
            status = "✓" if p['enabled'] else "✗"
            print(f"\n{status} {p['pattern_name']}")
            print(f"   Pattern: {p['regex_pattern']}")
            print(f"   Priorità: {p['priority']}")
            print(f"   Case-sensitive: {'Sì' if p['case_sensitive'] else 'No'}")
            if p['description']:
                print(f"   Descrizione: {p['description']}")
            if p['last_used']:
                print(f"   Ultimo uso: {p['last_used']}")
        
        print("\n" + "="*80)


# Funzioni di utilità per retrocompatibilità con il codice esistente
def create_pattern_manager(db_path: Optional[str] = None) -> ImagePatternManager:
    """Factory function per creare un gestore di pattern"""
    return ImagePatternManager(db_path)


def find_image_label_enhanced(doc, para_index: int, document_path: str = None,
                             pattern_manager: ImagePatternManager = None,
                             search_range: int = 3) -> str:
    """
    Versione migliorata di find_image_label con supporto per pattern configurabili
    
    Args:
        doc: Documento python-docx
        para_index: Indice del paragrafo
        document_path: Percorso del documento
        pattern_manager: Gestore dei pattern (se None, ne crea uno nuovo)
        search_range: Range di ricerca
        
    Returns:
        Label trovata (con suffisso _N se duplicata)
    """
    if pattern_manager is None:
        pattern_manager = ImagePatternManager()
    
    label, occurrence = pattern_manager.find_label_with_duplicates(
        doc, para_index, search_range, document_path
    )
    
    return label
