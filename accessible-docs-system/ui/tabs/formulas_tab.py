from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                             QTreeWidgetItem, QLabel, QPushButton, QTextEdit, 
                             QSplitter, QGroupBox, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class FormulasTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.equations_data = []
        self.categories_tree = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Formule ed Equazioni")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        self.stats_label = QLabel("Totale: 0")
        self.stats_label.setFont(QFont('Arial', 10))
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filtri
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtra:"))
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            'Tutte', 'algebra', 'calculus', 'geometry', 'statistics',
            'number_theory', 'special_functions', 'physics', 'other'
        ])
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addWidget(QLabel("Cerca:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca nel testo...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_filters)
        filter_layout.addWidget(btn_reset)
        
        layout.addLayout(filter_layout)
        
        # Splitter principale
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel sinistro - Tree view
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("Equazioni per categoria:"))
        
        self.equations_tree = QTreeWidget()
        self.equations_tree.setHeaderLabels(['Equazioni', 'Difficoltà'])
        self.equations_tree.setColumnWidth(0, 250)
        self.equations_tree.itemClicked.connect(self.on_equation_selected)
        left_layout.addWidget(self.equations_tree)
        
        # Bottoni azioni
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("Modifica")
        self.btn_edit.clicked.connect(self.on_edit_equation)
        self.btn_delete = QPushButton("Elimina")
        self.btn_delete.clicked.connect(self.on_delete_equation)
        btn_reclassify = QPushButton("Riclassifica")
        btn_reclassify.clicked.connect(self.on_reclassify_all)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(btn_reclassify)
        left_layout.addLayout(btn_layout)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Panel destro - Dettagli
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Testo equazione
        text_group = QGroupBox("Rappresentazione Testuale")
        text_layout = QVBoxLayout()
        self.equation_text = QTextEdit()
        self.equation_text.setReadOnly(True)
        self.equation_text.setMaximumHeight(100)
        text_layout.addWidget(self.equation_text)
        text_group.setLayout(text_layout)
        right_layout.addWidget(text_group)
        
        # MathML
        mathml_group = QGroupBox("MathML")
        mathml_layout = QVBoxLayout()
        self.mathml_text = QTextEdit()
        self.mathml_text.setReadOnly(True)
        mathml_layout.addWidget(self.mathml_text)
        mathml_group.setLayout(mathml_layout)
        right_layout.addWidget(mathml_group)
        
        # Info e contesto
        info_group = QGroupBox("Informazioni e Contesto")
        info_layout = QVBoxLayout()
        self.equation_info = QTextEdit()
        self.equation_info.setReadOnly(True)
        info_layout.addWidget(self.equation_info)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def load_equations(self, equations):
        """Carica equazioni e le organizza per categoria"""
        self.equations_data = equations
        self.rebuild_tree()
        self.update_stats()
    
    def rebuild_tree(self):
        """Ricostruisce albero categorie"""
        self.equations_tree.clear()
        self.categories_tree = {}
        
        # Dizionario nomi categorie leggibili
        category_names = {
            'algebra': 'Algebra',
            'calculus': 'Analisi',
            'geometry': 'Geometria',
            'statistics': 'Statistica',
            'number_theory': 'Teoria dei Numeri',
            'special_functions': 'Funzioni Speciali',
            'physics': 'Fisica',
            'other': 'Altro',
            'generic': 'Generico'
        }
        
        subcategory_names = {
            # Algebra
            'linear': 'Algebra Lineare',
            'polynomial': 'Polinomi',
            'equation': 'Equazioni',
            'inequality': 'Disequazioni',
            'system': 'Sistemi',
            # Calculus
            'derivative': 'Derivate',
            'integral': 'Integrali',
            'limit': 'Limiti',
            'series': 'Serie',
            'differential': 'Equazioni Differenziali',
            # Geometry
            'euclidean': 'Geometria Euclidea',
            'analytic': 'Geometria Analitica',
            'differential': 'Geometria Differenziale',
            'vector': 'Vettori',
            'trigonometry': 'Trigonometria',
            # Statistics
            'descriptive': 'Statistica Descrittiva',
            'probability': 'Probabilità',
            'distribution': 'Distribuzioni',
            'inference': 'Inferenza',
            'regression': 'Regressione',
            # Other
            'logic': 'Logica',
            'combinatorics': 'Combinatoria',
            'graph': 'Teoria dei Grafi',
            'misc': 'Varie'
        }
        
        # Filtra equazioni
        filtered_equations = self._get_filtered_equations()
        
        # Organizza per categoria e sottocategoria
        for i, eq in enumerate(filtered_equations):
            category = eq.get('category', 'generic')
            subcategory = eq.get('subcategory', None)
            
            # Crea nodo categoria se non esiste
            if category not in self.categories_tree:
                cat_name = category_names.get(category, category.title())
                cat_item = QTreeWidgetItem(self.equations_tree, [cat_name, ''])
                cat_item.setFont(0, QFont('Arial', 10, QFont.Weight.Bold))
                cat_item.setExpanded(True)
                self.categories_tree[category] = {
                    'item': cat_item,
                    'subcategories': {}
                }
            
            cat_node = self.categories_tree[category]
            
            # Crea nodo sottocategoria se esiste
            if subcategory:
                if subcategory not in cat_node['subcategories']:
                    subcat_name = subcategory_names.get(subcategory, subcategory.title())
                    subcat_item = QTreeWidgetItem(cat_node['item'], [subcat_name, ''])
                    subcat_item.setFont(0, QFont('Arial', 9, QFont.Weight.DemiBold))
                    cat_node['subcategories'][subcategory] = subcat_item
                
                parent_item = cat_node['subcategories'][subcategory]
            else:
                parent_item = cat_node['item']
            
            # Aggiungi equazione
            text_preview = eq.get('text_representation', 'Equazione')[:40]
            para = eq.get('paragraph_index', 'N/A')
            difficulty = eq.get('difficulty', 1)
            diff_stars = '⭐' * difficulty
            
            eq_item = QTreeWidgetItem(parent_item, [
                f"Eq.{i+1} - {text_preview}... (Par.{para})",
                diff_stars
            ])
            eq_item.setData(0, Qt.ItemDataRole.UserRole, i)  # Store index
    
    def _get_filtered_equations(self):
        """Restituisce equazioni filtrate"""
        filtered = self.equations_data
        
        # Filtra per categoria
        category_filter = self.category_filter.currentText()
        if category_filter != 'Tutte':
            filtered = [eq for eq in filtered if eq.get('category') == category_filter]
        
        # Filtra per ricerca
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [eq for eq in filtered 
                       if search_text in eq.get('text_representation', '').lower()]
        
        return filtered
    
    def apply_filters(self):
        """Applica filtri e ricostruisce albero"""
        self.rebuild_tree()
        self.update_stats()
    
    def reset_filters(self):
        """Reset filtri"""
        self.category_filter.setCurrentIndex(0)
        self.search_input.clear()
        self.rebuild_tree()
        self.update_stats()
    
    def update_stats(self):
        """Aggiorna statistiche"""
        filtered = self._get_filtered_equations()
        total = len(self.equations_data)
        shown = len(filtered)
        
        if shown == total:
            self.stats_label.setText(f"Totale equazioni: {total}")
        else:
            self.stats_label.setText(f"Mostrate: {shown} / {total}")
    
    def on_equation_selected(self, item):
        """Handler selezione equazione"""
        # Recupera indice equazione
        eq_index = item.data(0, Qt.ItemDataRole.UserRole)
        if eq_index is None:
            # Click su categoria/sottocategoria
            return
        
        if eq_index >= len(self.equations_data):
            return
        
        eq_data = self.equations_data[eq_index]
        
        # Mostra testo
        self.equation_text.setText(eq_data.get('text_representation', 'N/A'))
        
        # Mostra MathML
        self.mathml_text.setText(eq_data.get('mathml', 'N/A'))
        
        # Info dettagliate
        category = eq_data.get('category', 'N/A')
        subcategory = eq_data.get('subcategory', 'N/A')
        difficulty = eq_data.get('difficulty', 1)
        tags = eq_data.get('tags', [])
        
        # Context
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
        
        info = f"""📍 POSIZIONE
Paragrafo: {eq_data.get('paragraph_index', 'N/A')}

📚 CLASSIFICAZIONE
Categoria: {category}
Sottocategoria: {subcategory}
Difficoltà: {'⭐' * difficulty} ({difficulty}/5)
Tags: {', '.join(tags) if tags else 'Nessun tag'}

📖 CONTESTO PRIMA:
{before_text[:200]}...

📖 CONTESTO DOPO:
{after_text[:200]}...
"""
        self.equation_info.setText(info)
    
    def on_edit_equation(self):
        """Modifica equazione selezionata"""
        # TODO: implementare editing
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Info", "Funzionalità in sviluppo")
    
    def on_delete_equation(self):
        """Elimina equazione e marca dirty"""
        current_item = self.equations_tree.currentItem()
        if not current_item:
            return
        
        eq_index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if eq_index is None:
            return
        
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Conferma',
            'Vuoi eliminare questa equazione?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.equations_data[eq_index]
            self.rebuild_tree()
            self.update_stats()
            
            # Marca dirty per sync
            if hasattr(self.main_window, 'sync_manager'):
                self.main_window.sync_manager.mark_dirty('equations')
    
    def on_reclassify_all(self):
        """Riclassifica tutte le equazioni"""
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog
        
        reply = QMessageBox.question(
            self, 'Riclassifica Tutto',
            f'Vuoi riclassificare tutte le {len(self.equations_data)} equazioni?\n'
            'Questo potrebbe richiedere alcuni secondi.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Progress dialog
        progress = QProgressDialog("Riclassificazione in corso...", "Annulla", 
                                   0, len(self.equations_data), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        try:
            from core.formula_classifier import FormulaClassifier
            classifier = FormulaClassifier()
            
            reclassified = 0
            for i, eq in enumerate(self.equations_data):
                if progress.wasCanceled():
                    break
                
                text = eq.get('text_representation', '').strip()
                if text:
                    try:
                        result = classifier.classify(text)
                        eq['category'] = result.category
                        eq['subcategory'] = result.subcategory
                        eq['difficulty'] = result.difficulty
                        eq['tags'] = result.suggested_tags
                        reclassified += 1
                    except:
                        pass
                
                progress.setValue(i + 1)
            
            progress.close()
            
            # Ricostruisci albero
            self.rebuild_tree()
            self.update_stats()
            
            # Marca dirty
            if hasattr(self.main_window, 'sync_manager'):
                self.main_window.sync_manager.mark_dirty('equations')
            
            QMessageBox.information(
                self, 'Completato',
                f'Riclassificate {reclassified} equazioni su {len(self.equations_data)}'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Errore', f'Errore durante riclassificazione: {str(e)}')
