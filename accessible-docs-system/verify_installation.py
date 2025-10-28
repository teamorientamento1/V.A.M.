#!/usr/bin/env python3
"""
Script di diagnosi per verificare l'installazione dei pattern manager
"""

import sys
import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Verifica se un file esiste"""
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"✅ {description}")
        print(f"   → {filepath}")
        print(f"   → Dimensione: {size:,} bytes")
        return True
    else:
        print(f"❌ {description}")
        print(f"   → MANCANTE: {filepath}")
        return False

def check_imports():
    """Verifica che i moduli si possano importare"""
    print("\n" + "="*70)
    print("VERIFICA IMPORT")
    print("="*70 + "\n")
    
    errors = []
    
    # Test 1: Import ImagePatternManager
    try:
        from modules.jump_manager.image_pattern_manager import ImagePatternManager
        print("✅ ImagePatternManager importato correttamente")
    except ImportError as e:
        print(f"❌ Errore import ImagePatternManager:")
        print(f"   → {e}")
        errors.append(str(e))
    except Exception as e:
        print(f"❌ Errore generico ImagePatternManager:")
        print(f"   → {e}")
        errors.append(str(e))
    
    # Test 2: Import PatternManagerDialog
    try:
        from ui.dialogs.pattern_manager_dialog import PatternManagerDialog
        print("✅ PatternManagerDialog importato correttamente")
    except ImportError as e:
        print(f"❌ Errore import PatternManagerDialog:")
        print(f"   → {e}")
        errors.append(str(e))
    except Exception as e:
        print(f"❌ Errore generico PatternManagerDialog:")
        print(f"   → {e}")
        errors.append(str(e))
    
    # Test 3: Import JumpTab aggiornato
    try:
        from ui.tabs.jump_tab import JumpTab
        print("✅ JumpTab importato correttamente")
        
        # Verifica che abbia i nuovi metodi
        if hasattr(JumpTab, 'quick_add_pattern'):
            print("   ✅ Metodo quick_add_pattern trovato")
        else:
            print("   ❌ Metodo quick_add_pattern NON trovato")
            errors.append("JumpTab non ha quick_add_pattern")
        
        if hasattr(JumpTab, 'open_pattern_manager'):
            print("   ✅ Metodo open_pattern_manager trovato")
        else:
            print("   ❌ Metodo open_pattern_manager NON trovato")
            errors.append("JumpTab non ha open_pattern_manager")
            
    except ImportError as e:
        print(f"❌ Errore import JumpTab:")
        print(f"   → {e}")
        errors.append(str(e))
    except Exception as e:
        print(f"❌ Errore generico JumpTab:")
        print(f"   → {e}")
        errors.append(str(e))
    
    return errors

def check_pyqt():
    """Verifica PyQt6"""
    print("\n" + "="*70)
    print("VERIFICA PYQT6")
    print("="*70 + "\n")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 installato correttamente")
        return True
    except ImportError:
        print("❌ PyQt6 NON trovato")
        print("   → Installa con: pip install PyQt6")
        return False

def main():
    print("\n" + "="*70)
    print("DIAGNOSI INSTALLAZIONE PATTERN MANAGER")
    print("="*70 + "\n")
    
    # Verifica directory corrente
    cwd = Path.cwd()
    print(f"Directory corrente: {cwd}\n")
    
    # Cerca la cartella del progetto
    if not (cwd / "modules").exists():
        print("⚠️  Non sei nella directory del progetto!")
        print("   Vai in: vam/accessible-docs-system/")
        print("   E poi esegui: python verify_installation.py")
        return
    
    print("="*70)
    print("VERIFICA FILE")
    print("="*70 + "\n")
    
    files_ok = True
    
    # File 1: image_pattern_manager.py
    file1 = Path("modules/jump_manager/image_pattern_manager.py")
    if not check_file_exists(file1, "File 1: image_pattern_manager.py"):
        files_ok = False
        print("   SOLUZIONE: Scarica e copia in modules/jump_manager/\n")
    print()
    
    # File 2: pattern_manager_dialog.py
    file2 = Path("ui/dialogs/pattern_manager_dialog.py")
    if not check_file_exists(file2, "File 2: pattern_manager_dialog.py"):
        files_ok = False
        print("   SOLUZIONE: Scarica e copia in ui/dialogs/\n")
    print()
    
    # File 3: jump_tab.py
    file3 = Path("ui/tabs/jump_tab.py")
    if not check_file_exists(file3, "File 3: jump_tab.py (aggiornato)"):
        files_ok = False
        print("   SOLUZIONE: Scarica e sostituisci in ui/tabs/\n")
    else:
        # Verifica che contenga le nuove funzioni
        content = file3.read_text(encoding='utf-8')
        if 'quick_add_pattern' in content and 'open_pattern_manager' in content:
            print("   ✅ Contiene le nuove funzioni\n")
        else:
            print("   ⚠️  File vecchio! Non contiene le nuove funzioni")
            print("   SOLUZIONE: Riscarica e sostituisci jump_tab.py\n")
            files_ok = False
    
    # Se i file non ci sono, non ha senso continuare
    if not files_ok:
        print("="*70)
        print("❌ ALCUNI FILE MANCANO O SONO VECCHI")
        print("="*70)
        print("\nScarica i file da outputs/ e mettili nelle posizioni corrette.")
        print("Leggi INSTALLA_QUESTI_FILE.txt per le istruzioni.\n")
        return
    
    # Verifica PyQt6
    if not check_pyqt():
        print("\n❌ PyQt6 mancante - l'applicazione non può partire\n")
        return
    
    # Verifica import
    errors = check_imports()
    
    # Pulisci cache Python
    print("\n" + "="*70)
    print("PULIZIA CACHE PYTHON")
    print("="*70 + "\n")
    
    cache_cleaned = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = Path(root) / '__pycache__'
            try:
                import shutil
                shutil.rmtree(pycache_path)
                cache_cleaned += 1
                print(f"✅ Pulito: {pycache_path}")
            except Exception as e:
                print(f"⚠️  Errore pulizia {pycache_path}: {e}")
    
    if cache_cleaned > 0:
        print(f"\n✅ Pulite {cache_cleaned} directory __pycache__")
    else:
        print("✅ Nessuna cache da pulire")
    
    # RISULTATO FINALE
    print("\n" + "="*70)
    print("RISULTATO DIAGNOSI")
    print("="*70 + "\n")
    
    if not errors and files_ok:
        print("✅ TUTTO OK!")
        print("\n📋 PROSSIMI PASSI:")
        print("1. Chiudi l'applicazione se è aperta")
        print("2. Riavvia l'applicazione")
        print("3. Vai alla scheda Jump")
        print("4. Dovresti vedere i 2 nuovi pulsanti:")
        print("   [➕ Aggiungi Nome]  [⚙️ Gestisci Nomi]")
        print("\n5. Se ancora non li vedi, guarda gli errori nel terminale")
    else:
        print("❌ CI SONO PROBLEMI\n")
        
        if not files_ok:
            print("PROBLEMA: File mancanti o vecchi")
            print("SOLUZIONE:")
            print("  1. Scarica i 3 file da outputs/")
            print("  2. Mettili nelle posizioni corrette")
            print("  3. Riesegui questo script\n")
        
        if errors:
            print("PROBLEMI DI IMPORT:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            print("\nSOLUZIONE:")
            print("  1. Verifica che i file siano nelle posizioni corrette")
            print("  2. Controlla gli errori sopra")
            print("  3. Installa eventuali dipendenze mancanti")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrotto dall'utente\n")
    except Exception as e:
        print(f"\n❌ ERRORE INASPETTATO:\n{e}\n")
        import traceback
        traceback.print_exc()
