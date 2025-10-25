#!/usr/bin/env python3
"""
Script di esempio - Uso programmatico del sistema
Mostra come usare le API senza UI
"""
import sys
from pathlib import Path

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.knowledge_base import KnowledgeBase
from core.document_analyzer import WordAnalyzer
from modules.jump_manager.jump_creator import JumpManager
from modules.symbol_dictionary.symbol_manager import SymbolDictionary


def esempio_analisi_documento():
    """
    Esempio: Analizzare un documento Word e aggiungerlo al KB
    """
    print("\n" + "="*60)
    print("ESEMPIO 1: Analisi Documento Word")
    print("="*60)
    
    # 1. Inizializza Knowledge Base
    kb = KnowledgeBase()
    print("✓ Knowledge Base inizializzato")
    
    # 2. Crea analyzer
    analyzer = WordAnalyzer(kb)
    print("✓ Analyzer creato")
    
    # 3. Carica documento (se esiste)
    doc_path = Path("esempio_documento.docx")
    if not doc_path.exists():
        print(f"⚠ Documento di esempio non trovato: {doc_path}")
        print("  Crea un file 'esempio_documento.docx' con alcune equazioni")
        return
    
    analyzer.load_document(doc_path)
    print(f"✓ Documento caricato: {doc_path}")
    
    # 4. Analizza
    print("\nAnalisi in corso...")
    analysis = analyzer.analyze(discipline="mathematics")
    
    # 5. Mostra risultati
    print("\n--- RISULTATI ANALISI ---")
    stats = analysis['statistics']
    print(f"Paragrafi: {stats['total_paragraphs']}")
    print(f"Equazioni: {stats['total_equations']}")
    print(f"Immagini: {stats['total_images']}")
    print(f"Tabelle: {stats['total_tables']}")
    print(f"Riferimenti: {stats['total_references']}")
    
    if analysis['equations']:
        print("\nPrime 3 equazioni:")
        for i, eq in enumerate(analysis['equations'][:3], 1):
            print(f"  {i}. {eq['text_representation'][:50]}...")
    
    # 6. Impara e aggiungi al KB
    patterns_added = analyzer.learn_from_analysis(discipline="mathematics")
    print(f"\n✓ Aggiunti {patterns_added} pattern al Knowledge Base")
    
    # 7. Statistiche KB
    kb_stats = kb.get_statistics()
    print(f"\nStatistiche KB:")
    for disc, count in kb_stats['patterns_by_discipline'].items():
        if count > 0:
            print(f"  - {disc}: {count} pattern")
    
    kb.close()
    print("\n✓ Completato!")


def esempio_gestione_simboli():
    """
    Esempio: Gestire dizionario simboli
    """
    print("\n" + "="*60)
    print("ESEMPIO 2: Gestione Simboli")
    print("="*60)
    
    kb = KnowledgeBase()
    symbol_dict = SymbolDictionary(kb)
    
    # Aggiungi simboli custom
    print("\nAggiunta simboli personalizzati...")
    
    simboli_custom = {
        'α': 'alfa',
        'β': 'beta',
        'Σ': 'sommatoria',
        '∫': 'integrale',
        '∂': 'derivata parziale'
    }
    
    for symbol, pronunciation in simboli_custom.items():
        symbol_dict.set_pronunciation(symbol, pronunciation)
        print(f"  {symbol} → {pronunciation}")
    
    # Test pronuncia
    print("\nTest pronuncia context-aware:")
    test_cases = [
        ('d', 'dx', 'Dovrebbe dire "differenziale"'),
        ('d', 'variabile d', 'Dovrebbe dire "di"'),
        ('α', None, 'Dovrebbe dire "alfa"')
    ]
    
    for symbol, context, note in test_cases:
        pronunciation = symbol_dict._get_pronunciation(symbol, context)
        print(f"  {symbol} in '{context or 'nessun contesto'}': '{pronunciation}' ({note})")
    
    # Statistiche
    stats = symbol_dict.get_statistics()
    print(f"\nStatistiche dizionario:")
    print(f"  - Simboli default: {stats['default_symbols']}")
    print(f"  - Personalizzati: {stats['user_customized']}")
    
    # Salva preferenze
    prefs_path = Path("user_symbol_preferences.json")
    symbol_dict.save_user_preferences(prefs_path)
    print(f"\n✓ Preferenze salvate in: {prefs_path}")
    
    kb.close()


def esempio_backup_restore():
    """
    Esempio: Backup e ripristino Knowledge Base
    """
    print("\n" + "="*60)
    print("ESEMPIO 3: Backup e Ripristino")
    print("="*60)
    
    kb = KnowledgeBase()
    
    # Crea alcuni dati di test
    print("\nAggiunta dati di test...")
    for i in range(5):
        kb.add_pattern(
            discipline="mathematics",
            pattern_type="test_pattern",
            content_description=f"Pattern di test {i}",
            confidence_score=0.8
        )
    print("✓ 5 pattern di test aggiunti")
    
    # Crea backup
    print("\nCreazione backup...")
    backup_path = kb.create_backup('full')
    print(f"✓ Backup creato: {backup_path}")
    
    # Lista tutti i backup
    print("\nBackup disponibili:")
    backups = kb.list_backups()
    for i, backup in enumerate(backups[:5], 1):
        size_mb = backup['file_size_bytes'] / 1024 / 1024
        print(f"  {i}. {Path(backup['backup_path']).name}")
        print(f"     Tipo: {backup['backup_type']}, Size: {size_mb:.2f} MB")
        print(f"     Creato: {backup['created_at']}")
    
    print("\n✓ Sistema di backup funzionante!")
    
    kb.close()


def esempio_query_knowledge_base():
    """
    Esempio: Query e ricerca nel Knowledge Base
    """
    print("\n" + "="*60)
    print("ESEMPIO 4: Query Knowledge Base")
    print("="*60)
    
    kb = KnowledgeBase()
    
    # Aggiungi alcuni pattern di esempio
    print("\nPopola KB con pattern di esempio...")
    
    patterns_data = [
        {
            'discipline': 'mathematics',
            'pattern_type': 'definite_integral',
            'latex_representation': r'\int_{a}^{b} f(x) dx',
            'content_description': 'Integrale definito',
            'context_words': ['area', 'curva', 'intervallo']
        },
        {
            'discipline': 'physics',
            'pattern_type': 'force_equation',
            'latex_representation': r'F = ma',
            'content_description': 'Seconda legge di Newton',
            'context_words': ['forza', 'massa', 'accelerazione']
        },
        {
            'discipline': 'mathematics',
            'pattern_type': 'summation',
            'latex_representation': r'\sum_{i=1}^{n} i',
            'content_description': 'Sommatoria',
            'context_words': ['serie', 'somma']
        }
    ]
    
    for data in patterns_data:
        kb.add_pattern(**data)
    print(f"✓ Aggiunti {len(patterns_data)} pattern")
    
    # Query 1: Cerca pattern matematici
    print("\n--- Query 1: Pattern matematici ---")
    results = kb.find_similar_patterns(discipline="mathematics", limit=5)
    print(f"Trovati {len(results)} pattern:")
    for r in results:
        print(f"  - {r['pattern_type']}: {r['content_description']}")
    
    # Query 2: Cerca per LaTeX
    print("\n--- Query 2: Cerca 'integral' ---")
    results = kb.find_similar_patterns(latex="integral")
    if results:
        print(f"Match: {results[0]['latex_representation']}")
    
    # Statistiche complete
    print("\n--- Statistiche Complete ---")
    stats = kb.get_statistics()
    print(f"Pattern per disciplina:")
    for disc, count in stats['patterns_by_discipline'].items():
        if count > 0:
            print(f"  - {disc}: {count}")
    
    print(f"\nTop pattern types:")
    for ptype, count in stats['top_pattern_types'].items():
        print(f"  - {ptype}: {count}")
    
    kb.close()
    print("\n✓ Completato!")


def main():
    """Main - Esegui tutti gli esempi"""
    print("\n" + "█"*60)
    print("  ACCESSIBLE DOCS SYSTEM - Script di Esempio")
    print("█"*60)
    print()
    print("Questo script mostra come usare il sistema programmaticamente")
    print("senza interfaccia grafica.")
    print()
    
    try:
        # Esempio 1: Analisi documento
        # esempio_analisi_documento()  # Commentato: serve documento vero
        
        # Esempio 2: Simboli
        esempio_gestione_simboli()
        
        # Esempio 3: Backup
        esempio_backup_restore()
        
        # Esempio 4: Query KB
        esempio_query_knowledge_base()
        
        print("\n" + "█"*60)
        print("  ✓ TUTTI GLI ESEMPI COMPLETATI")
        print("█"*60)
        print()
        print("Puoi modificare questo script per adattarlo ai tuoi bisogni.")
        print("Controlla i file in core/ e modules/ per altre API disponibili.")
        print()
        
    except Exception as e:
        print(f"\n✗ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
