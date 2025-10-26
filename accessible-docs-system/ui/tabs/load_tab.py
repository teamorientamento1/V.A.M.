from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFileDialog, QMessageBox, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.document_analyzer import WordAnalyzer
from core.project_manager import ProjectManager


class LoadTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.analyzer = None
        self.project_manager = ProjectManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Carica Documento o Progetto")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # === CARICA DOCUMENTO ===
        doc_group = QGroupBox("Nuovo Documento")
        doc_layout = QVBoxLayout()
        
        doc_info = QLabel("Carica un nuovo documento Word per iniziare l'analisi e la creazione di jump.")
        doc_info.setWordWrap(True)
        doc_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc_layout.addWidget(doc_info)
        
        self.btn_load = QPushButton("📄 Seleziona File .docx")
        self.btn_load.setMinimumSize(250, 60)
        self.btn_load.setStyleSheet("background: #3498db; color: white; font-weight: bold; font-size: 12pt;")
        self.btn_load.clicked.connect(self.load_document)
        doc_layout.addWidget(self.btn_load)
        
        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)
        
        # Separatore
        layout.addWidget(QLabel("─" * 80))
        
        # === CARICA PROGETTO ===
        project_group = QGroupBox("Progetto Esistente")
        project_layout = QVBoxLayout()
        
        project_info = QLabel(
            "Carica un progetto salvato in precedenza per continuare il lavoro.\n"
            "Il progetto contiene documento e tutti i jump già creati."
        )
        project_info.setWordWrap(True)
        project_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        project_layout.addWidget(project_info)
        
        self.btn_load_project = QPushButton("📦 Carica Progetto .zip")
        self.btn_load_project.setMinimumSize(250, 60)
        self.btn_load_project.setStyleSheet("background: #2ecc71; color: white; font-weight: bold; font-size: 12pt;")
        self.btn_load_project.clicked.connect(self.load_project)
        project_layout.addWidget(self.btn_load_project)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        # === INFO CARICAMENTO ===
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setPlaceholderText("Le informazioni sul documento/progetto appariranno qui...")
        layout.addWidget(self.info_text)
        
        self.btn_analyze = QPushButton("▶ Analizza Documento")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setMinimumHeight(50)
        self.btn_analyze.setStyleSheet("background: #e74c3c; color: white; font-weight: bold; font-size: 12pt;")
        self.btn_analyze.clicked.connect(self.analyze_document)
        layout.addWidget(self.btn_analyze)
        
        self.setLayout(layout)
    
    def load_document(self):
        """Carica nuovo documento"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Documento", "", "Word Files (*.docx)"
        )
        
        if file_path:
            try:
                self.analyzer = WordAnalyzer(self.main_window.kb)
                self.analyzer.load_document(file_path)
                
                self.main_window.analyzer = self.analyzer
                
                info = f"📄 DOCUMENTO CARICATO\n\n"
                info += f"File: {file_path}\n\n"
                info += "Premi 'Analizza Documento' per iniziare l'elaborazione."
                
                self.info_text.setText(info)
                self.btn_analyze.setEnabled(True)
                self.main_window.on_document_loaded(file_path)
                
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile caricare documento:\n{str(e)}")
    
    def load_project(self):
        """Carica progetto esistente"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Progetto", "", "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            # Carica progetto
            project_data = self.project_manager.load_project(file_path)
            
            if not project_data:
                raise Exception("Errore nel caricamento del progetto")
            
            # Carica documento dal progetto
            doc_path = project_data['document_path']
            self.analyzer = WordAnalyzer(self.main_window.kb)
            self.analyzer.load_document(doc_path)
            self.main_window.analyzer = self.analyzer
            
            # Ripristina risultati analisi
            self.main_window.analysis_results = project_data['analysis_results']
            
            # Info
            info = f"📦 PROGETTO CARICATO\n\n"
            info += f"Nome: {project_data['document_name']}\n"
            info += f"Versione: {project_data['version']}\n"
            info += f"Salvato: {project_data['metadata']['save_date'][:10]}\n\n"
            
            stats = project_data.get('statistics', {})
            info += "Contenuto:\n"
            info += f"  • Immagini: {stats.get('total_images', 0)}\n"
            info += f"  • Tabelle: {stats.get('total_tables', 0)}\n"
            info += f"  • Equazioni: {stats.get('total_equations', 0)}\n"
            info += f"  • Jump creati: {stats.get('jumps_created', 0)}\n\n"
            info += "Progetto caricato! Puoi continuare il lavoro."
            
            self.info_text.setText(info)
            
            # Abilita schede
            self.main_window.on_document_loaded(doc_path)
            self.main_window.on_analysis_complete(project_data['analysis_results'])
            
            # Popola schede
            if hasattr(self.main_window, 'analysis_tab'):
                self.main_window.analysis_tab.display_results(project_data['analysis_results'])
            
            if hasattr(self.main_window, 'images_tab') and 'images' in project_data['analysis_results']:
                self.main_window.images_tab.load_images(project_data['analysis_results']['images'])
            
            if hasattr(self.main_window, 'formulas_tab') and 'equations' in project_data['analysis_results']:
                self.main_window.formulas_tab.load_equations(project_data['analysis_results']['equations'])
            
            if hasattr(self.main_window, 'jump_tab'):
                self.main_window.jump_tab.load_elements(project_data['analysis_results'])
            
            # TODO: Ripristina jump creati
            
            # Cleanup
            # self.project_manager.cleanup_temp_project(project_data['temp_dir'])
            
            QMessageBox.information(
                self,
                "Successo",
                "Progetto caricato con successo!\nPuoi continuare il lavoro dalle altre schede."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare progetto:\n{str(e)}")
    
    def analyze_document(self):
        """Analizza documento"""
        if self.analyzer:
            try:
                results = self.analyzer.analyze()
                self.main_window.on_analysis_complete(results)
                
                if hasattr(self.main_window, 'analysis_tab'):
                    self.main_window.analysis_tab.display_results(results)
                
                if hasattr(self.main_window, 'images_tab') and 'images' in results:
                    self.main_window.images_tab.load_images(results['images'])
                
                if hasattr(self.main_window, 'formulas_tab') and 'equations' in results:
                    self.main_window.formulas_tab.load_equations(results['equations'])
                
                if hasattr(self.main_window, 'jump_tab'):
                    self.main_window.jump_tab.load_elements(results)
                
                QMessageBox.information(self, "Successo", "Analisi completata!")
                
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'analisi:\n{str(e)}")
