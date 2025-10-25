#!/usr/bin/env python3
"""
Test script per verificare il funzionamento del sistema
"""
import sys
from pathlib import Path

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.knowledge_base import KnowledgeBase
from config.settings import DATABASE_PATH, BACKUP_DIR

def test_knowledge_base():
    """Test del Knowledge Base"""
    print("\n" + "=" * 60)
    print("TEST KNOWLEDGE BASE")
    print("=" * 60)
    
    try:
        # Inizializza KB
        print("\n1. Inizializzazione database...")
        kb = KnowledgeBase()
        print(f"   ✓ Database creato: {DATABASE_PATH}")
        
        # Test aggiunta pattern
        print("\n2. Aggiunta pattern di test...")
        pattern_id = kb.add_pattern(
            discipline="mathematics",
            pattern_type="integral",
            latex_representation="\\int_{0}^{1} x^2 dx",
            content_description="Integrale definito",
            context_words=["area", "curva"],
            confidence_score=0.9
        )
        print(f"   ✓ Pattern aggiunto con ID: {pattern_id}")
        
        # Test aggiunta simbolo
        print("\n3. Aggiunta simbolo di test...")
        symbol_id = kb.add_symbol(
            symbol="∫",
            discipline="mathematics",
            latex_code="\\int",
            category="operator",
            default_pronunciation="integrale"
        )
        print(f"   ✓ Simbolo aggiunto con ID: {symbol_id}")
        
        # Test ricerca
        print("\n4. Ricerca pattern simili...")
        results = kb.find_similar_patterns(
            latex="integral",
            discipline="mathematics"
        )
        print(f"   ✓ Trovati {len(results)} pattern")
        if results:
            print(f"     - Pattern: {results[0]['pattern_type']}")
        
        # Test statistiche
        print("\n5. Statistiche database...")
        stats = kb.get_statistics()
        print(f"   ✓ Pattern per disciplina:")
        for disc, count in stats['patterns_by_discipline'].items():
            print(f"     - {disc}: {count}")
        print(f"   ✓ Simboli totali: {stats['total_symbols']}")
        
        # Test backup
        print("\n6. Creazione backup...")
        backup_path = kb.create_backup('full')
        print(f"   ✓ Backup creato: {backup_path.name}")
        
        # Test backup list
        print("\n7. Lista backup...")
        backups = kb.list_backups()
        print(f"   ✓ Backup disponibili: {len(backups)}")
        
        # Chiudi
        kb.close()
        print("\n   ✓ Knowledge Base chiuso correttamente")
        
        print("\n" + "=" * 60)
        print("✓ TUTTI I TEST COMPLETATI CON SUCCESSO")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test degli import"""
    print("\n" + "=" * 60)
    print("TEST IMPORT MODULI")
    print("=" * 60)
    
    modules = [
        ('core.knowledge_base', 'KnowledgeBase'),
        ('core.document_analyzer', 'WordAnalyzer'),
        ('modules.jump_manager.jump_creator', 'JumpManager'),
        ('modules.symbol_dictionary.symbol_manager', 'SymbolDictionary'),
        ('config.settings', 'DATABASE_PATH'),
    ]
    
    all_ok = True
    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_path}.{class_name}")
        except Exception as e:
            print(f"✗ {module_path}.{class_name} - ERRORE: {e}")
            all_ok = False
    
    if all_ok:
        print("\n✓ Tutti gli import OK")
    else:
        print("\n✗ Alcuni import hanno fallito")
    
    return all_ok

def main():
    """Main test function"""
    print("\n")
    print("█" * 60)
    print("  ACCESSIBLE DOCS SYSTEM - TEST SUITE")
    print("█" * 60)
    
    # Test imports
    if not test_imports():
        print("\n✗ Test import falliti. Controllare l'installazione.")
        return False
    
    # Test KB
    if not test_knowledge_base():
        print("\n✗ Test Knowledge Base falliti.")
        return False
    
    print("\n")
    print("█" * 60)
    print("  ✓ TUTTI I TEST COMPLETATI CON SUCCESSO")
    print("█" * 60)
    print("\nIl sistema è pronto all'uso!")
    print(f"Avvia l'applicazione con: python main.py")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
