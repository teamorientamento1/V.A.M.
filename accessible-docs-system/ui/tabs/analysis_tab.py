from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit)
from PyQt6.QtGui import QFont


class AnalysisTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Risultati Analisi")
        title.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        self.setLayout(layout)
    
    def display_results(self, results):
        text = "=== ANALISI DOCUMENTO COMPLETATA ===\n\n"
        
        # Immagini
        if 'images' in results and results['images']:
            text += f"📷 IMMAGINI: {len(results['images'])}\n"
            for i, img in enumerate(results['images'][:10], 1):
                label = img.get('label', 'N/A')
                para = img.get('paragraph_index', 'N/A')
                text += f"  {i}. {label} - Paragrafo {para}\n"
            if len(results['images']) > 10:
                text += f"  ... e altre {len(results['images']) - 10}\n"
            text += "\n"
        
        # Tabelle
        if 'tables' in results and results['tables']:
            text += f"📊 TABELLE: {len(results['tables'])}\n"
            for i, table in enumerate(results['tables'][:10], 1):
                try:
                    rows = table.get('rows', [])
                    if isinstance(rows, list) and rows:
                        num_rows = len(rows)
                        first_row = rows[0]
                        num_cols = len(first_row) if isinstance(first_row, list) else 0
                        text += f"  {i}. {num_rows}x{num_cols} - Paragrafo {table.get('paragraph_index', 'N/A')}\n"
                    else:
                        text += f"  {i}. Tabella - Paragrafo {table.get('paragraph_index', 'N/A')}\n"
                except:
                    text += f"  {i}. Tabella - Paragrafo {table.get('paragraph_index', 'N/A')}\n"
            if len(results['tables']) > 10:
                text += f"  ... e altre {len(results['tables']) - 10}\n"
            text += "\n"
        
        # Equazioni
        if 'equations' in results and results['equations']:
            text += f"🧮 EQUAZIONI: {len(results['equations'])}\n"
            for i, eq in enumerate(results['equations'][:10], 1):
                eq_text = str(eq.get('text_representation', 'N/A'))[:40]
                para = eq.get('paragraph_index', 'N/A')
                text += f"  {i}. {eq_text}... - Paragrafo {para}\n"
            if len(results['equations']) > 10:
                text += f"  ... e altre {len(results['equations']) - 10}\n"
            text += "\n"
        
        # Riferimenti
        if 'references' in results and results['references']:
            text += f"🔗 RIFERIMENTI: {len(results['references'])}\n"
            ref_types = {}
            for ref in results['references']:
                ref_type = ref.get('type', 'unknown')
                ref_types[ref_type] = ref_types.get(ref_type, 0) + 1
            
            for ref_type, count in ref_types.items():
                text += f"  - {ref_type}: {count}\n"
            text += "\n"
        
        # Statistiche generali
        text += "=== STATISTICHE ===\n"
        total = 0
        for key in ['images', 'tables', 'equations']:
            if key in results and isinstance(results[key], list):
                total += len(results[key])
        text += f"Elementi totali analizzati: {total}\n"
        
        self.results_text.setText(text)
