"""
Symbol Dictionary - Gestisce simboli e la loro pronuncia per TTS
"""
from typing import Dict, List, Optional
import json
from pathlib import Path

from config.settings import *
from core.knowledge_base import KnowledgeBase


class SymbolDictionary:
    """
    Gestisce dizionario di simboli e mappature per sintesi vocale
    
    Permette di:
    - Identificare tutti i simboli in un documento
    - Personalizzare pronuncia per ogni simbolo
    - Gestire pronuncia context-aware (es. 'd' in 'dx' vs 'd' variabile)
    - Salvare preferenze studente
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.user_preferences = {}
        self.context_rules = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """
        Carica mappature di default per simboli comuni
        """
        self.default_mappings = {
            # Lettere greche
            'α': 'alfa',
            'β': 'beta', 
            'γ': 'gamma',
            'δ': 'delta',
            'ε': 'epsilon',
            'θ': 'theta',
            'λ': 'lambda',
            'μ': 'mu',
            'π': 'pi',
            'σ': 'sigma',
            'τ': 'tau',
            'φ': 'phi',
            'ω': 'omega',
            
            # Operatori
            '∫': 'integrale',
            '∑': 'sommatoria',
            '∏': 'produttoria',
            '∂': 'derivata parziale',
            '∇': 'nabla',
            '√': 'radice quadrata',
            '∞': 'infinito',
            
            # Relazioni
            '≤': 'minore o uguale',
            '≥': 'maggiore o uguale',
            '≠': 'diverso',
            '≈': 'circa uguale',
            '∈': 'appartiene',
            '∉': 'non appartiene',
            '⊂': 'contenuto',
            '⊆': 'contenuto o uguale',
            
            # Logica
            '∀': 'per ogni',
            '∃': 'esiste',
            '∧': 'e logico',
            '∨': 'o logico',
            '¬': 'non',
            '⇒': 'implica',
            '⇔': 'se e solo se',
            
            # Altro
            '°': 'gradi',
            '±': 'più o meno',
            '×': 'per',
            '÷': 'diviso',
            '·': 'punto',
        }
    
    def scan_document_symbols(self, document_analysis: Dict) -> Dict:
        """
        Scansiona documento e identifica tutti i simboli usati
        
        Args:
            document_analysis: Output del WordAnalyzer
        
        Returns:
            Dict con simboli trovati e loro occorrenze
        """
        symbols_found = {}
        
        # 1. Scansiona equazioni
        for eq in document_analysis.get('equations', []):
            text = eq.get('text_representation', '')
            symbols = self._extract_symbols_from_text(text)
            
            for symbol in symbols:
                if symbol not in symbols_found:
                    symbols_found[symbol] = {
                        'count': 0,
                        'contexts': [],
                        'in_equations': True,
                        'current_pronunciation': self._get_pronunciation(symbol)
                    }
                symbols_found[symbol]['count'] += 1
                symbols_found[symbol]['contexts'].append({
                    'type': 'equation',
                    'context': eq.get('context_before', '')[:50]
                })
        
        # 2. Scansiona testo normale
        # TODO: Implementare scan del testo per simboli
        
        return symbols_found
    
    def _extract_symbols_from_text(self, text: str) -> List[str]:
        """
        Estrae simboli speciali da un testo
        """
        symbols = []
        
        for char in text:
            # Considera simbolo se:
            # - È in default_mappings
            # - È unicode non-ASCII (simbolo matematico/greco)
            if char in self.default_mappings or (ord(char) > 127 and not char.isalnum()):
                if char not in symbols:
                    symbols.append(char)
        
        return symbols
    
    def _get_pronunciation(self, symbol: str, context: Optional[str] = None) -> str:
        """
        Ottiene la pronuncia di un simbolo
        
        Priorità:
        1. User preference (context-specific)
        2. User preference (generale)
        3. Context rule
        4. Default mapping
        5. Fallback a spelling
        """
        # 1. User preference context-specific
        if context and symbol in self.user_preferences:
            for pref in self.user_preferences[symbol]:
                if pref.get('context_pattern') and pref['context_pattern'] in context:
                    return pref['pronunciation']
        
        # 2. User preference generale
        if symbol in self.user_preferences:
            for pref in self.user_preferences[symbol]:
                if not pref.get('context_pattern'):
                    return pref['pronunciation']
        
        # 3. Context rule
        if context and symbol in self.context_rules:
            # TODO: Implementare matching context rules
            pass
        
        # 4. Default
        if symbol in self.default_mappings:
            return self.default_mappings[symbol]
        
        # 5. Fallback
        return f"simbolo {symbol}"
    
    def set_pronunciation(self, symbol: str, pronunciation: str, 
                         context_pattern: Optional[str] = None,
                         save_to_kb: bool = True):
        """
        Imposta pronuncia personalizzata per un simbolo
        
        Args:
            symbol: Il simbolo
            pronunciation: Come pronunciarlo
            context_pattern: Pattern opzionale per pronuncia context-specific
            save_to_kb: Se salvare nel knowledge base
        """
        if symbol not in self.user_preferences:
            self.user_preferences[symbol] = []
        
        pref = {
            'pronunciation': pronunciation,
            'context_pattern': context_pattern,
            'created_at': datetime.now().isoformat()
        }
        
        self.user_preferences[symbol].append(pref)
        
        if save_to_kb:
            self.kb.update_symbol_pronunciation(
                symbol=symbol,
                pronunciation=pronunciation,
                context=context_pattern,
                user_preference=True
            )
        
        print(f"Pronuncia impostata: {symbol} → {pronunciation}")
    
    def batch_update_symbols(self, symbols_dict: Dict[str, str]):
        """
        Aggiorna pronuncia di multipli simboli in batch
        
        Args:
            symbols_dict: {symbol: pronunciation}
        """
        for symbol, pronunciation in symbols_dict.items():
            self.set_pronunciation(symbol, pronunciation)
        
        print(f"Aggiornati {len(symbols_dict)} simboli")
    
    def create_tts_mapping_file(self, symbols_list: List[str], 
                               output_path: Path) -> None:
        """
        Crea file di mapping per software TTS
        
        Formato: symbol\tpronunciation
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Symbol to Speech Mapping\n")
            f.write("# symbol\tpronunciation\n")
            
            for symbol in symbols_list:
                pronunciation = self._get_pronunciation(symbol)
                f.write(f"{symbol}\t{pronunciation}\n")
        
        print(f"File mapping TTS creato: {output_path}")
    
    def identify_subscripts_superscripts(self, text: str) -> Dict:
        """
        Identifica apici e pedici in un testo
        
        Returns:
            Dict con posizioni e contenuti di apici/pedici
        """
        # TODO: Implementare
        # Cercare caratteri unicode subscript/superscript
        # O analizzare struttura XML delle equazioni
        
        result = {
            'subscripts': [],
            'superscripts': []
        }
        
        return result
    
    def apply_subscript_superscript_rules(self, element) -> str:
        """
        Applica regole di pronuncia per apici/pedici
        
        Es: x₁ → "x pedice 1"
            x² → "x al quadrato" o "x alla seconda"
        """
        # TODO: Implementare regole smart
        # - "al quadrato" per ²
        # - "al cubo" per ³
        # - "alla n-esima" per numeri
        # - "pedice/apice" + pronuncia per altri casi
        
        pass
    
    def load_user_preferences(self, filepath: Path):
        """Carica preferenze utente da file JSON"""
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                self.user_preferences = json.load(f)
            print(f"Preferenze caricate: {len(self.user_preferences)} simboli")
    
    def save_user_preferences(self, filepath: Path):
        """Salva preferenze utente su file JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
        print(f"Preferenze salvate: {filepath}")
    
    def get_statistics(self) -> Dict:
        """Ottiene statistiche sul dizionario"""
        return {
            'default_symbols': len(self.default_mappings),
            'user_customized': len(self.user_preferences),
            'context_rules': len(self.context_rules),
            'total_managed': len(self.default_mappings) + len(self.user_preferences)
        }
    
    def suggest_pronunciations(self, symbol: str) -> List[str]:
        """
        Suggerisce possibili pronuncie per un simbolo
        basandosi sul knowledge base
        """
        # Query al KB per vedere come altri hanno pronunciato questo simbolo
        # TODO: Implementare con query al KB
        
        suggestions = []
        
        # Fallback: suggerisci default se esiste
        if symbol in self.default_mappings:
            suggestions.append(self.default_mappings[symbol])
        
        return suggestions
