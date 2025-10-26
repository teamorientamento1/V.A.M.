"""
Reference Detail Dialog - Popup per visualizzare riferimenti con highlight
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor


class ReferenceDetailDialog(QDialog):
    """Dialog per visualizzare dettagli riferimento"""
    
    def __init__(self, reference_data, parent=None):
        super().__init__(parent)
        self.reference_data = reference_data
        self.selected = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Dettaglio Riferimento")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Header con info
        header = QLabel(f"Riferimento: Paragrafo {self.reference_data['paragraph_index']}")
        header.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(header)
        
        info_label = QLabel(f"Trovato: '{self.reference_data['variant_found']}' (label originale: '{self.reference_data['original_label']}')")
        layout.addWidget(info_label)
        
        # Separatore
        layout.addWidget(QLabel("─" * 80))
        
        # Area testo con highlight
        context_label = QLabel("Contesto esteso:")
        context_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        layout.addWidget(context_label)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setMinimumHeight(200)
        layout.addWidget(self.text_display)
        
        # Mostra testo con highlight
        self._display_highlighted_text()
        
        # Checkbox selezione
        self.check_select = QCheckBox("Seleziona questo riferimento per creare jump")
        self.check_select.setChecked(False)
        layout.addWidget(self.check_select)
        
        # Pulsanti
        button_layout = QHBoxLayout()
        
        self.btn_visualize = QPushButton("📄 Visualizza nel Documento")
        self.btn_visualize.setToolTip("Apre la posizione nel documento originale")
        button_layout.addWidget(self.btn_visualize)
        
        self.btn_ok = QPushButton("✓ OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setDefault(True)
        button_layout.addWidget(self.btn_ok)
        
        self.btn_cancel = QPushButton("✗ Chiudi")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _display_highlighted_text(self):
        """Mostra testo con evidenziazione della label"""
        full_text = self.reference_data['full_text']
        variant_found = self.reference_data['variant_found']
        
        # Setup formato highlight
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0))  # Giallo
        highlight_format.setFontWeight(QFont.Weight.Bold)
        
        # Setup formato normale
        normal_format = QTextCharFormat()
        
        # Inserisci testo
        cursor = self.text_display.textCursor()
        
        # Trova posizione della variante nel testo
        start_pos = full_text.lower().find(variant_found.lower())
        
        if start_pos != -1:
            # Testo prima
            before_text = full_text[:start_pos]
            cursor.insertText(before_text, normal_format)
            
            # Variante evidenziata
            matched_text = full_text[start_pos:start_pos + len(variant_found)]
            cursor.insertText(matched_text, highlight_format)
            
            # Testo dopo
            after_text = full_text[start_pos + len(variant_found):]
            cursor.insertText(after_text, normal_format)
        else:
            # Fallback: mostra tutto normale
            cursor.insertText(full_text, normal_format)
        
        # Aggiungi contesto extra se disponibile
        context_before = self.reference_data.get('context_before', '')
        context_after = self.reference_data.get('context_after', '')
        
        if context_before or context_after:
            cursor.insertText("\n\n" + "─" * 50 + "\n", normal_format)
            cursor.insertText("Contesto aggiuntivo:\n\n", normal_format)
            
            if context_before:
                cursor.insertText(f"[...prima]: {context_before}\n", normal_format)
            if context_after:
                cursor.insertText(f"[...dopo]: {context_after}\n", normal_format)
    
    def is_selected(self):
        """Ritorna se il riferimento è selezionato"""
        return self.check_select.isChecked()
    
    def accept(self):
        """Override accept per salvare selezione"""
        self.selected = self.check_select.isChecked()
        super().accept()
