"""
Jump Manager - Gestisce i collegamenti ipertestuali per immagini e riferimenti
"""
from typing import List, Dict, Optional, Tuple
from docx import Document
from docx.shared import RGBColor
from docx.oxml.shared import OxmlElement, qn
import re

from config.settings import *


class JumpManager:
    """
    Crea e gestisce collegamenti ipertestuali (jump points) nel documento:
    - Da immagini alle loro descrizioni
    - Da riferimenti nel testo agli elementi corrispondenti
    - Link di ritorno dalle descrizioni
    """
    
    def __init__(self, document: Document):
        self.document = document
        self.jumps_created = []
        self.descriptions_section_start = None
    
    def create_image_jumps(self, images: List[Dict], 
                          descriptions: Dict[str, str]) -> int:
        """
        Crea jump sopra le immagini verso le descrizioni
        
        Args:
            images: Lista di immagini trovate dall'analyzer
            descriptions: Dict {image_label: description_text}
        
        Returns:
            Numero di jump creati
        """
        jumps_count = 0
        
        print(f"Creazione jump per {len(images)} immagini...")
        
        for img in images:
            # Estrai label immagine (es. "Fig.2.5")
            label = img.get('label')
            if not label:
                # Prova a trovare label nel contesto
                label = self._extract_label_from_context(img)
            
            if not label:
                print(f"  ⚠ Immagine {img.get('index')} senza label, skip")
                continue
            
            # Verifica che esista descrizione
            if label not in descriptions:
                print(f"  ⚠ Nessuna descrizione per {label}")
                continue
            
            # Trova paragrafo dell'immagine
            para_index = img.get('paragraph_index')
            if para_index is None or para_index >= len(self.document.paragraphs):
                print(f"  ⚠ Paragrafo non trovato per {label}")
                continue
            
            image_paragraph = self.document.paragraphs[para_index]
            
            # Crea bookmark nella sezione descrizioni (lo faremo dopo)
            bookmark_name = f"{JUMP_PREFIX}{label.replace('.', '_').replace(' ', '_')}"
            
            # Crea link sopra/sotto l'immagine
            # Inseriamo un paragrafo nuovo prima dell'immagine
            # (in alternativa, si potrebbe mettere dopo)
            
            # Per ora, aggiungiamo il link nel paragrafo stesso
            # In produzione, dovresti inserire un nuovo paragrafo
            link_text = f"[Descrizione {label}]"
            self.create_hyperlink(image_paragraph, link_text, bookmark_name)
            
            # Registra il jump
            self.jumps_created.append({
                'type': 'image_to_description',
                'source_label': label,
                'source_paragraph': para_index,
                'target_bookmark': bookmark_name,
                'description': descriptions[label]
            })
            
            jumps_count += 1
            print(f"  ✓ Jump creato per {label}")
        
        print(f"Totale jump immagini creati: {jumps_count}")
        return jumps_count
    
    def _extract_label_from_context(self, image: Dict) -> Optional[str]:
        """
        Estrae label (Fig.X) dal contesto dell'immagine
        """
        import re
        
        # Cerca nel testo prima/dopo l'immagine
        context = image.get('context_before', '') + image.get('context_after', '')
        
        # Pattern per Figure/Fig
        patterns = [
            r'[Ff]ig(?:ure)?\.?\s*(\d+(?:\.\d+)?)',
            r'[Ff]igura\.?\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                return f"Fig.{match.group(1)}"
        
        return None
    
    def scan_and_create_reference_jumps(self, references: List[Dict]) -> int:
        """
        Scansiona riferimenti nel testo e li converte in jump
        
        Es: "come si vede in Fig.2.5" -> Fig.2.5 diventa cliccabile
        
        Args:
            references: Lista di riferimenti trovati dall'analyzer
        
        Returns:
            Numero di jump creati
        """
        jumps_count = 0
        
        print(f"Conversione {len(references)} riferimenti in jump...")
        
        # Raggruppa riferimenti per paragrafo per efficienza
        refs_by_paragraph = {}
        for ref in references:
            para_idx = ref['paragraph_index']
            if para_idx not in refs_by_paragraph:
                refs_by_paragraph[para_idx] = []
            refs_by_paragraph[para_idx].append(ref)
        
        # Per ogni paragrafo con riferimenti
        for para_idx, refs in refs_by_paragraph.items():
            if para_idx >= len(self.document.paragraphs):
                continue
            
            paragraph = self.document.paragraphs[para_idx]
            original_text = paragraph.text
            
            # Ordina riferimenti per posizione (dal fondo all'inizio per non sfasare indici)
            refs_sorted = sorted(refs, key=lambda r: r['position_in_paragraph'], reverse=True)
            
            for ref in refs_sorted:
                ref_type = ref['type']
                label = ref['label']
                full_match = ref['full_match']
                
                # Crea nome bookmark target
                if ref_type == 'figure':
                    bookmark_name = f"{JUMP_PREFIX}Fig_{label.replace('.', '_')}"
                elif ref_type == 'equation':
                    bookmark_name = f"{JUMP_PREFIX}Eq_{label.replace('.', '_')}"
                elif ref_type == 'table':
                    bookmark_name = f"{JUMP_PREFIX}Tab_{label.replace('.', '_')}"
                else:
                    continue  # Skip altri tipi per ora
                
                # Invece di modificare il testo (complesso), aggiungiamo link alla fine
                # In produzione, dovresti sostituire il testo con hyperlink inline
                # Questo richiede manipolazione più sofisticata del XML
                
                # Per ora, aggiungiamo nota con link
                link_text = f" [→{full_match}]"
                self.create_hyperlink(paragraph, link_text, bookmark_name)
                
                self.jumps_created.append({
                    'type': f'{ref_type}_reference',
                    'source_paragraph': para_idx,
                    'reference_text': full_match,
                    'target_bookmark': bookmark_name
                })
                
                jumps_count += 1
        
        print(f"Totale jump riferimenti creati: {jumps_count}")
        return jumps_count
    
    def create_descriptions_section(self, position: str = 'end') -> None:
        """
        Crea la sezione descrizioni alla fine del documento
        
        Args:
            position: 'end' o paragraph index dove inserire
        """
        if position == 'end':
            # Aggiungi separatore visivo
            self.document.add_page_break()
            
            # Aggiungi separatore testuale
            separator = self.document.add_paragraph()
            separator.add_run('_' * 80)
            
            # Aggiungi heading principale
            heading = self.document.add_heading('DESCRIZIONI IMMAGINI E FIGURE', level=1)
            
            # Aggiungi nota esplicativa
            note = self.document.add_paragraph()
            note.add_run('In questa sezione trovi le descrizioni dettagliate di tutte le immagini e figure. ').italic = True
            note.add_run('Usa i link di ritorno per tornare al testo principale.').italic = True
            
            # Segna l'inizio della sezione
            self.descriptions_section_start = len(self.document.paragraphs) - 1
            
            print("✓ Sezione descrizioni creata")
        else:
            # TODO: Implementare inserimento in posizione specifica
            print("⚠ Inserimento in posizione specifica non ancora implementato")
        
        # Aggiungi spazio
        self.document.add_paragraph()
    
    def add_description_with_return(self, label: str, description: str,
                                   source_paragraph_index: int) -> None:
        """
        Aggiunge una descrizione con link di ritorno
        
        Args:
            label: Etichetta (es. "Fig.2.5")
            description: Testo della descrizione
            source_paragraph_index: Indice paragrafo dove tornare
        """
        from docx.shared import RGBColor, Pt
        
        # Crea bookmark per questa descrizione
        bookmark_name = f"{JUMP_PREFIX}{label.replace('.', '_').replace(' ', '_')}"
        
        # Paragrafo per label + bookmark
        label_para = self.document.add_paragraph()
        self.create_bookmark(label_para, bookmark_name)
        
        # Label in grassetto e più grande
        label_run = label_para.add_run(f"{label}: ")
        label_run.bold = True
        label_run.font.size = Pt(14)
        label_run.font.color.rgb = RGBColor(0, 0, 128)  # Blu scuro
        
        # Paragrafo descrizione
        desc_para = self.document.add_paragraph(description)
        
        # Spazio
        self.document.add_paragraph()
        
        # Link di ritorno con blocco TTS
        return_para = self.document.add_paragraph()
        
        # Aggiungi commento XML per bloccare TTS
        self._apply_tts_block(return_para)
        
        # Crea bookmark target per il ritorno (nel paragrafo originale)
        if source_paragraph_index < len(self.document.paragraphs):
            return_bookmark = f"RETURN_FROM_{bookmark_name}"
            # Nota: in produzione dovresti creare questo bookmark nel paragrafo originale
            # Per ora il link ritorna in modo generico
        
        # Testo link ritorno
        return_run = return_para.add_run(RETURN_TEXT)
        return_run.italic = True
        return_run.font.size = Pt(10)
        return_run.font.color.rgb = RGBColor(128, 128, 128)  # Grigio
        
        # Se possibile, crea hyperlink di ritorno
        # (richiede bookmark nel paragrafo originale)
        
        # Separatore
        sep_para = self.document.add_paragraph()
        sep_run = sep_para.add_run('─' * 60)
        sep_run.font.color.rgb = RGBColor(200, 200, 200)
        
        self.document.add_paragraph()  # Spazio extra
        
        print(f"  ✓ Descrizione aggiunta: {label}")
    
    def _apply_tts_block(self, paragraph):
        """
        Applica marker per bloccare sintesi vocale
        """
        # Aggiungi commento XML per indicare ai screen reader di saltare
        from docx.oxml import OxmlElement
        
        comment = OxmlElement('w:commentRangeStart')
        # In alternativa, si potrebbe usare custom properties
        # Per ora aggiungiamo un marker nel testo nascosto
        
        # Testo nascosto con tag TTS
        hidden_run = paragraph.add_run(BLOCK_TTS_TAG)
        hidden_run.font.hidden = True
    
    def create_hyperlink(self, paragraph, run_text: str, anchor_name: str):
        """
        Crea un hyperlink in un paragrafo che punta a un bookmark
        
        Args:
            paragraph: Paragrafo Word dove inserire il link
            run_text: Testo del link
            anchor_name: Nome del bookmark target
        
        Returns:
            Elemento XML hyperlink creato
        """
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import RGBColor
        
        # Crea elemento hyperlink
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('w:anchor'), anchor_name)
        hyperlink.set(qn('w:history'), '1')
        
        # Crea nuovo run per il testo del link
        new_run = OxmlElement('w:r')
        
        # Stile del link (blu, sottolineato)
        rPr = OxmlElement('w:rPr')
        
        # Usa stile Hyperlink
        rStyle = OxmlElement('w:rStyle')
        rStyle.set(qn('w:val'), 'Hyperlink')
        rPr.append(rStyle)
        
        # Colore blu
        color = OxmlElement('w:color')
        color.set(qn('w:val'), '0000FF')
        rPr.append(color)
        
        # Sottolineato
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)
        
        new_run.append(rPr)
        
        # Aggiungi testo
        text_elem = OxmlElement('w:t')
        text_elem.text = run_text
        new_run.append(text_elem)
        
        # Assembla hyperlink
        hyperlink.append(new_run)
        
        # Aggiungi al paragrafo
        paragraph._element.append(hyperlink)
        
        return hyperlink
    
    def create_bookmark(self, paragraph, bookmark_name: str):
        """
        Crea un bookmark in un paragrafo
        
        Args:
            paragraph: Paragrafo Word dove creare il bookmark
            bookmark_name: Nome univoco del bookmark
        
        Returns:
            Tuple (bookmark_start, bookmark_end)
        """
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        
        # Genera ID univoco per questo bookmark
        bookmark_id = str(hash(bookmark_name) % 100000)
        
        # Bookmark start
        bookmark_start = OxmlElement('w:bookmarkStart')
        bookmark_start.set(qn('w:id'), bookmark_id)
        bookmark_start.set(qn('w:name'), bookmark_name)
        
        # Bookmark end
        bookmark_end = OxmlElement('w:bookmarkEnd')
        bookmark_end.set(qn('w:id'), bookmark_id)
        
        # Inserisci all'inizio del paragrafo
        paragraph._element.insert(0, bookmark_start)
        paragraph._element.append(bookmark_end)
        
        return (bookmark_start, bookmark_end)
    
    def validate_jumps(self) -> Dict:
        """
        Valida che tutti i jump abbiano target validi
        
        Returns:
            Dict con risultati validazione
        """
        validation = {
            'total_jumps': len(self.jumps_created),
            'valid': 0,
            'broken': 0,
            'missing_targets': []
        }
        
        # TODO: Implementare validazione
        # Verifica che ogni jump abbia un target esistente
        
        return validation
    
    def get_jumps_summary(self) -> Dict:
        """
        Ottiene un sommario di tutti i jump creati
        """
        summary = {
            'total': len(self.jumps_created),
            'by_type': {},
            'jumps': self.jumps_created
        }
        
        for jump in self.jumps_created:
            jump_type = jump.get('type', 'unknown')
            summary['by_type'][jump_type] = summary['by_type'].get(jump_type, 0) + 1
        
        return summary
    
    def scan_context_for_references(self, target_label: str, 
                                    scan_radius: int = 5) -> List[Dict]:
        """
        Scansiona paragrafi attorno a un'immagine per trovare altri riferimenti
        
        Es: se trovo Fig.2.5, cerco nelle pagine vicine altri "Fig.2.5" 
        da convertire in jump
        
        Args:
            target_label: Label da cercare (es. "Fig.2.5")
            scan_radius: Numero di paragrafi da scansionare prima/dopo
        
        Returns:
            Lista di posizioni dove il label appare
        """
        occurrences = []
        
        # Pattern per cercare il label (case insensitive)
        pattern = re.compile(re.escape(target_label), re.IGNORECASE)
        
        for idx, paragraph in enumerate(self.document.paragraphs):
            matches = pattern.finditer(paragraph.text)
            for match in matches:
                occurrences.append({
                    'paragraph_index': idx,
                    'position': match.start(),
                    'context': paragraph.text[max(0, match.start()-30):min(len(paragraph.text), match.end()+30)]
                })
        
        return occurrences

    
    def export_jump_map(self, output_path: str) -> None:
        """
        Esporta una mappa di tutti i jump in formato JSON
        Utile per debug e documentazione
        """
        import json
        
        jump_map = {
            'total_jumps': len(self.jumps_created),
            'jumps': self.jumps_created,
            'summary': self.get_jumps_summary()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(jump_map, f, indent=2, ensure_ascii=False)
        
        print(f"Mappa jump esportata: {output_path}")
