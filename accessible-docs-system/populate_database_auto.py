#!/usr/bin/env python3
"""
Script Automatico Popolamento Database Formule
Importa formule da DLMF e Wikipedia automaticamente
"""

import sys
from pathlib import Path

# Aggiungi path per import
sys.path.insert(0, str(Path(__file__).parent))

from core.formula_database import FormulaDatabase
from core.archive_importers.dlmf_importer import DLMFImporter, WikipediaFormulaImporter


def print_banner(text):
    """Stampa banner decorato"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def populate_database_standard():
    """
    Popola database con configurazione STANDARD
    - DLMF funzioni speciali (~500 formule)
    - Wikipedia calcolo base (~200 formule)
    
    Totale: ~700 formule
    Tempo: ~5-10 minuti
    """
    
    print_banner("📚 POPOLAMENTO AUTOMATICO DATABASE FORMULE")
    print("Configurazione: STANDARD PACK")
    print("Tempo stimato: 5-10 minuti")
    print("Formule attese: ~700")
    
    # 1. Crea database
    print("\n[1/4] Creazione database...")
    db = FormulaDatabase("formulas.db")
    print("✅ Database creato: formulas.db")
    
    # 2. Import DLMF
    print_banner("📥 FASE 1: IMPORT DLMF")
    print("Scaricamento da https://dlmf.nist.gov/")
    print("(Prima esecuzione: scarica da web, poi usa cache)\n")
    
    dlmf = DLMFImporter(cache_dir="dlmf_cache")
    
    # Capitoli funzioni speciali
    chapters_to_import = {
        '5': 'Gamma Function',
        '6': 'Exponential & Logarithmic',
        '7': 'Error Functions',
        '10': 'Bessel Functions',
        '15': 'Hypergeometric Functions',
        '25': 'Zeta Function'
    }
    
    dlmf_total = 0
    for chapter, name in chapters_to_import.items():
        print(f"[2/{len(chapters_to_import)+3}] Importando Capitolo {chapter}: {name}...")
        try:
            formulas = dlmf.import_chapter(chapter)
            count = dlmf.import_to_database(formulas, db)
            dlmf_total += count
            print(f"    ✅ {count} formule importate")
        except Exception as e:
            print(f"    ⚠️ Errore: {e}")
            print(f"    ↪ Continuo con prossimo capitolo...")
    
    print(f"\n✅ DLMF completato: {dlmf_total} formule importate")
    
    # 3. Import Wikipedia
    print_banner("📥 FASE 2: IMPORT WIKIPEDIA")
    print("Scaricamento da https://en.wikipedia.org/\n")
    
    wiki = WikipediaFormulaImporter()
    
    wiki_pages = {
        'calculus': 'Tabelle Integrali',
        'trig': 'Identità Trigonometriche',
        'series': 'Serie Matematiche',
        'derivatives': 'Tabelle Derivate'
    }
    
    wiki_total = 0
    for page_key, page_name in wiki_pages.items():
        print(f"[3/4] Importando {page_name}...")
        try:
            formulas = wiki.import_from_page(page_key)
            count = 0
            for formula in formulas:
                if db.add_formula(**formula, verified=False):
                    count += 1
            wiki_total += count
            print(f"    ✅ {count} formule importate")
        except Exception as e:
            print(f"    ⚠️ Errore: {e}")
            print(f"    ↪ Continuo con prossima pagina...")
    
    print(f"\n✅ Wikipedia completato: {wiki_total} formule importate")
    
    # 4. Statistiche finali
    print_banner("📊 STATISTICHE FINALI")
    
    stats = db.get_statistics()
    
    print(f"Totale formule nel database: {stats['total_formulas']}")
    print(f"Formule verificate: {stats['verified_formulas']}")
    print(f"Formule da verificare: {stats['total_formulas'] - stats['verified_formulas']}")
    
    print("\n📈 Distribuzione per categoria:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        percentage = count / stats['total_formulas'] * 100
        bar = '█' * int(percentage / 2)
        print(f"  {cat:20s} {count:4d} ({percentage:5.1f}%) {bar}")
    
    print("\n📊 Distribuzione per difficoltà:")
    for diff in range(1, 6):
        count = stats['by_difficulty'].get(diff, 0)
        if count > 0:
            percentage = count / stats['total_formulas'] * 100
            stars = '⭐' * diff
            print(f"  Livello {diff} {stars:10s} {count:4d} ({percentage:5.1f}%)")
    
    print_banner("✅ POPOLAMENTO COMPLETATO")
    
    print("Database pronto: formulas.db")
    print(f"Totale formule: {stats['total_formulas']}")
    print("\nProssimi passi:")
    print("  1. Apri GUI: cd gui && python formula_manager_gui.py")
    print("  2. Oppure usa da Python: from core.formula_database import FormulaDatabase")
    print("\nBuon lavoro! 🎓\n")
    
    db.close()


def populate_database_minimal():
    """
    Popola database con configurazione MINIMAL (veloce)
    - Solo capitoli DLMF essenziali (~200 formule)
    
    Tempo: ~2 minuti
    """
    
    print_banner("📚 POPOLAMENTO RAPIDO DATABASE FORMULE")
    print("Configurazione: MINIMAL PACK (veloce)")
    print("Tempo stimato: 2 minuti")
    print("Formule attese: ~200")
    
    db = FormulaDatabase("formulas.db")
    dlmf = DLMFImporter(cache_dir="dlmf_cache")
    
    # Solo i 3 capitoli più utili
    chapters = ['5', '6', '10']  # Gamma, Exp/Log, Bessel
    
    print("\nImportando capitoli essenziali...")
    formulas = dlmf.import_chapters(chapters)
    count = dlmf.import_to_database(formulas, db)
    
    print(f"\n✅ Database pronto con {count} formule")
    
    db.close()


def populate_database_full():
    """
    Popola database con configurazione FULL
    - Tutti i 36 capitoli DLMF (~3000 formule)
    - Tutte le pagine Wikipedia
    
    Tempo: ~30-60 minuti
    """
    
    print_banner("📚 POPOLAMENTO COMPLETO DATABASE FORMULE")
    print("Configurazione: FULL PACK (massima copertura)")
    print("⚠️ ATTENZIONE: Operazione lunga (~30-60 minuti)")
    print("Formule attese: ~3000+")
    
    confirm = input("\nVuoi continuare? (sì/no): ")
    if confirm.lower() not in ['sì', 'si', 's', 'yes', 'y']:
        print("Operazione annullata.")
        return
    
    db = FormulaDatabase("formulas.db")
    dlmf = DLMFImporter(cache_dir="dlmf_cache")
    wiki = WikipediaFormulaImporter()
    
    # Tutti i capitoli DLMF
    print("\n[1/2] Importando TUTTI i capitoli DLMF (36 capitoli)...")
    all_chapters = [str(i) for i in range(1, 37)]
    
    total = 0
    for i, chapter in enumerate(all_chapters, 1):
        print(f"  [{i}/36] Capitolo {chapter}...", end=' ')
        try:
            formulas = dlmf.import_chapter(chapter)
            count = dlmf.import_to_database(formulas, db)
            total += count
            print(f"✅ {count} formule")
        except Exception as e:
            print(f"⚠️ Errore")
    
    print(f"\n✅ DLMF completato: {total} formule")
    
    # Wikipedia
    print("\n[2/2] Importando Wikipedia...")
    wiki_pages = ['calculus', 'trig', 'series', 'derivatives']
    wiki_total = 0
    
    for page in wiki_pages:
        try:
            formulas = wiki.import_from_page(page)
            for formula in formulas:
                if db.add_formula(**formula, verified=False):
                    wiki_total += 1
        except:
            pass
    
    print(f"✅ Wikipedia completato: {wiki_total} formule")
    
    stats = db.get_statistics()
    print(f"\n✅ DATABASE COMPLETO: {stats['total_formulas']} formule totali")
    
    db.close()


def main():
    """Entry point"""
    
    print("\n" + "🎯" * 35)
    print("  SCRIPT POPOLAMENTO DATABASE FORMULE MATEMATICHE")
    print("🎯" * 35)
    
    print("\nSeleziona configurazione:")
    print("  [1] MINIMAL   - Veloce (~200 formule, 2 min)")
    print("  [2] STANDARD  - Bilanciato (~700 formule, 5-10 min) [RACCOMANDATO]")
    print("  [3] FULL      - Completo (~3000 formule, 30-60 min)")
    print("  [0] Esci")
    
    choice = input("\nScelta [1/2/3/0]: ").strip()
    
    if choice == '1':
        populate_database_minimal()
    elif choice == '2':
        populate_database_standard()
    elif choice == '3':
        populate_database_full()
    elif choice == '0':
        print("Uscita.")
    else:
        print("Scelta non valida.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrotto dall'utente.")
        print("Nota: Formule già importate sono salvate nel database.\n")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        print("Controlla che tutte le dipendenze siano installate:")
        print("  pip install -r requirements.txt\n")
