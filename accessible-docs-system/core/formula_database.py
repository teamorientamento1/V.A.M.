"""
Formula Database Manager
Gestisce database SQLite di formule matematiche con categorie gerarchiche e metadati
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib


class FormulaDatabase:
    """Gestisce database SQLite di formule matematiche"""
    
    # Schema categorie gerarchiche
    CATEGORIES = {
        'algebra': {
            'name': 'Algebra',
            'subcategories': {
                'linear': 'Algebra Lineare',
                'polynomial': 'Polinomi',
                'equation': 'Equazioni',
                'inequality': 'Disequazioni',
                'system': 'Sistemi'
            }
        },
        'calculus': {
            'name': 'Analisi',
            'subcategories': {
                'derivative': 'Derivate',
                'integral': 'Integrali',
                'limit': 'Limiti',
                'series': 'Serie',
                'differential': 'Equazioni Differenziali'
            }
        },
        'geometry': {
            'name': 'Geometria',
            'subcategories': {
                'euclidean': 'Geometria Euclidea',
                'analytic': 'Geometria Analitica',
                'differential': 'Geometria Differenziale',
                'vector': 'Vettori',
                'trigonometry': 'Trigonometria'
            }
        },
        'statistics': {
            'name': 'Statistica',
            'subcategories': {
                'descriptive': 'Statistica Descrittiva',
                'probability': 'Probabilità',
                'distribution': 'Distribuzioni',
                'inference': 'Inferenza',
                'regression': 'Regressione'
            }
        },
        'number_theory': {
            'name': 'Teoria dei Numeri',
            'subcategories': {
                'prime': 'Numeri Primi',
                'divisibility': 'Divisibilità',
                'congruence': 'Congruenze',
                'diophantine': 'Equazioni Diofantine'
            }
        },
        'special_functions': {
            'name': 'Funzioni Speciali',
            'subcategories': {
                'trigonometric': 'Funzioni Trigonometriche',
                'exponential': 'Esponenziali e Logaritmi',
                'gamma': 'Funzioni Gamma e Beta',
                'bessel': 'Funzioni di Bessel',
                'hypergeometric': 'Funzioni Ipergeometriche'
            }
        },
        'physics': {
            'name': 'Fisica',
            'subcategories': {
                'mechanics': 'Meccanica',
                'electromagnetism': 'Elettromagnetismo',
                'thermodynamics': 'Termodinamica',
                'quantum': 'Meccanica Quantistica',
                'relativity': 'Relatività'
            }
        },
        'other': {
            'name': 'Altro',
            'subcategories': {
                'logic': 'Logica',
                'combinatorics': 'Combinatoria',
                'graph': 'Teoria dei Grafi',
                'misc': 'Varie'
            }
        }
    }
    
    def __init__(self, db_path: str = "formulas.db"):
        """
        Inizializza database
        
        Args:
            db_path: Percorso file database SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Crea tabelle database se non esistono"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Tabella formule principali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latex TEXT NOT NULL,
                latex_hash TEXT UNIQUE NOT NULL,
                name TEXT,
                description TEXT,
                category TEXT NOT NULL,
                subcategory TEXT,
                difficulty INTEGER DEFAULT 1,
                source TEXT,
                source_url TEXT,
                tags TEXT,
                verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella varianti formule
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formula_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formula_id INTEGER NOT NULL,
                latex TEXT NOT NULL,
                variant_type TEXT,
                description TEXT,
                FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
            )
        """)
        
        # Tabella relazioni tra formule
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formula_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formula_id INTEGER NOT NULL,
                related_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE,
                FOREIGN KEY (related_id) REFERENCES formulas(id) ON DELETE CASCADE
            )
        """)
        
        # Tabella esempi applicazioni
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS formula_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                formula_id INTEGER NOT NULL,
                title TEXT,
                problem TEXT,
                solution TEXT,
                difficulty INTEGER DEFAULT 1,
                FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
            )
        """)
        
        # Indici per performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON formulas(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subcategory ON formulas(subcategory)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_latex_hash ON formulas(latex_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verified ON formulas(verified)")
        
        self.conn.commit()
    
    def _compute_latex_hash(self, latex: str) -> str:
        """Calcola hash univoco per formula LaTeX"""
        # Normalizza LaTeX (rimuove spazi extra, etc.)
        normalized = ' '.join(latex.split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def add_formula(self, latex: str, name: str = None, description: str = None,
                   category: str = 'other', subcategory: str = None,
                   difficulty: int = 1, source: str = None, source_url: str = None,
                   tags: List[str] = None, verified: bool = False) -> Optional[int]:
        """
        Aggiunge formula al database
        
        Args:
            latex: Codice LaTeX della formula
            name: Nome formula
            description: Descrizione formula
            category: Categoria principale
            subcategory: Sottocategoria
            difficulty: Difficoltà (1-5)
            source: Sorgente formula
            source_url: URL sorgente
            tags: Lista tag
            verified: Se formula è verificata
            
        Returns:
            ID formula inserita o None se già esiste
        """
        latex_hash = self._compute_latex_hash(latex)
        tags_str = json.dumps(tags) if tags else None
        
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO formulas 
                (latex, latex_hash, name, description, category, subcategory,
                 difficulty, source, source_url, tags, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (latex, latex_hash, name, description, category, subcategory,
                  difficulty, source, source_url, tags_str, verified))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Formula già esistente
            return None
    
    def get_formula(self, formula_id: int) -> Optional[Dict]:
        """Recupera formula per ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM formulas WHERE id = ?", (formula_id,))
        row = cursor.fetchone()
        
        if row:
            formula = dict(row)
            # Deserializza tags
            if formula['tags']:
                formula['tags'] = json.loads(formula['tags'])
            return formula
        return None
    
    def search_formulas(self, query: str = None, category: str = None,
                       subcategory: str = None, tags: List[str] = None,
                       verified_only: bool = False, limit: int = 100) -> List[Dict]:
        """
        Cerca formule nel database
        
        Args:
            query: Testo da cercare in name/description
            category: Filtra per categoria
            subcategory: Filtra per sottocategoria
            tags: Filtra per tags
            verified_only: Solo formule verificate
            limit: Numero massimo risultati
            
        Returns:
            Lista formule trovate
        """
        cursor = self.conn.cursor()
        
        sql = "SELECT * FROM formulas WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            query_pattern = f"%{query}%"
            params.extend([query_pattern, query_pattern])
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if subcategory:
            sql += " AND subcategory = ?"
            params.append(subcategory)
        
        if verified_only:
            sql += " AND verified = 1"
        
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql, params)
        results = []
        
        for row in cursor.fetchall():
            formula = dict(row)
            if formula['tags']:
                formula['tags'] = json.loads(formula['tags'])
            
            # Filtra per tags se specificato
            if tags:
                formula_tags = set(formula['tags'] or [])
                if not formula_tags.intersection(tags):
                    continue
            
            results.append(formula)
        
        return results
    
    def add_variant(self, formula_id: int, latex: str, variant_type: str = None,
                   description: str = None) -> int:
        """Aggiunge variante di una formula"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO formula_variants (formula_id, latex, variant_type, description)
            VALUES (?, ?, ?, ?)
        """, (formula_id, latex, variant_type, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_variants(self, formula_id: int) -> List[Dict]:
        """Recupera varianti di una formula"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM formula_variants WHERE formula_id = ?
        """, (formula_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_relation(self, formula_id: int, related_id: int,
                    relation_type: str, notes: str = None) -> int:
        """
        Aggiunge relazione tra formule
        
        Args:
            formula_id: ID formula principale
            related_id: ID formula correlata
            relation_type: Tipo relazione (derives_from, equivalent, generalizes, etc.)
            notes: Note sulla relazione
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO formula_relations (formula_id, related_id, relation_type, notes)
            VALUES (?, ?, ?, ?)
        """, (formula_id, related_id, relation_type, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_related(self, formula_id: int) -> List[Dict]:
        """Recupera formule correlate"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, f.name, f.latex, f.description
            FROM formula_relations r
            JOIN formulas f ON r.related_id = f.id
            WHERE r.formula_id = ?
        """, (formula_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_example(self, formula_id: int, title: str = None,
                   problem: str = None, solution: str = None,
                   difficulty: int = 1) -> int:
        """Aggiunge esempio di applicazione formula"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO formula_examples (formula_id, title, problem, solution, difficulty)
            VALUES (?, ?, ?, ?, ?)
        """, (formula_id, title, problem, solution, difficulty))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_examples(self, formula_id: int) -> List[Dict]:
        """Recupera esempi di una formula"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM formula_examples WHERE formula_id = ?
        """, (formula_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Recupera statistiche database"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Totale formule
        cursor.execute("SELECT COUNT(*) as count FROM formulas")
        stats['total_formulas'] = cursor.fetchone()['count']
        
        # Formule verificate
        cursor.execute("SELECT COUNT(*) as count FROM formulas WHERE verified = 1")
        stats['verified_formulas'] = cursor.fetchone()['count']
        
        # Per categoria
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM formulas 
            GROUP BY category
        """)
        stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Per difficoltà
        cursor.execute("""
            SELECT difficulty, COUNT(*) as count 
            FROM formulas 
            GROUP BY difficulty
        """)
        stats['by_difficulty'] = {row['difficulty']: row['count'] for row in cursor.fetchall()}
        
        return stats
    
    def export_category(self, category: str, output_file: str):
        """Esporta tutte le formule di una categoria in JSON"""
        formulas = self.search_formulas(category=category, limit=10000)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formulas, f, indent=2, ensure_ascii=False)
    
    def import_from_json(self, json_file: str, verify: bool = False) -> int:
        """
        Importa formule da file JSON
        
        Returns:
            Numero formule importate
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            formulas = json.load(f)
        
        count = 0
        for formula in formulas:
            formula_id = self.add_formula(
                latex=formula['latex'],
                name=formula.get('name'),
                description=formula.get('description'),
                category=formula.get('category', 'other'),
                subcategory=formula.get('subcategory'),
                difficulty=formula.get('difficulty', 1),
                source=formula.get('source'),
                source_url=formula.get('source_url'),
                tags=formula.get('tags'),
                verified=verify
            )
            if formula_id:
                count += 1
        
        return count
    
    def close(self):
        """Chiude connessione database"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test database
    db = FormulaDatabase("test_formulas.db")
    
    # Aggiungi formula esempio
    formula_id = db.add_formula(
        latex=r"\int_a^b f(x)\,dx = F(b) - F(a)",
        name="Teorema Fondamentale del Calcolo",
        description="Relazione tra integrale definito e primitiva",
        category="calculus",
        subcategory="integral",
        difficulty=2,
        tags=["integrale", "primitiva", "calcolo"],
        verified=True
    )
    
    print(f"Formula inserita con ID: {formula_id}")
    
    # Aggiungi variante
    if formula_id:
        db.add_variant(
            formula_id,
            latex=r"\int f'(x)\,dx = f(x) + C",
            variant_type="indefinite",
            description="Forma indefinita"
        )
    
    # Statistiche
    stats = db.get_statistics()
    print("\nStatistiche database:")
    print(f"Totale formule: {stats['total_formulas']}")
    print(f"Formule verificate: {stats['verified_formulas']}")
    
    db.close()
