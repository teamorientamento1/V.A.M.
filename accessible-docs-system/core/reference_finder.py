"""
Reference Finder - Ricerca riferimenti usando database pattern
"""

import re
from typing import List, Dict
from core.patterns_database import PatternsDatabase


class ReferenceFinder:
    """Trova riferimenti nel testo con database pattern"""
    
    def __init__(self, document, db_path: str = "data/patterns.db"):
        self.document = document
        self.db = PatternsDatabase(db_path)
    
    def find_references(self, label: str) -> List[Dict]:
        """
        Trova tutti i riferimenti a una label nel documento
        
        Args:
            label: Label da cercare (es. "Fig.2.5")
        
        Returns:
            Lista di dict con info sui riferimenti trovati
        """
        variants = self.generate_variants(label)
        references = []
        
        for i, paragraph in enumerate(self.document.paragraphs):
            text = paragraph.text
            
            for variant in variants:
                matches = self._find_variant_in_text(text, variant)
                
                for match in matches:
                    context = self._extract_context(text, match['start'], match['end'])
                    
                    references.append({
                        'paragraph_index': i,
                        'variant_found': match['text'],
                        'original_label': label,
                        'position': match['start'],
                        'context_before': context['before'],
                        'context_after': context['after'],
                        'full_text': text
                    })
        
        return references
    
    def generate_variants(self, label: str) -> List[str]:
        """
        Genera varianti usando database pattern
        
        Args:
            label: Es. "Fig.2.5" o "Esempio 5.5"
        
        Returns:
            Lista varianti
        """
        variants = set()
        
        parts = self._parse_label(label)
        if not parts:
            return [label]
        
        prefix = parts['prefix']
        number = parts['number']
        
        # Detect type dal prefix
        element_type = self._detect_element_type(prefix)
        
        # Ottieni keywords dal database
        patterns = self.db.get_patterns(element_type, enabled_only=True)
        
        for pattern in patterns:
            keyword = pattern['keyword']
            
            # Genera combinazioni
            variants.add(f"{keyword} {number}")
            variants.add(f"{keyword}.{number}")
            variants.add(f"{keyword}. {number}")
            
            # Case variations
            variants.add(f"{keyword.lower()} {number}")
            variants.add(f"{keyword.lower()}.{number}")
            variants.add(f"{keyword.capitalize()} {number}")
            variants.add(f"{keyword.upper()} {number}")
        
        return list(variants)
    
    def _detect_element_type(self, prefix: str) -> str:
        """Rileva tipo elemento dal prefix"""
        prefix_lower = prefix.lower()
        
        # Cerca in tutti i pattern quale matcha
        all_types = ['figure', 'table', 'equation', 'diagram']
        
        for elem_type in all_types:
            keywords = self.db.get_all_keywords(elem_type)
            for keyword in keywords:
                if keyword.lower() in prefix_lower or prefix_lower in keyword.lower():
                    return elem_type
        
        return 'figure'  # Default
    
    def _parse_label(self, label: str) -> Dict:
        """Estrae prefisso e numero"""
        patterns = [
            r'([A-Za-z]+)\.?\s*(\d+(?:\.\d+)?)',
            r'([A-Za-z]+)\s+(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, label)
            if match:
                return {
                    'prefix': match.group(1),
                    'number': match.group(2)
                }
        
        return None
    
    def _find_variant_in_text(self, text: str, variant: str) -> List[Dict]:
        """Trova occorrenze variante"""
        matches = []
        pattern = re.escape(variant)
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append({
                'text': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
        
        return matches
    
    def _extract_context(self, text: str, start: int, end: int, 
                        radius: int = 50) -> Dict:
        """Estrae contesto"""
        before_start = max(0, start - radius)
        after_end = min(len(text), end + radius)
        
        return {
            'before': text[before_start:start],
            'after': text[end:after_end]
        }
    
    def add_pattern_from_found(self, element_type: str, keyword: str, **kwargs):
        """Aggiunge pattern trovato al database"""
        return self.db.add_pattern(element_type, keyword, **kwargs)


def search_references_in_document(document, label: str) -> List[Dict]:
    """Helper function"""
    finder = ReferenceFinder(document)
    return finder.find_references(label)
