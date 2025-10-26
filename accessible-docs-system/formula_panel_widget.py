"""
Formula Panel Widget
Widget PyQt6 da integrare nel Jump Manager per ricerca formule
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QTextEdit, QComboBox, QGroupBox, QSplitter,
                             QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from jump_manager_formula_enhancer import JumpManagerFormulaEnhancer


class FormulaSearchPanel(QWidget):
    """
    Panel ricerca formule da integrare nel Jump Manager
    Emette signal quando formula selezionata per inserimento
    """
    
    # Signal emesso quando utente vuole usare una formula
    formula_selected = pyqtSignal(dict)  # Emette dict con info formula
    
    def __init__(self, db_path: str = "formulas.db", parent=None):
        super().__init__(parent)
        self.enhancer = JumpManagerFormulaEnhancer(db_path)
        self.current_results = []
        self.init_ui()
    
    def init_ui(self):
        """Inizializza UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("🔍 Ricerca Formule Database")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Filtri ricerca
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Cerca:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nome o descrizione formula...")
        self.search_input.returnPressed.connect(self.search_formulas)
        search_layout.addWidget(self.search_input)
        
        search_layout.addWidget(QLabel("Categoria:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            'Tutte', 'algebra', 'calculus', 'geometry', 'statistics',
            'number_theory', 'special_functions', 'physics', 'other'
        ])
        self.category_filter.currentTextChanged.connect(self.search_formulas)
        search_layout.addWidget(self.category_filter)
        
        btn_search = QPushButton("🔍 Cerca")
        btn_search.clicked.connect(self.search_formulas)
        search_layout.addWidget(btn_search)
        
        layout.addLayout(search_layout)
        
        # Splitter per risultati + dettagli
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tabella risultati
        results_group = QGroupBox("Risultati")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            'Nome', 'Categoria', 'Difficoltà', 'LaTeX Preview', 'Verificata'
        ])
        self.results_table.setColumnWidth(0, 200)
        self.results_table.setColumnWidth(3, 300)
        self.results_table.itemSelectionChanged.connect(self.on_formula_selected)
        self.results_table.doubleClicked.connect(self.use_selected_formula)
        results_layout.addWidget(self.results_table)
        
        self.result_count_label = QLabel("0 formule trovate")
        results_layout.addWidget(self.result_count_label)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        # Dettagli formula selezionata
        details_group = QGroupBox("Dettagli Formula")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        # Buttons azioni
        btn_layout = QHBoxLayout()
        
        btn_use = QPushButton("✅ Usa Questa Formula")
        btn_use.clicked.connect(self.use_selected_formula)
        btn_use.setStyleSheet("font-weight: bold; padding: 8px;")
        btn_layout.addWidget(btn_use)
        
        btn_copy_latex = QPushButton("📋 Copia LaTeX")
        btn_copy_latex.clicked.connect(self.copy_latex)
        btn_layout.addWidget(btn_copy_latex)
        
        btn_layout.addStretch()
        details_layout.addLayout(btn_layout)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
        # Ricerca iniziale
        self.search_formulas()
    
    def search_formulas(self):
        """Esegue ricerca formule"""
        query = self.search_input.text()
        category = self.category_filter.currentText()
        
        self.current_results = self.enhancer.search_formulas_for_ui(
            query=query if query else None,
            category=category,
            max_results=50
        )
        
        self.update_results_table()
    
    def update_results_table(self):
        """Aggiorna tabella risultati"""
        self.results_table.setRowCount(len(self.current_results))
        
        for i, formula in enumerate(self.current_results):
            # Nome
            self.results_table.setItem(i, 0, QTableWidgetItem(formula.get('name', 'N/A')))
            
            # Categoria
            cat = f"{formula['category']}/{formula.get('subcategory', '')}"
            self.results_table.setItem(i, 1, QTableWidgetItem(cat))
            
            # Difficoltà
            diff_stars = '⭐' * formula['difficulty']
            self.results_table.setItem(i, 2, QTableWidgetItem(diff_stars))
            
            # LaTeX preview
            self.results_table.setItem(i, 3, QTableWidgetItem(formula.get('latex_preview', '')))
            
            # Verificata
            verified = '✓' if formula.get('verified') else ''
            self.results_table.setItem(i, 4, QTableWidgetItem(verified))
        
        self.result_count_label.setText(f"{len(self.current_results)} formule trovate")
        
        # Clear dettagli
        self.details_text.clear()
    
    def on_formula_selected(self):
        """Handler selezione formula"""
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.current_results):
            return
        
        formula = self.current_results[row]
        
        # Mostra dettagli
        details = []
        details.append(f"📌 Nome: {formula.get('name', 'N/A')}")
        details.append(f"📚 Categoria: {formula['category']} / {formula.get('subcategory', 'N/A')}")
        details.append(f"⭐ Difficoltà: {formula['difficulty']}/5")
        details.append(f"✅ Verificata: {'Sì' if formula.get('verified') else 'No'}")
        
        if formula.get('source'):
            details.append(f"🔗 Fonte: {formula['source']}")
        
        details.append(f"\n📐 LaTeX:")
        details.append(formula['latex'])
        
        if formula.get('description'):
            details.append(f"\n📝 Descrizione:")
            details.append(formula['description'])
        
        self.details_text.setPlainText('\n'.join(details))
    
    def use_selected_formula(self):
        """Emette signal per usare formula selezionata"""
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Attenzione", "Seleziona una formula prima")
            return
        
        row = selected_rows[0].row()
        formula = self.current_results[row]
        
        # Emetti signal
        self.formula_selected.emit(formula)
        
        QMessageBox.information(
            self, 
            "Formula Selezionata",
            f"Formula '{formula.get('name', 'N/A')}' pronta per l'uso!"
        )
    
    def copy_latex(self):
        """Copia LaTeX negli appunti"""
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        formula = self.current_results[row]
        
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(formula['latex'])
        
        QMessageBox.information(self, "Copiato", "LaTeX copiato negli appunti!")
    
    def closeEvent(self, event):
        """Chiude enhancer"""
        self.enhancer.close()
        event.accept()


class FormulaSuggestionWidget(QWidget):
    """
    Widget compatto per suggerimenti formula inline
    Mostra suggerimento descrizione mentre utente crea salto
    """
    
    def __init__(self, db_path: str = "formulas.db", parent=None):
        super().__init__(parent)
        self.enhancer = JumpManagerFormulaEnhancer(db_path)
        self.current_suggestion = None
        self.init_ui()
    
    def init_ui(self):
        """Inizializza UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("💡 Suggerimento Automatico")
        header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(header)
        
        self.confidence_label = QLabel("")
        self.confidence_label.setStyleSheet("color: gray; font-size: 9pt;")
        header_layout.addWidget(self.confidence_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Area suggerimento
        self.suggestion_text = QTextEdit()
        self.suggestion_text.setReadOnly(True)
        self.suggestion_text.setMaximumHeight(100)
        self.suggestion_text.setStyleSheet("background-color: #ffffcc; border: 1px solid #cccc99;")
        layout.addWidget(self.suggestion_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_use = QPushButton("✅ Usa Suggerimento")
        btn_use.clicked.connect(self.use_suggestion)
        btn_layout.addWidget(btn_use)
        
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self.refresh_suggestion)
        btn_layout.addWidget(btn_refresh)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.hide()  # Nascosto fino a quando non c'è LaTeX da analizzare
    
    def analyze_latex(self, latex: str):
        """
        Analizza LaTeX e mostra suggerimento
        
        Args:
            latex: LaTeX da analizzare
        """
        if not latex or len(latex) < 5:
            self.hide()
            return
        
        # Ottieni suggerimento
        self.current_suggestion = self.enhancer.suggest_description_for_jump(latex)
        
        # Mostra
        self.show()
        self.update_suggestion_display()
    
    def update_suggestion_display(self):
        """Aggiorna display suggerimento"""
        if not self.current_suggestion:
            return
        
        # Confidenza
        confidence = self.current_suggestion['confidence']
        confidence_text = f"Confidenza: {confidence:.0%}"
        if confidence > 0.8:
            confidence_color = "green"
        elif confidence > 0.5:
            confidence_color = "orange"
        else:
            confidence_color = "red"
        self.confidence_label.setText(f"<span style='color: {confidence_color};'>{confidence_text}</span>")
        
        # Descrizione
        text = []
        text.append(f"📝 {self.current_suggestion['description']}")
        text.append(f"\n📚 Categoria: {self.current_suggestion['category']}")
        text.append(f"⭐ Difficoltà: {self.current_suggestion['difficulty']}/5")
        
        if self.current_suggestion['has_match']:
            best_match = self.current_suggestion['similar_formulas'][0]
            text.append(f"\n✅ Match trovato: {best_match.get('name', 'N/A')} ({best_match['similarity_score']:.0%})")
        
        self.suggestion_text.setPlainText('\n'.join(text))
    
    def use_suggestion(self):
        """Signal per usare suggerimento"""
        if not self.current_suggestion:
            return
        
        # Ritorna descrizione suggerita (da connettere al campo descrizione Jump Manager)
        return self.current_suggestion['description']
    
    def refresh_suggestion(self):
        """Forza refresh suggerimento"""
        # Clear cache e ri-analizza
        # (implementare se necessario)
        pass
    
    def get_current_description(self) -> str:
        """Ritorna descrizione corrente suggerita"""
        if self.current_suggestion:
            return self.current_suggestion['description']
        return ""
    
    def closeEvent(self, event):
        """Chiude enhancer"""
        self.enhancer.close()
        event.accept()


class BatchEnrichDialog(QWidget):
    """
    Dialog per arricchire batch di salti
    Mostra progress e statistiche
    """
    
    finished = pyqtSignal(list, dict)  # (jumps_enriched, stats)
    
    def __init__(self, jumps: list, db_path: str = "formulas.db", parent=None):
        super().__init__(parent)
        self.jumps = jumps
        self.enhancer = JumpManagerFormulaEnhancer(db_path)
        self.enriched_jumps = []
        self.stats = {}
        
        self.setWindowTitle("Arricchimento Salti")
        self.resize(500, 200)
        self.init_ui()
    
    def init_ui(self):
        """Inizializza UI"""
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"Arricchimento di {len(self.jumps)} salti..."))
        
        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.jumps))
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Preparazione...")
        layout.addWidget(self.status_label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        layout.addWidget(self.stats_text)
        
        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.close)
        btn_close.setEnabled(False)
        self.btn_close = btn_close
        layout.addWidget(btn_close)
        
        self.setLayout(layout)
    
    def start_enrichment(self):
        """Avvia processo arricchimento"""
        def progress_callback(current, total, status):
            self.progress_bar.setValue(current)
            self.status_label.setText(status)
        
        # Arricchisci
        self.enriched_jumps, self.stats = self.enhancer.enrich_all_jumps(
            self.jumps,
            progress_callback=progress_callback
        )
        
        # Mostra statistiche
        stats_text = []
        stats_text.append(f"✅ Arricchimento completato!")
        stats_text.append(f"\nTotale salti: {self.stats['total']}")
        stats_text.append(f"Arricchiti: {self.stats['enriched']}")
        stats_text.append(f"Con match database: {self.stats['with_match']}")
        stats_text.append(f"Senza LaTeX: {self.stats['no_latex']}")
        if self.stats['errors'] > 0:
            stats_text.append(f"⚠️ Errori: {self.stats['errors']}")
        
        self.stats_text.setPlainText('\n'.join(stats_text))
        self.status_label.setText("Completato!")
        self.btn_close.setEnabled(True)
        
        # Emetti signal
        self.finished.emit(self.enriched_jumps, self.stats)
    
    def closeEvent(self, event):
        """Chiude enhancer"""
        self.enhancer.close()
        event.accept()


if __name__ == "__main__":
    # Test widget standalone
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test FormulaSearchPanel
    panel = FormulaSearchPanel()
    panel.setWindowTitle("Test Formula Search Panel")
    panel.resize(800, 600)
    
    def on_formula_selected(formula):
        print(f"Formula selezionata: {formula.get('name')}")
        print(f"LaTeX: {formula['latex']}")
    
    panel.formula_selected.connect(on_formula_selected)
    panel.show()
    
    sys.exit(app.exec())
