#!/usr/bin/env python3
"""
Workflow Completo - Analisi + Jump Manager
Dimostra l'uso integrato di tutte le funzionalità
"""
import sys
import json
from pathlib import Path

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from docx import Document
from core.knowledge_base import KnowledgeBase
from core.document_analyzer import WordAnalyzer
from modules.jump_manager.jump_creator import JumpManager
from modules.symbol_dictionary.symbol_manager import SymbolDictionary

def workflow_completo_documento(doc_path: Path, descriptions_file: Path = None):
    """
    Workflow completo: Analisi → Jump → Esportazione
    
    Args:
        doc_path: Path al documento Word da elaborare
        descriptions_file: Path opzionale a file JSON con descrizioni immagini
    """
    print("\n" + "="*70)
    print("  WORKFLOW COMPLETO - DOCUMENTO ACCESSIBILE")
    print("="*70)
    print(f"\nDocumento: {doc_path.name}")
    
    # ========== FASE 1: ANALISI ==========
    print("\n" + "-"*70)
    print("FASE 1: ANALISI DOCUMENTO")
    print("-"*70)
    
    kb = KnowledgeBase()
    analyzer = WordAnalyzer(kb)
    
    if not analyzer.load_document(doc_path):
        print("✗ Errore caricamento documento")
        return False
    
    print("✓ Documento caricato")
    print("  Analisi in corso...")
    
    analysis = analyzer.analyze(discipline="mathematics")
    
    print("\n📊 RISULTATI ANALISI:")
    stats = analysis['statistics']
    print(f"  • Paragrafi: {stats['total_paragraphs']}")
    print(f"  • Equazioni: {stats['total_equations']}")
    print(f"  • Immagini: {stats['total_images']}")
    print(f"  • Tabelle: {stats['total_tables']}")
    print(f"  • Riferimenti: {stats['total_references']}")
    
    # Dettagli immagini
    if analysis['images']:
        print(f"\n📸 IMMAGINI TROVATE:")
        for img in analysis['images']:
            label = img.get('label', 'Nessun label')
            print(f"  • Immagine {img['index']}: {label}")
            if img.get('caption'):
                print(f"    Caption: {img['caption'][:60]}...")
    
    # Dettagli riferimenti
    if analysis['references']:
        print(f"\n🔗 RIFERIMENTI TROVATI:")
        ref_by_type = {}
        for ref in analysis['references']:
            ref_type = ref['type']
            ref_by_type[ref_type] = ref_by_type.get(ref_type, 0) + 1
        
        for ref_type, count in ref_by_type.items():
            print(f"  • {ref_type}: {count}")
    
    # ========== FASE 2: KNOWLEDGE BASE ==========
    print("\n" + "-"*70)
    print("FASE 2: APPRENDIMENTO KNOWLEDGE BASE")
    print("-"*70)
    
    patterns_added = analyzer.learn_from_analysis(discipline="mathematics")
    print(f"✓ {patterns_added} pattern aggiunti al Knowledge Base")
    
    kb_stats = kb.get_statistics()
    total_patterns = sum(kb_stats['patterns_by_discipline'].values())
    print(f"  Knowledge Base ora contiene: {total_patterns} pattern totali")
    
    # ========== FASE 3: GESTIONE DESCRIZIONI ==========
    print("\n" + "-"*70)
    print("FASE 3: PREPARAZIONE DESCRIZIONI IMMAGINI")
    print("-"*70)
    
    descriptions = {}
    
    if descriptions_file and descriptions_file.exists():
        # Carica da file JSON
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            descriptions = json.load(f)
        print(f"✓ {len(descriptions)} descrizioni caricate da {descriptions_file.name}")
    else:
        # Crea descrizioni placeholder
        print("ℹ File descrizioni non fornito, creo placeholder...")
        for img in analysis['images']:
            label = img.get('label', f"Img_{img['index']}")
            descriptions[label] = f"[Inserire qui la descrizione dettagliata per {label}]"
        
        # Salva template
        desc_template_path = doc_path.parent / f"{doc_path.stem}_descriptions.json"
        with open(desc_template_path, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, indent=2, ensure_ascii=False)
        print(f"✓ Template descrizioni salvato: {desc_template_path.name}")
        print(f"  → Modifica questo file e riesegui lo script")
    
    # ========== FASE 4: CREAZIONE JUMP ==========
    print("\n" + "-"*70)
    print("FASE 4: CREAZIONE COLLEGAMENTI IPERTESTUALI")
    print("-"*70)
    
    # Ricarica documento per modificarlo
    doc = Document(str(doc_path))
    jump_mgr = JumpManager(doc)
    
    # 4a. Crea sezione descrizioni
    print("\n  4a. Creazione sezione descrizioni...")
    jump_mgr.create_descriptions_section()
    print("  ✓ Sezione descrizioni creata")
    
    # 4b. Aggiungi descrizioni
    print("\n  4b. Aggiunta descrizioni immagini...")
    for img in analysis['images']:
        label = img.get('label')
        if label and label in descriptions:
            jump_mgr.add_description_with_return(
                label=label,
                description=descriptions[label],
                source_paragraph_index=img.get('paragraph_index', 0)
            )
    print(f"  ✓ {len([i for i in analysis['images'] if i.get('label')])} descrizioni aggiunte")
    
    # 4c. Crea jump immagini → descrizioni
    print("\n  4c. Creazione jump immagini...")
    jumps_img = jump_mgr.create_image_jumps(
        images=analysis['images'],
        descriptions=descriptions
    )
    print(f"  ✓ {jumps_img} jump immagini creati")
    
    # 4d. Converti riferimenti in link
    print("\n  4d. Conversione riferimenti in link...")
    jumps_ref = jump_mgr.scan_and_create_reference_jumps(
        references=analysis['references']
    )
    print(f"  ✓ {jumps_ref} riferimenti convertiti in jump")
    
    # 4e. Validazione
    print("\n  4e. Validazione jump...")
    validation = jump_mgr.validate_jumps()
    print(f"  ✓ Jump validati: {validation['total_jumps']} totali")
    
    # ========== FASE 5: GESTIONE SIMBOLI ==========
    print("\n" + "-"*70)
    print("FASE 5: GESTIONE SIMBOLI E PRONUNCIA")
    print("-"*70)
    
    symbol_dict = SymbolDictionary(kb)
    
    # Scansiona simboli
    symbols = symbol_dict.scan_document_symbols(analysis)
    print(f"✓ {len(symbols)} simboli unici trovati")
    
    if symbols:
        print("\n  Simboli più comuni:")
        sorted_symbols = sorted(symbols.items(), key=lambda x: x[1]['count'], reverse=True)
        for symbol, data in sorted_symbols[:10]:
            print(f"    • {symbol} → '{data['current_pronunciation']}' ({data['count']}x)")
        
        # Salva mapping TTS
        tts_file = doc_path.parent / f"{doc_path.stem}_tts_mapping.txt"
        symbol_dict.create_tts_mapping_file(list(symbols.keys()), tts_file)
        print(f"\n✓ Mapping TTS salvato: {tts_file.name}")
    
    # ========== FASE 6: ESPORTAZIONE ==========
    print("\n" + "-"*70)
    print("FASE 6: ESPORTAZIONE DOCUMENTO ACCESSIBILE")
    print("-"*70)
    
    output_path = doc_path.parent / f"{doc_path.stem}_accessibile.docx"
    doc.save(str(output_path))
    print(f"✓ Documento accessibile salvato: {output_path.name}")
    
    # Report finale
    report_path = doc_path.parent / f"{doc_path.stem}_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analyzer.generate_report())
        f.write("\n\n" + "="*70 + "\n")
        f.write("JUMP CREATI\n")
        f.write("="*70 + "\n")
        summary = jump_mgr.get_jumps_summary()
        f.write(f"Totale jump: {summary['total']}\n")
        f.write(f"Per tipo:\n")
        for jtype, count in summary['by_type'].items():
            f.write(f"  - {jtype}: {count}\n")
    
    print(f"✓ Report salvato: {report_path.name}")
    
    # Export mappa jump
    jump_map_path = doc_path.parent / f"{doc_path.stem}_jump_map.json"
    jump_mgr.export_jump_map(str(jump_map_path))
    
    # ========== COMPLETAMENTO ==========
    print("\n" + "="*70)
    print("  ✅ WORKFLOW COMPLETATO CON SUCCESSO!")
    print("="*70)
    
    print(f"\n📦 FILE GENERATI:")
    print(f"  • {output_path.name} - Documento accessibile")
    print(f"  • {report_path.name} - Report analisi")
    print(f"  • {jump_map_path.name} - Mappa jump")
    if not descriptions_file:
        print(f"  • {desc_template_path.name} - Template descrizioni")
    if symbols:
        print(f"  • {tts_file.name} - Mapping TTS simboli")
    
    print(f"\n💡 PROSSIMI PASSI:")
    if not descriptions_file:
        print(f"  1. Modifica {desc_template_path.name} con descrizioni reali")
        print(f"  2. Riesegui: python examples/workflow_completo.py {doc_path} {desc_template_path}")
    else:
        print(f"  1. Apri {output_path.name} in Microsoft Word")
        print(f"  2. Verifica i collegamenti ipertestuali")
        print(f"  3. Testa con screen reader se disponibile")
    
    kb.close()
    return True

def main():
    """Entry point"""
    print("\n" + "█"*70)
    print("  ACCESSIBLE DOCS SYSTEM - WORKFLOW COMPLETO")
    print("█"*70)
    
    # Controlla argomenti
    if len(sys.argv) < 2:
        print("\nUSO:")
        print(f"  python {Path(__file__).name} <documento.docx> [descrizioni.json]")
        print("\nESEMPI:")
        print(f"  python {Path(__file__).name} tesi.docx")
        print(f"  python {Path(__file__).name} tesi.docx tesi_descriptions.json")
        print("\nCERCA DOCUMENTI NELLA DIRECTORY CORRENTE...")
        
        # Cerca .docx
        docs = [f for f in Path.cwd().glob("*.docx") if not f.name.startswith("~$") and "test" not in f.name.lower()]
        
        if docs:
            print(f"\nDocumenti trovati ({len(docs)}):")
            for i, doc in enumerate(docs[:10], 1):
                print(f"  {i}. {doc.name}")
            
            print(f"\nUtilizzo primo documento: {docs[0].name}")
            doc_path = docs[0]
            descriptions_file = None
        else:
            print("\n⚠ Nessun documento trovato!")
            print("  Posiziona un file .docx nella stessa cartella dello script")
            return False
    else:
        doc_path = Path(sys.argv[1])
        descriptions_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        
        if not doc_path.exists():
            print(f"\n✗ File non trovato: {doc_path}")
            return False
    
    # Esegui workflow
    try:
        success = workflow_completo_documento(doc_path, descriptions_file)
        return success
    except Exception as e:
        print(f"\n✗ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
