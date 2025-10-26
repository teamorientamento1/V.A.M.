"""
Formula Classifier
Classifica automaticamente formule LaTeX in categorie basandosi su pattern e simboli
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Risultato classificazione formula"""
    category: str
    subcategory: str
    confidence: float
    reasoning: str
    suggested_tags: List[str]
    difficulty: int


class FormulaClassifier:
    """Classifica formule LaTeX automaticamente"""
    
    # Pattern per simboli matematici comuni
    SYMBOLS = {
        'integral': [r'\\int', r'\\iint', r'\\iiint', r'\\oint'],
        'derivative': [r'\\frac\{d', r'\\partial', r"'", r'\\dot', r'\\ddot'],
        'limit': [r'\\lim', r'\\limsup', r'\\liminf'],
        'sum': [r'\\sum', r'\\prod'],
        'matrix': [r'\\begin\{matrix\}', r'\\begin\{pmatrix\}', r'\\begin\{bmatrix\}'],
        'vector': [r'\\vec', r'\\mathbf', r'\\overrightarrow'],
        'trig': [r'\\sin', r'\\cos', r'\\tan', r'\\cot', r'\\sec', r'\\csc'],
        'exp_log': [r'\\exp', r'\\log', r'\\ln', r'e\^'],
        'greek': [r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\theta', r'\\lambda', r'\\mu', r'\\sigma', r'\\phi', r'\\psi', r'\\omega'],
        'inequality': [r'<', r'>', r'\\leq', r'\\geq', r'\\ll', r'\\gg', r'\\neq'],
        'equation': [r'='],
        'probability': [r'\\mathbb\{P\}', r'\\mathbb\{E\}', r'\\text\{Var\}', r'\\text\{Cov\}'],
        'special_functions': [r'\\Gamma', r'\\Beta', r'\\zeta', r'\\erf'],
        'bessel': [r'J_', r'Y_', r'I_', r'K_', r'\\text\{Bessel\}'],
        'geometry': [r'\\triangle', r'\\angle', r'\\parallel', r'\\perp'],
        'set_theory': [r'\\in', r'\\notin', r'\\subset', r'\\cup', r'\\cap', r'\\emptyset'],
        'logic': [r'\\land', r'\\lor', r'\\neg', r'\\implies', r'\\iff', r'\\forall', r'\\exists'],
        'number_theory': [r'\\gcd', r'\\lcm', r'\\mod', r'\\equiv', r'\\nmid', r'\\mid'],
        'physics': [r'\\hbar', r'\\nabla', r'\\Delta', r'\\partial_t', r'\\partial_x']
    }
    
    # Regole classificazione
    RULES = [
        # Analisi/Calcolo
        {
            'category': 'calculus',
            'subcategory': 'integral',
            'patterns': ['integral'],
            'weight': 10,
            'tags': ['integrale'],
            'difficulty_base': 2
        },
        {
            'category': 'calculus',
            'subcategory': 'derivative',
            'patterns': ['derivative'],
            'weight': 10,
            'tags': ['derivata'],
            'difficulty_base': 2
        },
        {
            'category': 'calculus',
            'subcategory': 'limit',
            'patterns': ['limit'],
            'weight': 10,
            'tags': ['limite'],
            'difficulty_base': 2
        },
        {
            'category': 'calculus',
            'subcategory': 'series',
            'patterns': ['sum', 'limit'],
            'weight': 8,
            'tags': ['serie', 'successione'],
            'difficulty_base': 3
        },
        {
            'category': 'calculus',
            'subcategory': 'differential',
            'patterns': ['derivative', 'equation'],
            'weight': 8,
            'tags': ['equazione differenziale'],
            'difficulty_base': 4
        },
        
        # Algebra
        {
            'category': 'algebra',
            'subcategory': 'linear',
            'patterns': ['matrix', 'vector'],
            'weight': 9,
            'tags': ['matrice', 'vettore', 'algebra lineare'],
            'difficulty_base': 3
        },
        {
            'category': 'algebra',
            'subcategory': 'polynomial',
            'patterns': ['equation'],
            'negative_patterns': ['derivative', 'integral'],
            'weight': 5,
            'tags': ['polinomio'],
            'difficulty_base': 2
        },
        {
            'category': 'algebra',
            'subcategory': 'inequality',
            'patterns': ['inequality'],
            'weight': 7,
            'tags': ['disequazione'],
            'difficulty_base': 2
        },
        
        # Geometria
        {
            'category': 'geometry',
            'subcategory': 'trigonometry',
            'patterns': ['trig'],
            'weight': 9,
            'tags': ['trigonometria'],
            'difficulty_base': 2
        },
        {
            'category': 'geometry',
            'subcategory': 'euclidean',
            'patterns': ['geometry'],
            'weight': 8,
            'tags': ['geometria euclidea'],
            'difficulty_base': 2
        },
        {
            'category': 'geometry',
            'subcategory': 'vector',
            'patterns': ['vector'],
            'weight': 7,
            'tags': ['vettore', 'geometria analitica'],
            'difficulty_base': 2
        },
        {
            'category': 'geometry',
            'subcategory': 'differential',
            'patterns': ['derivative', 'vector'],
            'weight': 7,
            'tags': ['geometria differenziale'],
            'difficulty_base': 4
        },
        
        # Statistica
        {
            'category': 'statistics',
            'subcategory': 'probability',
            'patterns': ['probability'],
            'weight': 10,
            'tags': ['probabilità'],
            'difficulty_base': 2
        },
        {
            'category': 'statistics',
            'subcategory': 'distribution',
            'patterns': ['probability', 'integral'],
            'weight': 8,
            'tags': ['distribuzione'],
            'difficulty_base': 3
        },
        
        # Teoria dei numeri
        {
            'category': 'number_theory',
            'subcategory': 'divisibility',
            'patterns': ['number_theory'],
            'weight': 9,
            'tags': ['teoria dei numeri'],
            'difficulty_base': 3
        },
        
        # Funzioni speciali
        {
            'category': 'special_functions',
            'subcategory': 'gamma',
            'patterns': ['special_functions'],
            'weight': 10,
            'tags': ['funzioni speciali'],
            'difficulty_base': 4
        },
        {
            'category': 'special_functions',
            'subcategory': 'bessel',
            'patterns': ['bessel'],
            'weight': 10,
            'tags': ['funzioni di Bessel'],
            'difficulty_base': 4
        },
        {
            'category': 'special_functions',
            'subcategory': 'trigonometric',
            'patterns': ['trig'],
            'weight': 6,
            'tags': ['funzioni trigonometriche'],
            'difficulty_base': 1
        },
        {
            'category': 'special_functions',
            'subcategory': 'exponential',
            'patterns': ['exp_log'],
            'weight': 7,
            'tags': ['esponenziale', 'logaritmo'],
            'difficulty_base': 2
        },
        
        # Fisica
        {
            'category': 'physics',
            'subcategory': 'quantum',
            'patterns': ['physics', 'derivative'],
            'weight': 8,
            'tags': ['fisica quantistica'],
            'difficulty_base': 5
        },
        {
            'category': 'physics',
            'subcategory': 'mechanics',
            'patterns': ['physics', 'vector'],
            'weight': 7,
            'tags': ['meccanica'],
            'difficulty_base': 3
        },
        
        # Altro
        {
            'category': 'other',
            'subcategory': 'logic',
            'patterns': ['logic'],
            'weight': 9,
            'tags': ['logica'],
            'difficulty_base': 3
        },
        {
            'category': 'other',
            'subcategory': 'misc',
            'patterns': [],
            'weight': 1,
            'tags': ['varie'],
            'difficulty_base': 1
        }
    ]
    
    def __init__(self):
        """Inizializza classificatore"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compila pattern regex per performance"""
        self.compiled_symbols = {}
        for symbol_type, patterns in self.SYMBOLS.items():
            self.compiled_symbols[symbol_type] = [
                re.compile(pattern) for pattern in patterns
            ]
    
    def _detect_symbols(self, latex: str) -> Dict[str, int]:
        """
        Rileva simboli presenti nella formula
        
        Returns:
            Dict con conteggio di ogni tipo di simbolo
        """
        symbol_counts = {}
        
        for symbol_type, patterns in self.compiled_symbols.items():
            count = 0
            for pattern in patterns:
                count += len(pattern.findall(latex))
            if count > 0:
                symbol_counts[symbol_type] = count
        
        return symbol_counts
    
    def _compute_complexity(self, latex: str, symbols: Dict[str, int]) -> int:
        """
        Calcola complessità formula (difficoltà 1-5)
        
        Fattori:
        - Lunghezza LaTeX
        - Numero e tipo di simboli
        - Nesting di operatori
        - Presenza simboli avanzati
        """
        difficulty = 1
        
        # Lunghezza
        if len(latex) > 100:
            difficulty += 1
        if len(latex) > 200:
            difficulty += 1
        
        # Operatori complessi
        complex_symbols = {'integral', 'derivative', 'limit', 'special_functions', 'bessel'}
        complex_count = sum(symbols.get(s, 0) for s in complex_symbols)
        if complex_count > 0:
            difficulty += 1
        if complex_count > 2:
            difficulty += 1
        
        # Nesting (conta parentesi graffe)
        brace_depth = 0
        max_depth = 0
        for char in latex:
            if char == '{':
                brace_depth += 1
                max_depth = max(max_depth, brace_depth)
            elif char == '}':
                brace_depth -= 1
        
        if max_depth > 5:
            difficulty += 1
        
        # Simboli greci (indicano formule più avanzate)
        if symbols.get('greek', 0) > 3:
            difficulty += 1
        
        return min(5, difficulty)
    
    def classify(self, latex: str) -> ClassificationResult:
        """
        Classifica formula LaTeX
        
        Args:
            latex: Codice LaTeX della formula
            
        Returns:
            Risultato classificazione con categoria, sottocategoria, confidenza
        """
        # Rileva simboli
        symbols = self._detect_symbols(latex)
        
        # Applica regole
        scores = []
        
        for rule in self.RULES:
            score = 0
            
            # Controlla pattern richiesti
            required_patterns = rule['patterns']
            if required_patterns:
                matches = sum(1 for p in required_patterns if symbols.get(p, 0) > 0)
                if matches == 0:
                    continue  # Nessun pattern richiesto trovato
                score = (matches / len(required_patterns)) * rule['weight']
            else:
                score = rule['weight']  # Regola default
            
            # Penalizza se presenti pattern negativi
            negative_patterns = rule.get('negative_patterns', [])
            if negative_patterns:
                neg_matches = sum(1 for p in negative_patterns if symbols.get(p, 0) > 0)
                if neg_matches > 0:
                    score *= 0.5
            
            scores.append((score, rule))
        
        # Ordina per score
        scores.sort(key=lambda x: x[0], reverse=True)
        
        if not scores or scores[0][0] == 0:
            # Fallback: classificazione generica
            best_rule = self.RULES[-1]  # Regola 'misc'
            confidence = 0.3
        else:
            best_rule = scores[0][1]
            confidence = min(1.0, scores[0][0] / 10)
        
        # Calcola difficoltà
        difficulty = self._compute_complexity(latex, symbols)
        difficulty = max(difficulty, best_rule['difficulty_base'])
        
        # Genera tags suggeriti
        suggested_tags = list(best_rule['tags'])
        
        # Aggiungi tag basati su simboli presenti
        if 'greek' in symbols:
            suggested_tags.append('simboli greci')
        if 'matrix' in symbols:
            suggested_tags.append('matrici')
        if 'sum' in symbols and 'limit' in symbols:
            suggested_tags.append('serie infinite')
        
        # Reasoning
        reasoning_parts = []
        if symbols:
            reasoning_parts.append(f"Simboli trovati: {', '.join(symbols.keys())}")
        reasoning_parts.append(f"Regola applicata: {best_rule['category']}/{best_rule['subcategory']}")
        reasoning = "; ".join(reasoning_parts)
        
        return ClassificationResult(
            category=best_rule['category'],
            subcategory=best_rule['subcategory'],
            confidence=confidence,
            reasoning=reasoning,
            suggested_tags=suggested_tags,
            difficulty=difficulty
        )
    
    def classify_batch(self, formulas: List[str]) -> List[ClassificationResult]:
        """Classifica lista di formule"""
        return [self.classify(f) for f in formulas]
    
    def suggest_improvements(self, latex: str, classification: ClassificationResult) -> List[str]:
        """
        Suggerisce miglioramenti per classificazione formula
        
        Returns:
            Lista suggerimenti per migliorare la classificazione
        """
        suggestions = []
        
        if classification.confidence < 0.5:
            suggestions.append("Classificazione incerta. Considera di aggiungere più contesto o nome alla formula.")
        
        if classification.category == 'other':
            suggestions.append("Formula classificata come 'Altro'. Potrebbe beneficiare di tag o descrizione più specifici.")
        
        symbols = self._detect_symbols(latex)
        
        if not symbols:
            suggestions.append("Nessun simbolo matematico riconosciuto. Verifica il LaTeX.")
        
        if len(latex) < 10:
            suggestions.append("Formula molto corta. Potrebbe mancare di contesto.")
        
        if classification.difficulty >= 4 and len(suggestions) == 0:
            suggestions.append("Formula complessa. Considera di aggiungere esempi o spiegazioni.")
        
        return suggestions if suggestions else ["Classificazione sembra buona!"]


def classify_and_add_to_db(latex: str, db, name: str = None, 
                           description: str = None) -> Optional[int]:
    """
    Classifica formula e la aggiunge al database
    
    Args:
        latex: Codice LaTeX
        db: Istanza FormulaDatabase
        name: Nome opzionale formula
        description: Descrizione opzionale
        
    Returns:
        ID formula inserita
    """
    classifier = FormulaClassifier()
    result = classifier.classify(latex)
    
    formula_id = db.add_formula(
        latex=latex,
        name=name,
        description=description,
        category=result.category,
        subcategory=result.subcategory,
        difficulty=result.difficulty,
        tags=result.suggested_tags,
        verified=False
    )
    
    return formula_id


if __name__ == "__main__":
    # Test classificatore
    classifier = FormulaClassifier()
    
    test_formulas = [
        r"\int_a^b f(x)\,dx = F(b) - F(a)",
        r"\frac{d}{dx}\sin(x) = \cos(x)",
        r"e^{i\pi} + 1 = 0",
        r"\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}",
        r"\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}",
        r"ax^2 + bx + c = 0",
        r"\mathbb{P}(A \cap B) = \mathbb{P}(A) \cdot \mathbb{P}(B|A)",
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
        r"J_\nu(x) = \sum_{m=0}^{\infty} \frac{(-1)^m}{m!\Gamma(m+\nu+1)}\left(\frac{x}{2}\right)^{2m+\nu}"
    ]
    
    print("CLASSIFICAZIONE FORMULE TEST\n")
    print("=" * 80)
    
    for latex in test_formulas:
        result = classifier.classify(latex)
        print(f"\nFormula: {latex[:60]}...")
        print(f"Categoria: {result.category} / {result.subcategory}")
        print(f"Confidenza: {result.confidence:.2f}")
        print(f"Difficoltà: {result.difficulty}/5")
        print(f"Tags: {', '.join(result.suggested_tags)}")
        print(f"Reasoning: {result.reasoning}")
        
        suggestions = classifier.suggest_improvements(latex, result)
        if suggestions:
            print(f"Suggerimenti: {suggestions[0]}")
        print("-" * 80)
