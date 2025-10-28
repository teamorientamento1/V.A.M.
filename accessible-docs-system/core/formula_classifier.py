"""
Formula Classifier
Classifica automaticamente formule LaTeX E testo matematico Unicode in categorie
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
    """Classifica formule LaTeX e testo matematico Unicode automaticamente"""
    
    # Pattern per simboli matematici comuni (LaTeX E Unicode)
    SYMBOLS = {
        'integral': [
            r'\\int', r'\\iint', r'\\iiint', r'\\oint',
            r'∫', r'∬', r'∭', r'∮'  # Unicode
        ],
        'derivative': [
            r'\\frac\{d', r'\\partial', r"'", r'\\dot', r'\\ddot',
            r'∂', r'∇', r'Δ'  # Unicode
        ],
        'limit': [
            r'\\lim', r'\\limsup', r'\\liminf',
            r'lim', r'→'  # Unicode (arrow per limiti)
        ],
        'sum': [
            r'\\sum', r'\\prod',
            r'∑', r'∏', r'Σ'  # Unicode
        ],
        'matrix': [
            r'\\begin\{matrix\}', r'\\begin\{pmatrix\}', r'\\begin\{bmatrix\}',
            r'\(.*,.*\)', r'\[.*,.*\]',  # Parentesi con virgole
            r'matrice', r'matrix',  # Parole chiave
            r'⋮', r'⋯', r'⋱'  # Simboli matrici Unicode
        ],
        'vector': [
            r'\\vec', r'\\mathbf', r'\\overrightarrow',
            r'vettore', r'vector', r'→', r'⃗'  # Unicode
        ],
        'trig': [
            r'\\sin', r'\\cos', r'\\tan', r'\\cot', r'\\sec', r'\\csc',
            r'\bsin\b', r'\bcos\b', r'\btan\b', r'\bcot\b', r'\bsec\b', r'\bcsc\b'  # Testo
        ],
        'exp_log': [
            r'\\exp', r'\\log', r'\\ln', r'e\^',
            r'\bexp\b', r'\blog\b', r'\bln\b', r'\be\^'  # Testo
        ],
        'greek': [
            r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\theta', r'\\lambda', 
            r'\\mu', r'\\sigma', r'\\phi', r'\\psi', r'\\omega',
            r'α', r'β', r'γ', r'δ', r'ε', r'ζ', r'η', r'θ', r'ι', r'κ', r'λ', 
            r'μ', r'ν', r'ξ', r'ο', r'π', r'ρ', r'σ', r'τ', r'υ', r'φ', r'χ', 
            r'ψ', r'ω', r'Ω', r'Δ', r'Γ', r'Λ', r'Σ', r'Φ', r'Ψ'  # Unicode
        ],
        'inequality': [
            r'<', r'>', r'\\leq', r'\\geq', r'\\ll', r'\\gg', r'\\neq',
            r'≤', r'≥', r'≠', r'≪', r'≫'  # Unicode
        ],
        'equation': [r'='],
        'probability': [
            r'\\mathbb\{P\}', r'\\mathbb\{E\}', r'\\text\{Var\}', r'\\text\{Cov\}',
            r'\bP\(', r'\bE\[', r'\bVar\b', r'\bCov\b'  # Testo
        ],
        'special_functions': [
            r'\\Gamma', r'\\Beta', r'\\zeta', r'\\erf',
            r'Γ', r'γ', r'ζ', r'erf'  # Unicode
        ],
        'bessel': [
            r'J_', r'Y_', r'I_', r'K_', r'\\text\{Bessel\}',
            r'Bessel'  # Testo
        ],
        'geometry': [
            r'\\triangle', r'\\angle', r'\\parallel', r'\\perp',
            r'△', r'∠', r'∥', r'⊥', r'°'  # Unicode
        ],
        'set_theory': [
            r'\\in', r'\\notin', r'\\subset', r'\\cup', r'\\cap', r'\\emptyset',
            r'∈', r'∉', r'⊂', r'⊆', r'∪', r'∩', r'∅', r'⊃', r'⊇'  # Unicode
        ],
        'logic': [
            r'\\land', r'\\lor', r'\\neg', r'\\implies', r'\\iff', r'\\forall', r'\\exists',
            r'∧', r'∨', r'¬', r'⇒', r'⟹', r'⇔', r'∀', r'∃'  # Unicode
        ],
        'number_theory': [
            r'\\gcd', r'\\lcm', r'\\mod', r'\\equiv', r'\\nmid', r'\\mid',
            r'\bgcd\b', r'\blcm\b', r'\bmod\b', r'≡', r'∤', r'∣'  # Unicode/testo
        ],
        'physics': [
            r'\\hbar', r'\\nabla', r'\\Delta', r'\\partial_t', r'\\partial_x',
            r'ℏ', r'∇', r'Δ', r'∂'  # Unicode
        ],
        'optimization': [
            r'\\min', r'\\max', r'\\arg\\min', r'\\arg\\max',
            r'\bmin\b', r'\bmax\b', r'argmin', r'argmax'  # Testo
        ],
        'superscript': [
            r'\^', r'⊤', r'²', r'³', r'⁴', r'⁵', r'⁶', r'⁷', r'⁸', r'⁹', r'⁰'  # Unicode superscript
        ],
        'subscript': [
            r'_', r'₀', r'₁', r'₂', r'₃', r'₄', r'₅', r'₆', r'₇', r'₈', r'₉'  # Unicode subscript
        ]
    }
    
    # Regole classificazione (stesso schema di prima)
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
            'patterns': ['equation', 'superscript'],
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
        {
            'category': 'algebra',
            'subcategory': 'system',
            'patterns': ['equation'],
            'count_threshold': 3,  # Almeno 3 uguaglianze = sistema
            'weight': 6,
            'tags': ['sistema di equazioni'],
            'difficulty_base': 3
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
        
        # Ottimizzazione
        {
            'category': 'optimization',
            'subcategory': 'linear_programming',
            'patterns': ['optimization', 'inequality'],
            'weight': 8,
            'tags': ['programmazione lineare', 'ottimizzazione'],
            'difficulty_base': 3
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
            'subcategory': 'set_theory',
            'patterns': ['set_theory'],
            'weight': 9,
            'tags': ['teoria degli insiemi'],
            'difficulty_base': 2
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
        """Compila pattern regex"""
        self.compiled_symbols = {}
        for symbol_type, patterns in self.SYMBOLS.items():
            self.compiled_symbols[symbol_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def _detect_symbols(self, text: str) -> Dict[str, int]:
        """
        Rileva simboli presenti nella formula
        
        Returns:
            Dict con conteggio di ogni tipo di simbolo
        """
        symbol_counts = {}
        
        for symbol_type, patterns in self.compiled_symbols.items():
            count = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                count += len(matches)
            if count > 0:
                symbol_counts[symbol_type] = count
        
        return symbol_counts
    
    def _compute_complexity(self, text: str, symbols: Dict[str, int]) -> int:
        """
        Calcola complessità formula (difficoltà 1-5)
        
        Fattori:
        - Lunghezza testo
        - Numero e tipo di simboli
        - Presenza simboli avanzati
        """
        difficulty = 1
        
        # Lunghezza
        if len(text) > 100:
            difficulty += 1
        if len(text) > 200:
            difficulty += 1
        
        # Operatori complessi
        complex_symbols = {'integral', 'derivative', 'limit', 'special_functions', 'bessel', 'matrix'}
        complex_count = sum(symbols.get(s, 0) for s in complex_symbols)
        if complex_count > 0:
            difficulty += 1
        if complex_count > 2:
            difficulty += 1
        
        # Simboli greci (indicano formule più avanzate)
        if symbols.get('greek', 0) > 3:
            difficulty += 1
        
        return min(5, difficulty)
    
    def classify(self, text: str) -> ClassificationResult:
        """
        Classifica formula (LaTeX o testo Unicode)
        
        Args:
            text: Testo matematico (LaTeX o Unicode)
            
        Returns:
            Risultato classificazione con categoria, sottocategoria, confidenza
        """
        # Rileva simboli
        symbols = self._detect_symbols(text)
        
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
                
                # Check count threshold se presente
                count_threshold = rule.get('count_threshold', 0)
                if count_threshold > 0:
                    # Controlla se il conteggio supera la soglia
                    total_count = sum(symbols.get(p, 0) for p in required_patterns)
                    if total_count < count_threshold:
                        continue
                
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
        difficulty = self._compute_complexity(text, symbols)
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
    
    def suggest_improvements(self, text: str, classification: ClassificationResult) -> List[str]:
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
        
        symbols = self._detect_symbols(text)
        
        if not symbols:
            suggestions.append("Nessun simbolo matematico riconosciuto. Verifica il testo.")
        
        if len(text) < 10:
            suggestions.append("Formula molto corta. Potrebbe mancare di contesto.")
        
        if classification.difficulty >= 4 and len(suggestions) == 0:
            suggestions.append("Formula complessa. Considera di aggiungere esempi o spiegazioni.")
        
        return suggestions if suggestions else ["Classificazione sembra buona!"]


def classify_and_add_to_db(text: str, db, name: str = None, 
                           description: str = None) -> Optional[int]:
    """
    Classifica formula e la aggiunge al database
    
    Args:
        text: Testo matematico (LaTeX o Unicode)
        db: Istanza FormulaDatabase
        name: Nome opzionale formula
        description: Descrizione opzionale
        
    Returns:
        ID formula inserita
    """
    classifier = FormulaClassifier()
    result = classifier.classify(text)
    
    formula_id = db.add_formula(
        latex=text,  # Salva come "latex" anche se è Unicode
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
    # Test classificatore con testo Unicode
    classifier = FormulaClassifier()
    
    test_formulas = [
        # LaTeX
        r"\int_a^b f(x)\,dx = F(b) - F(a)",
        r"\frac{d}{dx}\sin(x) = \cos(x)",
        # Unicode (come estratto da Word)
        r"f:Rn→R",
        r"Ω=x∈Rn:g(x)≤0, h(x)=0",
        r"maxc⊤xx∈P=x∈Rn:Ax≤b",
        r"(1,1),(1,3),(4,1)",
        r"AB−1",
        r"λx1+(1−λ)x2",
    ]
    
    print("CLASSIFICAZIONE FORMULE TEST\n")
    print("=" * 80)
    
    for text in test_formulas:
        result = classifier.classify(text)
        print(f"\nFormula: {text[:60]}...")
        print(f"Categoria: {result.category} / {result.subcategory}")
        print(f"Confidenza: {result.confidence:.2f}")
        print(f"Difficoltà: {result.difficulty}/5")
        print(f"Tags: {', '.join(result.suggested_tags)}")
        print("-" * 80)
