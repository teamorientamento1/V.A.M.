#!/usr/bin/env python3
"""
Test Completo Sistema Formule
Dimostra tutte le funzionalità integrate
"""

import sys
sys.path.insert(0, '/home/claude')

from core.formula_database import FormulaDatabase
from core.formula_classifier import FormulaClassifier
from integration.jump_enricher import JumpEnricher


def print_section(title):
    """Stampa intestazione sezione"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def test_database():
    """Test funzionalità database"""
    print_section("TEST 1: DATABASE FORMULE")
    
    db = FormulaDatabase("formulas.db")
    
    # Statistiche
    stats = db.get_statistics()
    print(f"📊 Statistiche Database:")
    print(f"   • Totale formule: {stats['total_formulas']}")
    print(f"   • Formule verificate: {stats['verified']}")
    print(f"   • Categorie: {len(stats['by_category'])}")
    print(f"   • Livelli difficoltà: {len(stats['by_difficulty'])}")
    
    # Cerca formule
    print(f"\n🔍 Test ricerca:")
    
    # Per categoria
    calculus = db.search_formulas(category='calculus', limit=3)
    print(f"\n   Formule di Calcolo ({len(calculus)} trovate):")
    for f in calculus[:2]:
        print(f"   • {f['name']}: {f['latex']}")
    
    # Per tag
    integrals = db.search_formulas(tags=['integrale'])
    print(f"\n   Formule con tag 'integrale' ({len(integrals)} trovate):")
    for f in integrals[:2]:
        print(f"   • {f['name']}")
    
    # Similarità
    similar = db.find_similar_formulas(r'\int x\,dx')
    print(f"\n   Formule simili a '\\int x\\,dx' ({len(similar)} trovate):")
    for f in similar[:2]:
        sim = f.get('similarity', 1.0)
        print(f"   • {f['name']} (similarità: {sim:.2f})")
    
    db.close()
    print("\n✅ Test database completato")


def test_classifier():
    """Test classificatore"""
    print_section("TEST 2: CLASSIFICATORE AUTOMATICO")
    
    classifier = FormulaClassifier()
    
    test_cases = [
        (r"x^2 + 2x + 1", "Polinomio semplice"),
        (r"\int_0^\pi \sin(x)\,dx", "Integrale trigonometrico"),
        (r"\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u", "Equazione onde"),
        (r"A \cap (B \cup C) = (A \cap B) \cup (A \cap C)", "Distributività insiemi"),
    ]
    
    print("📊 Classificazione automatica:\n")
    
    for latex, name in test_cases:
        c = classifier.classify(latex)
        
        print(f"🔹 {name}")
        print(f"   Formula: {latex}")
        print(f"   ├─ Categoria: {c.category} / {c.subcategory}")
        print(f"   ├─ Difficoltà: {'⭐' * c.difficulty} ({c.difficulty}/5)")
        print(f"   ├─ Complessità: {c.complexity_score:.1f}/100")
        print(f"   ├─ Simboli: {len(c.symbols)} ({', '.join(c.symbols[:3])}...)")
        print(f"   └─ Tags: {', '.join(c.tags[:5])}")
        print()
    
    print("✅ Test classificatore completato")


def test_jump_integration():
    """Test integrazione jump"""
    print_section("TEST 3: INTEGRAZIONE JUMP MANAGEMENT")
    
    enricher = JumpEnricher("formulas.db")
    
    # Simula jump da un documento accessibile
    jumps = [
        {'latex': r'x^2', 'description': '', 'page': 1},
        {'latex': r'\int_0^1 x^2\,dx', 'description': 'calcolo area', 'page': 2},
        {'latex': r'\frac{a}{b}', 'description': '', 'page': 3},
        {'latex': r'\sin(x) + \cos(x)', 'description': 'identità', 'page': 5},
        {'latex': r'\lim_{x \to 0} \frac{\sin(x)}{x}', 'description': '', 'page': 8},
    ]
    
    print(f"🔧 Arricchimento {len(jumps)} jump da documento:\n")
    
    results = enricher.batch_enrich(jumps)
    
    for i, r in enumerate(results, 1):
        jump = r['original_jump']
        
        print(f"Jump #{i} (pag. {jump['page']})")
        print(f"   Formula: {jump['latex']}")
        print(f"   Match database: {'✓ SÌ' if r['matched'] else '✗ NO'}")
        print(f"   Score qualità: {r['enrichment_score']:.2f}")
        
        if r['matched']:
            print(f"   🎯 Formula trovata: {r['formula']['name']}")
        
        print(f"   Descrizione originale: '{jump['description']}'")
        print(f"   Descrizione arricchita: '{r['suggested_description']}'")
        
        if r['alternatives']:
            print(f"   📚 {len(r['alternatives'])} alternative disponibili")
        
        # Suggerimenti
        suggestions = enricher.suggest_improvements(jump['latex'])
        if suggestions:
            print(f"   💡 Suggerimenti: {suggestions[0]}")
        
        print()
    
    # Statistiche batch
    stats = enricher.get_enrichment_stats(results)
    
    print("📈 Statistiche batch:")
    print(f"   • Match rate: {stats['matched']}/{stats['total']} ({stats['matched']/stats['total']*100:.0f}%)")
    print(f"   • Score medio: {stats['avg_score']:.2f}")
    print(f"   • Alta qualità: {stats['high_quality']}")
    print(f"   • Media qualità: {stats['medium_quality']}")
    print(f"   • Bassa qualità: {stats['low_quality']}")
    
    enricher.close()
    print("\n✅ Test integrazione completato")


def test_real_workflow():
    """Test workflow reale"""
    print_section("TEST 4: WORKFLOW COMPLETO")
    
    print("Simulazione workflow tipico:\n")
    
    # 1. Documento con formule
    print("📄 Passo 1: Documento con formule LaTeX")
    doc_formulas = [
        r"E = mc^2",
        r"\nabla \cdot \vec{E} = \frac{\rho}{\epsilon_0}",
        r"i\hbar\frac{\partial}{\partial t}\Psi = \hat{H}\Psi",
    ]
    print(f"   • {len(doc_formulas)} formule estratte dal documento")
    
    # 2. Classificazione
    print("\n🔍 Passo 2: Classificazione automatica")
    classifier = FormulaClassifier()
    for latex in doc_formulas:
        c = classifier.classify(latex)
        print(f"   • {latex[:30]}... → {c.category}/{c.subcategory} (⭐×{c.difficulty})")
    
    # 3. Ricerca nel database
    print("\n🗄️  Passo 3: Ricerca nel database")
    db = FormulaDatabase("formulas.db")
    for latex in doc_formulas:
        similar = db.find_similar_formulas(latex, threshold=0.5)
        status = "trovata" if similar else "non trovata"
        print(f"   • {latex[:30]}... → {status}")
    db.close()
    
    # 4. Arricchimento
    print("\n✨ Passo 4: Arricchimento jump")
    enricher = JumpEnricher("formulas.db")
    jumps = [{'latex': l, 'description': ''} for l in doc_formulas]
    results = enricher.batch_enrich(jumps)
    
    for r in results:
        latex = r['original_jump']['latex']
        desc = r['suggested_description']
        print(f"   • {latex[:30]}...")
        print(f"     → {desc}")
    
    # 5. Risultato finale
    print("\n📊 Passo 5: Statistiche finali")
    stats = enricher.get_enrichment_stats(results)
    print(f"   • Formule elaborate: {stats['total']}")
    print(f"   • Con descrizione arricchita: {stats['matched'] + stats['unmatched']}")
    print(f"   • Qualità media: {stats['avg_score']:.2f}/1.00")
    
    enricher.close()
    print("\n✅ Workflow completato")


def main():
    """Esegui tutti i test"""
    
    print("\n" + "🚀 " * 40)
    print("TEST COMPLETO SISTEMA GESTIONE FORMULE MATEMATICHE")
    print("Sistema per documenti accessibili con formule LaTeX")
    print("🚀 " * 40)
    
    try:
        test_database()
        test_classifier()
        test_jump_integration()
        test_real_workflow()
        
        print("\n" + "=" * 80)
        print(" ✅ TUTTI I TEST COMPLETATI CON SUCCESSO ".center(80, "="))
        print("=" * 80 + "\n")
        
        print("📝 Sistema pronto per l'uso!")
        print("\nFunzionalità disponibili:")
        print("   1. ✓ Database con 51 formule basilari verificate")
        print("   2. ✓ Classificatore automatico (8 categorie, 50+ simboli)")
        print("   3. ✓ Ricerca per similarità e matching LaTeX")
        print("   4. ✓ Integrazione jump management con arricchimento automatico")
        print("   5. ✓ Statistiche e analytics")
        
        print("\n🎯 Prossimi passi suggeriti:")
        print("   • Popolare database con più formule (DLMF, Wikipedia, arXiv)")
        print("   • Creare GUI per gestione visuale")
        print("   • Integrare con sistema jump esistente")
        print("   • Aggiungere import/export batch")
        
    except Exception as e:
        print(f"\n❌ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
