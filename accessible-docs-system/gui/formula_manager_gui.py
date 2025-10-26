"""
Formula Manager GUI
Interfaccia grafica per gestire database formule matematiche
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                             QLineEdit, QTextEdit, QComboBox, QSpinBox, QGroupBox,
                             QTabWidget, QFileDialog, QMessageBox, QDialog,
                             QDialogButtonBox, QCheckBox, QProgressBar, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

# Import core modules
from formula_database import FormulaDatabase
from formula_classifier import FormulaClassifier
from dlmf_importer import DLMFImporter
from arxiv_importer import ArxivImporter


class ImportWorker(QThread):
    """Thread per importazione formule in background"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    
    def __init__(self, importer_type, *args):
        super().__init__()
        self.importer_type = importer_type
        self.args = args
    
    def run(self):
        """Esegue importazione"""
        if self.importer_type == 'dlmf':
            importer = DLMFImporter()
            chapters = self.args[0]
            formulas = []
            for i, chapter in enumerate(chapters):
                self.progress.emit(int((i + 1) / len(chapters) * 100), 
                                 f"Importando capitolo {chapter}...")
                chapter_formulas = importer.import_chapter(chapter)
                formulas.extend(chapter_formulas)
            self.finished.emit(formulas)
            
        elif self.importer_type == 'arxiv':
            importer = ArxivImporter()
            arxiv_ids = self.args[0]
            formulas = []
            for i, arxiv_id in enumerate(arxiv_ids):
                self.progress.emit(int((i + 1) / len(arxiv_ids) * 100),
                                 f"Importando {arxiv_id}...")
                paper_formulas = importer.import_from_arxiv(arxiv_id)
                formulas.extend(paper_formulas)
            self.finished.emit(formulas)


class FormulaDetailsDialog(QDialog):
    """Dialog per dettagli/modifica formula"""
    
    def __init__(self, formula_data=None, parent=None):
        super().__init__(parent)
        self.formula_data = formula_data or {}
        self.setWindowTitle("Dettagli Formula")
        self.resize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # LaTeX
        layout.addWidget(QLabel("LaTeX:"))
        self.latex_edit = QTextEdit()
        self.latex_edit.setPlainText(self.formula_data.get('latex', ''))
        self.latex_edit.setMaximumHeight(100)
        layout.addWidget(self.latex_edit)
        
        # Nome
        layout.addWidget(QLabel("Nome:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.formula_data.get('name', ''))
        layout.addWidget(self.name_edit)
        
        # Descrizione
        layout.addWidget(QLabel("Descrizione:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.formula_data.get('description', ''))
        self.desc_edit.setMaximumHeight(80)
        layout.addWidget(self.desc_edit)
        
        # Categoria/Sottocategoria
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Categoria:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            'algebra', 'calculus', 'geometry', 'statistics',
            'number_theory', 'special_functions', 'physics', 'other'
        ])
        self.category_combo.setCurrentText(self.formula_data.get('category', 'other'))
        cat_layout.addWidget(self.category_combo)
        
        cat_layout.addWidget(QLabel("Sottocategoria:"))
        self.subcategory_edit = QLineEdit()
        self.subcategory_edit.setText(self.formula_data.get('subcategory', ''))
        cat_layout.addWidget(self.subcategory_edit)
        layout.addLayout(cat_layout)
        
        # Difficoltà
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficoltà (1-5):"))
        self.difficulty_spin = QSpinBox()
        self.difficulty_spin.setRange(1, 5)
        self.difficulty_spin.setValue(self.formula_data.get('difficulty', 1))
        diff_layout.addWidget(self.difficulty_spin)
        diff_layout.addStretch()
        layout.addLayout(diff_layout)
        
        # Source
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.source_edit = QLineEdit()
        self.source_edit.setText(self.formula_data.get('source', ''))
        source_layout.addWidget(self.source_edit)
        layout.addLayout(source_layout)
        
        # Verified
        self.verified_check = QCheckBox("Formula Verificata")
        self.verified_check.setChecked(self.formula_data.get('verified', False))
        layout.addWidget(self.verified_check)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_formula_data(self):
        """Ritorna dati formula modificati"""
        return {
            'latex': self.latex_edit.toPlainText(),
            'name': self.name_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'category': self.category_combo.currentText(),
            'subcategory': self.subcategory_edit.text(),
            'difficulty': self.difficulty_spin.value(),
            'source': self.source_edit.text(),
            'verified': self.verified_check.isChecked()
        }


class FormulaManagerGUI(QMainWindow):
    """GUI principale per gestione database formule"""
    
    def __init__(self):
        super().__init__()
        self.db = None
        self.classifier = FormulaClassifier()
        self.current_formulas = []
        
        self.setWindowTitle("Formula Database Manager")
        self.resize(1200, 800)
        self.init_ui()
        
        # Carica database default
        self.load_database("formulas.db")
    
    def init_ui(self):
        """Inizializza UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Toolbar superiore
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # Tab principale
        tabs = QTabWidget()
        tabs.addTab(self.create_browse_tab(), "📚 Sfoglia")
        tabs.addTab(self.create_add_tab(), "➕ Aggiungi")
        tabs.addTab(self.create_import_tab(), "📥 Importa")
        tabs.addTab(self.create_stats_tab(), "📊 Statistiche")
        layout.addLayout(toolbar)
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Pronto")
    
    def create_toolbar(self):
        """Crea toolbar superiore"""
        layout = QHBoxLayout()
        
        # Database path
        layout.addWidget(QLabel("Database:"))
        self.db_path_label = QLabel("formulas.db")
        self.db_path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.db_path_label)
        
        # Buttons
        btn_open = QPushButton("📂 Apri DB")
        btn_open.clicked.connect(self.open_database)
        layout.addWidget(btn_open)
        
        btn_new = QPushButton("🆕 Nuovo DB")
        btn_new.clicked.connect(self.new_database)
        layout.addWidget(btn_new)
        
        layout.addStretch()
        
        # Formula count
        self.count_label = QLabel("0 formule")
        layout.addWidget(self.count_label)
        
        return layout
    
    def create_browse_tab(self):
        """Tab per sfogliare formule"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtri ricerca
        filter_group = QGroupBox("Filtri")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Cerca:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nome o descrizione...")
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_edit)
        
        filter_layout.addWidget(QLabel("Categoria:"))
        self.filter_category = QComboBox()
        self.filter_category.addItems(['Tutte', 'algebra', 'calculus', 'geometry', 
                                       'statistics', 'number_theory', 'special_functions', 
                                       'physics', 'other'])
        self.filter_category.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_category)
        
        self.verified_only_check = QCheckBox("Solo verificate")
        self.verified_only_check.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.verified_only_check)
        
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self.apply_filters)
        filter_layout.addWidget(btn_refresh)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Tabella formule
        self.formulas_table = QTableWidget()
        self.formulas_table.setColumnCount(7)
        self.formulas_table.setHorizontalHeaderLabels([
            'ID', 'Nome', 'LaTeX (preview)', 'Categoria', 'Sottocategoria', 
            'Difficoltà', 'Verificata'
        ])
        self.formulas_table.setColumnWidth(2, 300)
        self.formulas_table.doubleClicked.connect(self.edit_formula)
        layout.addWidget(self.formulas_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_edit = QPushButton("✏️ Modifica")
        btn_edit.clicked.connect(self.edit_formula)
        btn_layout.addWidget(btn_edit)
        
        btn_delete = QPushButton("🗑️ Elimina")
        btn_delete.clicked.connect(self.delete_formula)
        btn_layout.addWidget(btn_delete)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_add_tab(self):
        """Tab per aggiungere formule"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Form
        form_group = QGroupBox("Nuova Formula")
        form_layout = QVBoxLayout()
        
        # LaTeX
        form_layout.addWidget(QLabel("LaTeX:"))
        self.add_latex = QTextEdit()
        self.add_latex.setPlaceholderText(r"\int_a^b f(x)\,dx = F(b) - F(a)")
        self.add_latex.setMaximumHeight(100)
        form_layout.addWidget(self.add_latex)
        
        # Auto-classify button
        btn_classify = QPushButton("🤖 Classifica Automaticamente")
        btn_classify.clicked.connect(self.auto_classify)
        form_layout.addWidget(btn_classify)
        
        # Nome
        form_layout.addWidget(QLabel("Nome:"))
        self.add_name = QLineEdit()
        form_layout.addWidget(self.add_name)
        
        # Descrizione
        form_layout.addWidget(QLabel("Descrizione:"))
        self.add_description = QTextEdit()
        self.add_description.setMaximumHeight(80)
        form_layout.addWidget(self.add_description)
        
        # Categoria
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Categoria:"))
        self.add_category = QComboBox()
        self.add_category.addItems(['algebra', 'calculus', 'geometry', 'statistics',
                                   'number_theory', 'special_functions', 'physics', 'other'])
        cat_layout.addWidget(self.add_category)
        
        cat_layout.addWidget(QLabel("Sottocategoria:"))
        self.add_subcategory = QLineEdit()
        cat_layout.addWidget(self.add_subcategory)
        form_layout.addLayout(cat_layout)
        
        # Difficoltà
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficoltà:"))
        self.add_difficulty = QSpinBox()
        self.add_difficulty.setRange(1, 5)
        self.add_difficulty.setValue(1)
        diff_layout.addWidget(self.add_difficulty)
        diff_layout.addStretch()
        form_layout.addLayout(diff_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Aggiungi al Database")
        btn_add.clicked.connect(self.add_formula)
        btn_add.setStyleSheet("font-weight: bold; padding: 10px;")
        btn_layout.addWidget(btn_add)
        
        btn_clear = QPushButton("🧹 Pulisci")
        btn_clear.clicked.connect(self.clear_add_form)
        btn_layout.addWidget(btn_clear)
        form_layout.addLayout(btn_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addStretch()
        
        return widget
    
    def create_import_tab(self):
        """Tab per importare formule da archivi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # DLMF Import
        dlmf_group = QGroupBox("📚 Importa da DLMF")
        dlmf_layout = QVBoxLayout()
        dlmf_layout.addWidget(QLabel("Seleziona capitoli da importare:"))
        
        self.dlmf_chapters = QLineEdit()
        self.dlmf_chapters.setPlaceholderText("Es: 5,6,10 (Gamma, Exp/Log, Bessel)")
        dlmf_layout.addWidget(self.dlmf_chapters)
        
        btn_dlmf = QPushButton("📥 Importa da DLMF")
        btn_dlmf.clicked.connect(self.import_dlmf)
        dlmf_layout.addWidget(btn_dlmf)
        
        dlmf_group.setLayout(dlmf_layout)
        layout.addWidget(dlmf_group)
        
        # arXiv Import
        arxiv_group = QGroupBox("📄 Importa da arXiv")
        arxiv_layout = QVBoxLayout()
        arxiv_layout.addWidget(QLabel("Inserisci arXiv ID (separati da virgola):"))
        
        self.arxiv_ids = QLineEdit()
        self.arxiv_ids.setPlaceholderText("Es: 2301.12345, math/0601001")
        arxiv_layout.addWidget(self.arxiv_ids)
        
        btn_arxiv = QPushButton("📥 Importa da arXiv")
        btn_arxiv.clicked.connect(self.import_arxiv)
        arxiv_layout.addWidget(btn_arxiv)
        
        arxiv_group.setLayout(arxiv_layout)
        layout.addWidget(arxiv_group)
        
        # Progress bar
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)
        
        self.import_status = QLabel("")
        layout.addWidget(self.import_status)
        
        layout.addStretch()
        
        return widget
    
    def create_stats_tab(self):
        """Tab statistiche"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.stats_text)
        
        btn_refresh = QPushButton("🔄 Aggiorna Statistiche")
        btn_refresh.clicked.connect(self.update_stats)
        layout.addWidget(btn_refresh)
        
        return widget
    
    def load_database(self, path: str):
        """Carica database"""
        if self.db:
            self.db.close()
        
        self.db = FormulaDatabase(path)
        self.db_path_label.setText(path)
        self.apply_filters()
        self.update_stats()
        self.statusBar().showMessage(f"Database caricato: {path}")
    
    def open_database(self):
        """Apre database esistente"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri Database", "", "Database (*.db)"
        )
        if path:
            self.load_database(path)
    
    def new_database(self):
        """Crea nuovo database"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Nuovo Database", "formulas.db", "Database (*.db)"
        )
        if path:
            self.load_database(path)
    
    def apply_filters(self):
        """Applica filtri e aggiorna tabella"""
        query = self.search_edit.text()
        category = self.filter_category.currentText()
        verified_only = self.verified_only_check.isChecked()
        
        # Ricerca
        self.current_formulas = self.db.search_formulas(
            query=query if query else None,
            category=category if category != 'Tutte' else None,
            verified_only=verified_only,
            limit=1000
        )
        
        # Aggiorna tabella
        self.formulas_table.setRowCount(len(self.current_formulas))
        
        for i, formula in enumerate(self.current_formulas):
            self.formulas_table.setItem(i, 0, QTableWidgetItem(str(formula['id'])))
            self.formulas_table.setItem(i, 1, QTableWidgetItem(formula.get('name', '')))
            
            # LaTeX preview (primi 50 char)
            latex_preview = formula['latex'][:50] + "..." if len(formula['latex']) > 50 else formula['latex']
            self.formulas_table.setItem(i, 2, QTableWidgetItem(latex_preview))
            
            self.formulas_table.setItem(i, 3, QTableWidgetItem(formula['category']))
            self.formulas_table.setItem(i, 4, QTableWidgetItem(formula.get('subcategory', '')))
            self.formulas_table.setItem(i, 5, QTableWidgetItem(str(formula['difficulty'])))
            self.formulas_table.setItem(i, 6, QTableWidgetItem('✓' if formula['verified'] else ''))
        
        self.count_label.setText(f"{len(self.current_formulas)} formule")
    
    def auto_classify(self):
        """Classifica automaticamente formula"""
        latex = self.add_latex.toPlainText()
        if not latex:
            return
        
        result = self.classifier.classify(latex)
        
        self.add_category.setCurrentText(result.category)
        self.add_subcategory.setText(result.subcategory)
        self.add_difficulty.setValue(result.difficulty)
        
        # Mostra risultato
        QMessageBox.information(
            self,
            "Classificazione Automatica",
            f"Categoria: {result.category}/{result.subcategory}\n"
            f"Confidenza: {result.confidence:.2%}\n"
            f"Difficoltà: {result.difficulty}/5\n"
            f"Tags suggeriti: {', '.join(result.suggested_tags)}\n\n"
            f"Reasoning: {result.reasoning}"
        )
    
    def add_formula(self):
        """Aggiunge formula al database"""
        latex = self.add_latex.toPlainText()
        if not latex:
            QMessageBox.warning(self, "Errore", "Inserisci LaTeX")
            return
        
        formula_id = self.db.add_formula(
            latex=latex,
            name=self.add_name.text() or None,
            description=self.add_description.toPlainText() or None,
            category=self.add_category.currentText(),
            subcategory=self.add_subcategory.text() or None,
            difficulty=self.add_difficulty.value()
        )
        
        if formula_id:
            QMessageBox.information(self, "Successo", f"Formula aggiunta con ID {formula_id}")
            self.clear_add_form()
            self.apply_filters()
        else:
            QMessageBox.warning(self, "Errore", "Formula già esistente")
    
    def clear_add_form(self):
        """Pulisce form aggiunta"""
        self.add_latex.clear()
        self.add_name.clear()
        self.add_description.clear()
        self.add_subcategory.clear()
        self.add_difficulty.setValue(1)
    
    def edit_formula(self):
        """Modifica formula selezionata"""
        row = self.formulas_table.currentRow()
        if row < 0:
            return
        
        formula = self.current_formulas[row]
        
        dialog = FormulaDetailsDialog(formula, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Aggiorna database (TODO: implementa update in FormulaDatabase)
            QMessageBox.information(self, "Info", "Modifica non ancora implementata nel database")
    
    def delete_formula(self):
        """Elimina formula selezionata"""
        row = self.formulas_table.currentRow()
        if row < 0:
            return
        
        formula = self.current_formulas[row]
        
        reply = QMessageBox.question(
            self, "Conferma",
            f"Eliminare formula '{formula.get('name', formula['id'])}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: implementa delete in FormulaDatabase
            QMessageBox.information(self, "Info", "Eliminazione non ancora implementata")
    
    def import_dlmf(self):
        """Importa da DLMF"""
        chapters_text = self.dlmf_chapters.text()
        if not chapters_text:
            QMessageBox.warning(self, "Errore", "Inserisci numeri capitoli")
            return
        
        chapters = [c.strip() for c in chapters_text.split(',')]
        
        self.import_progress.setVisible(True)
        self.import_progress.setValue(0)
        
        # Avvia worker thread
        self.import_worker = ImportWorker('dlmf', chapters)
        self.import_worker.progress.connect(self.update_import_progress)
        self.import_worker.finished.connect(self.import_finished)
        self.import_worker.start()
    
    def import_arxiv(self):
        """Importa da arXiv"""
        ids_text = self.arxiv_ids.text()
        if not ids_text:
            QMessageBox.warning(self, "Errore", "Inserisci arXiv IDs")
            return
        
        ids = [id.strip() for id in ids_text.split(',')]
        
        self.import_progress.setVisible(True)
        self.import_progress.setValue(0)
        
        self.import_worker = ImportWorker('arxiv', ids)
        self.import_worker.progress.connect(self.update_import_progress)
        self.import_worker.finished.connect(self.import_finished)
        self.import_worker.start()
    
    def update_import_progress(self, value, status):
        """Aggiorna progress bar import"""
        self.import_progress.setValue(value)
        self.import_status.setText(status)
    
    def import_finished(self, formulas):
        """Import completato"""
        self.import_progress.setVisible(False)
        
        if not formulas:
            QMessageBox.warning(self, "Import", "Nessuna formula trovata")
            return
        
        # Importa in database
        count = 0
        for formula in formulas:
            formula_id = self.db.add_formula(**formula, verified=True)
            if formula_id:
                count += 1
        
        QMessageBox.information(
            self, "Import Completato",
            f"Importate {count} formule su {len(formulas)}\n"
            f"Duplicate: {len(formulas) - count}"
        )
        
        self.apply_filters()
        self.update_stats()
    
    def update_stats(self):
        """Aggiorna statistiche"""
        stats = self.db.get_statistics()
        
        text = "=" * 60 + "\n"
        text += "STATISTICHE DATABASE FORMULE\n"
        text += "=" * 60 + "\n\n"
        
        text += f"Totale formule: {stats['total_formulas']}\n"
        text += f"Formule verificate: {stats['verified_formulas']}\n\n"
        
        text += "Per categoria:\n"
        for cat, count in stats['by_category'].items():
            text += f"  {cat}: {count}\n"
        
        text += "\nPer difficoltà:\n"
        for diff, count in stats['by_difficulty'].items():
            text += f"  Livello {diff}: {count}\n"
        
        self.stats_text.setPlainText(text)
    
    def closeEvent(self, event):
        """Chiude database alla chiusura"""
        if self.db:
            self.db.close()
        event.accept()


def main():
    """Avvia GUI"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = FormulaManagerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
