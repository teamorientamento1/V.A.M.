#!/usr/bin/env python3
"""
Test Script - Integrazione Jump Manager + Database Formule
Verifica che tutti i componenti funzionino correttamente
"""

import sys
from pathlib import Path

# Aggiungi path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("TEST INTEGRAZIONE JUMP MANAGER + DATABASE FORMULE")
print("=" * 70)

# Test 1: Import moduli
print("\n[1/6] Test import moduli...")
try:
    from core.formula_database import FormulaDatabase
    from core.formula_classifier import FormulaClassifier
    from core.formula_integration import FormulaIntegration
    from jump_manager_formula_enhancer import JumpManagerFormulaEnhancer
    print("  ✅ Tutti i moduli importati correttamente")
except ImportError as e:
    print(f"  ❌ Errore import: {e}")
    sys.exit(1)

# Test 2: Database
print("\n[2/6] Test connessione database...")
try:
    db = FormulaDatabase("formulas.db")
    stats = db.get_statistics()
    print(f"  ✅ Database connesso")
    print(f"     Totale formule: {stats['total_formulas']}")
    
    if stats['total_formulas'] == 0:
        print("  ⚠️  ATTENZIONE: Database vuoto!")
        print("     Esegui: python populate_database_auto.py")
    
    db.close()
except Exception as e:
    print(f"  ❌ Errore database: {e}")
    sys.exit(1)

# Test 3: Classificatore
print("\n[3/6] Test classificatore...")
try:
    classifier = FormulaClassifier()
    test_latex = r"\int_a^b f(x)\,dx"
    result = classifier.classify(test_latex)
    print(f"  ✅ Classificatore funzionante")
    print(f"     Test: {test_latex}")
    print(f"     Categoria: {result.category}/{result.subcategory}")
    print(f"     Difficoltà: {result.difficulty}/5")
except Exception as e:
    print(f"  ❌ Errore classificatore: {e}")
    sys.exit(1)

# Test 4: Enhancer - Suggerimento
print("\n[4/6] Test enhancer - suggerimento descrizione...")
try:
    enhancer = JumpManagerFormulaEnhancer("formulas.db")
    
    test_latex = r"\sum_{n=1}^{\infty} \frac{1}{n^2}"
    suggestion = enhancer.suggest_description_for_jump(test_latex)
    
    print(f"  ✅ Enhancer funzionante")
    print(f"     Test: {test_latex}")
    print(f"     Descrizione: {suggestion['description']}")
    print(f"     Confidenza: {suggestion['confidence']:.2%}")
    print(f"     Match trovato: {suggestion['has_match']}")
    
except Exception as e:
    print(f"  ❌ Errore enhancer: {e}")
    enhancer.close()
    sys.exit(1)

# Test 5: Enhancer - Arricchimento jump
print("\n[5/6] Test enhancer - arricchimento jump...")
try:
    test_jump = {
        'id': 1,
        'label': 'eq:test',
        'latex': r"\frac{d}{dx}\sin(x) = \cos(x)",
        'type': 'equation'
    }
    
    enriched = enhancer.enrich_single_jump(test_jump)
    
    print(f"  ✅ Arricchimento jump funzionante")
    print(f"     Jump originale: {test_jump['label']}")
    
    if 'formula_metadata' in enriched:
        print(f"     ✨ Match database trovato:")
        print(f"        ID: {enriched['formula_metadata']['database_id']}")
        print(f"        Nome: {enriched['formula_metadata']['name']}")
        print(f"        Categoria: {enriched['formula_metadata']['category']}")
    else:
        print(f"     ℹ️  Nessun match database (normale se DB ha poche formule)")
    
except Exception as e:
    print(f"  ❌ Errore arricchimento: {e}")
    enhancer.close()
    sys.exit(1)

# Test 6: Ricerca formule
print("\n[6/6] Test ricerca formule...")
try:
    results = enhancer.search_formulas_for_ui(query="integral", max_results=3)
    
    print(f"  ✅ Ricerca funzionante")
    print(f"     Query: 'integral'")
    print(f"     Risultati: {len(results)}")
    
    if results:
        for i, r in enumerate(results[:3], 1):
            print(f"        {i}. {r.get('name', 'N/A')[:50]}")
    
    enhancer.close()
    
except Exception as e:
    print(f"  ❌ Errore ricerca: {e}")
    enhancer.close()
    sys.exit(1)

# Test 7: Test GUI widgets (opzionale, solo se PyQt6 disponibile)
print("\n[7/7] Test GUI widgets (opzionale)...")
try:
    from PyQt6.QtWidgets import QApplication
    from formula_panel_widget import FormulaSearchPanel, FormulaSuggestionWidget
    
    print("  ✅ Widget GUI disponibili")
    print("     FormulaSearchPanel: OK")
    print("     FormulaSuggestionWidget: OK")
    
except ImportError:
    print("  ⚠️  PyQt6 non installato (opzionale per GUI)")
    print("     Per installare: pip3 install PyQt6")

# Riepilogo finale
print("\n" + "=" * 70)
print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
print("=" * 70)

print("\n📊 Riepilogo:")
print(f"  Database formule: {stats['total_formulas']} formule")
print(f"  Categorie: {len(stats['by_category'])}")
print(f"  Formule verificate: {stats['verified_formulas']}")

if stats['total_formulas'] < 100:
    print("\n💡 Consiglio: Popola il database con più formule")
    print("   Esegui: python populate_database_auto.py")

print("\n🚀 Prossimi passi:")
print("  1. Integra nel tuo Jump Manager seguendo GUIDA_INTEGRAZIONE_JUMP_MANAGER.md")
print("  2. Testa con la GUI: cd gui && python3 formula_manager_gui.py")
print("  3. (Opzionale) Popola database con più formule")

print("\n✨ Il sistema è pronto all'uso!\n")
