"""
Formula Integration
Integra database formule con sistema di gestione salti per documenti accessibili
"""

from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path
import json

from formula_database import FormulaDatabase
from formula_classifier import FormulaClassifier


class FormulaIntegration:
    """Integra database formule con sistema salti"""
    
    def __init__(self, formula_db: FormulaDatabase):
        """
        Inizializza integrazione
        
        Args:
            formula_db: Istanza FormulaDatabase
        """
        self.db = formula_db
        self.classifier = FormulaClassifier()
    
    def find_similar_formulas(self, latex: str, max_results: int = 10) -> List[Dict]:
        """
        Trova formule simili nel database
        
        Args:
            latex: LaTeX formula da cercare
            max_results: Numero massimo risultati
            
        Returns:
            Lista formule simili ordinate per rilevanza
        """
        # Prima classifica la formula
        classification = self.classifier.classify(latex)
        
        # Cerca nel database per categoria
        candidates = self.db.search_formulas(
            category=classification.category,
            subcategory=classification.subcategory,
            limit=100
        )
        
        # Calcola similarity score
        results = []
        for candidate in candidates:
            score = self._compute_similarity(latex, candidate['latex'])
            if score > 0.3:  # Threshold minimo
                candidate['similarity_score'] = score
                results.append(candidate)
        
        # Ordina per score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:max_results]
    
    def _compute_similarity(self, latex1: str, latex2: str) -> float:
        """
        Calcola similarity tra due formule LaTeX (semplificato)
        
        Uses:
        - Exact match → 1.0
        - Token overlap
        - Symbol similarity
        """
        # Normalizza
        norm1 = self._normalize_latex(latex1)
        norm2 = self._normalize_latex(latex2)
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Tokenize
        tokens1 = set(self._tokenize_latex(norm1))
        tokens2 = set(self._tokenize_latex(norm2))
        
        # Jaccard similarity
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _normalize_latex(self, latex: str) -> str:
        """Normalizza LaTeX per confronto"""
        # Rimuovi spazi multipli
        latex = ' '.join(latex.split())
        # Lowercase
        latex = latex.lower()
        # Rimuovi label
        latex = re.sub(r'\\label\{[^}]*\}', '', latex)
        return latex
    
    def _tokenize_latex(self, latex: str) -> List[str]:
        """Tokenize LaTeX in simboli"""
        # Trova comandi LaTeX
        commands = re.findall(r'\\[a-zA-Z]+', latex)
        # Trova simboli
        symbols = re.findall(r'[a-zA-Z0-9_^{}]+', latex)
        return commands + symbols
    
    def suggest_description(self, latex: str, element_type: str = 'equation') -> str:
        """
        Suggerisce descrizione per formula basandosi su database
        
        Args:
            latex: LaTeX formula
            element_type: Tipo elemento ('equation', 'table', 'figure')
            
        Returns:
            Descrizione suggerita
        """
        # Trova formule simili
        similar = self.find_similar_formulas(latex, max_results=3)
        
        if not similar:
            # Fallback: classificazione automatica
            classification = self.classifier.classify(latex)
            return f"Formula di tipo {classification.subcategory} (categoria {classification.category})"
        
        # Usa descrizione della formula più simile
        best_match = similar[0]
        
        if best_match['similarity_score'] > 0.8:
            # Match molto buono, usa descrizione esistente
            desc = best_match.get('description', '')
            if desc:
                return desc
        
        # Match parziale, costruisci descrizione combinata
        name = best_match.get('name', '')
        category = best_match['category']
        subcategory = best_match.get('subcategory', '')
        
        desc_parts = []
        if name:
            desc_parts.append(f"Simile a: {name}")
        desc_parts.append(f"Tipo: {subcategory or category}")
        
        return ". ".join(desc_parts)
    
    def analyze_document_formulas(self, latex_content: str) -> Dict:
        """
        Analizza formule in documento LaTeX
        
        Args:
            latex_content: Contenuto documento LaTeX
            
        Returns:
            Dict con statistiche e formule trovate
        """
        # Estrai equazioni (usa stesso pattern di arxiv_importer)
        from arxiv_importer import ArxivImporter
        importer = ArxivImporter()
        equations = importer._extract_equations(latex_content)
        
        # Classifica ogni equazione
        analyzed = []
        for i, eq in enumerate(equations):
            classification = self.classifier.classify(eq)
            similar = self.find_similar_formulas(eq, max_results=1)
            
            analyzed.append({
                'index': i,
                'latex': eq,
                'category': classification.category,
                'subcategory': classification.subcategory,
                'difficulty': classification.difficulty,
                'confidence': classification.confidence,
                'has_match': len(similar) > 0 and similar[0]['similarity_score'] > 0.7,
                'suggested_description': self.suggest_description(eq)
            })
        
        # Statistiche
        categories = {}
        difficulties = {}
        for item in analyzed:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1
            
            diff = item['difficulty']
            difficulties[diff] = difficulties.get(diff, 0) + 1
        
        return {
            'total_formulas': len(analyzed),
            'formulas': analyzed,
            'categories': categories,
            'difficulties': difficulties,
            'avg_difficulty': sum(item['difficulty'] for item in analyzed) / len(analyzed) if analyzed else 0,
            'matched_formulas': sum(1 for item in analyzed if item['has_match'])
        }
    
    def enrich_jump_with_formula_info(self, jump_data: Dict, latex: str) -> Dict:
        """
        Arricchisce dati salto con info da database formule
        
        Args:
            jump_data: Dati salto esistenti
            latex: LaTeX formula associata al salto
            
        Returns:
            Jump data arricchito
        """
        # Trova formule simili
        similar = self.find_similar_formulas(latex, max_results=1)
        
        enriched = jump_data.copy()
        
        if similar and similar[0]['similarity_score'] > 0.7:
            match = similar[0]
            
            # Aggiungi metadati formula
            enriched['formula_metadata'] = {
                'database_id': match['id'],
                'name': match.get('name'),
                'category': match['category'],
                'subcategory': match.get('subcategory'),
                'difficulty': match['difficulty'],
                'similarity': match['similarity_score'],
                'source': match.get('source'),
                'verified': match.get('verified', False)
            }
            
            # Se manca descrizione, usa quella del database
            if not jump_data.get('description') and match.get('description'):
                enriched['description'] = match['description']
            
            # Aggiungi esempi se disponibili
            examples = self.db.get_examples(match['id'])
            if examples:
                enriched['formula_examples'] = examples
        
        return enriched
    
    def batch_enrich_jumps(self, jumps: List[Dict]) -> List[Dict]:
        """
        Arricchisce batch di salti con info formule
        
        Args:
            jumps: Lista salti da arricchire (devono avere campo 'latex')
            
        Returns:
            Lista salti arricchiti
        """
        enriched_jumps = []
        
        for jump in jumps:
            latex = jump.get('latex')
            if latex:
                enriched = self.enrich_jump_with_formula_info(jump, latex)
                enriched_jumps.append(enriched)
            else:
                enriched_jumps.append(jump)
        
        return enriched_jumps
    
    def export_jumps_to_json(self, jumps: List[Dict], output_file: str):
        """Esporta salti arricchiti in JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jumps, f, indent=2, ensure_ascii=False)
    
    def generate_formula_report(self, document_path: str, output_path: str):
        """
        Genera report analisi formule documento
        
        Args:
            document_path: Path documento LaTeX
            output_path: Path file output report
        """
        # Leggi documento
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analizza
        analysis = self.analyze_document_formulas(content)
        
        # Genera report
        report = []
        report.append("=" * 80)
        report.append("REPORT ANALISI FORMULE")
        report.append("=" * 80)
        report.append(f"\nDocumento: {document_path}")
        report.append(f"Totale formule trovate: {analysis['total_formulas']}")
        report.append(f"Formule con match in database: {analysis['matched_formulas']}")
        report.append(f"Difficoltà media: {analysis['avg_difficulty']:.2f}/5")
        
        report.append("\nDistribuzione per categoria:")
        for cat, count in sorted(analysis['categories'].items()):
            percentage = count / analysis['total_formulas'] * 100
            report.append(f"  {cat}: {count} ({percentage:.1f}%)")
        
        report.append("\nDistribuzione per difficoltà:")
        for diff, count in sorted(analysis['difficulties'].items()):
            report.append(f"  Livello {diff}: {count}")
        
        report.append("\n" + "=" * 80)
        report.append("DETTAGLIO FORMULE")
        report.append("=" * 80)
        
        for formula in analysis['formulas']:
            report.append(f"\n[Formula {formula['index'] + 1}]")
            report.append(f"LaTeX: {formula['latex'][:100]}...")
            report.append(f"Categoria: {formula['category']}/{formula['subcategory']}")
            report.append(f"Difficoltà: {formula['difficulty']}/5")
            report.append(f"Match in DB: {'Sì' if formula['has_match'] else 'No'}")
            report.append(f"Descrizione suggerita: {formula['suggested_description']}")
            report.append("-" * 80)
        
        # Salva report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))


class FormulaPatternMatcher:
    """
    Matcher per trovare pattern formule comuni
    Utile per auto-completamento e suggerimenti
    """
    
    def __init__(self, db: FormulaDatabase):
        self.db = db
        
        # Costruisci indice pattern comuni
        self.patterns = self._build_pattern_index()
    
    def _build_pattern_index(self) -> Dict[str, List[Dict]]:
        """Costruisce indice pattern comuni da database"""
        patterns = {}
        
        # Recupera tutte formule verificate
        formulas = self.db.search_formulas(verified_only=True, limit=10000)
        
        for formula in formulas:
            # Estrai pattern chiave (comandi LaTeX principali)
            latex = formula['latex']
            commands = re.findall(r'\\[a-zA-Z]+', latex)
            
            for cmd in set(commands):
                if cmd not in patterns:
                    patterns[cmd] = []
                patterns[cmd].append(formula)
        
        return patterns
    
    def find_by_pattern(self, partial_latex: str, max_results: int = 5) -> List[Dict]:
        """
        Trova formule che matchano pattern parziale
        
        Args:
            partial_latex: LaTeX parziale (es. "\\int")
            max_results: Numero massimo risultati
            
        Returns:
            Lista formule matchanti
        """
        # Estrai comandi dal pattern
        commands = re.findall(r'\\[a-zA-Z]+', partial_latex)
        
        if not commands:
            return []
        
        # Cerca formule con questi comandi
        candidates = []
        for cmd in commands:
            if cmd in self.patterns:
                candidates.extend(self.patterns[cmd])
        
        # Rimuovi duplicati mantenendo ordine
        seen = set()
        unique = []
        for formula in candidates:
            if formula['id'] not in seen:
                seen.add(formula['id'])
                unique.append(formula)
        
        return unique[:max_results]


def demo_integration():
    """Demo integrazione"""
    # Crea/carica database
    db = FormulaDatabase("formulas.db")
    
    # Crea integration
    integration = FormulaIntegration(db)
    
    # Esempio: analizza formula
    test_latex = r"\int_a^b f(x)\,dx = F(b) - F(a)"
    
    print("=== RICERCA FORMULE SIMILI ===")
    similar = integration.find_similar_formulas(test_latex)
    for i, formula in enumerate(similar, 1):
        print(f"\n{i}. {formula.get('name', 'N/A')}")
        print(f"   Similarity: {formula['similarity_score']:.2%}")
        print(f"   LaTeX: {formula['latex'][:60]}...")
    
    print("\n=== DESCRIZIONE SUGGERITA ===")
    description = integration.suggest_description(test_latex)
    print(description)
    
    # Esempio: arricchisci jump
    print("\n=== ARRICCHIMENTO JUMP ===")
    jump = {
        'id': 1,
        'type': 'equation',
        'label': 'eq:fundamental',
        'latex': test_latex
    }
    
    enriched = integration.enrich_jump_with_formula_info(jump, test_latex)
    if 'formula_metadata' in enriched:
        print("Jump arricchito con metadata formula:")
        print(f"  Database ID: {enriched['formula_metadata']['database_id']}")
        print(f"  Nome: {enriched['formula_metadata']['name']}")
        print(f"  Categoria: {enriched['formula_metadata']['category']}")
        print(f"  Difficoltà: {enriched['formula_metadata']['difficulty']}/5")
    
    db.close()


if __name__ == "__main__":
    demo_integration()
