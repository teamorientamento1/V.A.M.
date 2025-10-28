"""
Sistema di tracking per jump creati
Tiene traccia di quali jump sono stati creati per prevenire sovrascritture accidentali
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class JumpTracker:
    """Gestisce il tracking dei jump creati nel documento"""
    
    def __init__(self, document_path: Optional[str] = None):
        """
        Args:
            document_path: Path del documento Word corrente
        """
        self.document_path = document_path
        self.jumps = {}  # {element_label: jump_info}
        self.tracking_file = None
        
        if document_path:
            self.load_tracking_file()
    
    def set_document(self, document_path: str):
        """Imposta il documento corrente e carica il tracking"""
        self.document_path = document_path
        self.load_tracking_file()
    
    def get_tracking_file_path(self) -> Optional[Path]:
        """Ottiene il path del file di tracking per il documento corrente"""
        if not self.document_path:
            return None
        
        doc_path = Path(self.document_path)
        # Salva il tracking nella stessa cartella del documento
        # con nome: .documento_jump_tracking.json
        tracking_path = doc_path.parent / f".{doc_path.stem}_jump_tracking.json"
        return tracking_path
    
    def load_tracking_file(self):
        """Carica il file di tracking se esiste"""
        self.jumps = {}
        tracking_path = self.get_tracking_file_path()
        
        if tracking_path and tracking_path.exists():
            try:
                with open(tracking_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.jumps = data.get('jumps', {})
            except Exception as e:
                print(f"Errore caricamento tracking: {e}")
                self.jumps = {}
    
    def save_tracking_file(self):
        """Salva il file di tracking"""
        tracking_path = self.get_tracking_file_path()
        
        if not tracking_path:
            return False
        
        try:
            data = {
                'document': str(self.document_path),
                'last_updated': datetime.now().isoformat(),
                'jumps': self.jumps
            }
            
            with open(tracking_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Errore salvataggio tracking: {e}")
            return False
    
    def add_jump(self, element_label: str, description: str, 
                 references_count: int, element_type: str = 'image'):
        """
        Registra un jump creato
        
        Args:
            element_label: Etichetta dell'elemento (es. "Fig. 2.5")
            description: Descrizione assegnata
            references_count: Numero di riferimenti creati
            element_type: Tipo elemento (image, table, equation)
        """
        self.jumps[element_label] = {
            'description': description,
            'description_preview': description[:100] + '...' if len(description) > 100 else description,
            'references_count': references_count,
            'element_type': element_type,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        self.save_tracking_file()
    
    def update_jump(self, element_label: str, description: str, references_count: int):
        """Aggiorna un jump esistente"""
        if element_label in self.jumps:
            self.jumps[element_label]['description'] = description
            self.jumps[element_label]['description_preview'] = description[:100] + '...' if len(description) > 100 else description
            self.jumps[element_label]['references_count'] = references_count
            self.jumps[element_label]['last_modified'] = datetime.now().isoformat()
            
            self.save_tracking_file()
            return True
        return False
    
    def has_jump(self, element_label: str) -> bool:
        """Verifica se esiste un jump per questa etichetta"""
        return element_label in self.jumps
    
    def get_jump_info(self, element_label: str) -> Optional[Dict]:
        """Ottiene le informazioni su un jump esistente"""
        return self.jumps.get(element_label)
    
    def delete_jump(self, element_label: str) -> bool:
        """Elimina un jump dal tracking"""
        if element_label in self.jumps:
            del self.jumps[element_label]
            self.save_tracking_file()
            return True
        return False
    
    def get_all_jumps(self) -> List[Dict]:
        """
        Ottiene lista di tutti i jump creati
        
        Returns:
            Lista di dict con label e info
        """
        result = []
        for label, info in self.jumps.items():
            result.append({
                'label': label,
                **info
            })
        
        # Ordina per data di creazione (più recenti prima)
        result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return result
    
    def get_statistics(self) -> Dict:
        """Ottiene statistiche sui jump creati"""
        total = len(self.jumps)
        by_type = {}
        total_references = 0
        
        for info in self.jumps.values():
            elem_type = info.get('element_type', 'unknown')
            by_type[elem_type] = by_type.get(elem_type, 0) + 1
            total_references += info.get('references_count', 0)
        
        return {
            'total_jumps': total,
            'by_type': by_type,
            'total_references': total_references,
            'avg_references_per_jump': round(total_references / total, 2) if total > 0 else 0
        }
    
    def clear_all(self):
        """Cancella tutti i jump (con cautela!)"""
        self.jumps = {}
        self.save_tracking_file()
    
    def export_to_list(self) -> List[str]:
        """Esporta lista semplice di etichette con jump"""
        return sorted(list(self.jumps.keys()))


def test_jump_tracker():
    """Test del sistema di tracking"""
    print("=== TEST JUMP TRACKER ===\n")
    
    # Crea tracker con documento fittizio
    tracker = JumpTracker("test_document.docx")
    
    # Test 1: Aggiungi jump
    print("1. Aggiungi jump:")
    tracker.add_jump("Fig. 2.5", "Grafico che mostra l'andamento...", 3, "image")
    tracker.add_jump("Tab. 1", "Tabella riassuntiva dei dati", 2, "table")
    print(f"   ✓ Jump aggiunti: {len(tracker.jumps)}")
    
    # Test 2: Verifica esistenza
    print("\n2. Verifica esistenza:")
    print(f"   Fig. 2.5 esiste: {tracker.has_jump('Fig. 2.5')}")
    print(f"   Fig. 2.6 esiste: {tracker.has_jump('Fig. 2.6')}")
    
    # Test 3: Ottieni info
    print("\n3. Info jump:")
    info = tracker.get_jump_info("Fig. 2.5")
    if info:
        print(f"   Descrizione: {info['description_preview']}")
        print(f"   Riferimenti: {info['references_count']}")
    
    # Test 4: Update
    print("\n4. Aggiorna jump:")
    tracker.update_jump("Fig. 2.5", "Descrizione aggiornata più dettagliata", 5)
    info = tracker.get_jump_info("Fig. 2.5")
    print(f"   Nuovi riferimenti: {info['references_count']}")
    
    # Test 5: Statistiche
    print("\n5. Statistiche:")
    stats = tracker.get_statistics()
    print(f"   Totale jump: {stats['total_jumps']}")
    print(f"   Per tipo: {stats['by_type']}")
    print(f"   Totale riferimenti: {stats['total_references']}")
    
    # Test 6: Lista tutti
    print("\n6. Lista tutti i jump:")
    all_jumps = tracker.get_all_jumps()
    for jump in all_jumps:
        print(f"   • {jump['label']} - {jump['element_type']} ({jump['references_count']} refs)")
    
    # Cleanup
    tracking_file = tracker.get_tracking_file_path()
    if tracking_file and tracking_file.exists():
        tracking_file.unlink()
    
    print("\n✅ Test completati")


if __name__ == "__main__":
    test_jump_tracker()
