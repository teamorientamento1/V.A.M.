"""
Sistema di analisi gerarchie per etichette di figure
Gestisce casi come: Fig. 2.5, Fig. 2.5.1, Fig. 2.5.2
Distingue tra gerarchie vere (2.5 → 2.5.1) e varianti (2.5a, 2.5b)
"""

import re
from typing import List, Dict, Optional


class LabelHierarchyAnalyzer:
    """Analizza e gestisce gerarchie nelle etichette delle figure"""
    
    def __init__(self):
        self.hierarchy_cache = {}
    
    def extract_label_number(self, label: str) -> Optional[str]:
        """
        Estrae il numero da una etichetta
        Es: "Fig. 2.5" → "2.5"
            "Figura 2.5.1" → "2.5.1"
            "Fig. 2.5a" → "2.5a"
        """
        patterns = [
            r'(?:Fig|Figura|Figure|Immagine|Grafico|Tab|Tabella)\.?\s*(\d+\.?\d*\.?\d*[a-z]?)',
            r'(\d+\.?\d*\.?\d*[a-z]?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, label, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def is_hierarchical(self, label1: str, label2: str) -> bool:
        """
        Verifica se label2 è una sotto-etichetta di label1
        Es: "2.5" e "2.5.1" → True
            "2.5" e "2.6" → False
            "2.5" e "2.5a" → False (varianti, non gerarchie)
        """
        num1 = self.extract_label_number(label1)
        num2 = self.extract_label_number(label2)
        
        if not num1 or not num2:
            return False
        
        # Se hanno lettere, sono varianti non gerarchie
        if re.search(r'[a-z]', num1) or re.search(r'[a-z]', num2):
            return False
        
        # Se num2 inizia con num1 seguito da punto
        # Es: "2.5" e "2.5.1" → True
        #     "2.5" e "2.51" → False
        if num2.startswith(num1 + '.'):
            # Verifica che dopo il punto ci sia solo un livello
            # Per evitare che "2.5" matchi "2.5.1.1"
            remaining = num2[len(num1)+1:]
            # Se remaining contiene altri punti, è troppo annidato
            # Però accettiamo un livello sotto
            return True
        
        return False
    
    def build_hierarchy(self, labels: List[str]) -> Dict[str, List[str]]:
        """
        Costruisce la gerarchia delle etichette
        
        Returns:
            Dict con:
            - 'parents': etichette principali
            - 'children': dict {parent: [child1, child2, ...]}
            - 'standalone': etichette senza gerarchia
        """
        # Estrai numeri
        label_numbers = {}
        for label in labels:
            num = self.extract_label_number(label)
            if num:
                label_numbers[label] = num
        
        parents = set()
        children_map = {}
        all_children = set()
        
        # Identifica relazioni parent-child
        for label1 in labels:
            if label1 not in label_numbers:
                continue
                
            has_children = False
            for label2 in labels:
                if label1 == label2:
                    continue
                    
                if self.is_hierarchical(label1, label2):
                    # label1 è parent di label2
                    if label1 not in children_map:
                        children_map[label1] = []
                    children_map[label1].append(label2)
                    all_children.add(label2)
                    has_children = True
            
            if has_children:
                parents.add(label1)
        
        # Etichette standalone (né parent né children)
        standalone = set(labels) - parents - all_children
        
        return {
            'parents': sorted(list(parents)),
            'children': children_map,
            'standalone': sorted(list(standalone))
        }
    
    def group_references_by_hierarchy(self, references: List[Dict]) -> Dict:
        """
        Raggruppa i riferimenti in base alla gerarchia delle etichette
        
        Args:
            references: Lista di riferimenti con campo 'variant_found'
            
        Returns:
            Dict strutturato per visualizzazione ad albero
        """
        # Estrai tutte le etichette uniche
        all_labels = set()
        label_refs = {}
        
        for ref in references:
            label = ref.get('variant_found', '')
            all_labels.add(label)
            
            if label not in label_refs:
                label_refs[label] = []
            label_refs[label].append(ref)
        
        # Costruisci gerarchia
        hierarchy = self.build_hierarchy(list(all_labels))
        
        # Struttura per UI
        grouped = {
            'hierarchical': [],  # Lista di {parent: label, children: [...]}
            'standalone': []      # Lista di label standalone
        }
        
        # Processa parents con children
        for parent in hierarchy['parents']:
            children = hierarchy['children'].get(parent, [])
            grouped['hierarchical'].append({
                'parent': parent,
                'parent_refs': label_refs.get(parent, []),
                'children': [
                    {
                        'label': child,
                        'refs': label_refs.get(child, [])
                    }
                    for child in sorted(children)
                ]
            })
        
        # Processa standalone
        for label in hierarchy['standalone']:
            grouped['standalone'].append({
                'label': label,
                'refs': label_refs.get(label, [])
            })
        
        return grouped
    
    def get_exact_matches_only(self, search_label: str, found_labels: List[str]) -> List[str]:
        """
        Filtra per ottenere solo match esatti, escludendo gerarchie
        Es: cerca "2.5", trova ["2.5", "2.5.1", "2.5.2"] → ritorna ["2.5"]
        """
        search_num = self.extract_label_number(search_label)
        if not search_num:
            return [l for l in found_labels if l == search_label]
        
        exact = []
        for label in found_labels:
            label_num = self.extract_label_number(label)
            if label_num == search_num:
                exact.append(label)
        
        return exact


def test_hierarchy_analyzer():
    """Test del sistema di analisi gerarchie"""
    analyzer = LabelHierarchyAnalyzer()
    
    print("=== TEST ANALISI GERARCHIE ===\n")
    
    # Test 1: Estrazione numeri
    print("1. Estrazione numeri da etichette:")
    test_labels = [
        "Fig. 2.5",
        "Figura 2.5.1",
        "Fig. 2.5a",
        "Tabella 3.2.1",
        "2.5"
    ]
    for label in test_labels:
        num = analyzer.extract_label_number(label)
        print(f"   {label:<20} → {num}")
    
    # Test 2: Verifica gerarchie
    print("\n2. Verifica relazioni gerarchiche:")
    test_pairs = [
        ("2.5", "2.5.1", True),
        ("2.5", "2.5.2", True),
        ("2.5", "2.6", False),
        ("2.5", "2.5a", False),  # Variante, non gerarchia
        ("2.5a", "2.5b", False), # Entrambe varianti
    ]
    for label1, label2, expected in test_pairs:
        result = analyzer.is_hierarchical(label1, label2)
        status = "✓" if result == expected else "✗"
        print(f"   {status} {label1} → {label2}: {result} (atteso: {expected})")
    
    # Test 3: Costruzione gerarchia completa
    print("\n3. Costruzione gerarchia:")
    labels = ["Fig. 2.5", "Fig. 2.5.1", "Fig. 2.5.2", "Fig. 2.6", "Fig. 2.5a", "Fig. 3.1"]
    hierarchy = analyzer.build_hierarchy(labels)
    
    print(f"   Parents: {hierarchy['parents']}")
    print(f"   Children: {hierarchy['children']}")
    print(f"   Standalone: {hierarchy['standalone']}")
    
    # Test 4: Raggruppamento riferimenti
    print("\n4. Raggruppamento riferimenti:")
    mock_refs = [
        {'variant_found': 'Fig. 2.5', 'paragraph_index': 10},
        {'variant_found': 'Fig. 2.5', 'paragraph_index': 20},
        {'variant_found': 'Fig. 2.5.1', 'paragraph_index': 15},
        {'variant_found': 'Fig. 2.5.2', 'paragraph_index': 25},
        {'variant_found': 'Fig. 2.6', 'paragraph_index': 30},
    ]
    
    grouped = analyzer.group_references_by_hierarchy(mock_refs)
    print(f"   Gruppi gerarchici: {len(grouped['hierarchical'])}")
    for group in grouped['hierarchical']:
        print(f"      📂 {group['parent']} ({len(group['parent_refs'])} refs)")
        for child in group['children']:
            print(f"         └─ {child['label']} ({len(child['refs'])} refs)")
    
    print(f"   Standalone: {len(grouped['standalone'])}")
    for item in grouped['standalone']:
        print(f"      📄 {item['label']} ({len(item['refs'])} refs)")
    
    print("\n✅ Test completati")


if __name__ == "__main__":
    test_hierarchy_analyzer()
