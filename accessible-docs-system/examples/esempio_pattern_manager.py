"""
Script di esempio per gestire i pattern di etichette delle immagini
"""

from modules.jump_manager.image_pattern_manager import ImagePatternManager


def esempio_base():
    """Esempio base di utilizzo"""
    print("\n" + "="*80)
    print("ESEMPIO BASE - Visualizzazione e gestione pattern")
    print("="*80)
    
    # Crea il gestore
    manager = ImagePatternManager()
    
    # Mostra tutti i pattern
    manager.list_patterns()
    
    # Mostra statistiche
    stats = manager.get_label_statistics()
    print(f"\nStatistiche globali:")
    print(f"  Totale etichette trovate: {stats['total_labels']}")
    print(f"  Pattern più usati: {stats['pattern_usage']}")
    if stats['duplicates']:
        print(f"  Duplicati trovati: {len(stats['duplicates'])}")


def esempio_aggiungi_pattern():
    """Esempio: aggiungere nuovi pattern personalizzati"""
    print("\n" + "="*80)
    print("ESEMPIO - Aggiunta di nuovi pattern")
    print("="*80)
    
    manager = ImagePatternManager()
    
    # Aggiungi pattern per "Esempio"
    manager.add_pattern(
        pattern_name="esempio_custom",
        regex_pattern=r'Esempio\.?\s*(\d+\.?\d*[a-z]?)',
        priority=65,
        description="Riconoscimento di esempi numerati",
        case_sensitive=False
    )
    
    # Aggiungi pattern per "Didascalia"
    manager.add_pattern(
        pattern_name="didascalia_custom",
        regex_pattern=r'Didascalia\.?\s*(\d+\.?\d*[a-z]?)',
        priority=60,
        description="Riconoscimento di didascalie numerate"
    )
    
    # Aggiungi pattern per formati alternativi
    manager.add_pattern(
        pattern_name="illustrazione",
        regex_pattern=r'Illustrazione\.?\s*(\d+\.?\d*[a-z]?)',
        priority=55,
        description="Illustrazioni numerate"
    )
    
    # Pattern per formati con lettere (Es: "Fig 2a", "Esempio 3b")
    manager.add_pattern(
        pattern_name="figura_lettere",
        regex_pattern=r'Fig\.?\s*(\d+[a-z])',
        priority=105,  # Alta priorità per formati specifici
        description="Figure con lettere (Fig 2a, Fig 3b)"
    )
    
    print("\n✓ Pattern aggiunti con successo!")
    manager.list_patterns()


def esempio_modifica_pattern():
    """Esempio: modificare pattern esistenti"""
    print("\n" + "="*80)
    print("ESEMPIO - Modifica di pattern esistenti")
    print("="*80)
    
    manager = ImagePatternManager()
    
    # Disabilita un pattern
    manager.update_pattern("grafico", enabled=False)
    print("✓ Pattern 'grafico' disabilitato")
    
    # Cambia la priorità di un pattern
    manager.update_pattern("esempio", priority=120)
    print("✓ Priorità di 'esempio' aumentata a 120")
    
    # Aggiorna il regex di un pattern
    manager.update_pattern(
        "figura",
        regex_pattern=r'Fig\.?\s*(\d+\.?\d*[a-z]?)',
        description="Figura standard aggiornata"
    )
    print("✓ Pattern 'figura' aggiornato")
    
    manager.list_patterns()


def esempio_rimuovi_pattern():
    """Esempio: rimuovere pattern"""
    print("\n" + "="*80)
    print("ESEMPIO - Rimozione di pattern")
    print("="*80)
    
    manager = ImagePatternManager()
    
    # Rimuovi un pattern custom
    manager.remove_pattern("didascalia_custom")
    print("✓ Pattern rimosso")
    
    manager.list_patterns()


def esempio_trova_etichette():
    """Esempio: trovare etichette nel testo"""
    print("\n" + "="*80)
    print("ESEMPIO - Ricerca di etichette nel testo")
    print("="*80)
    
    manager = ImagePatternManager()
    
    testi_esempio = [
        "Come mostrato in Figura 2.1, il risultato è evidente.",
        "Vedi Fig. 3a per maggiori dettagli.",
        "Esempio 5: applicazione pratica del teorema.",
        "La Didascalia 12 illustra il processo.",
        "Grafico 7: andamento nel tempo.",
        "Riferimento alla Tabella 4.2 in appendice.",
        "Nella Immagine 9 possiamo vedere...",
        "Schema 6b rappresenta la struttura.",
    ]
    
    print("\nTest di riconoscimento su vari testi:\n")
    
    for testo in testi_esempio:
        risultato = manager.find_label_in_text(testo)
        if risultato:
            label, pattern_name = risultato
            print(f"✓ '{testo}'")
            print(f"  → Trovata: '{label}' (pattern: {pattern_name})\n")
        else:
            print(f"✗ '{testo}'")
            print(f"  → Nessuna etichetta trovata\n")


def esempio_gestione_duplicati():
    """Esempio: gestione dei duplicati"""
    print("\n" + "="*80)
    print("ESEMPIO - Gestione duplicati")
    print("="*80)
    
    manager = ImagePatternManager()
    
    # Pulisci eventuali tracce precedenti
    manager.clear_document_labels("documento_test.docx")
    
    # Simula il ritrovamento della stessa etichetta più volte
    print("\nSimulazione di etichette duplicate:")
    
    # Mock di un documento (in un caso reale useresti python-docx)
    class MockDoc:
        def __init__(self, texts):
            self.paragraphs = [type('obj', (object,), {'text': t}) for t in texts]
    
    doc = MockDoc([
        "Testo introduttivo",
        "Come si vede in Figura 1, il risultato...",
        "[IMMAGINE 1]",
        "Continuando con Figura 2...",
        "[IMMAGINE 2]",
        "La Figura 1 mostra anche...",  # Duplicato!
        "[IMMAGINE 1 BIS]",
        "Infine Figura 3...",
        "[IMMAGINE 3]",
    ])
    
    # Trova le etichette
    etichette_trovate = []
    for i, para in enumerate(doc.paragraphs):
        if "[IMMAGINE" in para.text:
            label, occurrence = manager.find_label_with_duplicates(
                doc, i, search_range=2, document_path="documento_test.docx"
            )
            etichette_trovate.append((i, label, occurrence))
            print(f"Paragrafo {i}: '{label}' (occorrenza #{occurrence})")
    
    # Mostra statistiche
    print("\nStatistiche del documento:")
    stats = manager.get_label_statistics("documento_test.docx")
    print(f"  Totale etichette: {stats['total_labels']}")
    print(f"  Pattern usati: {stats['pattern_usage']}")
    print(f"  Duplicati: {stats['duplicates']}")


def esempio_import_pattern_custom():
    """Esempio: importare pattern da una lista personalizzata"""
    print("\n" + "="*80)
    print("ESEMPIO - Import pattern da configurazione personalizzata")
    print("="*80)
    
    manager = ImagePatternManager()
    
    # Pattern personalizzati per un progetto specifico
    pattern_custom = [
        ("foto", r'Foto\.?\s*(\d+\.?\d*[a-z]?)', 70, "Fotografie numerate"),
        ("screenshot", r'Screenshot\.?\s*(\d+\.?\d*[a-z]?)', 65, "Screenshot numerati"),
        ("box", r'Box\.?\s*(\d+\.?\d*[a-z]?)', 60, "Box di approfondimento"),
        ("nota_figura", r'Nota\s+(?:alla\s+)?Figura\.?\s*(\d+\.?\d*[a-z]?)', 55, "Note alle figure"),
    ]
    
    print("Importazione pattern personalizzati:")
    for name, regex, priority, desc in pattern_custom:
        if manager.add_pattern(name, regex, priority, desc):
            print(f"  ✓ Aggiunto: {name}")
        else:
            print(f"  ⚠ Saltato: {name} (già esistente)")
    
    manager.list_patterns()


def menu_interattivo():
    """Menu interattivo per gestire i pattern"""
    print("\n" + "="*80)
    print("MENU INTERATTIVO - Gestione Pattern Immagini")
    print("="*80)
    
    manager = ImagePatternManager()
    
    while True:
        print("\n" + "-"*80)
        print("Scegli un'opzione:")
        print("  1. Visualizza tutti i pattern")
        print("  2. Aggiungi nuovo pattern")
        print("  3. Rimuovi pattern")
        print("  4. Abilita/disabilita pattern")
        print("  5. Modifica priorità pattern")
        print("  6. Test riconoscimento su testo")
        print("  7. Visualizza statistiche")
        print("  0. Esci")
        print("-"*80)
        
        scelta = input("\nScelta: ").strip()
        
        if scelta == "0":
            print("Arrivederci!")
            break
            
        elif scelta == "1":
            manager.list_patterns()
            
        elif scelta == "2":
            print("\nAggiungi nuovo pattern:")
            name = input("  Nome pattern: ").strip()
            regex = input("  Espressione regolare: ").strip()
            priority = input("  Priorità (default 50): ").strip()
            priority = int(priority) if priority else 50
            desc = input("  Descrizione: ").strip()
            
            manager.add_pattern(name, regex, priority, desc)
            
        elif scelta == "3":
            manager.list_patterns()
            name = input("\nNome pattern da rimuovere: ").strip()
            manager.remove_pattern(name)
            
        elif scelta == "4":
            manager.list_patterns()
            name = input("\nNome pattern: ").strip()
            stato = input("Abilita (1) o disabilita (0): ").strip()
            if stato in ['0', '1']:
                manager.update_pattern(name, enabled=bool(int(stato)))
            
        elif scelta == "5":
            manager.list_patterns()
            name = input("\nNome pattern: ").strip()
            priority = input("Nuova priorità: ").strip()
            if priority.isdigit():
                manager.update_pattern(name, priority=int(priority))
            
        elif scelta == "6":
            testo = input("\nInserisci il testo da testare: ").strip()
            risultato = manager.find_label_in_text(testo)
            if risultato:
                label, pattern_name = risultato
                print(f"\n✓ Etichetta trovata: '{label}'")
                print(f"  Pattern usato: {pattern_name}")
            else:
                print("\n✗ Nessuna etichetta trovata")
        
        elif scelta == "7":
            stats = manager.get_label_statistics()
            print(f"\nStatistiche globali:")
            print(f"  Totale etichette: {stats['total_labels']}")
            print(f"  Pattern usati:")
            for pattern, count in stats['pattern_usage'].items():
                print(f"    - {pattern}: {count}")
            if stats['duplicates']:
                print(f"\n  Duplicati trovati: {len(stats['duplicates'])}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "list":
            manager = ImagePatternManager()
            manager.list_patterns()
        
        elif comando == "add" and len(sys.argv) >= 4:
            manager = ImagePatternManager()
            name = sys.argv[2]
            regex = sys.argv[3]
            priority = int(sys.argv[4]) if len(sys.argv) > 4 else 50
            desc = sys.argv[5] if len(sys.argv) > 5 else ""
            manager.add_pattern(name, regex, priority, desc)
        
        elif comando == "remove" and len(sys.argv) >= 3:
            manager = ImagePatternManager()
            manager.remove_pattern(sys.argv[2])
        
        elif comando == "stats":
            manager = ImagePatternManager()
            stats = manager.get_label_statistics()
            print(f"Totale etichette: {stats['total_labels']}")
            print(f"Pattern usati: {stats['pattern_usage']}")
        
        elif comando == "interactive":
            menu_interattivo()
        
        else:
            print("Uso: python esempio_pattern_manager.py [comando] [argomenti]")
            print("Comandi disponibili:")
            print("  list - Mostra tutti i pattern")
            print("  add <nome> <regex> [priorità] [descrizione] - Aggiungi pattern")
            print("  remove <nome> - Rimuovi pattern")
            print("  stats - Mostra statistiche")
            print("  interactive - Menu interattivo")
    
    else:
        # Esegui tutti gli esempi
        print("\n" + "="*80)
        print("ESEMPI DI UTILIZZO DEL PATTERN MANAGER")
        print("="*80)
        
        esempio_base()
        input("\nPremi INVIO per continuare...")
        
        esempio_aggiungi_pattern()
        input("\nPremi INVIO per continuare...")
        
        esempio_trova_etichette()
        input("\nPremi INVIO per continuare...")
        
        esempio_gestione_duplicati()
        input("\nPremi INVIO per continuare...")
        
        # Menu interattivo opzionale
        scelta = input("\nVuoi aprire il menu interattivo? (s/n): ").strip().lower()
        if scelta == 's':
            menu_interattivo()
