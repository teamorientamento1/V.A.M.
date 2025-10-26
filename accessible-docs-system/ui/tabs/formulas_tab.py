from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QTextEdit, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class FormulasTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.equations_data = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Formule ed Equazioni")
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("Equazioni nel documento:"))
        self.equations_list = QListWidget()
        self.equations_list.itemClicked.connect(self.on_equation_selected)
        left_layout.addWidget(self.equations_list)
        
        self.stats_label = QLabel("Totale: 0")
        left_layout.addWidget(self.stats_label)
        
        # Pulsanti modifica
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Modifica")
        self.btn_edit.clicked.connect(self.on_edit_equation)
        self.btn_delete = QPushButton("Elimina")
        self.btn_delete.clicked.connect(self.on_delete_equation)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        left_layout.addLayout(btn_layout)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        text_group = QGroupBox("Rappresentazione Testuale")
        text_layout = QVBoxLayout()
        self.equation_text = QTextEdit()
        self.equation_text.setReadOnly(True)
        self.equation_text.setMaximumHeight(100)
        text_layout.addWidget(self.equation_text)
        text_group.setLayout(text_layout)
        right_layout.addWidget(text_group)
        
        mathml_group = QGroupBox("MathML")
        mathml_layout = QVBoxLayout()
        self.mathml_text = QTextEdit()
        self.mathml_text.setReadOnly(True)
        mathml_layout.addWidget(self.mathml_text)
        mathml_group.setLayout(mathml_layout)
        right_layout.addWidget(mathml_group)
        
        info_group = QGroupBox("Informazioni")
        info_layout = QVBoxLayout()
        self.equation_info = QTextEdit()
        self.equation_info.setReadOnly(True)
        self.equation_info.setMaximumHeight(100)
        info_layout.addWidget(self.equation_info)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def load_equations(self, equations):
        self.equations_list.clear()
        self.equations_data = equations
        
        for i, eq in enumerate(equations, 1):
            text_repr = eq.get('text_representation', 'Equazione')[:50]
            para = eq.get('paragraph_index', 'N/A')
            self.equations_list.addItem(f"Eq.{i} - {text_repr}... (Par.{para})")
        
        self.stats_label.setText(f"Totale equazioni: {len(equations)}")
    
    def on_equation_selected(self, item):
        index = self.equations_list.row(item)
        if index >= len(self.equations_data):
            return
            
        eq_data = self.equations_data[index]
        
        self.equation_text.setText(eq_data.get('text_representation', 'N/A'))
        self.mathml_text.setText(eq_data.get('mathml', 'N/A'))
        
        # Context come lista
        context_before = eq_data.get('context_before', [])
        context_after = eq_data.get('context_after', [])
        
        if isinstance(context_before, list):
            before_text = '\n'.join(context_before)
        else:
            before_text = str(context_before)
        
        if isinstance(context_after, list):
            after_text = '\n'.join(context_after)
        else:
            after_text = str(context_after)
        
        info = f"""Posizione: Paragrafo {eq_data.get('paragraph_index', 'N/A')}
Categoria: {eq_data.get('category', 'generic')}

Contesto prima:
{before_text[:100]}...

Contesto dopo:
{after_text[:100]}...
"""
        self.equation_info.setText(info)
    
    def on_edit_equation(self):
        # TODO: implementare editing
        pass
    
    def on_delete_equation(self):
        """Elimina equazione e marca dirty"""
        index = self.equations_list.currentRow()
        if index >= 0:
            del self.equations_data[index]
            self.equations_list.takeItem(index)
            
            # Marca dirty per sync
            self.main_window.sync_manager.mark_dirty('equations')
            
            self.stats_label.setText(f"Totale equazioni: {len(self.equations_data)}")
