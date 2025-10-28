#!/usr/bin/env python3
"""
Script di migrazione per aggiornare i pattern regex nel database patterns.db
Questo script aggiorna i pattern esistenti per supportare la numerazione multi-livello (es: 5.2.2)
"""

import sqlite3
from pathlib import Path

def update_patterns():
    """Aggiorna i pattern nel database per supportare numeri multi-livello"""
    
    # Trova il database patterns.db
    script_dir = Path(__file__).parent
    db_path = script_dir / "data" / "patterns.db"
    
    if not db_path.exists():
        print(f"❌ Database non trovato: {db_path}")
        print("   Il database verrà creato automaticamente con i nuovi pattern al primo avvio.")
        return
    
    print(f"📂 Trovato database: {db_path}")
    print("🔄 Aggiornamento pattern in corso...\n")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Pattern aggiornati per supportare numerazione multi-livello
    # (\d+(?:\.\d+)*[a-z]?) cattura: 5, 5.2, 5.2.2, 5.2.2.1, 11a, etc.
    updates = [
        ("figura", r'Fig\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Figura standard (Fig, Fig.) - supporta multi-livello"),
        ("figura_estesa", r'Figura\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Figura scritta per esteso - supporta multi-livello"),
        ("figure_en", r'Figure\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Figure in inglese - supporta multi-livello"),
        ("immagine", r'Immagine\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Immagine - supporta multi-livello"),
        ("grafico", r'Grafico\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Grafico - supporta multi-livello"),
        ("tabella", r'Tab\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Tabella abbreviata - supporta multi-livello"),
        ("tabella_estesa", r'Tabella\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Tabella per esteso - supporta multi-livello"),
        ("esempio", r'Esempio\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Esempio - supporta multi-livello (es: 5.2.2)"),
        ("didascalia", r'Didascalia\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Didascalia - supporta multi-livello"),
        ("schema", r'Schema\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Schema - supporta multi-livello"),
        ("diagramma", r'Diagramma\.?\s*(\d+(?:\.\d+)*[a-z]?)', "Diagramma - supporta multi-livello"),
    ]
    
    updated = 0
    added = 0
    
    for pattern_name, regex_pattern, description in updates:
        # Verifica se il pattern esiste
        cursor.execute(
            "SELECT id, regex_pattern FROM image_label_patterns WHERE pattern_name = ?",
            (pattern_name,)
        )
        result = cursor.fetchone()
        
        if result:
            # Pattern esistente - aggiorna
            old_regex = result[1]
            if old_regex != regex_pattern:
                cursor.execute("""
                    UPDATE image_label_patterns 
                    SET regex_pattern = ?, description = ?
                    WHERE pattern_name = ?
                """, (regex_pattern, description, pattern_name))
                print(f"  ✓ Aggiornato '{pattern_name}':")
                print(f"    Vecchio: {old_regex}")
                print(f"    Nuovo:   {regex_pattern}\n")
                updated += 1
            else:
                print(f"  ⏭  Saltato '{pattern_name}' (già aggiornato)")
        else:
            # Pattern non esistente - aggiungi
            cursor.execute("""
                INSERT INTO image_label_patterns 
                (pattern_name, regex_pattern, priority, description)
                VALUES (?, ?, ?, ?)
            """, (pattern_name, regex_pattern, 65, description))
            print(f"  ➕ Aggiunto nuovo pattern '{pattern_name}'\n")
            added += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print(f"✅ MIGRAZIONE COMPLETATA!")
    print(f"   Pattern aggiornati: {updated}")
    print(f"   Pattern aggiunti: {added}")
    print("="*70)
    print("\n💡 I nuovi pattern supportano ora numeri multi-livello come:")
    print("   • Esempio 5.2.2")
    print("   • Fig. 11.3.4.1")
    print("   • Schema 2.5a")
    print("\n🔄 Ricarica il documento nel programma per applicare le modifiche.")


if __name__ == "__main__":
    print("="*70)
    print("MIGRAZIONE DATABASE PATTERN - Supporto Multi-Livello")
    print("="*70)
    print()
    
    try:
        update_patterns()
    except Exception as e:
        print(f"\n❌ ERRORE durante la migrazione:")
        print(f"   {str(e)}")
        print("\n💡 Se hai problemi, puoi eliminare il file data/patterns.db")
        print("   e verrà ricreato automaticamente con i nuovi pattern.")
