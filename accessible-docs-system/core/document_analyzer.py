"""
Analizzatore di documenti Word - Estrae e analizza tutti gli elementi
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn
import hashlib

from config.settings import *
from core.knowledge_base import KnowledgeBase


class WordAnalyzer:
    """
    Analizza documenti Word ed estrae:
    - Equazioni matematiche (Office Math)
    - Immagini e figure
    - Tabelle
    - Riferimenti (Fig.X.Y, Eq.X.Y, etc.)
    - Testo normale
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.document = None
        self.analysis_result = None
    
    def load_document(self, doc_path: Path) -> bool:
        """
        Carica un documento Word
        """
        try:
            self.document = Document(str(doc_path))
            print(f"Documento caricato: {doc_path}")
            return True
        except Exception as e:
            print(f"Errore nel caricamento: {e}")
            return False
    
    def analyze(self, discipline: str = "generic") -> Dict:
        """
        Analisi completa del documento
        
        Returns:
            Dict con tutti gli elementi trovati
        """
        if not self.document:
            raise ValueError("Nessun documento caricato")
        
        print("Inizio analisi documento...")
        
        result = {
            'equations': [],
            'images': [],
            'tables': [],
            'references': [],
            'text_structure': [],
            'statistics': {},
            'discipline': discipline
        }
        
        # 1. Analizza equazioni
        result['equations'] = self._extract_equations()
        print(f"  - Trovate {len(result['equations'])} equazioni")
        
        # 2. Analizza immagini
        result['images'] = self._extract_images()
        print(f"  - Trovate {len(result['images'])} immagini")
        
        # 3. Analizza tabelle
        result['tables'] = self._extract_tables()
        print(f"  - Trovate {len(result['tables'])} tabelle")
        
        # 4. Trova riferimenti (Fig.X, Eq.Y, etc.)
        result['references'] = self._find_references()
        print(f"  - Trovati {len(result['references'])} riferimenti")
        
        # 5. Analizza struttura testo
        result['text_structure'] = self._analyze_text_structure()
        
        # 6. Statistiche
        result['statistics'] = self._compute_statistics(result)
        
        self.analysis_result = result
        print("Analisi completata!")
        
        return result
    
    def _extract_equations(self) -> List[Dict]:
        """
        Estrae tutte le equazioni Office Math dal documento
        """
        equations = []
        
        for paragraph in self.document.paragraphs:
            # Cerca elementi OfficeMath nel paragrafo
            for elem in paragraph._element.iter():
                if elem.tag.endswith('oMath'):
                    equation_data = self._parse_equation(elem, paragraph)
                    if equation_data:
                        equations.append(equation_data)
        
        return equations
    
    def _parse_equation(self, omath_elem, paragraph) -> Optional[Dict]:
        """
        Analizza un elemento Office Math e lo converte
        
        TODO: Implementare conversione MathML -> LaTeX completa
        Per ora estrae testo e struttura base
        """
        try:
            # Estrai il MathML/OMML
            mathml = omath_elem.xml
            
            # Estrai testo semplificato
            text_content = ''.join(omath_elem.itertext())
            
            # Trova contesto
            context = self._get_context_around_paragraph(paragraph)
            
            # Crea hash univoco
            equation_hash = hashlib.md5(mathml.encode()).hexdigest()
            
            equation_data = {
                'mathml': mathml,
                'text_representation': text_content,
                'hash': equation_hash,
                'context_before': context['before'],
                'context_after': context['after'],
                'paragraph_index': self._get_paragraph_index(paragraph),
                'structure': self._analyze_equation_structure(omath_elem)
            }
            
            return equation_data
            
        except Exception as e:
            print(f"Errore nell'analisi equazione: {e}")
            return None
    
    def _analyze_equation_structure(self, omath_elem) -> Dict:
        """
        Analizza la struttura di un'equazione
        Identifica: frazioni, integrali, somme, matrici, etc.
        """
        structure = {
            'type': 'unknown',
            'components': [],
            'has_fraction': False,
            'has_integral': False,
            'has_sum': False,
            'has_matrix': False,
            'has_superscript': False,
            'has_subscript': False
        }
        
        # Cerca elementi specifici nell'XML
        xml_str = omath_elem.xml
        
        # Frazione
        if 'f' in xml_str or 'frac' in xml_str:
            structure['has_fraction'] = True
            structure['type'] = 'fraction'
        
        # Integrale
        if '∫' in xml_str or 'int' in xml_str:
            structure['has_integral'] = True
            structure['type'] = 'integral'
        
        # Sommatoria
        if '∑' in xml_str or 'sum' in xml_str:
            structure['has_sum'] = True
            structure['type'] = 'summation'
        
        # Apici/pedici
        if 'sSup' in xml_str or 'sup' in xml_str:
            structure['has_superscript'] = True
        if 'sSub' in xml_str or 'sub' in xml_str:
            structure['has_subscript'] = True
        
        # TODO: Analisi più approfondita della struttura
        # - Identificare numeratore/denominatore nelle frazioni
        # - Estremi di integrazione
        # - Dimensioni matrici
        # etc.
        
        return structure
    
    def _extract_images(self) -> List[Dict]:
        """
        Estrae tutte le immagini/figure dal documento
        """
        images = []
        image_index = 0
        
        # Mappa per tenere traccia delle immagini già trovate
        found_images = set()
        
        # Metodo 1: Cerca attraverso le relationships (immagini embedded)
        for rel_id, rel in self.document.part.rels.items():
            if "image" in rel.target_ref:
                image_index += 1
                
                image_data = {
                    'index': image_index,
                    'rel_id': rel_id,
                    'filename': rel.target_ref.split('/')[-1],
                    'content_type': rel.target_part.content_type,
                    'image_bytes': rel.target_part.blob,
                    'size_bytes': len(rel.target_part.blob),
                    'paragraph_index': None,
                    'label': None,
                    'caption': None,
                    'context_before': '',
                    'context_after': '',
                    'has_caption': False,
                    'width': None,
                    'height': None
                }
                
                # Trova dove è usata questa immagine nel documento
                location = self._find_image_location(rel_id)
                if location:
                    image_data.update(location)
                
                # Cerca label nel contesto
                if image_data['paragraph_index'] is not None:
                    context = self._get_context_around_index(image_data['paragraph_index'])
                    image_data['context_before'] = context['before']
                    image_data['context_after'] = context['after']
                    
                    # Estrai label (Fig.X.Y)
                    label = self._extract_image_label(context['before'] + context['after'])
                    if label:
                        image_data['label'] = label
                
                images.append(image_data)
                found_images.add(rel_id)
        
        # Metodo 2: Scansiona paragrafi per immagini inline (drawing)
        for para_idx, paragraph in enumerate(self.document.paragraphs):
            # Cerca elementi w:drawing nel XML del paragrafo
            for elem in paragraph._element.iter():
                # Namespace Word per drawing
                if elem.tag.endswith('}drawing') or elem.tag.endswith('}pict'):
                    # Verifica se questa immagine è già stata trovata
                    # Cerca blip (reference all'immagine)
                    blip_elem = self._find_blip_in_element(elem)
                    if blip_elem is not None:
                        embed_id = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                        
                        if embed_id and embed_id not in found_images:
                            # Nuova immagine trovata
                            image_index += 1
                            
                            # Cerca relationship
                            if embed_id in self.document.part.rels:
                                rel = self.document.part.rels[embed_id]
                                
                                image_data = {
                                    'index': image_index,
                                    'rel_id': embed_id,
                                    'filename': rel.target_ref.split('/')[-1],
                                    'content_type': rel.target_part.content_type,
                                    'image_bytes': rel.target_part.blob,
                                    'size_bytes': len(rel.target_part.blob),
                                    'paragraph_index': para_idx,
                                    'label': None,
                                    'caption': None,
                                    'context_before': '',
                                    'context_after': '',
                                    'has_caption': False,
                                    'width': None,
                                    'height': None
                                }
                                
                                # Estrai dimensioni se disponibili
                                dims = self._extract_image_dimensions(elem)
                                if dims:
                                    image_data['width'] = dims['width']
                                    image_data['height'] = dims['height']
                                
                                # Contesto
                                context = self._get_context_around_index(para_idx)
                                image_data['context_before'] = context['before']
                                image_data['context_after'] = context['after']
                                
                                # Label
                                label = self._extract_image_label(context['before'] + context['after'])
                                if label:
                                    image_data['label'] = label
                                
                                # Cerca caption (spesso nel paragrafo stesso o quello dopo)
                                caption = self._extract_caption(para_idx)
                                if caption:
                                    image_data['caption'] = caption
                                    image_data['has_caption'] = True
                                    if not image_data['label']:
                                        # Prova ad estrarre label dalla caption
                                        label = self._extract_image_label(caption)
                                        if label:
                                            image_data['label'] = label
                                
                                images.append(image_data)
                                found_images.add(embed_id)
        
        # Cerca immagini nelle tabelle
        for table_idx, table in enumerate(self.document.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    # Scansiona paragrafi nella cella
                    for cell_para in cell.paragraphs:
                        for elem in cell_para._element.iter():
                            if elem.tag.endswith('}drawing') or elem.tag.endswith('}pict'):
                                blip_elem = self._find_blip_in_element(elem)
                                if blip_elem is not None:
                                    embed_id = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                    
                                    if embed_id and embed_id not in found_images:
                                        image_index += 1
                                        
                                        if embed_id in self.document.part.rels:
                                            rel = self.document.part.rels[embed_id]
                                            
                                            image_data = {
                                                'index': image_index,
                                                'rel_id': embed_id,
                                                'filename': rel.target_ref.split('/')[-1],
                                                'content_type': rel.target_part.content_type,
                                                'image_bytes': rel.target_part.blob,
                                                'size_bytes': len(rel.target_part.blob),
                                                'paragraph_index': None,
                                                'in_table': True,
                                                'table_index': table_idx,
                                                'row_index': row_idx,
                                                'cell_index': cell_idx,
                                                'label': None,
                                                'caption': cell.text[:100],  # Usa testo cella come caption
                                                'context_before': '',
                                                'context_after': '',
                                                'has_caption': bool(cell.text),
                                                'width': None,
                                                'height': None
                                            }
                                            
                                            # Cerca label nel testo della cella
                                            label = self._extract_image_label(cell.text)
                                            if label:
                                                image_data['label'] = label
                                            
                                            images.append(image_data)
                                            found_images.add(embed_id)
        
        return images
    
    def _find_blip_in_element(self, element):
        """Trova elemento blip (riferimento immagine) nell'XML"""
        # Cerca in profondità l'elemento a:blip
        for child in element.iter():
            if child.tag.endswith('}blip'):
                return child
        return None
    
    def _find_image_location(self, rel_id: str) -> Optional[Dict]:
        """Trova in quale paragrafo si trova un'immagine dato il rel_id"""
        for para_idx, paragraph in enumerate(self.document.paragraphs):
            # Cerca nel XML del paragrafo
            para_xml = paragraph._element.xml
            if rel_id in para_xml:
                return {
                    'paragraph_index': para_idx,
                    'in_table': False
                }
        
        # Cerca nelle tabelle
        for table_idx, table in enumerate(self.document.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in row.cells:
                    for para in cell.paragraphs:
                        if rel_id in para._element.xml:
                            return {
                                'paragraph_index': None,
                                'in_table': True,
                                'table_index': table_idx,
                                'row_index': row_idx,
                                'cell_index': cell_idx
                            }
        
        return None
    
    def _extract_image_dimensions(self, drawing_element) -> Optional[Dict]:
        """Estrae larghezza e altezza da elemento drawing"""
        try:
            # Cerca elementi cx e cy (dimensioni in EMU - English Metric Units)
            # 914400 EMU = 1 inch
            for elem in drawing_element.iter():
                if elem.tag.endswith('}extent'):
                    cx = elem.get('cx')  # width
                    cy = elem.get('cy')  # height
                    if cx and cy:
                        # Converti da EMU a pixel (96 DPI)
                        width_px = int(cx) / 914400 * 96
                        height_px = int(cy) / 914400 * 96
                        return {
                            'width': round(width_px),
                            'height': round(height_px)
                        }
        except:
            pass
        return None
    
    def _extract_caption(self, para_idx: int) -> Optional[str]:
        """Estrae caption dall'immagine (paragrafo stesso o successivo)"""
        # Caption è spesso nel paragrafo stesso o in quello dopo
        captions = []
        
        # Paragrafo corrente
        if para_idx < len(self.document.paragraphs):
            para_text = self.document.paragraphs[para_idx].text.strip()
            if para_text and self._looks_like_caption(para_text):
                captions.append(para_text)
        
        # Paragrafo successivo
        if para_idx + 1 < len(self.document.paragraphs):
            next_text = self.document.paragraphs[para_idx + 1].text.strip()
            if next_text and self._looks_like_caption(next_text):
                captions.append(next_text)
        
        # Paragrafo precedente (meno comune ma possibile)
        if para_idx > 0:
            prev_text = self.document.paragraphs[para_idx - 1].text.strip()
            if prev_text and self._looks_like_caption(prev_text):
                captions.append(prev_text)
        
        return captions[0] if captions else None
    
    def _looks_like_caption(self, text: str) -> bool:
        """Verifica se un testo sembra una caption"""
        # Euristiche per identificare caption
        caption_patterns = [
            r'^[Ff]ig(?:ure|ura)?\.?\s*\d+',
            r'^[Ii]mmagine\.?\s*\d+',
            r'^[Tt]ab(?:le|ella)?\.?\s*\d+',
            r'^[Gg]rafico\.?\s*\d+',
            r'^[Ss]chema\.?\s*\d+',
        ]
        
        for pattern in caption_patterns:
            if re.search(pattern, text):
                return True
        
        # Caption tipicamente brevi (< 200 caratteri) e non troppo brevi (> 10)
        if 10 < len(text) < 200:
            # Non deve sembrare un paragrafo normale
            if not text.endswith('.') or text.count('.') <= 2:
                return True
        
        return False
    
    def _extract_image_label(self, text: str) -> Optional[str]:
        """Estrae label immagine (es. Fig.2.5) dal testo"""
        patterns = [
            r'[Ff]ig(?:ure|ura)?\.?\s*(\d+(?:\.\d+)?)',
            r'[Ii]mmagine\.?\s*(\d+(?:\.\d+)?)',
            r'[Gg]rafico\.?\s*(\d+(?:\.\d+)?)',
            r'[Ss]chema\.?\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"Fig.{match.group(1)}"
        
        return None
    
    def _get_context_around_index(self, para_idx: int) -> Dict:
        """Ottiene contesto prima e dopo un paragrafo specifico"""
        before_text = ""
        after_text = ""
        
        # Testo prima (2 paragrafi)
        for i in range(max(0, para_idx - 2), para_idx):
            before_text += self.document.paragraphs[i].text + " "
        
        # Testo dopo (2 paragrafi)
        for i in range(para_idx + 1, min(len(self.document.paragraphs), para_idx + 3)):
            after_text += self.document.paragraphs[i].text + " "
        
        return {
            'before': before_text.strip()[:CONTEXT_RADIUS],
            'after': after_text.strip()[:CONTEXT_RADIUS]
        }
    
    def _extract_tables(self) -> List[Dict]:
        """
        Estrae tutte le tabelle dal documento
        """
        tables = []
        
        for idx, table in enumerate(self.document.tables):
            table_data = {
                'index': idx,
                'rows': len(table.rows),
                'cols': len(table.columns) if table.rows else 0,
                'content': [],
                'has_equations': False,
                'context_before': None,
                'context_after': None
            }
            
            # Estrai contenuto celle
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text
                    row_data.append(cell_text)
                    
                    # Verifica se ci sono equazioni nella cella
                    # TODO: Implementare check equazioni nelle celle
                
                table_data['content'].append(row_data)
            
            # Trova contesto attorno alla tabella
            # TODO: Implementare estrazione contesto
            
            tables.append(table_data)
        
        return tables
    
    def _find_references(self) -> List[Dict]:
        """
        Trova tutti i riferimenti a figure, equazioni, tabelle, etc.
        
        Pattern comuni:
        - Fig. 2.5, Figure 2.5
        - Eq. (3.1), Equation (3.1)
        - Tab. 4.2, Table 4.2
        - [1], [23], etc. (bibliografia)
        """
        references = []
        
        # Pattern regex per riferimenti
        patterns = {
            'figure': r'(?i)fig(?:ure)?\.?\s*(\d+(?:\.\d+)?)',
            'equation': r'(?i)eq(?:uation)?\.?\s*\(?(\d+(?:\.\d+)?)\)?',
            'table': r'(?i)tab(?:le)?\.?\s*(\d+(?:\.\d+)?)',
            'citation': r'\[(\d+)\]'
        }
        
        for para_idx, paragraph in enumerate(self.document.paragraphs):
            text = paragraph.text
            
            for ref_type, pattern in patterns.items():
                matches = re.finditer(pattern, text)
                for match in matches:
                    references.append({
                        'type': ref_type,
                        'label': match.group(1),
                        'full_match': match.group(0),
                        'paragraph_index': para_idx,
                        'position_in_paragraph': match.start(),
                        'context': text[max(0, match.start()-50):min(len(text), match.end()+50)]
                    })
        
        return references
    
    def _analyze_text_structure(self) -> List[Dict]:
        """
        Analizza la struttura del testo (heading, paragrafi, etc.)
        """
        structure = []
        
        for idx, paragraph in enumerate(self.document.paragraphs):
            para_info = {
                'index': idx,
                'text': paragraph.text[:100],  # Prime 100 char
                'style': paragraph.style.name if paragraph.style else 'Normal',
                'is_heading': False,
                'level': None
            }
            
            # Verifica se è un heading
            if paragraph.style and 'Heading' in paragraph.style.name:
                para_info['is_heading'] = True
                # Estrai livello (Heading 1, Heading 2, etc.)
                level_match = re.search(r'Heading (\d+)', paragraph.style.name)
                if level_match:
                    para_info['level'] = int(level_match.group(1))
            
            structure.append(para_info)
        
        return structure
    
    def _get_context_around_paragraph(self, target_paragraph) -> Dict:
        """
        Ottiene il testo prima e dopo un paragrafo specifico
        """
        target_idx = self._get_paragraph_index(target_paragraph)
        
        # Testo prima
        before_text = ""
        for i in range(max(0, target_idx - 2), target_idx):
            before_text += self.document.paragraphs[i].text + " "
        
        # Testo dopo
        after_text = ""
        for i in range(target_idx + 1, min(len(self.document.paragraphs), target_idx + 3)):
            after_text += self.document.paragraphs[i].text + " "
        
        return {
            'before': before_text.strip()[:CONTEXT_RADIUS],
            'after': after_text.strip()[:CONTEXT_RADIUS]
        }
    
    def _get_paragraph_index(self, paragraph) -> int:
        """Trova l'indice di un paragrafo"""
        for idx, para in enumerate(self.document.paragraphs):
            if para == paragraph:
                return idx
        return -1
    
    def _compute_statistics(self, analysis: Dict) -> Dict:
        """
        Calcola statistiche sull'analisi
        """
        stats = {
            'total_paragraphs': len(self.document.paragraphs),
            'total_equations': len(analysis['equations']),
            'total_images': len(analysis['images']),
            'total_tables': len(analysis['tables']),
            'total_references': len(analysis['references']),
            'references_by_type': {},
            'equation_types': {}
        }
        
        # Conta riferimenti per tipo
        for ref in analysis['references']:
            ref_type = ref['type']
            stats['references_by_type'][ref_type] = stats['references_by_type'].get(ref_type, 0) + 1
        
        # Conta tipi di equazioni
        for eq in analysis['equations']:
            eq_type = eq['structure']['type']
            stats['equation_types'][eq_type] = stats['equation_types'].get(eq_type, 0) + 1
        
        return stats
    
    def learn_from_analysis(self, discipline: str = "generic") -> int:
        """
        Impara dall'analisi e popola il Knowledge Base
        
        Returns:
            Numero di pattern aggiunti
        """
        if not self.analysis_result:
            raise ValueError("Nessuna analisi disponibile. Esegui prima analyze()")
        
        print("Inizio apprendimento dall'analisi...")
        patterns_added = 0
        
        # 1. Impara dalle equazioni
        for eq in self.analysis_result['equations']:
            pattern_id = self.kb.add_pattern(
                discipline=discipline,
                pattern_type='equation_' + eq['structure']['type'],
                mathml_representation=eq['mathml'],
                content_description=eq['text_representation'],
                context_words=[eq['context_before'], eq['context_after']],
                visual_signature=eq['hash'],
                created_from='word_analysis'
            )
            
            # Aggiungi contesto
            self.kb.add_context(
                pattern_id=pattern_id,
                surrounding_text=eq['context_before'] + " " + eq['context_after']
            )
            
            patterns_added += 1
        
        # 2. Impara dai simboli nelle equazioni
        # TODO: Estrarre e catalogare tutti i simboli usati
        
        # 3. Impara dai riferimenti
        # TODO: Imparare pattern di riferimenti
        
        print(f"Apprendimento completato: {patterns_added} pattern aggiunti")
        return patterns_added
    
    def generate_report(self) -> str:
        """
        Genera un report testuale dell'analisi
        """
        if not self.analysis_result:
            return "Nessuna analisi disponibile"
        
        stats = self.analysis_result['statistics']
        
        report = f"""
=== REPORT ANALISI DOCUMENTO ===

Disciplina: {self.analysis_result['discipline']}

STATISTICHE GENERALI:
- Paragrafi totali: {stats['total_paragraphs']}
- Equazioni trovate: {stats['total_equations']}
- Immagini trovate: {stats['total_images']}
- Tabelle trovate: {stats['total_tables']}
- Riferimenti trovati: {stats['total_references']}

TIPI DI EQUAZIONI:
"""
        for eq_type, count in stats['equation_types'].items():
            report += f"  - {eq_type}: {count}\n"
        
        report += "\nRIFERIMENTI PER TIPO:\n"
        for ref_type, count in stats['references_by_type'].items():
            report += f"  - {ref_type}: {count}\n"
        
        return report
