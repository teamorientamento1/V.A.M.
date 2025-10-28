from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QTextEdit, QSplitter, QGroupBox,
                             QListWidgetItem, QMessageBox, QCheckBox, QLineEdit,
                             QTreeWidget, QTreeWidgetItem, QFrame, QDialog, QDialogButtonBox,
                             QTreeWidgetItemIterator, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor, QBrush
import io
from PIL import Image
from core.reference_finder import search_references_in_document
from ui.dialogs.reference_detail_dialog import ReferenceDetailDialog
from ui.dialogs.pattern_manager_dialog import PatternManagerDialog
from modules.jump_manager.image_pattern_manager import ImagePatternManager
from modules.jump_manager.reference_deduplicator import ReferenceDeduplicator
from modules.jump_manager.label_hierarchy_analyzer import LabelHierarchyAnalyzer
from modules.jump_manager.jump_tracker import JumpTracker
from modules.jump_manager.jump_creator import JumpManager


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
        self.deduplicator = ReferenceDeduplicator(similarity_threshold=0.85)
        self.hierarchy_analyzer = LabelHierarchyAnalyzer()
        self.jump_tracker = JumpTracker()
        self.jump_manager = None  # Verrà creato quando si carica un documento
        self.edit_mode = False  # True quando si modifica jump esistente
        self.init_ui()

    def _nearest_label_by_paragraph(self, element_para_index, all_references):
        """Restituisce (etichetta, tipo) del riferimento più vicino per paragrafo.
        all_references: lista di dict con chiavi: 'label','type','paragraph_index'.
        In caso di parità, preferisce il riferimento precedente (sopra)."""
        best = None
        best_dist = None
        for ref in all_references:
            pi = ref.get('paragraph_index')
            if pi is None:
                continue
            dist = abs(pi - element_para_index)
            # tie-break: preferisci precedente
            tie = best is not None and dist == best_dist and pi < element_para_index and best[2] >= element_para_index
            if best is None or dist < best_dist or tie:
                best = (ref.get('label'), ref.get('type'), pi)
                best_dist = dist
        if best is None:
            return None, None
        return best[0], best[1]

        
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
        
        # === BANNER MODALITÀ MODIFICA ===
        self.edit_mode_banner = QFrame()
        self.edit_mode_banner.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ff9800;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        edit_mode_layout = QHBoxLayout()
        self.edit_mode_label = QLabel("⚠️ MODALITÀ MODIFICA - Stai modificando un jump esistente")
        self.edit_mode_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.edit_mode_label.setStyleSheet("color: #e65100;")
        edit_mode_layout.addWidget(self.edit_mode_label)
        
        self.btn_cancel_edit = QPushButton("❌ Annulla Modifica")
        self.btn_cancel_edit.setStyleSheet("background: #ff5722; color: white; font-weight: bold;")
        self.btn_cancel_edit.clicked.connect(self.cancel_edit_mode)
        edit_mode_layout.addWidget(self.btn_cancel_edit)
        
        self.edit_mode_banner.setLayout(edit_mode_layout)
        self.edit_mode_banner.hide()
        layout.addWidget(self.edit_mode_banner)
        
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
        
        # === PULSANTE VEDI TUTTI JUMP ===
        self.btn_view_all_jumps = QPushButton("📋 Vedi Tutti Jump Creati")
        self.btn_view_all_jumps.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_view_all_jumps.clicked.connect(self.show_all_jumps_dialog)
        layout.addWidget(self.btn_view_all_jumps)
        
        # Lista elementi
        self.elements_list = QListWidget()
        self.elements_list.itemClicked.connect(self.on_element_clicked)
        layout.addWidget(self.elements_list)
        
        panel.setLayout(layout)
        return panel
    
    def create_preview_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        
        group_before = QGroupBox("Testo prima (10 righe)")
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
        
        group_after = QGroupBox("Testo dopo (10 righe)")
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
        
        self.references_list = QTreeWidget()
        self.references_list.setHeaderLabels(["Riferimenti Trovati"])
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
        
        self.btn_create = QPushButton("✨ Crea Jump")
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
        
        # === ORDINAMENTO PER PAGINA ===
        # Ordina elementi per page_number (se disponibile) o paragraph_index (fallback)
        self.filtered_elements.sort(key=lambda x: x.get('page_number') or x.get('paragraph_index') or 0)
        
        for elem in self.filtered_elements:
            elem_type = elem.get('elem_type')
            label = elem.get('label', 'N/A')
            
            # Usa page_number se disponibile, altrimenti stima dalla paragraph_index
            page = elem.get('page_number')
            if page is None:
                para = elem.get('paragraph_index')
                if para is None or para == 'N/A':
                    para = 0
                page = self.estimate_page_number(para)
            
            # Controlla se esiste già jump per questo elemento
            has_jump = self.jump_tracker.has_jump(label)
            jump_indicator = " ✅" if has_jump else ""
            
            if elem_type == 'image':
                text = f"📷 {label} - Pag.{page}{jump_indicator}"
            elif elem_type == 'table':
                text = f"📊 Tabella Pag.{page}{jump_indicator}"
            elif elem_type == 'equation':
                text = f"🧮 {str(label)[:30]}... - Pag.{page}{jump_indicator}"
            else:
                text = f"{label} - Pag.{page}{jump_indicator}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, elem)
            
            # Sfondo verde chiaro per elementi con jump
            if has_jump:
                item.setBackground(QBrush(QColor(200, 255, 200)))
                item.setToolTip(f"Jump già creato per {label}")
            
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
        
        # === CONTROLLO JUMP ESISTENTE ===
        if self.jump_tracker.has_jump(label):
            jump_info = self.jump_tracker.get_jump_info(label)
            
            # Mostra dialog di conferma
            reply = self.show_existing_jump_dialog(label, jump_info)
            
            if reply == QMessageBox.StandardButton.Cancel:
                # Utente ha annullato
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # Utente vuole modificare
                self.enter_edit_mode(label, jump_info)
            # Se No, procede in modalità normale (elimina e ricrea)
        else:
            # Nessun jump esistente, modalità creazione normale
            self.exit_edit_mode()
        
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
            
            # Deduplicazione automatica dei riferimenti
            original_count = len(refs)
            if refs:
                refs = self.deduplicator.deduplicate_references(refs, strategy='smart')
                duplicates_removed = original_count - len(refs)
            else:
                duplicates_removed = 0
            
            self.current_references = refs
            
            if refs:
                # Analizza gerarchie
                grouped = self.hierarchy_analyzer.group_references_by_hierarchy(refs)
                
                # Conta totale
                total_refs = len(refs)
                
                # Mostra informazioni
                if duplicates_removed > 0:
                    result_text = f"✓ Trovati {total_refs} riferimenti unici ({duplicates_removed} duplicati rimossi)"
                else:
                    result_text = f"✓ Trovati {total_refs} riferimenti:"
                
                self.search_results_label.setText(result_text)
                
                self.references_list.clear()
                self.references_list.show()
                self.hint_label.show()
                
                # === VISUALIZZAZIONE GERARCHICA ===
                
                # Gruppi gerarchici (parent con children)
                for group in grouped['hierarchical']:
                    parent_label = group['parent']
                    parent_refs = group['parent_refs']
                    children = group['children']
                    
                    # Item parent (espandibile)
                    parent_text = f"📂 {parent_label} [{len(parent_refs)} refs]"
                    parent_item = QTreeWidgetItem([parent_text])
                    parent_item.setFlags(parent_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    parent_item.setCheckState(0, Qt.CheckState.Checked)  # Pre-selezionato
                    parent_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'parent', 'label': parent_label, 'refs': parent_refs})
                    parent_item.setExpanded(True)
                    
                    # Aggiungi riferimenti del parent
                    for ref in parent_refs:
                        self._add_reference_child(parent_item, ref, is_parent_ref=True)
                    
                    # Aggiungi children (sottofigure)
                    for child_data in children:
                        child_label = child_data['label']
                        child_refs = child_data['refs']
                        
                        child_text = f"   └─ 📷 {child_label} [{len(child_refs)} refs]"
                        child_item = QTreeWidgetItem([child_text])
                        child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        child_item.setCheckState(0, Qt.CheckState.Unchecked)  # NON pre-selezionato
                        child_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'child', 'label': child_label, 'refs': child_refs})
                        
                        # Aggiungi riferimenti del child
                        for ref in child_refs:
                            self._add_reference_child(child_item, ref, is_parent_ref=False)
                        
                        parent_item.addChild(child_item)
                    
                    self.references_list.addTopLevelItem(parent_item)
                
                # Elementi standalone (senza gerarchia)
                for item_data in grouped['standalone']:
                    label_text = item_data['label']
                    refs_list = item_data['refs']
                    
                    if len(refs_list) == 1:
                        # Singolo riferimento, mostra direttamente
                        ref = refs_list[0]
                        item = self._create_reference_item(ref, label_text)
                        self.references_list.addTopLevelItem(item)
                    else:
                        # Multipli riferimenti, crea gruppo
                        group_text = f"📄 {label_text} [{len(refs_list)} refs]"
                        group_item = QTreeWidgetItem([group_text])
                        group_item.setFlags(group_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        group_item.setCheckState(0, Qt.CheckState.Checked)
                        group_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'standalone', 'label': label_text, 'refs': refs_list})
                        group_item.setExpanded(True)
                        
                        for ref in refs_list:
                            self._add_reference_child(group_item, ref, is_parent_ref=True)
                        
                        self.references_list.addTopLevelItem(group_item)
                
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
    
    def _create_reference_item(self, ref, label):
        """Crea item per singolo riferimento"""
        para_index = ref.get('paragraph_index', 0)
        if para_index is None:
            para_index = 0
        page = self.estimate_page_number(para_index)
        context = f"{ref.get('context_before', '')[-30:]}{ref.get('variant_found', '')}{ref.get('context_after', '')[:30]}"
        item_text = f"▫ Pag.{page}: ...{context}..."
        
        item = QTreeWidgetItem([item_text])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked)
        item.setData(0, Qt.ItemDataRole.UserRole, ref)
        
        return item
    
    def _add_reference_child(self, parent_item, ref, is_parent_ref=True):
        """Aggiunge riferimento come child di un parent item"""
        para_index = ref.get('paragraph_index', 0)
        if para_index is None:
            para_index = 0
        page = self.estimate_page_number(para_index)
        context = f"{ref.get('context_before', '')[-30:]}{ref.get('variant_found', '')}{ref.get('context_after', '')[:30]}"
        
        ref_text = f"      Pag.{page}: ...{context}..."
        ref_item = QTreeWidgetItem([ref_text])
        ref_item.setData(0, Qt.ItemDataRole.UserRole, ref)
        ref_item.setFlags(ref_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)  # Non checkable
        
        parent_item.addChild(ref_item)
    
    def show_reference_detail(self, item):
        """Mostra dialog dettaglio riferimento"""
        ref_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not ref_data or not isinstance(ref_data, dict):
            return
        
        # Se è un gruppo, non aprire dialog
        if 'refs' in ref_data:
            return
        
        dialog = ReferenceDetailDialog(ref_data, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            if dialog.is_selected() and item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Checked)
    
    def select_all_references(self):
        """Seleziona tutti i riferimenti nell'albero"""
        iterator = QTreeWidgetItemIterator(self.references_list, QTreeWidgetItemIterator.IteratorFlag.HasChildren | QTreeWidgetItemIterator.IteratorFlag.NoChildren)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Checked)
            iterator += 1
    
    def create_reference_jumps(self):
        """Crea jump per i riferimenti selezionati nell'albero"""
        # Raccogli tutti i riferimenti selezionati
        selected = []
        
        iterator = QTreeWidgetItemIterator(
            self.references_list, 
            QTreeWidgetItemIterator.IteratorFlag.Checked
        )
        
        while iterator.value():
            item = iterator.value()
            # Prendi i dati dal parent se è un gruppo
            data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if isinstance(data, dict) and 'refs' in data:
                # È un gruppo (parent o standalone)
                selected.extend(data['refs'])
            elif isinstance(data, dict) and 'paragraph_index' in data:
                # È un singolo riferimento
                selected.append(data)
            
            iterator += 1
        
        if not selected:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno un riferimento")
            return
        
        description = self.description_text.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Attenzione", "Inserisci una descrizione")
            return
        
        label = self.search_label_input.text().strip()
        if not label:
            label = self.current_element.get('label', 'Elemento') if self.current_element else 'Elemento'
        
        # === SALVA NEL TRACKER ===
        elem_type = self.current_element.get('elem_type', 'image') if self.current_element else 'image'
        
        if self.edit_mode:
            # Aggiorna jump esistente
            self.jump_tracker.update_jump(label, description, len(selected))
            msg = f"✏️ Jump aggiornato per '{label}' ({len(selected)} riferimenti)"
        else:
            # Crea nuovo jump
            self.jump_tracker.add_jump(label, description, len(selected), elem_type)
            msg = f"✅ Creati {len(selected)} jump per '{label}'"
        
        QMessageBox.information(self, "Jump Creati", msg)
        
        # Aggiorna summary
        summary = self.jumps_summary.toPlainText()
        summary += f"\n{msg}"
        self.jumps_summary.setText(summary)
        
        # Esci da modalità edit se attiva
        if self.edit_mode:
            self.exit_edit_mode()
        
        # Aggiorna lista elementi per mostrare ✅
        self.apply_filter(self.current_filter)
    
    def edit_individual_descriptions(self):
        QMessageBox.information(self, "Info", "Funzione in sviluppo")
    
    def create_jump(self):
        """Crea un jump nel documento Word per l'elemento selezionato"""
        if not self.current_element:
            QMessageBox.warning(self, "Errore", "Nessun elemento selezionato")
            return
        
        description = self.description_text.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Errore", "Inserisci una descrizione")
            return
        
        # Verifica che jump_manager sia inizializzato
        if not self.jump_manager:
            if hasattr(self.main_window, 'analyzer') and getattr(self.main_window.analyzer, 'document', None):
                self.jump_manager = JumpManager(self.main_window.analyzer.document)
            else:
                QMessageBox.critical(
                    self, 
                    "Errore", 
                    "JumpManager non inizializzato.\n\n"
                    "Assicurati di aver caricato un documento nella scheda 'Carica' prima di creare jump."
                )
                return
        
        # Verifica che ci sia accesso al documento
        if not hasattr(self.main_window, 'analyzer') or not self.main_window.analyzer:
            QMessageBox.critical(
                self, 
                "Errore", 
                "Documento non disponibile.\n\n"
                "Ricarica il documento nella scheda 'Carica'."
            )
            return
        
        label = self.current_element.get('label', 'Elemento')
        elem_type = self.current_element.get('elem_type')
        link_text = self.link_text_input.text().strip() or f"📖 Descrizione {label}"
        
        try:
            # Crea il jump nel documento Word
            if elem_type == 'image':
                # Per le immagini, usa create_image_jump_with_preview
                # Determina etichetta per vicinanza pura
                all_refs = self.current_references if hasattr(self, 'current_references') else []
                element = self.current_element
                nearest_label, nearest_type = self._nearest_label_by_paragraph(element['paragraph_index'], all_refs)
                if nearest_label:
                    label = nearest_label
                    elem_type = nearest_type or element.get('type', 'image')

                jump_info = self.jump_manager.create_image_jump_with_preview(
                    image_data=self.current_element,
                    description=description,
                    return_text="↩ Torna al testo"
                )
            else:
                # Per altri tipi, usa il metodo generico
                jump_info = self.jump_manager.add_simple_description(
                    label=label,
                    description=description
                )
            
            if jump_info:
                # Registra nel JumpTracker
                self.jump_tracker.add_jump(
                    element_label=label,
                    description=description,
                    references_count=0,  # Aggiornato successivamente se ci sono riferimenti
                    element_type=elem_type
                )
                
                # Chiedi dove salvare il documento
                doc_path = self.main_window.analyzer.doc_path
                save_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Salva documento con jump",
                    doc_path.replace('.docx', '_with_jumps.docx'),
                    "Word Documents (*.docx)"
                )
                
                if save_path:
                    # Salva il documento
                    self.main_window.analyzer.document.save(save_path)
                    
                    QMessageBox.information(
                        self, 
                        "Jump Creato!", 
                        f"✅ Jump creato con successo per: {label}\n\n"
                        f"📄 Documento salvato in:\n{save_path}\n\n"
                        f"💡 Apri il documento Word per vedere il jump in azione!"
                    )
                    
                    # Aggiorna il summary
                    summary = self.jumps_summary.toPlainText()
                    summary += f"\n✓ {label}: {description[:40]}..."
                    self.jumps_summary.setText(summary)
                    
                    # Pulisci i campi
                    self.description_text.clear()
                    
                    # Esci da modalità edit se attiva
                    if self.edit_mode:
                        self.exit_edit_mode()
                    
                    # Aggiorna la lista per mostrare il ✅
                    self.apply_filter(self.current_filter)
                else:
                    # Utente ha annullato il salvataggio
                    QMessageBox.warning(
                        self,
                        "Salvataggio Annullato",
                        "Il jump è stato creato nel documento in memoria ma non è stato salvato.\n\n"
                        "Riprova a creare il jump e scegli dove salvare il file."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Impossibile creare il jump per {label}.\n\n"
                    "Verifica che l'elemento sia ancora presente nel documento."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore durante la creazione del jump",
                f"Si è verificato un errore:\n\n{str(e)}\n\n"
                "Verifica che il documento sia ancora aperto e accessibile."
            )
            import traceback
            traceback.print_exc()
    
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
        base_name = re.sub(r'[0-9\.\s]+
                    parent, '', label).strip()
        
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
    
    def estimate_page_number(self, paragraph_index) -> int:
        """
        DEPRECATO: Questa funzione è ora usata solo come fallback quando page_number non è disponibile.
        
        Stima il numero di pagina basandosi sull'indice del paragrafo.
        Assume circa 40 paragrafi per pagina (media per documenti Word standard).
        Questa è una stima molto approssimativa e dovrebbe essere sostituita 
        con il campo page_number estratto direttamente dal documento.
        
        Args:
            paragraph_index: Indice del paragrafo nel documento (può essere int, None, o 'N/A')
            
        Returns:
            Numero di pagina stimato (partendo da 1), o 1 se l'indice non è valido
        """
        # Gestisci casi None, 'N/A', o valori non validi
        if paragraph_index is None or paragraph_index == 'N/A':
            return 1
        
        try:
            para_idx = int(paragraph_index)
            paragraphs_per_page = 40  # Media per documenti standard
            page = (para_idx // paragraphs_per_page) + 1
            return page
        except (ValueError, TypeError):
            # Se non è convertibile a int, restituisci pagina 1
            return 1
    
    def open_pattern_manager(self):
        """Apre la finestra di gestione completa dei pattern"""
        dialog = PatternManagerDialog(self)
        dialog.exec()
    
    def show_existing_jump_dialog(self, label, jump_info):
        """
        Mostra dialog quando l'utente clicca su elemento con jump già creato
        
        Returns:
            QMessageBox.StandardButton (Yes per modificare, No per eliminare e ricreare, Cancel per annullare)
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("⚠️ Jump Già Esistente")
        
        description_preview = jump_info.get('description_preview', 'N/A')
        refs_count = jump_info.get('references_count', 0)
        created_at = jump_info.get('created_at', 'N/A')
        
        text = f"""<b>{label}</b> ha già un jump creato:<br><br>
<b>Descrizione attuale:</b><br>
<i>"{description_preview}"</i><br><br>
<b>Riferimenti creati:</b> {refs_count}<br>
<b>Creato il:</b> {created_at[:10] if created_at != 'N/A' else 'N/A'}<br><br>
<b>Cosa vuoi fare?</b>
"""
        
        msg.setText(text)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        
        msg.button(QMessageBox.StandardButton.Yes).setText("✏️ Modifica Jump Esistente")
        msg.button(QMessageBox.StandardButton.No).setText("🔄 Elimina e Ricrea")
        msg.button(QMessageBox.StandardButton.Cancel).setText("❌ Annulla")
        
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        return msg.exec()
    
    def enter_edit_mode(self, label, jump_info):
        """Entra in modalità modifica per un jump esistente"""
        self.edit_mode = True
        self.edit_mode_banner.show()
        
        # Carica descrizione esistente
        description = jump_info.get('description', '')
        self.description_text.setPlainText(description)
        
        # Cambia testo pulsante
        self.btn_create.setText("💾 Salva Modifiche")
        self.btn_create.setStyleSheet("background: #ff9800; color: white; font-weight: bold;")
    
    def exit_edit_mode(self):
        """Esce dalla modalità modifica"""
        self.edit_mode = False
        self.edit_mode_banner.hide()
        
        # Ripristina pulsante normale
        self.btn_create.setText("✨ Crea Jump")
        self.btn_create.setStyleSheet("")
    
    def cancel_edit_mode(self):
        """Annulla la modalità modifica"""
        reply = QMessageBox.question(
            self,
            "Annulla Modifica",
            "Sei sicuro di voler annullare le modifiche?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.exit_edit_mode()
            self.description_text.clear()
            self.current_element = None
    
    def show_all_jumps_dialog(self):
        """Mostra dialog con tutti i jump creati"""
        all_jumps = self.jump_tracker.get_all_jumps()
        
        if not all_jumps:
            QMessageBox.information(
                self,
                "Nessun Jump Creato",
                "Non ci sono ancora jump creati per questo documento."
            )
            return
        
        dialog = AllJumpsDialog(all_jumps, self.jump_tracker, self)
        dialog.exec()
        
        # Aggiorna lista elementi dopo eventuale eliminazione
        self.apply_filter(self.current_filter)
    
    def load_document(self, document_path):
        """Carica il tracking per un nuovo documento"""
        self.jump_tracker.set_document(document_path)
        
        # Inizializza JumpManager con il documento dell'analyzer
        if hasattr(self.main_window, 'analyzer') and self.main_window.analyzer:
            if hasattr(self.main_window.analyzer, 'document') and self.main_window.analyzer.document:
                self.jump_manager = JumpManager(self.main_window.analyzer.document)
                print(f"✓ JumpManager inizializzato per {document_path}")
            else:
                print("⚠ Documento non disponibile in analyzer")
        else:
            print("⚠ Analyzer non disponibile")
        
        self.apply_filter(self.current_filter)


class AllJumpsDialog(QDialog):
    """Dialog per visualizzare tutti i jump creati"""
    
    def __init__(self, jumps, tracker, parent=None):
        super().__init__(parent)
        self.jumps = jumps
        self.jump_tracker = tracker
        self.setWindowTitle("📋 Tutti i Jump Creati")
        self.setMinimumSize(700, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Titolo
        title = QLabel(f"📋 Jump Creati: {len(self.jumps)}")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Statistiche
        stats = self.jump_tracker.get_statistics()
        stats_text = f"Totale riferimenti: {stats['total_references']} | Media: {stats['avg_references_per_jump']} refs/jump"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(stats_label)
        
        # Lista jump
        self.jump_list = QTreeWidget()
        self.jump_list.setHeaderLabels(["Label", "Tipo", "Riferimenti", "Data Creazione"])
        self.jump_list.setColumnWidth(0, 200)
        self.jump_list.setColumnWidth(1, 100)
        self.jump_list.setColumnWidth(2, 100)
        
        for jump in self.jumps:
            label = jump.get('label', 'N/A')
            elem_type = jump.get('element_type', 'N/A')
            refs_count = jump.get('references_count', 0)
            created_at = jump.get('created_at', 'N/A')[:10]
            
            item = QTreeWidgetItem([label, elem_type, str(refs_count), created_at])
            item.setData(0, Qt.ItemDataRole.UserRole, jump)
            
            # Aggiungi anteprima descrizione come child
            desc_preview = jump.get('description_preview', '')
            if desc_preview:
                desc_item = QTreeWidgetItem([f"📝 {desc_preview}"])
                desc_item.setForeground(0, QBrush(QColor(100, 100, 100)))
                item.addChild(desc_item)
            
            self.jump_list.addTopLevelItem(item)
        
        layout.addWidget(self.jump_list)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        
        self.btn_delete = QPushButton("🗑️ Elimina Selezionato")
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_delete.setStyleSheet("background: #f44336; color: white;")
        buttons_layout.addWidget(self.btn_delete)
        
        buttons_layout.addStretch()
        
        self.btn_close = QPushButton("✅ Chiudi")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def delete_selected(self):
        """Elimina il jump selezionato"""
        current = self.jump_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Nessuna Selezione", "Seleziona un jump da eliminare.")
            return
        
        # Se è un child (descrizione), prendi il parent
        if current.parent():
            current = current.parent()
        
        jump_data = current.data(0, Qt.ItemDataRole.UserRole)
        if not jump_data:
            return
        
        label = jump_data.get('label', '')
        
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare il jump per '{label}'?\n\nQuesta azione non può essere annullata.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.jump_tracker.delete_jump(label):
                # Rimuovi dalla lista
                index = self.jump_list.indexOfTopLevelItem(current)
                self.jump_list.takeTopLevelItem(index)
                
                # Aggiorna contatore
                remaining = self.jump_list.topLevelItemCount()
                self.findChild(QLabel).setText(f"📋 Jump Creati: {remaining}")
                
                QMessageBox.information(self, "Successo", f"Jump per '{label}' eliminato con successo.")
                    parent