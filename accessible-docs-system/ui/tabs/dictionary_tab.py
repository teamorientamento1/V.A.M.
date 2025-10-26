from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QLineEdit, QTextEdit, QGroupBox, QComboBox)
from PyQt6.QtGui import QFont


class DictionaryTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.symbols_dict = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Dizionario Simboli")
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Descrizione
        desc = QLabel("Gestisci la pronuncia dei simboli matematici per sintesi vocale")
        desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(desc)
        
        # Sezione aggiunta simbolo
        add_group = QGroupBox("Aggiungi/Modifica Simbolo")
        add_layout = QHBoxLayout()
        
        add_layout.addWidget(QLabel("Simbolo:"))
        self.symbol_input = QLineEdit()
        self.symbol_input.setMaximumWidth(100)
        self.symbol_input.setPlaceholderText("es. α")
        add_layout.addWidget(self.symbol_input)
        
        add_layout.addWidget(QLabel("Pronuncia:"))
        self.pronunciation_input = QLineEdit()
        self.pronunciation_input.setPlaceholderText("es. alpha")
        add_layout.addWidget(self.pronunciation_input)
        
        add_layout.addWidget(QLabel("Categoria:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Lettere Greche",
            "Operatori",
            "Apici/Pedici",
            "Simboli Speciali",
            "Altro"
        ])
        add_layout.addWidget(self.category_combo)
        
        self.btn_add = QPushButton("Aggiungi")
        self.btn_add.clicked.connect(self.add_symbol)
        add_layout.addWidget(self.btn_add)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Lista simboli salvati
        symbols_group = QGroupBox("Simboli Salvati")
        symbols_layout = QVBoxLayout()
        
        self.symbols_list = QListWidget()
        self.symbols_list.itemClicked.connect(self.on_symbol_selected)
        symbols_layout.addWidget(self.symbols_list)
        
        # Pulsanti gestione
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Modifica")
        self.btn_edit.clicked.connect(self.edit_symbol)
        self.btn_delete = QPushButton("Elimina")
        self.btn_delete.clicked.connect(self.delete_symbol)
        self.btn_export = QPushButton("Esporta Dizionario")
        
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_export)
        symbols_layout.addLayout(btn_layout)
        
        symbols_group.setLayout(symbols_layout)
        layout.addWidget(symbols_group)
        
        # Stats
        self.stats_label = QLabel("Simboli nel dizionario: 0")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
        # Carica simboli predefiniti
        self.load_default_symbols()
    
    def load_default_symbols(self):
        """Carica simboli predefiniti comuni"""
        defaults = {
            'α': ('alpha', 'Lettere Greche'),
            'β': ('beta', 'Lettere Greche'),
            'γ': ('gamma', 'Lettere Greche'),
            'Δ': ('delta maiuscola', 'Lettere Greche'),
            '∑': ('sommatoria', 'Operatori'),
            '∫': ('integrale', 'Operatori'),
            '∂': ('derivata parziale', 'Operatori'),
            '√': ('radice quadrata', 'Operatori'),
            '≈': ('circa uguale', 'Simboli Speciali'),
            '≠': ('diverso', 'Simboli Speciali'),
            '≤': ('minore o uguale', 'Simboli Speciali'),
            '≥': ('maggiore o uguale', 'Simboli Speciali'),
        }
        
        for symbol, (pronunciation, category) in defaults.items():
            self.symbols_dict[symbol] = {'pronunciation': pronunciation, 'category': category}
            self.symbols_list.addItem(f"{symbol} → {pronunciation} ({category})")
        
        self.update_stats()
    
    def add_symbol(self):
        symbol = self.symbol_input.text().strip()
        pronunciation = self.pronunciation_input.text().strip()
        category = self.category_combo.currentText()
        
        if not symbol or not pronunciation:
            return
        
        self.symbols_dict[symbol] = {'pronunciation': pronunciation, 'category': category}
        self.symbols_list.addItem(f"{symbol} → {pronunciation} ({category})")
        
        self.symbol_input.clear()
        self.pronunciation_input.clear()
        self.update_stats()
    
    def on_symbol_selected(self, item):
        text = item.text()
        symbol = text.split(' → ')[0]
        
        if symbol in self.symbols_dict:
            self.symbol_input.setText(symbol)
            self.pronunciation_input.setText(self.symbols_dict[symbol]['pronunciation'])
            idx = self.category_combo.findText(self.symbols_dict[symbol]['category'])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
    
    def edit_symbol(self):
        self.add_symbol()  # Sovrascrive
    
    def delete_symbol(self):
        current = self.symbols_list.currentItem()
        if current:
            symbol = current.text().split(' → ')[0]
            if symbol in self.symbols_dict:
                del self.symbols_dict[symbol]
                self.symbols_list.takeItem(self.symbols_list.row(current))
                self.update_stats()
    
    def update_stats(self):
        self.stats_label.setText(f"Simboli nel dizionario: {len(self.symbols_dict)}")
