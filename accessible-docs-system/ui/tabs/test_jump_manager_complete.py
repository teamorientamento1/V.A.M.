from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QTextEdit, QSplitter, QGroupBox,
                             QListWidgetItem, QMessageBox, QCheckBox, QLineEdit,
                             QTreeWidget, QTreeWidgetItem, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
import io
from PIL import Image
from core.reference_finder import search_references_in_document
from ui.dialogs.reference_detail_dialog import ReferenceDetailDialog
from ui.dialogs.pattern_manager_dialog import PatternManagerDialog
from modules.jump_manager.image_pattern_manager import ImagePatternManager


class JumpTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.elements_data = []
        self.filtered_elements = []
        self.current_element = None
        self.current_references = []
        self.current_filter = 'all'
        self.pattern_manager = ImagePatternManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # === BANNER WARNING ===
        self.warning_banner = QFrame()
        self.warning_banner.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        warning_layout = QHBoxLayout()
        self.warning_label = QLabel("⚠ Modifiche in corso in altre schede. Clicca per aggiornare.")
        self.warning_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.warning_label.setStyleSheet("color: #856404;")
        warning_layout.addWidget(self.warning_label)
        
        self.btn_warning_refresh = QPushButton("🔄 Aggiorna Ora")
        self.btn_warning_refresh.setStyleSheet("background: #ffc107; font-weight: bold;")
        self.btn_warning_refresh.clicked.connect(self.refresh_from_other_tabs)
        warning_layout.addWidget(self.btn_warning_refresh)
        
        self.warning_banner.setLayout(warning_layout)
        self.warning_banner.hide()
        layout.addWidget(self.warning_banner)
        
        # === SPLITTER PRINCIPALE ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_filters_panel()
        splitter.addWidget(left_panel)
        
        center_panel = self.create_preview_panel()
        splitter.addWidget(center_panel)
        
        right_panel = self.create_config_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([200, 550, 450])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def create_filters_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Filtri")
        title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # === INDICATORE AGGIORNAMENTO ===
        self.update_indicator = QLabel("✓ Aggiornato")
        self.update_indicator.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.update_indicator)
        
        self.filter_tree = QTreeWidget()
        self.filter_tree.setHeaderHidden(True)
        self.filter_tree.itemClicked.connect(self.on_filter_changed)
        
        self.filter_all = QTreeWidgetItem(["Tutti (0)"])
        self.filter_tree.addTopLevelItem(self.filter_all)
        
        self.filter_images = QTreeWidgetItem(["▼ Immagini (0)"])
        self.filter_tree.addTopLevelItem(self.filter_images)
        
        self.filter_tables = QTreeWidgetItem(["▼ Tabelle (0)"])
        self.filter_tree.addTopLevelItem(self.filter_tables)
        
        self.filter_equations = QTreeWidgetItem(["▼ Equazioni (0)"])
        self.filter_tree.addTopLevelItem(self.filter_equations)
        
        self.filter_eq_matrix = QTreeWidgetItem(["Matrici (0)"])
        self.filter_eq_super = QTreeWidgetItem(["Apici/Pedici (0)"])
        self.filter_eq_frac = QTreeWidgetItem(["Frazioni (0)"])
        self.filter_eq_int = QTreeWidgetItem(["Integrali (0)"])
        self.filter_eq_other = QTreeWidgetItem(["Altro (0)"])
        
        self.filter_equations.addChildren([
            self.filter_eq_matrix,
            self.filter_eq_super,
            self.filter_eq_frac,
            self.filter_eq_int,
            self.filter_eq_other
        ])
        
        layout.addWidget(self.filter_tree)
        
        self.stats_label = QLabel("0 elementi")
        layout.addWidget(self.stats_label)
        
        # Lista elementi
        self.elements_list = QListWidget()
        self.elements_list.itemClicked.connect(self.on_element_clicked)
        layout.addWidget(self.elements_list)
        
        panel.setLayout(layout)
        return panel
    
    def create_preview_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        group_before = QGroupBox("Testo prima (5 righe)")
        layout_before = QVBoxLayout()
        self.text_before = QTextEdit()
        self.text_before.setReadOnly(True)
        self.text_before.setMaximumHeight(150)
        layout_before.addWidget(self.text_before)
        group_before.setLayout(layout_before)
        layout.addWidget(group_before)
        
        group_preview = QGroupBox("Preview Elemento")
        layout_preview = QVBoxLayout()
        
        self.element_preview = QLabel("Seleziona un elemento")
        self.element_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.element_preview.setMinimumHeight(300)
        self.element_preview.setStyleSheet("border: 2px solid #ccc; background: #f9f9f9;")
        self.element_preview.setWordWrap(True)
        layout_preview.addWidget(self.element_preview)
        
        self.adjacent_warning = QLabel()
        self.adjacent_warning.setStyleSheet("color: #ff6600; font-weight: bold;")
        self.adjacent_warning.hide()
        layout_preview.addWidget(self.adjacent_warning)
        
        group_preview.setLayout(layout_preview)
        layout.addWidget(group_preview)
        
        group_after = QGroupBox("Testo dopo (5 righe)")
        layout_after = QVBoxLayout()
        self.text_after = QTextEdit()
        self.text_after.setReadOnly(True)
        self.text_after.setMaximumHeight(150)
        layout_after.addWidget(self.text_after)
        group_after.setLayout(layout_after)
        layout.addWidget(group_after)
        
        panel.setLayout(layout)
        return panel
    
    def create_config_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        self.element_info = QLabel("Tipo: - | Label: - | Par: -")
        self.element_info.setStyleSheet("padding: 5px; background: #e8e8e8;")
        layout.addWidget(self.element_info)
        
        group_search = QGroupBox("Ricerca Riferimenti")
        layout_search = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cerca:"))
        self.search_label_input = QLineEdit()
        self.search_label_input.setPlaceholderText("Fig.2.5")
        search_layout.addWidget(self.search_label_input)
        
        self.btn_search = QPushButton("🔍 Trova")
        self.btn_search.clicked.connect(self.search_references)
        search_layout.addWidget(self.btn_search)
        layout_search.addLayout(search_layout)
        
        # === PULSANTI GESTIONE PATTERN ===
        pattern_buttons = QHBoxLayout()
        
        self.btn_add_pattern = QPushButton("➕ Aggiungi Nome")
        self.btn_add_pattern.setToolTip("Aggiungi il nome corrente all'elenco dei nomi riconosciuti")
        self.btn_add_pattern.setStyleSheet("background: #4CAF50; color: white;")
        self.btn_add_pattern.clicked.connect(self.quick_add_pattern)
        pattern_buttons.addWidget(self.btn_add_pattern)
        
        self.btn_manage_patterns = QPushButton("⚙️ Gestisci Nomi")
        self.btn_manage_patterns.setToolTip("Visualizza e gestisci tutti i nomi delle immagini")
        self.btn_manage_patterns.clicked.connect(self.open_pattern_manager)
        pattern_buttons.addWidget(self.btn_manage_patterns)
        
        layout_search.addLayout(pattern_buttons)
        
        self.search_results_label = QLabel("")
        layout_search.addWidget(self.search_results_label)
        
        self.references_list = QListWidget()
        self.references_list.setMaximumHeight(150)
        self.references_list.itemDoubleClicked.connect(self.show_reference_detail)
        self.references_list.hide()
        layout_search.addWidget(self.references_list)
        
        hint_label = QLabel("💡 Doppio-click su riferimento per visualizzare dettagli")
        hint_label.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        hint_label.hide()
        self.hint_label = hint_label
        layout_search.addWidget(hint_label)
        
        ref_buttons = QHBoxLayout()
        self.btn_select_all_refs = QPushButton("✓ Seleziona Tutti")
        self.btn_select_all_refs.clicked.connect(self.select_all_references)
        self.btn_select_all_refs.hide()
        ref_buttons.addWidget(self.btn_select_all_refs)
        
        self.btn_create_refs = QPushButton("Crea Jump Selezionati")
        self.btn_create_refs.clicked.connect(self.create_reference_jumps)
        self.btn_create_refs.hide()
        ref_buttons.addWidget(self.btn_create_refs)
        layout_search.addLayout(ref_buttons)
        
        self.btn_edit_individual = QPushButton("Modifica Descrizioni")
        self.btn_edit_individual.clicked.connect(self.edit_individual_descriptions)
        self.btn_edit_individual.hide()
        layout_search.addWidget(self.btn_edit_individual)
        
        group_search.setLayout(layout_search)
        layout.addWidget(group_search)
        
        group_link = QGroupBox("Configurazione Link")
        layout_link = QVBoxLayout()
        
        link_layout = QHBoxLayout()
        link_layout.addWidget(QLabel("Testo link:"))
        self.link_text_input = QLineEdit()
        self.link_text_input.setPlaceholderText("📖 Descrizione Fig.2.5")
        link_layout.addWidget(self.link_text_input)
        layout_link.addLayout(link_layout)
        
        layout_link.addWidget(QLabel("Descrizione completa:"))
        self.description_text = QTextEdit()
        self.description_text.setPlaceholderText("Descrivi dettagliatamente l'elemento...")
        self.description_text.setMinimumHeight(150)
        layout_link.addWidget(self.description_text)
        
        self.same_desc_check = QCheckBox("Usa stessa descrizione per tutti")
        self.same_desc_check.setChecked(True)
        self.same_desc_check.hide()
        layout_link.addWidget(self.same_desc_check)
        
        group_link.setLayout(layout_link)
        layout.addWidget(group_link)
        
        buttons_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("Anteprima")
        self.btn_preview.setEnabled(False)
        buttons_layout.addWidget(self.btn_preview)
        
        self.btn_create = QPushButton("✓ Crea Jump")
        self.btn_create.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        self.btn_create.setEnabled(False)
        self.btn_create.clicked.connect(self.create_jump)
        buttons_layout.addWidget(self.btn_create)
        
        self.btn_apply_all = QPushButton("Applica a Tutti")
        self.btn_apply_all.setEnabled(False)
        buttons_layout.addWidget(self.btn_apply_all)
        
        layout.addLayout(buttons_layout)
        
        group_summary = QGroupBox("Jump Creati")
        layout_summary = QVBoxLayout()
        self.jumps_summary = QTextEdit()
        self.jumps_summary.setReadOnly(True)
        self.jumps_summary.setMaximumHeight(80)
        layout_summary.addWidget(self.jumps_summary)
        group_summary.setLayout(layout_summary)
        layout.addWidget(group_summary)
        
        panel.setLayout(layout)
        return panel
    
    def showEvent(self, event):
        super().showEvent(event)
        self.check_sync()
    
    def check_sync(self):
        """Controlla se ci sono modifiche e mostra banner"""
        sync_mgr = self.main_window.sync_manager
        
        if sync_mgr.is_dirty('images') or sync_mgr.is_dirty('tables') or sync_mgr.is_dirty('equations'):
            self.warning_banner.show()
            self.update_indicator.setText("⚠ Aggiornamento disponibile")
            self.update_indicator.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.warning_banner.hide()
            self.update_indicator.setText("✓ Aggiornato")
            self.update_indicator.setStyleSheet("color: green; font-weight: bold;")
    
    def refresh_from_other_tabs(self):
        if hasattr(self.main_window, 'analysis_results'):
            self.load_elements(self.main_window.analysis_results)
            
            sync_mgr = self.main_window.sync_manager
            sync_mgr.clear_dirty('images')
            sync_mgr.clear_dirty('tables')
            sync_mgr.clear_dirty('equations')
            
            self.warning_banner.hide()
            self.update_indicator.setText("✓ Aggiornato")
            self.update_indicator.setStyleSheet("color: green; font-weight: bold;")
    
    def load_elements(self, analysis_results):
        self.elements_data = []
        
        if 'images' in analysis_results:
            for img in analysis_results['images']:
                img['elem_type'] = 'image'
                self.elements_data.append(img)
        
        if 'tables' in analysis_results:
            for table in analysis_results['tables']:
                table['elem_type'] = 'table'
                self.elements_data.append(table)
        
        if 'equations' in analysis_results:
            for eq in analysis_results['equations']:
                eq['elem_type'] = 'equation'
                self.elements_data.append(eq)
        
        self.update_filter_counts()
        self.apply_filter(self.current_filter)
    
    def update_filter_counts(self):
        images_count = sum(1 for e in self.elements_data if e.get('elem_type') == 'image')
        tables_count = sum(1 for e in self.elements_data if e.get('elem_type') == 'table')
        equations_count = sum(1 for e in self.elements_data if e.get('elem_type') == 'equation')
        
        self.filter_all.setText(0, f"Tutti ({len(self.elements_data)})")
        self.filter_images.setText(0, f"▼ Immagini ({images_count})")
        self.filter_tables.setText(0, f"▼ Tabelle ({tables_count})")
        self.filter_equations.setText(0, f"▼ Equazioni ({equations_count})")
        
        self.filter_eq_other.setText(0, f"Altro ({equations_count})")
    
    def on_filter_changed(self, item, column):
        """Applica filtro quando cliccato"""
        text = item.text(0)
        
        if "Tutti" in text:
            self.current_filter = 'all'
        elif "Immagini" in text:
            self.current_filter = 'image'
        elif "Tabelle" in text:
            self.current_filter = 'table'
        elif "Equazioni" in text or "Altro" in text:
            self.current_filter = 'equation'
        
        self.apply_filter(self.current_filter)
    
    def apply_filter(self, filter_type):
        """Filtra elementi per tipo"""
        self.elements_list.clear()
        self.filtered_elements = []
        
        for elem in self.elements_data:
            if filter_type == 'all' or elem.get('elem_type') == filter_type:
                self.filtered_elements.append(elem)
        
        for elem in self.filtered_elements:
            elem_type = elem.get('elem_type')
            label = elem.get('label', 'N/A')
            para = elem.get('paragraph_index', 'N/A')
            
            if elem_type == 'image':
                text = f"📷 {label} - Par.{para}"
            elif elem_type == 'table':
                text = f"📊 Tabella {para}"
            elif elem_type == 'equation':
                text = f"🧮 {str(label)[:30]}... - Par.{para}"
            else:
                text = f"{label} - Par.{para}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, elem)
            self.elements_list.addItem(item)
        
        self.stats_label.setText(f"{len(self.filtered_elements)} elementi")
    
    def on_element_clicked(self, item):
        element_data = item.data(Qt.ItemDataRole.UserRole)
        if element_data:
            self.on_element_selected(element_data)
    
    def on_element_selected(self, element_data):
        self.current_element = element_data.copy()
        elem_type = element_data.get('elem_type')
        
        label = element_data.get('label', 'N/A')
        para = element_data.get('paragraph_index', 'N/A')
        self.element_info.setText(f"Tipo: {elem_type.upper()} | Label: {label} | Par: {para}")
        
        self.show_context_text(element_data)
        
        if elem_type == 'image':
            self.show_image_preview(element_data)
        elif elem_type == 'table':
            self.show_table_preview(element_data)
        elif elem_type == 'equation':
            self.show_equation_preview(element_data)
        
        self.search_label_input.setText(str(label))
        self.link_text_input.setText(f"📖 Descrizione {label}")
        
        self.btn_create.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_apply_all.setEnabled(True)
    
    def show_context_text(self, element_data):
        if 'context_before' in element_data:
            before = element_data['context_before']
            if isinstance(before, list):
                self.text_before.setText('\n'.join(before))
            else:
                self.text_before.setText(str(before))
        else:
            self.text_before.setText("Contesto non disponibile")
        
        if 'context_after' in element_data:
            after = element_data['context_after']
            if isinstance(after, list):
                self.text_after.setText('\n'.join(after))
            else:
                self.text_after.setText(str(after))
        else:
            self.text_after.setText("Contesto non disponibile")
    
    def show_image_preview(self, img_data):
        try:
            if 'image_part' in img_data and img_data['image_part']:
                image_bytes = img_data['image_part'].blob
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                pil_image.thumbnail((500, 280), Image.Resampling.LANCZOS)
                
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                
                pixmap = QPixmap()
                pixmap.loadFromData(img_byte_arr.getvalue())
                self.element_preview.setPixmap(pixmap)
            else:
                self.element_preview.setText("Preview non disponibile")
        except Exception as e:
            self.element_preview.setText(f"Errore\n{str(e)}")
    
    def show_table_preview(self, table_data):
        text = "TABELLA\n\n"
        if 'rows' in table_data:
            for i, row in enumerate(table_data['rows'][:5]):
                text += f"Riga {i+1}: {' | '.join([str(c)[:20] for c in row[:5]])}\n"
            if len(table_data['rows']) > 5:
                text += f"\n... altre {len(table_data['rows'])-5} righe"
        self.element_preview.setText(text)
        self.element_preview.setPixmap(QPixmap())
    
    def show_equation_preview(self, eq_data):
        text = "EQUAZIONE\n\n"
        text += eq_data.get('text_representation', 'N/A')
        self.element_preview.setText(text)
        self.element_preview.setPixmap(QPixmap())
    
    def search_references(self):
        label = self.search_label_input.text().strip()
        if not label:
            return
        
        if hasattr(self.main_window, 'analyzer') and self.main_window.analyzer:
            doc = self.main_window.analyzer.document
            refs = search_references_in_document(doc, label)
            
            self.current_references = refs
            
            if refs:
                self.search_results_label.setText(f"✓ Trovati {len(refs)} riferimenti:")
                
                self.references_list.clear()
                self.references_list.show()
                self.hint_label.show()
                
                for ref in refs:
                    context = f"{ref['context_before'][-30:]}{ref['variant_found']}{ref['context_after'][:30]}"
                    item_text = f"□ Par.{ref['paragraph_index']}: ...{context}..."
                    item = QListWidgetItem(item_text)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    item.setData(Qt.ItemDataRole.UserRole, ref)
                    self.references_list.addItem(item)
                
                self.btn_select_all_refs.show()
                self.btn_create_refs.show()
                self.btn_edit_individual.show()
                self.same_desc_check.show()
            else:
                self.search_results_label.setText("Nessun riferimento trovato")
                self.references_list.hide()
                self.hint_label.hide()
                self.btn_select_all_refs.hide()
                self.btn_create_refs.hide()
                self.btn_edit_individual.hide()
                self.same_desc_check.hide()
    
    def show_reference_detail(self, item):
        """Mostra dialog dettaglio riferimento"""
        ref_data = item.data(Qt.ItemDataRole.UserRole)
        if not ref_data:
            return
        
        dialog = ReferenceDetailDialog(ref_data, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            if dialog.is_selected():
                item.setCheckState(Qt.CheckState.Checked)
    
    def select_all_references(self):
        for i in range(self.references_list.count()):
            item = self.references_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def create_reference_jumps(self):
        selected = []
        for i in range(self.references_list.count()):
            item = self.references_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(self.current_references[i])
        
        if not selected:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un riferimento")
            return
        
        description = self.description_text.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Attenzione", "Inserisci una descrizione")
            return
        
        QMessageBox.information(self, "Jump Creati", f"Creati {len(selected)} jump per riferimenti")
        
        label = self.search_label_input.text()
        summary = self.jumps_summary.toPlainText()
        summary += f"\n✓ {len(selected)} riferimenti a '{label}'"
        self.jumps_summary.setText(summary)
    
    def edit_individual_descriptions(self):
        QMessageBox.information(self, "Info", "Funzione in sviluppo")
    
    def create_jump(self):
        if not self.current_element:
            QMessageBox.warning(self, "Errore", "Nessun elemento selezionato")
            return
        
        description = self.description_text.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Errore", "Inserisci una descrizione")
            return
        
        label = self.current_element.get('label', 'Elemento')
        
        QMessageBox.information(self, "Jump Creato", f"Jump creato per: {label}")
        
        summary = self.jumps_summary.toPlainText()
        summary += f"\n✓ {label}: {description[:40]}..."
        self.jumps_summary.setText(summary)
        
        self.description_text.clear()
    
    def quick_add_pattern(self):
        """Aggiunge velocemente il nome corrente all'elenco dei pattern"""
        label = self.search_label_input.text().strip()
        
        if not label:
            QMessageBox.warning(
                self, 
                "Campo Vuoto", 
                "Inserisci prima un nome nel campo 'Cerca' (es: Esempio, Didascalia, Screenshot)"
            )
            return
        
        # Rimuovi numeri e spazi per ottenere il nome base
        import re
        base_name = re.sub(r'[0-9\.\s]+$', '', label).strip()
        
        if not base_name:
            QMessageBox.warning(
                self,
                "Nome non Valido",
                "Il nome deve contenere almeno una lettera (es: Esempio, Didascalia)"
            )
            return
        
        # Chiedi conferma
        reply = QMessageBox.question(
            self,
            "Aggiungi Nome",
            f"Vuoi aggiungere '{base_name}' all'elenco dei nomi riconosciuti?\n\n"
            f"Dopo l'aggiunta, il sistema riconoscerà automaticamente:\n"
            f"  • {base_name} 1\n"
            f"  • {base_name}. 2\n"
            f"  • {base_name} 3a\n"
            f"  • etc.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Crea pattern regex base
        pattern_name = base_name.lower().replace(' ', '_')
        regex = rf'{base_name}\.?\s*(\d+\.?\d*[a-z]?)'
        
        # Aggiungi il pattern
        success = self.pattern_manager.add_pattern(
            pattern_name=pattern_name,
            regex_pattern=regex,
            priority=70,  # Priorità media
            description=f"Aggiunto velocemente dalla GUI - riconosce {base_name} numerati"
        )
        
        if success:
            QMessageBox.information(
                self,
                "Successo!",
                f"✅ Nome '{base_name}' aggiunto con successo!\n\n"
                f"D'ora in poi il sistema riconoscerà automaticamente questo nome nelle immagini."
            )
        else:
            # Già esistente, chiedi se vuole aprire la gestione
            reply = QMessageBox.question(
                self,
                "Nome Già Esistente",
                f"Il nome '{base_name}' esiste già nell'elenco.\n\n"
                f"Vuoi aprire la finestra di gestione per modificarlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.open_pattern_manager()
    
    def open_pattern_manager(self):
        """Apre la finestra di gestione completa dei pattern"""
        dialog = PatternManagerDialog(self)
        dialog.exec()
