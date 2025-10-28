"""
Dialog per gestire i pattern di riconoscimento delle etichette delle immagini
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                             QSpinBox, QTextEdit, QMessageBox, QHeaderView,
                             QGroupBox, QCheckBox, QSplitter, QWidget, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from modules.jump_manager.image_pattern_manager import ImagePatternManager


class PatternManagerDialog(QDialog):
    """Finestra per gestire i pattern di riconoscimento"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_manager = ImagePatternManager()
        self.setWindowTitle("Gestione Nomi Immagini")
        self.setMinimumSize(900, 600)
        self.init_ui()
        self.load_patterns()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # === TITOLO E DESCRIZIONE ===
        title = QLabel("📋 Gestione Nomi Riconosciuti per Immagini")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        desc = QLabel(
            "Qui puoi vedere e modificare i nomi che il sistema riconosce per le immagini.\n"
            "Esempi: Fig., Figura, Figure, Immagine, Esempio, Didascalia, etc."
        )
        desc.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(desc)
        
        # === SPLITTER PER TABELLA E FORM ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === PANNELLO SINISTRA: TABELLA PATTERN ===
        left_panel = self.create_table_panel()
        splitter.addWidget(left_panel)
        
        # === PANNELLO DESTRA: FORM AGGIUNTA/MODIFICA ===
        right_panel = self.create_form_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([500, 400])
        layout.addWidget(splitter)
        
        # === BOTTONI FINALI ===
        buttons_layout = QHBoxLayout()
        
        self.btn_stats = QPushButton("📊 Statistiche")
        self.btn_stats.clicked.connect(self.show_statistics)
        buttons_layout.addWidget(self.btn_stats)
        
        buttons_layout.addStretch()
        
        self.btn_close = QPushButton("Chiudi")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def create_table_panel(self):
        """Pannello con la tabella dei pattern"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Etichetta
        label = QLabel("Pattern Esistenti:")
        label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        layout.addWidget(label)
        
        # Tabella
        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(6)
        self.pattern_table.setHorizontalHeaderLabels([
            "✓", "Nome", "Riconosce", "Priorità", "Descrizione", "Azioni"
        ])
        
        # Impostazioni tabella
        self.pattern_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pattern_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pattern_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Ridimensiona colonne
        header = self.pattern_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Riconosce
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Priorità
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Descrizione
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Azioni
        
        self.pattern_table.itemSelectionChanged.connect(self.on_pattern_selected)
        
        layout.addWidget(self.pattern_table)
        
        # Info contatore
        self.pattern_count_label = QLabel("0 pattern totali")
        self.pattern_count_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.pattern_count_label)
        
        panel.setLayout(layout)
        return panel
    
    def create_form_panel(self):
        """Pannello con il form per aggiungere/modificare pattern"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # === GRUPPO AGGIUNGI/MODIFICA ===
        group = QGroupBox("Aggiungi / Modifica Pattern")
        group_layout = QVBoxLayout()
        
        # Nome
        group_layout.addWidget(QLabel("Nome del Pattern:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("es: esempio, didascalia, screenshot")
        group_layout.addWidget(self.input_name)
        
        # Regex
        group_layout.addWidget(QLabel("Cosa Riconoscere (testo o regex):"))
        self.input_regex = QLineEdit()
        self.input_regex.setPlaceholderText("es: Esempio oppure Esempio\.?\s*(\d+)")
        group_layout.addWidget(self.input_regex)
        
        # Suggerimenti regex
        hint = QLabel(
            "💡 Esempi:\n"
            "  • 'Esempio' → riconosce 'Esempio' nel testo\n"
            "  • 'Esempio\.?\s*(\d+)' → riconosce 'Esempio 1', 'Esempio. 2', etc."
        )
        hint.setStyleSheet("color: #0066cc; font-size: 9pt; padding: 5px; background: #e8f4fd; border-radius: 3px;")
        hint.setWordWrap(True)
        group_layout.addWidget(hint)
        
        # Priorità
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priorità:"))
        self.input_priority = QSpinBox()
        self.input_priority.setMinimum(1)
        self.input_priority.setMaximum(999)
        self.input_priority.setValue(50)
        self.input_priority.setToolTip("Più alto = cercato per primo")
        priority_layout.addWidget(self.input_priority)
        priority_layout.addWidget(QLabel("(più alto = cerca per primo)"))
        priority_layout.addStretch()
        group_layout.addLayout(priority_layout)
        
        # Descrizione
        group_layout.addWidget(QLabel("Descrizione (opzionale):"))
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Descrizione di cosa serve questo pattern...")
        self.input_description.setMaximumHeight(60)
        group_layout.addWidget(self.input_description)
        
        # Case sensitive
        self.input_case_sensitive = QCheckBox("Case-sensitive (distingui maiuscole/minuscole)")
        group_layout.addWidget(self.input_case_sensitive)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # === BOTTONI AZIONI ===
        buttons_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("➕ Aggiungi Nuovo")
        self.btn_add.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        self.btn_add.clicked.connect(self.add_pattern)
        buttons_layout.addWidget(self.btn_add)
        
        self.btn_update = QPushButton("✏️ Aggiorna Selezionato")
        self.btn_update.setEnabled(False)
        self.btn_update.clicked.connect(self.update_pattern)
        buttons_layout.addWidget(self.btn_update)
        
        layout.addLayout(buttons_layout)
        
        # === GRUPPO TEST ===
        test_group = QGroupBox("🧪 Test Riconoscimento")
        test_layout = QVBoxLayout()
        
        test_layout.addWidget(QLabel("Testa se il pattern riconosce un testo:"))
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("es: Vedi Esempio 5 per dettagli")
        test_layout.addWidget(self.test_input)
        
        self.btn_test = QPushButton("🔍 Testa")
        self.btn_test.clicked.connect(self.test_pattern)
        test_layout.addWidget(self.btn_test)
        
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        self.test_result.setStyleSheet("padding: 5px; margin-top: 5px;")
        test_layout.addWidget(self.test_result)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def load_patterns(self):
        """Carica i pattern nella tabella"""
        patterns = self.pattern_manager.get_patterns(enabled_only=False)
        
        self.pattern_table.setRowCount(0)
        
        for pattern in patterns:
            row = self.pattern_table.rowCount()
            self.pattern_table.insertRow(row)
            
            # Colonna 0: Checkbox abilitato
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(
                Qt.CheckState.Checked if pattern['enabled'] else Qt.CheckState.Unchecked
            )
            self.pattern_table.setItem(row, 0, checkbox_item)
            
            # Colonna 1: Nome
            name_item = QTableWidgetItem(pattern['pattern_name'])
            if not pattern['enabled']:
                name_item.setForeground(QColor('#999'))
            self.pattern_table.setItem(row, 1, name_item)
            
            # Colonna 2: Regex
            regex_item = QTableWidgetItem(pattern['regex_pattern'][:50])
            if not pattern['enabled']:
                regex_item.setForeground(QColor('#999'))
            self.pattern_table.setItem(row, 2, regex_item)
            
            # Colonna 3: Priorità
            priority_item = QTableWidgetItem(str(pattern['priority']))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not pattern['enabled']:
                priority_item.setForeground(QColor('#999'))
            self.pattern_table.setItem(row, 3, priority_item)
            
            # Colonna 4: Descrizione
            desc = pattern.get('description', '')
            desc_item = QTableWidgetItem(desc[:40] + '...' if len(desc) > 40 else desc)
            if not pattern['enabled']:
                desc_item.setForeground(QColor('#999'))
            self.pattern_table.setItem(row, 4, desc_item)
            
            # Colonna 5: Bottone elimina
            btn_delete = QPushButton("🗑️")
            btn_delete.setToolTip("Elimina pattern")
            btn_delete.setMaximumWidth(40)
            btn_delete.clicked.connect(lambda checked, p=pattern: self.delete_pattern(p['pattern_name']))
            self.pattern_table.setCellWidget(row, 5, btn_delete)
            
            # Salva i dati nel row
            name_item.setData(Qt.ItemDataRole.UserRole, pattern)
        
        # Aggiorna contatore
        enabled_count = sum(1 for p in patterns if p['enabled'])
        self.pattern_count_label.setText(
            f"{len(patterns)} pattern totali ({enabled_count} attivi, {len(patterns)-enabled_count} disattivi)"
        )
        
        # Connetti il cambio di checkbox
        self.pattern_table.itemChanged.connect(self.on_checkbox_changed)
    
    def on_checkbox_changed(self, item):
        """Gestisce il cambio di stato del checkbox"""
        if item.column() == 0:  # Colonna checkbox
            row = item.row()
            name_item = self.pattern_table.item(row, 1)
            if name_item:
                pattern = name_item.data(Qt.ItemDataRole.UserRole)
                if pattern:
                    enabled = item.checkState() == Qt.CheckState.Checked
                    self.pattern_manager.update_pattern(
                        pattern['pattern_name'],
                        enabled=enabled
                    )
                    # Ricarica per aggiornare i colori
                    self.pattern_table.itemChanged.disconnect(self.on_checkbox_changed)
                    self.load_patterns()
                    self.pattern_table.itemChanged.connect(self.on_checkbox_changed)
    
    def on_pattern_selected(self):
        """Quando un pattern viene selezionato nella tabella"""
        selected = self.pattern_table.selectedItems()
        if selected:
            row = selected[0].row()
            name_item = self.pattern_table.item(row, 1)
            pattern = name_item.data(Qt.ItemDataRole.UserRole)
            
            if pattern:
                # Popola il form con i dati del pattern selezionato
                self.input_name.setText(pattern['pattern_name'])
                self.input_regex.setText(pattern['regex_pattern'])
                self.input_priority.setValue(pattern['priority'])
                self.input_description.setText(pattern.get('description', ''))
                self.input_case_sensitive.setChecked(bool(pattern.get('case_sensitive', 0)))
                
                self.btn_update.setEnabled(True)
                self.btn_add.setText("➕ Aggiungi come Nuovo")
    
    def add_pattern(self):
        """Aggiunge un nuovo pattern"""
        name = self.input_name.text().strip()
        regex = self.input_regex.text().strip()
        priority = self.input_priority.value()
        description = self.input_description.toPlainText().strip()
        case_sensitive = self.input_case_sensitive.isChecked()
        
        if not name:
            QMessageBox.warning(self, "Errore", "Inserisci un nome per il pattern")
            return
        
        if not regex:
            QMessageBox.warning(self, "Errore", "Inserisci cosa deve riconoscere")
            return
        
        # Se il regex non contiene simboli regex, rendilo più flessibile
        if not any(c in regex for c in r'.*+?[](){}^$|\\'):
            # Aggiungi pattern base per numeri
            regex = rf'{regex}\.?\s*(\d+\.?\d*[a-z]?)'
            
            reply = QMessageBox.question(
                self,
                "Pattern Suggerito",
                f"Il testo inserito verrà convertito in questo pattern:\n\n{regex}\n\n"
                f"Questo riconoscerà:\n"
                f"  • {self.input_regex.text()} 1\n"
                f"  • {self.input_regex.text()}. 2\n"
                f"  • {self.input_regex.text()} 3a\n\n"
                f"Vuoi usare questo pattern?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Aggiungi pattern
        success = self.pattern_manager.add_pattern(
            name, regex, priority, description, case_sensitive
        )
        
        if success:
            QMessageBox.information(self, "Successo", f"Pattern '{name}' aggiunto!")
            self.clear_form()
            self.load_patterns()
        else:
            QMessageBox.warning(self, "Errore", f"Pattern '{name}' già esistente")
    
    def update_pattern(self):
        """Aggiorna il pattern selezionato"""
        selected = self.pattern_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Errore", "Seleziona un pattern da modificare")
            return
        
        row = selected[0].row()
        name_item = self.pattern_table.item(row, 1)
        old_pattern = name_item.data(Qt.ItemDataRole.UserRole)
        old_name = old_pattern['pattern_name']
        
        # Nuovi valori
        regex = self.input_regex.text().strip()
        priority = self.input_priority.value()
        description = self.input_description.toPlainText().strip()
        case_sensitive = self.input_case_sensitive.isChecked()
        
        if not regex:
            QMessageBox.warning(self, "Errore", "Il pattern non può essere vuoto")
            return
        
        # Aggiorna
        success = self.pattern_manager.update_pattern(
            old_name,
            regex_pattern=regex,
            priority=priority,
            description=description,
            case_sensitive=case_sensitive
        )
        
        if success:
            QMessageBox.information(self, "Successo", f"Pattern '{old_name}' aggiornato!")
            self.clear_form()
            self.load_patterns()
        else:
            QMessageBox.warning(self, "Errore", "Errore nell'aggiornamento del pattern")
    
    def delete_pattern(self, pattern_name):
        """Elimina un pattern"""
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare il pattern '{pattern_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.pattern_manager.remove_pattern(pattern_name)
            if success:
                QMessageBox.information(self, "Successo", "Pattern eliminato")
                self.load_patterns()
            else:
                QMessageBox.warning(self, "Errore", "Errore nell'eliminazione")
    
    def test_pattern(self):
        """Testa se un pattern riconosce un testo"""
        text = self.test_input.text().strip()
        if not text:
            self.test_result.setText("⚠️ Inserisci un testo da testare")
            self.test_result.setStyleSheet("color: orange; padding: 5px; background: #fff3cd;")
            return
        
        result = self.pattern_manager.find_label_in_text(text)
        
        if result:
            label, pattern_name = result
            self.test_result.setText(
                f"✅ TROVATO!\n"
                f"Etichetta: '{label}'\n"
                f"Pattern usato: {pattern_name}"
            )
            self.test_result.setStyleSheet("color: green; padding: 5px; background: #d4edda; border-radius: 3px;")
        else:
            self.test_result.setText(
                "❌ NON TROVATO\n"
                "Nessun pattern riconosce questo testo.\n"
                "Prova ad aggiungere un nuovo pattern!"
            )
            self.test_result.setStyleSheet("color: red; padding: 5px; background: #f8d7da; border-radius: 3px;")
    
    def show_statistics(self):
        """Mostra statistiche sull'uso dei pattern"""
        stats = self.pattern_manager.get_label_statistics()
        
        msg = f"📊 STATISTICHE USO PATTERN\n\n"
        msg += f"Totale etichette riconosciute: {stats['total_labels']}\n\n"
        
        if stats['pattern_usage']:
            msg += "Pattern più usati:\n"
            for pattern, count in sorted(stats['pattern_usage'].items(), key=lambda x: x[1], reverse=True)[:10]:
                msg += f"  • {pattern}: {count} volte\n"
        else:
            msg += "Nessun pattern ancora utilizzato.\n"
        
        if stats['duplicates']:
            msg += f"\n⚠️ Duplicati trovati: {len(stats['duplicates'])}\n"
            msg += "(Gestiti automaticamente con suffissi _2, _3, etc.)"
        
        QMessageBox.information(self, "Statistiche", msg)
    
    def clear_form(self):
        """Pulisce il form"""
        self.input_name.clear()
        self.input_regex.clear()
        self.input_priority.setValue(50)
        self.input_description.clear()
        self.input_case_sensitive.setChecked(False)
        self.btn_update.setEnabled(False)
        self.btn_add.setText("➕ Aggiungi Nuovo")
        self.pattern_table.clearSelection()
