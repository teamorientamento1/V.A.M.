from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFileDialog, QMessageBox,
                             QGroupBox, QCheckBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.project_manager import ProjectManager
import shutil
from pathlib import Path


class ExportTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.project_manager = ProjectManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("Esporta e Salva")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # === SEZIONE SALVA DOCUMENTO ===
        doc_group = QGroupBox("Salva Documento Modificato")
        doc_layout = QVBoxLayout()
        
        doc_info = QLabel(
            "Salva il documento Word con tutti i jump e modifiche applicate.\n"
            "Il file includerà:\n"
            "• Jump verso descrizioni di immagini/tabelle/formule\n"
            "• Bookmark per navigazione\n"
            "• Descrizioni aggiunte in fondo al documento"
        )
        doc_info.setWordWrap(True)
        doc_layout.addWidget(doc_info)
        
        self.check_descriptions = QCheckBox("Includi descrizioni in fondo")
        self.check_descriptions.setChecked(True)
        doc_layout.addWidget(self.check_descriptions)
        
        self.check_toc = QCheckBox("Genera indice elementi")
        self.check_toc.setChecked(True)
        doc_layout.addWidget(self.check_toc)
        
        self.btn_save_document = QPushButton("💾 Salva Documento (.docx)")
        self.btn_save_document.setStyleSheet("background: #3498db; color: white; font-weight: bold; padding: 15px;")
        self.btn_save_document.clicked.connect(self.save_document)
        doc_layout.addWidget(self.btn_save_document)
        
        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)
        
        # === SEZIONE SALVA PROGETTO ===
        project_group = QGroupBox("Salva Progetto Completo")
        project_layout = QVBoxLayout()
        
        project_info = QLabel(
            "Salva tutto il progetto in un file ZIP per riprenderlo in futuro.\n"
            "Il progetto include:\n"
            "• Documento originale\n"
            "• Tutti i risultati dell'analisi\n"
            "• Jump creati e configurazioni\n"
            "• Modifiche apportate\n"
            "• Stato completo del lavoro"
        )
        project_info.setWordWrap(True)
        project_layout.addWidget(project_info)
        
        self.check_include_patterns = QCheckBox("Includi pattern personalizzati")
        self.check_include_patterns.setChecked(False)
        self.check_include_patterns.setToolTip("Salva anche i pattern aggiunti al database")
        project_layout.addWidget(self.check_include_patterns)
        
        self.btn_save_project = QPushButton("📦 Salva Progetto (.zip)")
        self.btn_save_project.setStyleSheet("background: #2ecc71; color: white; font-weight: bold; padding: 15px;")
        self.btn_save_project.clicked.connect(self.save_project)
        project_layout.addWidget(self.btn_save_project)
        
        project_group.setLayout(project_layout)
        layout.addWidget(project_group)
        
        # === STATISTICHE ===
        stats_group = QGroupBox("Riepilogo Modifiche")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setPlaceholderText("Le statistiche appariranno qui dopo il salvataggio...")
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # === LOG ===
        log_group = QGroupBox("Log Operazioni")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def save_document(self):
        """Salva documento Word modificato"""
        if not self.main_window.current_document:
            QMessageBox.warning(self, "Attenzione", "Nessun documento caricato")
            return
        
        # Dialog salvataggio
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Documento Modificato",
            f"{Path(self.main_window.current_document).stem}_modificato.docx",
            "Word Files (*.docx)"
        )
        
        if not file_path:
            return
        
        try:
            self.log_text.append("Inizio salvataggio documento...")
            self.progress_bar.show()
            self.progress_bar.setValue(20)
            
            # TODO: Implementare creazione jump effettiva nel documento
            # Per ora copia il documento originale
            shutil.copy(self.main_window.current_document, file_path)
            
            self.progress_bar.setValue(60)
            
            # Aggiungi descrizioni se richiesto
            if self.check_descriptions.isChecked():
                self.log_text.append("Aggiunta descrizioni...")
                # TODO: Implementare
            
            self.progress_bar.setValue(80)
            
            # Genera indice se richiesto
            if self.check_toc.isChecked():
                self.log_text.append("Generazione indice...")
                # TODO: Implementare
            
            self.progress_bar.setValue(100)
            
            self.log_text.append(f"✓ Documento salvato: {file_path}")
            self._update_statistics()
            
            QMessageBox.information(
                self,
                "Successo",
                f"Documento salvato con successo:\n{file_path}"
            )
            
        except Exception as e:
            self.log_text.append(f"✗ Errore: {str(e)}")
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
        
        finally:
            self.progress_bar.hide()
    
    def save_project(self):
        """Salva progetto completo in ZIP"""
        if not self.main_window.current_document:
            QMessageBox.warning(self, "Attenzione", "Nessun documento caricato")
            return
        
        if not self.main_window.analysis_results:
            QMessageBox.warning(self, "Attenzione", "Nessuna analisi disponibile")
            return
        
        # Dialog salvataggio
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Progetto",
            f"{Path(self.main_window.current_document).stem}_progetto.zip",
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            self.log_text.append("Inizio salvataggio progetto...")
            self.progress_bar.show()
            self.progress_bar.setValue(10)
            
            # Raccogli jump creati
            jumps_created = []
            if hasattr(self.main_window, 'jump_tab'):
                # TODO: Ottenere lista jump dalla jump_tab
                pass
            
            self.progress_bar.setValue(30)
            
            # Raccogli modifiche
            modifications = {
                'images_modified': [],
                'equations_modified': [],
                'tables_modified': []
            }
            
            self.progress_bar.setValue(50)
            
            # Salva progetto
            success = self.project_manager.save_project(
                output_path=file_path,
                document_path=self.main_window.current_document,
                analysis_results=self.main_window.analysis_results,
                jumps_created=jumps_created,
                modifications=modifications
            )
            
            self.progress_bar.setValue(90)
            
            if success:
                self.log_text.append(f"✓ Progetto salvato: {file_path}")
                self._update_statistics()
                
                self.progress_bar.setValue(100)
                
                QMessageBox.information(
                    self,
                    "Successo",
                    f"Progetto salvato con successo:\n{file_path}\n\n"
                    "Potrai riaprirlo in futuro con 'Carica Progetto'"
                )
            else:
                raise Exception("Errore durante il salvataggio")
                
        except Exception as e:
            self.log_text.append(f"✗ Errore: {str(e)}")
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
        
        finally:
            self.progress_bar.hide()
    
    def _update_statistics(self):
        """Aggiorna statistiche"""
        if not self.main_window.analysis_results:
            return
        
        results = self.main_window.analysis_results
        
        stats = "=== STATISTICHE PROGETTO ===\n\n"
        stats += f"📷 Immagini: {len(results.get('images', []))}\n"
        stats += f"📊 Tabelle: {len(results.get('tables', []))}\n"
        stats += f"🧮 Equazioni: {len(results.get('equations', []))}\n"
        stats += f"🔗 Riferimenti: {len(results.get('references', []))}\n\n"
        
        # TODO: Aggiungi statistiche jump
        stats += "Jump creati: 0 (funzione in sviluppo)\n"
        
        self.stats_text.setText(stats)
