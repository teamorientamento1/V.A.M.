"""
Document Analyzer - Analisi completa documenti Word
"""

from docx import Document
from typing import Dict, List, Optional
import re


class WordAnalyzer:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.document = None
        self.doc_path = None
        
    def load_document(self, doc_path: str):
        """Carica documento Word"""
        self.doc_path = doc_path
        self.document = Document(doc_path)
        
    def analyze(self, discipline: str = "mathematics") -> Dict:
        """Analizza il documento"""
        if not self.document:
            raise ValueError("Nessun documento caricato")
        
        results = {
            'images': self._extract_images(),
            'tables': self._extract_tables(),
            'equations': self._extract_equations(),
            'references': self._extract_references()
        }
        
        return results
    
    def _extract_images(self) -> List[Dict]:
        """Estrae immagini con contesto 5 righe sopra/sotto"""
        images = []
        
        for rel_id, rel in self.document.part.rels.items():
            if "image" in rel.target_ref:
                location = self._find_image_paragraph(rel_id)
                
                if location is not None:
                    # Ottieni contesto 5 righe
                    context = self._get_context_5_lines(location)
                    
                    # Cerca label
                    label = self._extract_image_label(
                        ' '.join(context['before']) + ' ' + ' '.join(context['after'])
                    )
                    
                    # Rileva elementi adiacenti
                    adjacent = self._detect_adjacent_elements(location)
                    
                    image_data = {
                        'paragraph_index': location,
                        'label': label or f"IMG_{len(images)+1}",
                        'rel_id': rel_id,
                        'filename': rel.target_ref.split('/')[-1],
                        'content_type': rel.target_part.content_type,
                        'image_part': rel.target_part,
                        'context_before': context['before'],  # Lista di 5 stringhe
                        'context_after': context['after'],    # Lista di 5 stringhe
                        'has_adjacent_before': adjacent['before'],
                        'has_adjacent_after': adjacent['after']
                    }
                    
                    images.append(image_data)
        
        return images
    
    def _find_image_paragraph(self, rel_id: str) -> Optional[int]:
        """Trova paragrafo contenente immagine"""
        for i, paragraph in enumerate(self.document.paragraphs):
            for run in paragraph.runs:
                run_element = run._element
                blips = run_element.findall('.//{*}blip')
                for blip in blips:
                    embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if embed_id == rel_id:
                        return i
        return None
    
    def _get_context_5_lines(self, para_idx: int) -> Dict:
        """Ottiene esattamente 5 righe prima e 5 dopo"""
        before_lines = []
        after_lines = []
        
        # 5 paragrafi prima
        for i in range(max(0, para_idx - 5), para_idx):
            before_lines.append(self.document.paragraphs[i].text)
        
        # 5 paragrafi dopo
        for i in range(para_idx + 1, min(len(self.document.paragraphs), para_idx + 6)):
            after_lines.append(self.document.paragraphs[i].text)
        
        return {
            'before': before_lines,
            'after': after_lines
        }
    
    def _detect_adjacent_elements(self, para_idx: int) -> Dict:
        """Rileva se ci sono immagini adiacenti"""
        has_before = False
        has_after = False
        
        if para_idx > 0:
            has_before = self._paragraph_has_image(para_idx - 1)
        
        if para_idx < len(self.document.paragraphs) - 1:
            has_after = self._paragraph_has_image(para_idx + 1)
        
        return {
            'before': has_before,
            'after': has_after
        }
    
    def _paragraph_has_image(self, para_idx: int) -> bool:
        """Verifica se paragrafo ha immagine"""
        if para_idx < 0 or para_idx >= len(self.document.paragraphs):
            return False
        
        paragraph = self.document.paragraphs[para_idx]
        for run in paragraph.runs:
            blips = run._element.findall('.//{*}blip')
            if blips:
                return True
        return False
    
    def _extract_image_label(self, text: str) -> Optional[str]:
        """Estrae label immagine"""
        patterns = [
            r'[Ff]ig(?:ure|ura)?\.?\s*(\d+(?:\.\d+)?)',
            r'[Ii]mmagine\.?\s*(\d+(?:\.\d+)?)',
            r'[Gg]rafico\.?\s*(\d+(?:\.\d+)?)',
            r'[Ff]igure\.?\s*(\d+(?:\.\d+)?)',
            r'[Tt]ab(?:ella)?\.?\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                prefix = "Fig" if "ig" in pattern.lower() else "Tab"
                return f"{prefix}.{match.group(1)}"
        
        return None
    
    def _extract_tables(self) -> List[Dict]:
        """Estrae tabelle"""
        tables = []
        
        for i, table in enumerate(self.document.tables):
            rows_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                rows_data.append(row_data)
            
            table_data = {
                'index': i,
                'rows': rows_data,
                'num_rows': len(rows_data),
                'num_cols': len(rows_data[0]) if rows_data else 0,
                'paragraph_index': None
            }
            
            tables.append(table_data)
        
        return tables
    
    def _extract_equations(self) -> List[Dict]:
        """Estrae equazioni con categoria"""
        equations = []
        
        for i, paragraph in enumerate(self.document.paragraphs):
            omath_elements = paragraph._element.findall('.//{*}oMath')
            
            for omath in omath_elements:
                text = ''.join(omath.itertext())
                
                try:
                    from lxml import etree
                    mathml = etree.tostring(omath, encoding='unicode')
                except:
                    mathml = str(omath)
                
                context = self._get_context_5_lines(i)
                
                eq_data = {
                    'paragraph_index': i,
                    'text_representation': text,
                    'mathml': mathml,
                    'context_before': context['before'],
                    'context_after': context['after'],
                    'category': 'generic',  # Per ora sempre generic
                    'sub_categories': []
                }
                
                equations.append(eq_data)
        
        return equations
    
    def _extract_references(self) -> List[Dict]:
        """Estrae riferimenti"""
        references = []
        
        patterns = {
            'figure': r'[Ff]ig(?:ure|ura)?\.?\s*(\d+(?:\.\d+)?)',
            'table': r'[Tt]ab(?:ella)?\.?\s*(\d+(?:\.\d+)?)',
            'equation': r'[Ee]q(?:uation|uazione)?\.?\s*(\d+(?:\.\d+)?)',
        }
        
        for i, paragraph in enumerate(self.document.paragraphs):
            text = paragraph.text
            
            for ref_type, pattern in patterns.items():
                for match in re.finditer(pattern, text):
                    references.append({
                        'type': ref_type,
                        'label': match.group(0),
                        'number': match.group(1),
                        'paragraph_index': i,
                        'position': match.start()
                    })
        
        return references
