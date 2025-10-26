import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt

from ui.tabs.load_tab import LoadTab
from ui.tabs.analysis_tab import AnalysisTab
from ui.tabs.images_tab import ImagesTab
from ui.tabs.formulas_tab import FormulasTab
from ui.tabs.dictionary_tab import DictionaryTab
from ui.tabs.jump_tab import JumpTab
from ui.tabs.export_tab import ExportTab

from core.knowledge_base import KnowledgeBase
from core.sync_manager import SyncManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kb = KnowledgeBase()
        self.sync_manager = SyncManager()  # Inizializza sync manager
        self.current_document = None
        self.analysis_results = None
        self.analyzer = None  # Riferimento all'analyzer
        
        self.setWindowTitle("Sistema Documenti Accessibili")
        self.setGeometry(100, 100, 1200, 800)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Schede
        self.load_tab = LoadTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.images_tab = ImagesTab(self)
        self.formulas_tab = FormulasTab(self)
        self.dictionary_tab = DictionaryTab(self)
        self.jump_tab = JumpTab(self)
        self.export_tab = ExportTab(self)
        
        self.tabs.addTab(self.load_tab, "Carica Documento")
        self.tabs.addTab(self.analysis_tab, "Analisi")
        self.tabs.addTab(self.images_tab, "Immagini")
        self.tabs.addTab(self.formulas_tab, "Formule")
        self.tabs.addTab(self.dictionary_tab, "Dizionario")
        self.tabs.addTab(self.jump_tab, "Jump Manager")
        self.tabs.addTab(self.export_tab, "Esporta")
        
        # Disabilita schede fino al caricamento
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, False)
    
    def on_document_loaded(self, doc_path):
        self.current_document = doc_path
        self.tabs.setTabEnabled(1, True)
        
    def on_analysis_complete(self, results):
        self.analysis_results = results
        for i in range(2, self.tabs.count()):
            self.tabs.setTabEnabled(i, True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
