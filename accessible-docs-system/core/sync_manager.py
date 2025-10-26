"""
Sync Manager - Gestisce sincronizzazione tra schede
"""

from datetime import datetime


class SyncManager:
    """Gestisce i dirty flags per sincronizzazione tra schede"""
    
    def __init__(self):
        self.dirty_flags = {
            'images': False,
            'tables': False,
            'equations': False,
            'all': False
        }
        
        self.timestamps = {
            'images': None,
            'tables': None,
            'equations': None
        }
        
        self.modified_elements = {
            'images': [],
            'tables': [],
            'equations': []
        }
    
    def mark_dirty(self, tab_name):
        """Segna una scheda come modificata"""
        if tab_name in self.dirty_flags:
            self.dirty_flags[tab_name] = True
            self.timestamps[tab_name] = datetime.now()
    
    def is_dirty(self, tab_name):
        """Verifica se una scheda è stata modificata"""
        return self.dirty_flags.get(tab_name, False)
    
    def clear_dirty(self, tab_name):
        """Pulisce il flag di modifica"""
        if tab_name in self.dirty_flags:
            self.dirty_flags[tab_name] = False
    
    def clear_all(self):
        """Pulisce tutti i flag"""
        for key in self.dirty_flags:
            self.dirty_flags[key] = False
    
    def get_last_modified(self, tab_name):
        """Ottiene timestamp ultima modifica"""
        return self.timestamps.get(tab_name)
    
    def add_modified_element(self, tab_name, element_data):
        """Registra un elemento modificato"""
        if tab_name in self.modified_elements:
            self.modified_elements[tab_name].append({
                'element': element_data,
                'timestamp': datetime.now()
            })
    
    def get_modified_elements(self, tab_name):
        """Ottiene lista elementi modificati"""
        return self.modified_elements.get(tab_name, [])
    
    def clear_modified_elements(self, tab_name):
        """Pulisce lista elementi modificati"""
        if tab_name in self.modified_elements:
            self.modified_elements[tab_name] = []
    
    def has_any_changes(self):
        """Verifica se ci sono modifiche in qualsiasi scheda"""
        return any(self.dirty_flags.values())
    
    def get_dirty_tabs(self):
        """Ottiene lista schede modificate"""
        return [tab for tab, dirty in self.dirty_flags.items() if dirty]
