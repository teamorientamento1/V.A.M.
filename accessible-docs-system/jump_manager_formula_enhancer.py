"""
Jump Manager Formula Enhancer
Estende il Jump Manager con funzionalità database formule
"""

from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path

from core.formula_database import FormulaDatabase
from core.formula_integration import FormulaIntegration


class JumpManagerFormulaEnhancer:
    """Estende Jump Manager con database formule"""
    
    def __init__(self, formula_db_path: str = "formulas.db"):
        """
        Inizializza enhancer
        
        Args:
            formula_db_path: Path database formule
        """
        self.db = FormulaDatabase(formula_db_path)
        self.integration = FormulaIntegration(self.db)
        
        # Cache per performance
        self._suggestion_cache = {}
    
    def suggest_description_for_jump(self, latex: str, 
                                     jump_type: str = 'equation') -> Dict:
        """
        Suggerisce descrizione automatica per un salto basandosi sul database
        
        Args:
            latex: LaTeX dell'elemento
            jump_type: Tipo salto ('equation', 'table', 'figure')
            
        Returns:
            Dict con suggerimenti:
            {
                'description': str,              # Descrizione suggerita
                'similar_formulas': List[Dict],  # Formule simili trovate
                'confidence': float,             # Confidenza suggerimento (0-1)
                'category': str,                 # Categoria riconosciuta
                'difficulty': int,               # Difficoltà stimata (1-5)
                'has_match': bool               # Se trovato match nel database
            }
        """
        # Controlla cache
        cache_key = f"{jump_type}:{latex}"
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key]
        
        # Trova formule simili
        similar = self.integration.find_similar_formulas(latex, max_results=3)
        
        # Genera descrizione
        description = self.integration.suggest_description(latex, jump_type)
        
        # Classifica formula per metadata
        from core.formula_classifier import FormulaClassifier
        classifier = FormulaClassifier()
        classification = classifier.classify(latex)
        
        # Prepara risultato
        result = {
            'description': description,
            'similar_formulas': similar,
            'confidence': similar[0]['similarity_score'] if similar else classification.confidence,
            'category': classification.category,
            'subcategory': classification.subcategory,
            'difficulty': classification.difficulty,
            'has_match': len(similar) > 0 and similar[0]['similarity_score'] > 0.7,
            'suggested_tags': classification.suggested_tags
        }
        
        # Salva in cache
        self._suggestion_cache[cache_key] = result
        
        return result
    
    def enrich_single_jump(self, jump: Dict) -> Dict:
        """
        Arricchisce un singolo salto con info da database
        
        Args:
            jump: Dict salto con almeno campo 'latex'
            
        Returns:
            Jump arricchito con metadata formula
        """
        if 'latex' not in jump:
            return jump
        
        latex = jump['latex']
        enriched = self.integration.enrich_jump_with_formula_info(jump, latex)
        
        return enriched
    
    def enrich_all_jumps(self, jumps: List[Dict], 
                         progress_callback=None) -> Tuple[List[Dict], Dict]:
        """
        Arricchisce batch di salti con info formule
        
        Args:
            jumps: Lista salti da arricchire
            progress_callback: Callback(current, total, status) per progress bar
            
        Returns:
            (jumps_arricchiti, statistiche)
        """
        enriched = []
        stats = {
            'total': len(jumps),
            'enriched': 0,
            'with_match': 0,
            'no_latex': 0,
            'errors': 0
        }
        
        for i, jump in enumerate(jumps):
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, len(jumps), f"Elaborando salto {i+1}/{len(jumps)}")
            
            # Salta se non ha latex
            if 'latex' not in jump or not jump['latex']:
                enriched.append(jump)
                stats['no_latex'] += 1
                continue
            
            try:
                # Arricchisci
                enriched_jump = self.enrich_single_jump(jump)
                enriched.append(enriched_jump)
                
                stats['enriched'] += 1
                
                # Conta match
                if 'formula_metadata' in enriched_jump:
                    stats['with_match'] += 1
                    
            except Exception as e:
                print(f"Errore arricchimento salto {i}: {e}")
                enriched.append(jump)  # Usa originale se errore
                stats['errors'] += 1
        
        return enriched, stats
    
    def search_formulas_for_ui(self, query: str = None, 
                               category: str = None,
                               max_results: int = 20) -> List[Dict]:
        """
        Cerca formule nel database (ottimizzato per UI)
        
        Args:
            query: Testo da cercare
            category: Filtra per categoria
            max_results: Numero massimo risultati
            
        Returns:
            Lista formule con preview LaTeX
        """
        results = self.db.search_formulas(
            query=query,
            category=category if category != 'Tutte' else None,
            limit=max_results
        )
        
        # Aggiungi preview LaTeX (primi 100 char)
        for r in results:
            latex = r['latex']
            r['latex_preview'] = latex[:100] + "..." if len(latex) > 100 else latex
        
        return results
    
    def get_formula_details(self, formula_id: int) -> Optional[Dict]:
        """
        Recupera dettagli completi formula per display
        
        Args:
            formula_id: ID formula nel database
            
        Returns:
            Dict con tutti i dettagli inclusi varianti, esempi, relazioni
        """
        formula = self.db.get_formula(formula_id)
        if not formula:
            return None
        
        # Aggiungi varianti
        formula['variants'] = self.db.get_variants(formula_id)
        
        # Aggiungi formule correlate
        formula['related'] = self.db.get_related(formula_id)
        
        # Aggiungi esempi
        formula['examples'] = self.db.get_examples(formula_id)
        
        return formula
    
    def analyze_document(self, latex_content: str) -> Dict:
        """
        Analizza documento completo e genera report
        
        Args:
            latex_content: Contenuto documento LaTeX
            
        Returns:
            Dict con analisi completa
        """
        return self.integration.analyze_document_formulas(latex_content)
    
    def get_statistics(self) -> Dict:
        """Ritorna statistiche database"""
        return self.db.get_statistics()
    
    def close(self):
        """Chiude connessione database"""
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class QuickFormulaLookup:
    """
    Helper veloce per lookup formule durante editing
    Usato per auto-completamento e suggerimenti inline
    """
    
    def __init__(self, enhancer: JumpManagerFormulaEnhancer):
        self.enhancer = enhancer
        
        # Patterns comuni per auto-completamento
        self.common_patterns = [
            (r'\\int', 'integral'),
            (r'\\frac\{d', 'derivative'),
            (r'\\sum', 'series'),
            (r'\\prod', 'product'),
            (r'\\lim', 'limit'),
            (r'\\sin|\\cos|\\tan', 'trigonometry'),
            (r'\\Gamma', 'gamma function'),
            (r'\\int.*\\int', 'multiple integral')
        ]
    
    def detect_formula_type(self, partial_latex: str) -> Optional[str]:
        """
        Rileva tipo formula da LaTeX parziale
        
        Args:
            partial_latex: LaTeX parziale (es. durante digitazione)
            
        Returns:
            Tipo formula o None
        """
        for pattern, formula_type in self.common_patterns:
            if re.search(pattern, partial_latex):
                return formula_type
        return None
    
    def get_autocomplete_suggestions(self, partial_latex: str, 
                                     limit: int = 5) -> List[Dict]:
        """
        Suggerimenti auto-completamento basati su LaTeX parziale
        
        Args:
            partial_latex: LaTeX parziale
            limit: Numero massimo suggerimenti
            
        Returns:
            Lista formule simili che potrebbero completare l'input
        """
        if len(partial_latex) < 3:
            return []
        
        # Rileva tipo
        formula_type = self.detect_formula_type(partial_latex)
        
        # Cerca formule simili
        results = self.enhancer.integration.find_similar_formulas(
            partial_latex, 
            max_results=limit
        )
        
        # Filtra per tipo se rilevato
        if formula_type:
            # TODO: Filtra per categoria se implementato
            pass
        
        return results
    
    def get_similar_examples(self, latex: str, limit: int = 3) -> List[Dict]:
        """
        Trova esempi simili per una formula
        
        Args:
            latex: LaTeX formula
            limit: Numero massimo esempi
            
        Returns:
            Lista esempi da formule simili
        """
        # Trova formule simili
        similar = self.enhancer.integration.find_similar_formulas(latex, max_results=5)
        
        examples = []
        for formula in similar:
            # Recupera esempi per questa formula
            formula_examples = self.enhancer.db.get_examples(formula['id'])
            examples.extend(formula_examples)
            
            if len(examples) >= limit:
                break
        
        return examples[:limit]


# Utility functions per integrazione facile

def create_enhancer(db_path: str = "formulas.db") -> JumpManagerFormulaEnhancer:
    """
    Factory function per creare enhancer
    
    Args:
        db_path: Path database formule
        
    Returns:
        Istanza JumpManagerFormulaEnhancer pronta all'uso
    """
    return JumpManagerFormulaEnhancer(db_path)


def quick_suggest(latex: str, db_path: str = "formulas.db") -> str:
    """
    Quick function per ottenere descrizione suggerita
    
    Args:
        latex: LaTeX formula
        db_path: Path database
        
    Returns:
        Descrizione suggerita
    """
    with create_enhancer(db_path) as enhancer:
        result = enhancer.suggest_description_for_jump(latex)
        return result['description']


def quick_enrich(jump: Dict, db_path: str = "formulas.db") -> Dict:
    """
    Quick function per arricchire singolo salto
    
    Args:
        jump: Dict salto
        db_path: Path database
        
    Returns:
        Salto arricchito
    """
    with create_enhancer(db_path) as enhancer:
        return enhancer.enrich_single_jump(jump)


if __name__ == "__main__":
    # Test enhancer
    print("=== TEST JUMP MANAGER FORMULA ENHANCER ===\n")
    
    enhancer = create_enhancer("formulas.db")
    
    # Test 1: Suggerisci descrizione
    test_latex = r"\int_a^b f(x)\,dx"
    print(f"Formula test: {test_latex}\n")
    
    suggestion = enhancer.suggest_description_for_jump(test_latex)
    print(f"Descrizione suggerita: {suggestion['description']}")
    print(f"Categoria: {suggestion['category']}/{suggestion['subcategory']}")
    print(f"Difficoltà: {suggestion['difficulty']}/5")
    print(f"Confidenza: {suggestion['confidence']:.2%}")
    print(f"Match trovato: {suggestion['has_match']}")
    
    if suggestion['similar_formulas']:
        print(f"\nFormule simili trovate: {len(suggestion['similar_formulas'])}")
        for i, f in enumerate(suggestion['similar_formulas'][:3], 1):
            print(f"  {i}. {f.get('name', 'N/A')} (similarity: {f['similarity_score']:.2%})")
    
    # Test 2: Arricchisci jump
    print("\n=== TEST ARRICCHIMENTO JUMP ===\n")
    test_jump = {
        'id': 1,
        'type': 'equation',
        'label': 'eq:fundamental',
        'latex': test_latex,
        'description': ''
    }
    
    enriched = enhancer.enrich_single_jump(test_jump)
    print(f"Jump originale: {test_jump}")
    print(f"\nJump arricchito:")
    if 'formula_metadata' in enriched:
        print(f"  - Database ID: {enriched['formula_metadata']['database_id']}")
        print(f"  - Nome: {enriched['formula_metadata']['name']}")
        print(f"  - Categoria: {enriched['formula_metadata']['category']}")
        print(f"  - Verificata: {enriched['formula_metadata']['verified']}")
    
    # Statistiche
    print("\n=== STATISTICHE DATABASE ===\n")
    stats = enhancer.get_statistics()
    print(f"Totale formule: {stats['total_formulas']}")
    print(f"Formule verificate: {stats['verified_formulas']}")
    
    enhancer.close()
