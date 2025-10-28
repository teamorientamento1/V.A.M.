"""
Sistema di deduplicazione dei riferimenti
Elimina riferimenti duplicati o troppo simili nello stesso documento
"""

from typing import List, Dict, Set
from difflib import SequenceMatcher
import re


class ReferenceDeduplicator:
    """Gestisce la deduplicazione intelligente dei riferimenti"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Soglia di similarità (0-1) per considerare due riferimenti duplicati
        """
        self.similarity_threshold = similarity_threshold
        self.seen_contexts = set()
        
    def deduplicate_references(self, references: List[Dict], strategy: str = 'smart') -> List[Dict]:
        """
        Deduplica una lista di riferimenti
        
        Args:
            references: Lista di riferimenti da deduplicare
            strategy: Strategia di deduplicazione
                - 'exact': Solo duplicati esatti
                - 'context': Basata sul contesto
                - 'position': Basata sulla posizione nel documento
                - 'smart': Combinazione intelligente (default)
                
        Returns:
            Lista di riferimenti dedupplicati
        """
        if not references:
            return []
            
        if strategy == 'exact':
            return self._deduplicate_exact(references)
        elif strategy == 'context':
            return self._deduplicate_by_context(references)
        elif strategy == 'position':
            return self._deduplicate_by_position(references)
        else:  # smart
            return self._deduplicate_smart(references)
    
    def _deduplicate_exact(self, references: List[Dict]) -> List[Dict]:
        """Rimuove solo i duplicati esatti basati su paragraph_index"""
        seen_indices = set()
        unique_refs = []
        
        for ref in references:
            para_idx = ref.get('paragraph_index')
            if para_idx not in seen_indices:
                seen_indices.add(para_idx)
                unique_refs.append(ref)
                
        return unique_refs
    
    def _deduplicate_by_context(self, references: List[Dict]) -> List[Dict]:
        """Deduplica basandosi sulla similarità del contesto"""
        unique_refs = []
        
        for ref in references:
            context = self._extract_context(ref)
            
            # Verifica se esiste un contesto molto simile
            is_duplicate = False
            for existing_context in self.seen_contexts:
                similarity = self._calculate_similarity(context, existing_context)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                self.seen_contexts.add(context)
                unique_refs.append(ref)
                
        return unique_refs
    
    def _deduplicate_by_position(self, references: List[Dict]) -> List[Dict]:
        """Deduplica basandosi sulla vicinanza nel documento"""
        if not references:
            return []
            
        # Ordina per posizione
        sorted_refs = sorted(references, key=lambda x: x.get('paragraph_index', 0))
        unique_refs = [sorted_refs[0]]
        
        min_distance = 3  # Minimo 3 paragrafi di distanza
        
        for ref in sorted_refs[1:]:
            last_idx = unique_refs[-1].get('paragraph_index', 0)
            curr_idx = ref.get('paragraph_index', 0)
            
            if abs(curr_idx - last_idx) >= min_distance:
                unique_refs.append(ref)
                
        return unique_refs
    
    def _deduplicate_smart(self, references: List[Dict]) -> List[Dict]:
        """Strategia intelligente che combina più approcci"""
        if not references:
            return []
        
        # Fase 1: Rimuovi duplicati esatti
        unique_refs = self._deduplicate_exact(references)
        
        # Fase 2: Analizza contesto e posizione
        final_refs = []
        self.seen_contexts = set()
        
        for i, ref in enumerate(unique_refs):
            context = self._extract_context(ref)
            para_idx = ref.get('paragraph_index', 0)
            
            # Verifica similarità del contesto
            is_context_duplicate = False
            for existing_context in self.seen_contexts:
                similarity = self._calculate_similarity(context, existing_context)
                if similarity >= self.similarity_threshold:
                    is_context_duplicate = True
                    break
            
            # Verifica vicinanza con l'ultimo riferimento aggiunto
            is_position_duplicate = False
            if final_refs:
                last_idx = final_refs[-1].get('paragraph_index', 0)
                if abs(para_idx - last_idx) < 2:  # Troppo vicino
                    is_position_duplicate = True
            
            # Aggiungi solo se passa entrambi i test
            if not is_context_duplicate and not is_position_duplicate:
                self.seen_contexts.add(context)
                final_refs.append(ref)
        
        return final_refs
    
    def _extract_context(self, reference: Dict) -> str:
        """Estrae il contesto completo da un riferimento"""
        before = reference.get('context_before', '')
        variant = reference.get('variant_found', '')
        after = reference.get('context_after', '')
        
        # Normalizza e concatena
        context = f"{before} {variant} {after}"
        context = re.sub(r'\s+', ' ', context).strip().lower()
        
        return context
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcola la similarità tra due testi (0-1)"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def get_duplicates_report(self, references: List[Dict]) -> Dict:
        """
        Genera un report sui duplicati trovati
        
        Returns:
            Dict con statistiche sui duplicati
        """
        if not references:
            return {
                'total_references': 0,
                'exact_duplicates': 0,
                'context_duplicates': 0,
                'position_duplicates': 0,
                'unique_references': 0
            }
        
        total = len(references)
        exact_unique = len(self._deduplicate_exact(references))
        context_unique = len(self._deduplicate_by_context(references))
        position_unique = len(self._deduplicate_by_position(references))
        smart_unique = len(self._deduplicate_smart(references))
        
        return {
            'total_references': total,
            'exact_duplicates': total - exact_unique,
            'context_duplicates': total - context_unique,
            'position_duplicates': total - position_unique,
            'smart_deduplication': smart_unique,
            'reduction_percentage': round((1 - smart_unique / total) * 100, 2) if total > 0 else 0
        }
    
    def mark_duplicates(self, references: List[Dict]) -> List[Dict]:
        """
        Marca i duplicati invece di rimuoverli
        Aggiunge il campo 'is_duplicate' a ogni riferimento
        """
        unique_refs_set = set()
        for ref in self._deduplicate_smart(references):
            unique_refs_set.add(id(ref))
        
        marked_refs = []
        for ref in references:
            ref_copy = ref.copy()
            ref_copy['is_duplicate'] = id(ref) not in unique_refs_set
            marked_refs.append(ref_copy)
        
        return marked_refs


def test_deduplicator():
    """Test del sistema di deduplicazione"""
    
    # Crea riferimenti di test con alcuni duplicati
    test_refs = [
        {
            'paragraph_index': 10,
            'variant_found': 'Fig. 1',
            'context_before': 'Come mostrato in',
            'context_after': 'possiamo vedere'
        },
        {
            'paragraph_index': 10,  # Duplicato esatto
            'variant_found': 'Fig. 1',
            'context_before': 'Come mostrato in',
            'context_after': 'possiamo vedere'
        },
        {
            'paragraph_index': 11,  # Troppo vicino
            'variant_found': 'Figura 1',
            'context_before': 'Come indicato in',
            'context_after': 'si può notare'
        },
        {
            'paragraph_index': 50,  # Diverso
            'variant_found': 'Fig. 1',
            'context_before': 'Nella sezione precedente',
            'context_after': 'abbiamo discusso'
        },
        {
            'paragraph_index': 100,  # Diverso
            'variant_found': 'Figura 1',
            'context_before': 'In conclusione',
            'context_after': 'rappresenta il risultato'
        }
    ]
    
    dedup = ReferenceDeduplicator(similarity_threshold=0.85)
    
    print("=== TEST DEDUPLICAZIONE ===\n")
    print(f"Riferimenti originali: {len(test_refs)}")
    
    # Test strategie diverse
    exact = dedup.deduplicate_references(test_refs, strategy='exact')
    print(f"Strategia 'exact': {len(exact)} riferimenti")
    
    context = dedup.deduplicate_references(test_refs, strategy='context')
    print(f"Strategia 'context': {len(context)} riferimenti")
    
    position = dedup.deduplicate_references(test_refs, strategy='position')
    print(f"Strategia 'position': {len(position)} riferimenti")
    
    smart = dedup.deduplicate_references(test_refs, strategy='smart')
    print(f"Strategia 'smart': {len(smart)} riferimenti")
    
    # Report
    print("\n=== REPORT DUPLICATI ===")
    report = dedup.get_duplicates_report(test_refs)
    for key, value in report.items():
        print(f"{key}: {value}")
    
    # Riferimenti marcati
    print("\n=== RIFERIMENTI MARCATI ===")
    marked = dedup.mark_duplicates(test_refs)
    for i, ref in enumerate(marked):
        status = "❌ DUPLICATO" if ref['is_duplicate'] else "✓ UNICO"
        print(f"{i+1}. Par.{ref['paragraph_index']} - {status}")


if __name__ == "__main__":
    test_deduplicator()
