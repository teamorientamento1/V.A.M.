#!/usr/bin/env python3
"""
Popola database con formule LaTeX BASILARI
Include: apici, pedici, frazioni, radici, operatori comuni, simboli matematici
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.formula_database import FormulaDatabase


def get_basic_formulas():
    """Ritorna lista formule basilari LaTeX"""
    
    formulas = []
    
    # === APICI E PEDICI ===
    formulas.extend([
        {
            'latex': r'x^2',
            'name': 'Apice (elevamento a potenza)',
            'description': 'x al quadrato - usa ^ per apici',
            'category': 'algebra',
            'subcategory': 'polynomial',
            'difficulty': 1,
            'tags': ['base', 'apice', 'potenza'],
        },
        {
            'latex': r'x^n',
            'name': 'Apice generico',
            'description': 'x alla n - apice con variabile',
            'category': 'algebra',
            'subcategory': 'polynomial',
            'difficulty': 1,
            'tags': ['base', 'apice', 'potenza'],
        },
        {
            'latex': r'x_i',
            'name': 'Pedice (indice)',
            'description': 'x pedice i - usa _ per pedici',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'pedice', 'indice'],
        },
        {
            'latex': r'x_{ij}',
            'name': 'Pedice doppio',
            'description': 'x pedice ij - pedici multipli',
            'category': 'algebra',
            'subcategory': 'linear',
            'difficulty': 1,
            'tags': ['base', 'pedice', 'matrice'],
        },
        {
            'latex': r'x_i^2',
            'name': 'Apice e pedice insieme',
            'description': 'x pedice i al quadrato',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'apice', 'pedice'],
        },
    ])
    
    # === FRAZIONI ===
    formulas.extend([
        {
            'latex': r'\frac{a}{b}',
            'name': 'Frazione semplice',
            'description': 'a su b - frazione base',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'frazione'],
        },
        {
            'latex': r'\frac{x^2 + 1}{x - 1}',
            'name': 'Frazione con polinomi',
            'description': 'Frazione con numeratore e denominatore complessi',
            'category': 'algebra',
            'subcategory': 'polynomial',
            'difficulty': 2,
            'tags': ['frazione', 'polinomio'],
        },
        {
            'latex': r'\frac{1}{2}',
            'name': 'Un mezzo',
            'description': 'Frazione numerica 1/2',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'frazione', 'numero'],
        },
    ])
    
    # === RADICI ===
    formulas.extend([
        {
            'latex': r'\sqrt{x}',
            'name': 'Radice quadrata',
            'description': 'Radice quadrata di x',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'radice'],
        },
        {
            'latex': r'\sqrt[n]{x}',
            'name': 'Radice n-esima',
            'description': 'Radice n-esima di x',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'radice'],
        },
        {
            'latex': r'\sqrt{x^2 + y^2}',
            'name': 'Radice di somma di quadrati',
            'description': 'Distanza euclidea - radice di somma quadrati',
            'category': 'geometry',
            'subcategory': 'analytic',
            'difficulty': 2,
            'tags': ['radice', 'distanza', 'pitagora'],
        },
    ])
    
    # === SOMMATORIE E PRODUTTORIE ===
    formulas.extend([
        {
            'latex': r'\sum_{i=1}^{n} x_i',
            'name': 'Sommatoria',
            'description': 'Somma da i=1 a n di x_i',
            'category': 'calculus',
            'subcategory': 'series',
            'difficulty': 2,
            'tags': ['base', 'sommatoria', 'serie'],
        },
        {
            'latex': r'\prod_{i=1}^{n} x_i',
            'name': 'Produttoria',
            'description': 'Prodotto da i=1 a n di x_i',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 2,
            'tags': ['base', 'produttoria'],
        },
        {
            'latex': r'\sum_{k=0}^{\infty} a_k',
            'name': 'Serie infinita',
            'description': 'Somma da k=0 a infinito',
            'category': 'calculus',
            'subcategory': 'series',
            'difficulty': 2,
            'tags': ['sommatoria', 'infinito', 'serie'],
        },
    ])
    
    # === INTEGRALI E DERIVATE BASE ===
    formulas.extend([
        {
            'latex': r'\int f(x)\,dx',
            'name': 'Integrale indefinito',
            'description': 'Integrale indefinito di f(x)',
            'category': 'calculus',
            'subcategory': 'integral',
            'difficulty': 2,
            'tags': ['base', 'integrale'],
        },
        {
            'latex': r'\int_a^b f(x)\,dx',
            'name': 'Integrale definito',
            'description': 'Integrale definito da a a b',
            'category': 'calculus',
            'subcategory': 'integral',
            'difficulty': 2,
            'tags': ['base', 'integrale', 'definito'],
        },
        {
            'latex': r'\frac{d}{dx}f(x)',
            'name': 'Derivata',
            'description': 'Derivata di f(x) rispetto a x',
            'category': 'calculus',
            'subcategory': 'derivative',
            'difficulty': 2,
            'tags': ['base', 'derivata'],
        },
        {
            'latex': r'\frac{\partial}{\partial x}f(x,y)',
            'name': 'Derivata parziale',
            'description': 'Derivata parziale rispetto a x',
            'category': 'calculus',
            'subcategory': 'derivative',
            'difficulty': 3,
            'tags': ['derivata', 'parziale'],
        },
    ])
    
    # === LIMITI ===
    formulas.extend([
        {
            'latex': r'\lim_{x \to a} f(x)',
            'name': 'Limite',
            'description': 'Limite di f(x) per x che tende ad a',
            'category': 'calculus',
            'subcategory': 'limit',
            'difficulty': 2,
            'tags': ['base', 'limite'],
        },
        {
            'latex': r'\lim_{x \to \infty} f(x)',
            'name': 'Limite all\'infinito',
            'description': 'Limite per x che tende a infinito',
            'category': 'calculus',
            'subcategory': 'limit',
            'difficulty': 2,
            'tags': ['limite', 'infinito'],
        },
        {
            'latex': r'\lim_{x \to 0^+} f(x)',
            'name': 'Limite destro',
            'description': 'Limite destro (da destra) per x→0',
            'category': 'calculus',
            'subcategory': 'limit',
            'difficulty': 2,
            'tags': ['limite', 'laterale'],
        },
    ])
    
    # === VETTORI E MATRICI ===
    formulas.extend([
        {
            'latex': r'\vec{v}',
            'name': 'Vettore',
            'description': 'Vettore v (notazione freccia)',
            'category': 'geometry',
            'subcategory': 'vector',
            'difficulty': 1,
            'tags': ['base', 'vettore'],
        },
        {
            'latex': r'\mathbf{v}',
            'name': 'Vettore (grassetto)',
            'description': 'Vettore v (notazione grassetto)',
            'category': 'geometry',
            'subcategory': 'vector',
            'difficulty': 1,
            'tags': ['base', 'vettore'],
        },
        {
            'latex': r'\begin{pmatrix} a & b \\ c & d \end{pmatrix}',
            'name': 'Matrice 2x2',
            'description': 'Matrice 2x2 con parentesi tonde',
            'category': 'algebra',
            'subcategory': 'linear',
            'difficulty': 2,
            'tags': ['base', 'matrice'],
        },
        {
            'latex': r'\begin{bmatrix} x \\ y \\ z \end{bmatrix}',
            'name': 'Vettore colonna',
            'description': 'Vettore colonna 3D',
            'category': 'geometry',
            'subcategory': 'vector',
            'difficulty': 2,
            'tags': ['vettore', 'matrice'],
        },
    ])
    
    # === OPERATORI LOGICI ===
    formulas.extend([
        {
            'latex': r'A \land B',
            'name': 'AND logico',
            'description': 'A e B (congiunzione logica)',
            'category': 'other',
            'subcategory': 'logic',
            'difficulty': 1,
            'tags': ['base', 'logica', 'operatore'],
        },
        {
            'latex': r'A \lor B',
            'name': 'OR logico',
            'description': 'A o B (disgiunzione logica)',
            'category': 'other',
            'subcategory': 'logic',
            'difficulty': 1,
            'tags': ['base', 'logica', 'operatore'],
        },
        {
            'latex': r'\neg A',
            'name': 'NOT logico',
            'description': 'Non A (negazione logica)',
            'category': 'other',
            'subcategory': 'logic',
            'difficulty': 1,
            'tags': ['base', 'logica', 'operatore'],
        },
        {
            'latex': r'A \implies B',
            'name': 'Implicazione',
            'description': 'A implica B',
            'category': 'other',
            'subcategory': 'logic',
            'difficulty': 1,
            'tags': ['base', 'logica', 'implicazione'],
        },
        {
            'latex': r'A \iff B',
            'name': 'Doppia implicazione',
            'description': 'A se e solo se B',
            'category': 'other',
            'subcategory': 'logic',
            'difficulty': 1,
            'tags': ['base', 'logica', 'equivalenza'],
        },
    ])
    
    # === INSIEMI ===
    formulas.extend([
        {
            'latex': r'x \in A',
            'name': 'Appartenenza',
            'description': 'x appartiene ad A',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'insieme', 'appartenenza'],
        },
        {
            'latex': r'A \cup B',
            'name': 'Unione',
            'description': 'Unione di A e B',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'insieme', 'unione'],
        },
        {
            'latex': r'A \cap B',
            'name': 'Intersezione',
            'description': 'Intersezione di A e B',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'insieme', 'intersezione'],
        },
        {
            'latex': r'A \subseteq B',
            'name': 'Sottoinsieme',
            'description': 'A sottoinsieme di B',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'insieme', 'sottoinsieme'],
        },
        {
            'latex': r'\emptyset',
            'name': 'Insieme vuoto',
            'description': 'Insieme vuoto (nessun elemento)',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'insieme', 'vuoto'],
        },
    ])
    
    # === SIMBOLI SPECIALI ===
    formulas.extend([
        {
            'latex': r'\infty',
            'name': 'Infinito',
            'description': 'Simbolo infinito',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'infinito'],
        },
        {
            'latex': r'\pm',
            'name': 'Più o meno',
            'description': 'Più o meno (±)',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'operatore'],
        },
        {
            'latex': r'\approx',
            'name': 'Circa uguale',
            'description': 'Approssimativamente uguale',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'uguaglianza'],
        },
        {
            'latex': r'\neq',
            'name': 'Diverso',
            'description': 'Diverso da (≠)',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'disuguaglianza'],
        },
        {
            'latex': r'\leq',
            'name': 'Minore o uguale',
            'description': 'Minore o uguale a (≤)',
            'category': 'algebra',
            'subcategory': 'inequality',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'disuguaglianza'],
        },
        {
            'latex': r'\geq',
            'name': 'Maggiore o uguale',
            'description': 'Maggiore o uguale a (≥)',
            'category': 'algebra',
            'subcategory': 'inequality',
            'difficulty': 1,
            'tags': ['base', 'simbolo', 'disuguaglianza'],
        },
    ])
    
    # === LETTERE GRECHE COMUNI ===
    formulas.extend([
        {
            'latex': r'\alpha, \beta, \gamma, \delta',
            'name': 'Lettere greche minuscole comuni',
            'description': 'alpha, beta, gamma, delta',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'greco', 'lettere'],
        },
        {
            'latex': r'\pi',
            'name': 'Pi greco',
            'description': 'Pi greco (π ≈ 3.14159)',
            'category': 'geometry',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'greco', 'costante'],
        },
        {
            'latex': r'\theta, \phi, \psi',
            'name': 'Angoli (lettere greche)',
            'description': 'theta, phi, psi - usati per angoli',
            'category': 'geometry',
            'subcategory': 'trigonometry',
            'difficulty': 1,
            'tags': ['base', 'greco', 'angolo'],
        },
        {
            'latex': r'\lambda',
            'name': 'Lambda',
            'description': 'lambda - autovalore, lunghezza d\'onda',
            'category': 'other',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'greco'],
        },
        {
            'latex': r'\mu, \sigma',
            'name': 'Media e deviazione standard',
            'description': 'mu (media), sigma (dev. standard)',
            'category': 'statistics',
            'subcategory': 'descriptive',
            'difficulty': 1,
            'tags': ['base', 'greco', 'statistica'],
        },
    ])
    
    # === FUNZIONI COMUNI ===
    formulas.extend([
        {
            'latex': r'\sin(x), \cos(x), \tan(x)',
            'name': 'Funzioni trigonometriche base',
            'description': 'Seno, coseno, tangente',
            'category': 'geometry',
            'subcategory': 'trigonometry',
            'difficulty': 1,
            'tags': ['base', 'trigonometria', 'funzione'],
        },
        {
            'latex': r'e^x',
            'name': 'Esponenziale',
            'description': 'e alla x (esponenziale naturale)',
            'category': 'special_functions',
            'subcategory': 'exponential',
            'difficulty': 1,
            'tags': ['base', 'esponenziale', 'e'],
        },
        {
            'latex': r'\ln(x)',
            'name': 'Logaritmo naturale',
            'description': 'Logaritmo naturale (base e)',
            'category': 'special_functions',
            'subcategory': 'exponential',
            'difficulty': 1,
            'tags': ['base', 'logaritmo'],
        },
        {
            'latex': r'\log_{10}(x)',
            'name': 'Logaritmo decimale',
            'description': 'Logaritmo in base 10',
            'category': 'special_functions',
            'subcategory': 'exponential',
            'difficulty': 1,
            'tags': ['base', 'logaritmo'],
        },
        {
            'latex': r'|x|',
            'name': 'Valore assoluto',
            'description': 'Valore assoluto di x',
            'category': 'algebra',
            'subcategory': 'misc',
            'difficulty': 1,
            'tags': ['base', 'assoluto'],
        },
    ])
    
    return formulas


def main():
    """Popola database con formule basilari"""
    
    print("=" * 70)
    print("POPOLAMENTO DATABASE CON FORMULE BASILARI")
    print("=" * 70)
    
    # Carica database
    db = FormulaDatabase("formulas.db")
    
    # Statistiche pre-import
    stats_pre = db.get_statistics()
    print(f"\nDatabase attuale: {stats_pre['total_formulas']} formule")
    
    # Ottieni formule basilari
    basic_formulas = get_basic_formulas()
    print(f"Formule basilari da aggiungere: {len(basic_formulas)}")
    
    # Conferma
    risposta = input("\nVuoi aggiungere queste formule basilari? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("Operazione annullata.")
        db.close()
        return
    
    # Aggiungi formule
    print("\nAggiungendo formule...")
    added = 0
    duplicates = 0
    
    for formula in basic_formulas:
        formula_id = db.add_formula(
            latex=formula['latex'],
            name=formula['name'],
            description=formula['description'],
            category=formula['category'],
            subcategory=formula['subcategory'],
            difficulty=formula['difficulty'],
            tags=formula['tags'],
            source='Built-in',
            source_url=None,
            verified=True
        )
        
        if formula_id:
            added += 1
        else:
            duplicates += 1
    
    # Statistiche post-import
    stats_post = db.get_statistics()
    
    print("\n" + "=" * 70)
    print("COMPLETATO")
    print("=" * 70)
    print(f"\nFormule aggiunte: {added}")
    print(f"Duplicate (già presenti): {duplicates}")
    print(f"Totale formule nel database: {stats_post['total_formulas']}")
    
    print("\n📊 Distribuzione per categoria:")
    for cat, count in sorted(stats_post['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat:20s}: {count:4d}")
    
    print("\n✅ Database aggiornato con formule basilari!")
    print("\nProssimi passi:")
    print("  1. Apri GUI: cd gui && python3 formula_manager_gui.py")
    print("  2. Testa integrazione: python3 test_integration.py")
    
    db.close()


if __name__ == "__main__":
    main()
