"""
Reference Patterns - Archivio pattern per ricerca riferimenti intelligente
"""

PATTERNS = {
    'figure': {
        'full': ['figura', 'figure', 'fig'],
        'abbrev': ['fig.', 'fig'],
        'singular': ['figura', 'figure'],
        'plural': ['figure', 'figures', 'figuras'],
        'languages': {
            'it': ['figura', 'figure', 'fig', 'fig.'],
            'en': ['figure', 'fig', 'fig.'],
            'es': ['figura', 'fig', 'fig.']
        }
    },
    'table': {
        'full': ['tabella', 'table', 'tab'],
        'abbrev': ['tab.', 'tab'],
        'singular': ['tabella', 'table', 'tabla'],
        'plural': ['tabelle', 'tables', 'tablas'],
        'languages': {
            'it': ['tabella', 'tabelle', 'tab', 'tab.'],
            'en': ['table', 'tab', 'tab.'],
            'es': ['tabla', 'tab', 'tab.']
        }
    },
    'equation': {
        'full': ['equazione', 'equation', 'eq'],
        'abbrev': ['eq.', 'eq'],
        'singular': ['equazione', 'equation', 'ecuación'],
        'plural': ['equazioni', 'equations', 'ecuaciones'],
        'languages': {
            'it': ['equazione', 'equazioni', 'eq', 'eq.'],
            'en': ['equation', 'eq', 'eq.'],
            'es': ['ecuación', 'eq', 'eq.']
        }
    },
    'graph': {
        'full': ['grafico', 'graph', 'gráfico'],
        'abbrev': ['graf.', 'graf'],
        'singular': ['grafico', 'graph', 'gráfico'],
        'plural': ['grafici', 'graphs', 'gráficos'],
        'languages': {
            'it': ['grafico', 'grafici', 'graf', 'graf.'],
            'en': ['graph', 'graf', 'graf.'],
            'es': ['gráfico', 'graf', 'graf.']
        }
    },
    'image': {
        'full': ['immagine', 'image', 'imagen'],
        'abbrev': ['img.', 'img'],
        'singular': ['immagine', 'image', 'imagen'],
        'plural': ['immagini', 'images', 'imágenes'],
        'languages': {
            'it': ['immagine', 'immagini', 'img', 'img.'],
            'en': ['image', 'img', 'img.'],
            'es': ['imagen', 'img', 'img.']
        }
    },
    'schema': {
        'full': ['schema', 'scheme', 'diagram'],
        'abbrev': ['sch.', 'sch'],
        'singular': ['schema', 'scheme', 'diagram'],
        'plural': ['schemi', 'schemes', 'diagrams'],
        'languages': {
            'it': ['schema', 'schemi', 'sch', 'sch.'],
            'en': ['scheme', 'diagram', 'sch', 'sch.'],
            'es': ['esquema', 'sch', 'sch.']
        }
    }
}


def get_all_variants(element_type='figure'):
    """Ottiene tutte le varianti per un tipo di elemento"""
    if element_type not in PATTERNS:
        return []
    
    pattern = PATTERNS[element_type]
    all_variants = set()
    
    # Aggiungi tutte le varianti
    all_variants.update(pattern.get('full', []))
    all_variants.update(pattern.get('abbrev', []))
    all_variants.update(pattern.get('singular', []))
    all_variants.update(pattern.get('plural', []))
    
    # Aggiungi varianti multilingua
    for lang_variants in pattern.get('languages', {}).values():
        all_variants.update(lang_variants)
    
    return list(all_variants)


def detect_element_type(label):
    """Rileva il tipo di elemento dalla label"""
    label_lower = label.lower()
    
    for elem_type, pattern in PATTERNS.items():
        all_variants = get_all_variants(elem_type)
        for variant in all_variants:
            if variant in label_lower:
                return elem_type
    
    return 'unknown'
