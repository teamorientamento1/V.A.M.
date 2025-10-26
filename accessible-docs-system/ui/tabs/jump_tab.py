"""
Jump Manager Tab - UI Completa per Gestione Collegamenti
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import json
from typing import Dict, List, Optional

class JumpManagerTab(ttk.Frame):
    """
    Tab completo per gestione jump con:
    - Selezione tipo elemento (immagine/equazione/tabella)
    - Lista elementi trovati
    - Creazione jump con preview
    - Validazione collegamenti
    - Export/import configurazioni
    """
    
    def __init__(self, parent, app_controller):
        super().__init__(parent, padding="10")
        self.app = app_controller
        
        # Dati
        self.current_analysis = None
        self.jumps_created = []
        self.descriptions = {}
        self.selected_element = None
        self.next_jump_id = 1
        
        self._create_ui()
    
    def _create_ui(self):
        """Crea interfaccia completa"""
        # Main container con scrollbar
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header con titolo e stats
        self._create_header(main_container)
        
        # Contenuto principale in 2 colonne
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Colonna sinistra: Selezione elementi
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_elements_panel(left_panel)
        
        # Colonna destra: Jump e configurazione
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._create_jump_config_panel(right_panel)
        
        # Bottom: Azioni e preview
        self._create_actions_panel(main_container)
    
    def _create_header(self, parent):
        """Header con titolo e statistiche"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Titolo
        title = ttk.Label(header_frame, text="🔗 Jump Manager", 
                         font=('Arial', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Stats
        self.stats_var = tk.StringVar(value="Nessun documento caricato")
        stats_label = ttk.Label(header_frame, textvariable=self.stats_var,
                               font=('Arial', 10, 'italic'))
        stats_label.pack(side=tk.RIGHT)
    
    def _create_elements_panel(self, parent):
        """Panel selezione elementi"""
        # Titolo
        ttk.Label(parent, text="1. Seleziona Elementi", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Tipo elemento
        type_frame = ttk.LabelFrame(parent, text="Tipo Elemento", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.element_type_var = tk.StringVar(value="images")
        
        element_types = [
            ("📸 Immagini", "images"),
            ("∑ Equazioni", "equations"),
            ("📊 Tabelle", "tables")
        ]
        
        for text, value in element_types:
            ttk.Radiobutton(type_frame, text=text, variable=self.element_type_var,
                          value=value, command=self._on_type_changed).pack(anchor=tk.W)
        
        # Lista elementi
        list_frame = ttk.LabelFrame(parent, text="Elementi Trovati", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview elementi
        columns = ('ID', 'Label', 'Posizione', 'Ha Jump')
        self.elements_tree = ttk.Treeview(list_frame, columns=columns, 
                                          show='headings', height=10)
        
        self.elements_tree.heading('ID', text='ID')
        self.elements_tree.heading('Label', text='Label')
        self.elements_tree.heading('Posizione', text='Posizione')
        self.elements_tree.heading('Ha Jump', text='Jump')
        
        self.elements_tree.column('ID', width=50)
        self.elements_tree.column('Label', width=100)
        self.elements_tree.column('Posizione', width=100)
        self.elements_tree.column('Ha Jump', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.elements_tree.yview)
        self.elements_tree.configure(yscrollcommand=scrollbar.set)
        
        self.elements_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selezione
        self.elements_tree.bind('<<TreeviewSelect>>', self._on_element_selected)
        
        # Info elemento selezionato
        info_frame = ttk.LabelFrame(parent, text="Info Elemento", padding="5")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.element_info_text = tk.Text(info_frame, height=4, wrap=tk.WORD,
                                         font=('Courier', 9))
        self.element_info_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_jump_config_panel(self, parent):
        """Panel configurazione jump"""
        # Titolo
        ttk.Label(parent, text="2. Configura Jump", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Descrizione
        desc_frame = ttk.LabelFrame(parent, text="Descrizione Elemento", padding="10")
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Textarea descrizione
        self.description_text = scrolledtext.ScrolledText(desc_frame, height=8,
                                                          wrap=tk.WORD,
                                                          font=('Arial', 10))
        self.description_text.pack(fill=tk.BOTH, expand=True)
        
        # Pulsanti descrizione
        desc_buttons = ttk.Frame(desc_frame)
        desc_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(desc_buttons, text="📋 Carica da File",
                  command=self._load_descriptions_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(desc_buttons, text="💾 Salva Descrizioni",
                  command=self._save_descriptions_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(desc_buttons, text="🤖 Genera Auto",
                  command=self._generate_auto_description).pack(side=tk.LEFT, padx=2)
        
        # Opzioni jump
        options_frame = ttk.LabelFrame(parent, text="Opzioni Jump", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Testo link
        ttk.Label(options_frame, text="Testo Link:").pack(anchor=tk.W)
        self.link_text_var = tk.StringVar(value="[Vedi descrizione]")
        ttk.Entry(options_frame, textvariable=self.link_text_var,
                 width=30).pack(fill=tk.X, pady=(0, 10))
        
        # Posizione link
        ttk.Label(options_frame, text="Posizione Link:").pack(anchor=tk.W)
        self.link_position_var = tk.StringVar(value="after")
        pos_frame = ttk.Frame(options_frame)
        pos_frame.pack(fill=tk.X)
        ttk.Radiobutton(pos_frame, text="Prima", variable=self.link_position_var,
                       value="before").pack(side=tk.LEFT)
        ttk.Radiobutton(pos_frame, text="Dopo", variable=self.link_position_var,
                       value="after").pack(side=tk.LEFT)
        ttk.Radiobutton(pos_frame, text="Inline", variable=self.link_position_var,
                       value="inline").pack(side=tk.LEFT)
        
        # Opzioni avanzate
        self.add_return_link_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Aggiungi link di ritorno",
                       variable=self.add_return_link_var).pack(anchor=tk.W, pady=5)
        
        self.block_tts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Blocca TTS su link ritorno",
                       variable=self.block_tts_var).pack(anchor=tk.W)
        
        # Pulsante crea jump
        ttk.Button(options_frame, text="➕ Crea Jump per Elemento Selezionato",
                  command=self._create_jump_for_selected,
                  style='Accent.TButton').pack(fill=tk.X, pady=(10, 0))
    
    def _create_actions_panel(self, parent):
        """Panel azioni e preview"""
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Colonna sinistra: Jump creati
        left = ttk.LabelFrame(actions_frame, text="Jump Creati", padding="10")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Lista jump
        jump_columns = ('ID', 'Tipo', 'Da', 'A', 'Stato')
        self.jumps_tree = ttk.Treeview(left, columns=jump_columns,
                                       show='headings', height=6)
        
        for col in jump_columns:
            self.jumps_tree.heading(col, text=col)
            self.jumps_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(left, orient=tk.VERTICAL,
                                 command=self.jumps_tree.yview)
        self.jumps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.jumps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti jump
        jump_buttons = ttk.Frame(left)
        jump_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(jump_buttons, text="🗑️ Elimina",
                  command=self._delete_selected_jump).pack(side=tk.LEFT, padx=2)
        ttk.Button(jump_buttons, text="✏️ Modifica",
                  command=self._edit_selected_jump).pack(side=tk.LEFT, padx=2)
        ttk.Button(jump_buttons, text="✓ Valida Tutti",
                  command=self._validate_all_jumps).pack(side=tk.LEFT, padx=2)
        
        # Colonna destra: Azioni globali
        right = ttk.LabelFrame(actions_frame, text="Azioni", padding="10")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Azioni batch
        ttk.Label(right, text="Creazione Batch:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Button(right, text="🎯 Crea Jump per Tutti gli Elementi",
                  command=self._create_all_jumps).pack(fill=tk.X, pady=2)
        ttk.Button(right, text="🔍 Scansiona Riferimenti e Crea Jump",
                  command=self._scan_and_create_references).pack(fill=tk.X, pady=2)
        
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Export/Import
        ttk.Label(right, text="Gestione:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Button(right, text="📤 Esporta Configurazione Jump",
                  command=self._export_jump_config).pack(fill=tk.X, pady=2)
        ttk.Button(right, text="📥 Importa Configurazione",
                  command=self._import_jump_config).pack(fill=tk.X, pady=2)
        
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Finalizzazione
        ttk.Label(right, text="Documento:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Button(right, text="✓ Applica Jump al Documento",
                  command=self._apply_jumps_to_document,
                  style='Accent.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(right, text="💾 Salva Documento con Jump",
                  command=self._save_document_with_jumps,
                  style='Accent.TButton').pack(fill=tk.X, pady=2)
    
    # ========== EVENT HANDLERS ==========
    
    def _on_type_changed(self):
        """Cambiato tipo elemento"""
        self._refresh_elements_list()
    
    def _on_element_selected(self, event):
        """Elemento selezionato"""
        selection = self.elements_tree.selection()
        if not selection:
            return
        
        item = self.elements_tree.item(selection[0])
        element_id = item['values'][0]
        
        # Trova elemento nell'analysis
        element_type = self.element_type_var.get()
        elements = self.current_analysis.get(element_type, [])
        
        for elem in elements:
            if elem.get('index') == element_id:
                self.selected_element = elem
                self._show_element_info(elem)
                self._load_element_description(elem)
                break
    
    def _show_element_info(self, element):
        """Mostra info elemento"""
        self.element_info_text.delete(1.0, tk.END)
        
        info = f"ID: {element.get('index')}\n"
        info += f"Label: {element.get('label', 'N/A')}\n"
        info += f"Paragrafo: {element.get('paragraph_index', 'N/A')}\n"
        
        # Caption (potrebbe essere None)
        if element.get('caption'):
            caption_text = str(element['caption'])[:50]
            info += f"Caption: {caption_text}...\n"
        
        # Text representation (per equazioni)
        if element.get('text_representation'):
            text_repr = str(element['text_representation'])[:50]
            info += f"Testo: {text_repr}...\n"
        
        # Context (se disponibile)
        if element.get('context_before'):
            context = str(element['context_before'])[:30]
            info += f"Contesto: ...{context}...\n"
        
        self.element_info_text.insert(1.0, info)
    
    def _load_element_description(self, element):
        """Carica descrizione elemento se esiste"""
        label = element.get('label', f"Element_{element.get('index')}")
        
        if label in self.descriptions:
            self.description_text.delete(1.0, tk.END)
            self.description_text.insert(1.0, self.descriptions[label])
        else:
            # Genera placeholder
            self.description_text.delete(1.0, tk.END)
            placeholder = f"[Inserisci qui la descrizione dettagliata per {label}]\n\n"
            placeholder += "Suggerimenti:\n"
            placeholder += "- Descrivi cosa mostra l'elemento\n"
            placeholder += "- Spiega il suo significato\n"
            placeholder += "- Collega al contesto\n"
            self.description_text.insert(1.0, placeholder)
    
    def _create_jump_for_selected(self):
        """Crea jump per elemento selezionato"""
        if not self.selected_element:
            messagebox.showwarning("Attenzione", "Seleziona prima un elemento")
            return
        
        # Ottieni descrizione
        description = self.description_text.get(1.0, tk.END).strip()
        if not description or description.startswith("[Inserisci"):
            if not messagebox.askyesno("Conferma", 
                "Descrizione mancante o placeholder.\nCreare jump comunque?"):
                return
        
        # Salva descrizione
        label = self.selected_element.get('label', f"Element_{self.selected_element.get('index')}")
        self.descriptions[label] = description
        
        # Crea jump
        jump = {
            'id': self.next_jump_id,
            'type': self.element_type_var.get()[:-1],  # Rimuovi 's' finale
            'source_element': self.selected_element,
            'target_label': label,
            'description': description,
            'link_text': self.link_text_var.get(),
            'link_position': self.link_position_var.get(),
            'add_return_link': self.add_return_link_var.get(),
            'block_tts': self.block_tts_var.get(),
            'status': 'created'
        }
        
        self.jumps_created.append(jump)
        self.next_jump_id += 1
        
        # Aggiorna UI
        self._refresh_jumps_tree()
        self._refresh_elements_list()  # Per aggiornare colonna "Ha Jump"
        
        messagebox.showinfo("Successo", f"Jump #{jump['id']} creato per {label}")
    
    def _create_all_jumps(self):
        """Crea jump per tutti gli elementi"""
        element_type = self.element_type_var.get()
        elements = self.current_analysis.get(element_type, [])
        
        if not elements:
            messagebox.showinfo("Info", "Nessun elemento da elaborare")
            return
        
        if not messagebox.askyesno("Conferma",
            f"Creare jump per tutti i {len(elements)} elementi?\n"
            "Le descrizioni mancanti avranno placeholder."):
            return
        
        created = 0
        for elem in elements:
            # Skip se ha già jump
            label = elem.get('label', f"Element_{elem.get('index')}")
            if any(j['target_label'] == label for j in self.jumps_created):
                continue
            
            # Usa descrizione esistente o placeholder
            if label not in self.descriptions:
                self.descriptions[label] = f"[Descrizione da completare per {label}]"
            
            jump = {
                'id': self.next_jump_id,
                'type': element_type[:-1],
                'source_element': elem,
                'target_label': label,
                'description': self.descriptions[label],
                'link_text': self.link_text_var.get(),
                'link_position': self.link_position_var.get(),
                'add_return_link': self.add_return_link_var.get(),
                'block_tts': self.block_tts_var.get(),
                'status': 'created'
            }
            
            self.jumps_created.append(jump)
            self.next_jump_id += 1
            created += 1
        
        self._refresh_jumps_tree()
        self._refresh_elements_list()
        
        messagebox.showinfo("Completato", 
            f"Creati {created} jump.\n"
            f"Ricorda di completare le descrizioni placeholder!")
    
    def _scan_and_create_references(self):
        """Scansiona riferimenti e crea jump"""
        if not self.current_analysis:
            messagebox.showwarning("Attenzione", "Nessuna analisi caricata")
            return
        
        references = self.current_analysis.get('references', [])
        if not references:
            messagebox.showinfo("Info", "Nessun riferimento trovato")
            return
        
        messagebox.showinfo("Info",
            f"Trovati {len(references)} riferimenti.\n"
            f"Creazione jump automatici in corso...")
        
        # Crea jump per riferimenti
        # TODO: Implementare logica riferimenti
        messagebox.showinfo("Info", "Funzione in sviluppo")
    
    def _delete_selected_jump(self):
        """Elimina jump selezionato"""
        selection = self.jumps_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un jump")
            return
        
        item = self.jumps_tree.item(selection[0])
        jump_id = item['values'][0]
        
        if messagebox.askyesno("Conferma", f"Eliminare jump #{jump_id}?"):
            self.jumps_created = [j for j in self.jumps_created if j['id'] != jump_id]
            self._refresh_jumps_tree()
            self._refresh_elements_list()
    
    def _edit_selected_jump(self):
        """Modifica jump selezionato"""
        selection = self.jumps_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un jump")
            return
        
        item = self.jumps_tree.item(selection[0])
        jump_id = item['values'][0]
        
        # Trova jump
        jump = next((j for j in self.jumps_created if j['id'] == jump_id), None)
        if not jump:
            return
        
        # Carica nei campi di modifica
        self.selected_element = jump['source_element']
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, jump['description'])
        self.link_text_var.set(jump['link_text'])
        
        messagebox.showinfo("Modifica", 
            "Jump caricato nei campi.\n"
            "Modifica i valori e ricrea il jump.")
    
    def _validate_all_jumps(self):
        """Valida tutti i jump"""
        if not self.jumps_created:
            messagebox.showinfo("Info", "Nessun jump da validare")
            return
        
        # TODO: Implementare validazione
        valid = 0
        warnings = []
        
        for jump in self.jumps_created:
            # Check descrizione
            if not jump['description'] or jump['description'].startswith("["):
                warnings.append(f"Jump #{jump['id']}: descrizione placeholder")
            else:
                valid += 1
        
        message = f"Validazione completata:\n"
        message += f"✓ {valid} jump validi\n"
        if warnings:
            message += f"⚠ {len(warnings)} warning\n\n"
            message += "\n".join(warnings[:5])
            if len(warnings) > 5:
                message += f"\n... e altri {len(warnings)-5}"
        
        messagebox.showinfo("Validazione", message)
    
    def _load_descriptions_file(self):
        """Carica descrizioni da file JSON"""
        filepath = filedialog.askopenfilename(
            title="Carica Descrizioni",
            filetypes=[("JSON", "*.json"), ("Tutti", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                self.descriptions.update(loaded)
                messagebox.showinfo("Successo", 
                    f"Caricate {len(loaded)} descrizioni")
                
                # Ricarica descrizione corrente se presente
                if self.selected_element:
                    self._load_element_description(self.selected_element)
                    
            except Exception as e:
                messagebox.showerror("Errore", f"Errore caricamento: {e}")
    
    def _save_descriptions_file(self):
        """Salva descrizioni su file JSON"""
        if not self.descriptions:
            messagebox.showinfo("Info", "Nessuna descrizione da salvare")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Salva Descrizioni",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tutti", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.descriptions, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Successo", 
                    f"Salvate {len(self.descriptions)} descrizioni")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore salvataggio: {e}")
    
    def _generate_auto_description(self):
        """Genera descrizione automatica (placeholder intelligente)"""
        if not self.selected_element:
            messagebox.showwarning("Attenzione", "Seleziona un elemento")
            return
        
        element = self.selected_element
        element_type = self.element_type_var.get()[:-1]
        
        # Genera descrizione basata su tipo e contesto
        description = f"Descrizione auto-generata per {element_type}:\n\n"
        
        label = element.get('label')
        if label:
            description += f"Etichetta: {label}\n"
        
        caption = element.get('caption')
        if caption:
            caption_text = str(caption)[:200]
            description += f"Caption: {caption_text}\n\n"
        
        context_before = element.get('context_before')
        if context_before:
            context_text = str(context_before)[:100]
            description += f"Contesto: {context_text}...\n\n"
        
        description += "[Completa con dettagli specifici]"
        
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, description)
        
        messagebox.showinfo("Info", "Descrizione base generata. Completa i dettagli!")
    
    def _export_jump_config(self):
        """Esporta configurazione jump"""
        if not self.jumps_created:
            messagebox.showinfo("Info", "Nessun jump da esportare")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Esporta Configurazione Jump",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tutti", "*.*")]
        )
        
        if filepath:
            try:
                config = {
                    'jumps': self.jumps_created,
                    'descriptions': self.descriptions,
                    'metadata': {
                        'total_jumps': len(self.jumps_created),
                        'element_types': list(set(j['type'] for j in self.jumps_created))
                    }
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Successo", "Configurazione esportata")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore export: {e}")
    
    def _import_jump_config(self):
        """Importa configurazione jump"""
        filepath = filedialog.askopenfilename(
            title="Importa Configurazione Jump",
            filetypes=[("JSON", "*.json"), ("Tutti", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'jumps' in config:
                    self.jumps_created = config['jumps']
                if 'descriptions' in config:
                    self.descriptions = config['descriptions']
                
                self._refresh_jumps_tree()
                self._refresh_elements_list()
                
                messagebox.showinfo("Successo", 
                    f"Importati {len(self.jumps_created)} jump")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore import: {e}")
    
    def _apply_jumps_to_document(self):
        """Applica i jump al documento Word"""
        if not self.jumps_created:
            messagebox.showwarning("Attenzione", "Nessun jump da applicare")
            return
        
        if not hasattr(self.app, 'analyzer') or not self.app.analyzer:
            messagebox.showwarning("Attenzione", "Carica prima un documento")
            return
        
        messagebox.showinfo("Applicazione Jump",
            f"Applicazione di {len(self.jumps_created)} jump al documento...\n"
            "Questa operazione può richiedere alcuni secondi.")
        
        # TODO: Chiamare JumpManager per applicare effettivamente i jump
        # Per ora simuliamo
        messagebox.showinfo("Info", "Funzione in fase di integrazione finale")
    
    def _save_document_with_jumps(self):
        """Salva documento con jump applicati"""
        filepath = filedialog.asksaveasfilename(
            title="Salva Documento con Jump",
            defaultextension=".docx",
            filetypes=[("Word", "*.docx"), ("Tutti", "*.*")]
        )
        
        if filepath:
            messagebox.showinfo("Salvataggio",
                f"Salvataggio documento con {len(self.jumps_created)} jump...\n"
                f"Path: {filepath}")
            
            # TODO: Salvare effettivamente
            messagebox.showinfo("Info", "Funzione in fase di integrazione finale")
    
    # ========== UTILITY METHODS ==========
    
    def load_analysis(self, analysis: Dict):
        """Carica analisi documento"""
        self.current_analysis = analysis
        self.jumps_created = []
        self.descriptions = {}
        self.selected_element = None
        
        # Aggiorna stats
        stats = analysis.get('statistics', {})
        self.stats_var.set(
            f"📊 Immagini: {stats.get('total_images', 0)} | "
            f"Equazioni: {stats.get('total_equations', 0)} | "
            f"Tabelle: {stats.get('total_tables', 0)}"
        )
        
        self._refresh_elements_list()
    
    def _refresh_elements_list(self):
        """Aggiorna lista elementi"""
        # Pulisci
        for item in self.elements_tree.get_children():
            self.elements_tree.delete(item)
        
        if not self.current_analysis:
            return
        
        # Ottieni elementi del tipo selezionato
        element_type = self.element_type_var.get()
        elements = self.current_analysis.get(element_type, [])
        
        # IMPORTANTE: Limita numero elementi mostrati per performance
        MAX_DISPLAY = 500
        total_elements = len(elements)
        display_elements = elements[:MAX_DISPLAY]
        
        # Avvisa se ci sono troppi elementi
        if total_elements > MAX_DISPLAY:
            messagebox.showinfo("Info", 
                f"Trovati {total_elements} elementi!\n"
                f"Mostro solo i primi {MAX_DISPLAY} per performance.\n"
                f"Usa la ricerca o il batch processing per gestirli tutti.")
        
        # Popola tree
        for elem in display_elements:
            elem_id = elem.get('index', 0)
            label = elem.get('label', f"Element {elem_id}")
            
            # Posizione
            para_idx = elem.get('paragraph_index')
            if para_idx is not None:
                position = f"Para {para_idx}"
            elif elem.get('in_table'):
                position = f"Tab {elem.get('table_index', '?')}"
            else:
                position = "N/A"
            
            # Ha jump?
            has_jump = "✓" if any(j['target_label'] == label for j in self.jumps_created) else ""
            
            self.elements_tree.insert('', tk.END, values=(
                elem_id, label, position, has_jump
            ))
        
        # Aggiorna stats con totale
        if hasattr(self, 'stats_var'):
            stats = self.current_analysis.get('statistics', {})
            self.stats_var.set(
                f"📊 Immagini: {stats.get('total_images', 0)} | "
                f"Equazioni: {stats.get('total_equations', 0)} | "
                f"Tabelle: {stats.get('total_tables', 0)} | "
                f"Mostrando: {len(display_elements)}/{total_elements} {element_type}"
            )
    
    def _refresh_jumps_tree(self):
        """Aggiorna lista jump creati"""
        # Pulisci
        for item in self.jumps_tree.get_children():
            self.jumps_tree.delete(item)
        
        # Popola
        for jump in self.jumps_created:
            source_label = jump['source_element'].get('label', 'N/A')
            
            self.jumps_tree.insert('', tk.END, values=(
                jump['id'],
                jump['type'].capitalize(),
                source_label,
                jump['target_label'],
                '✓' if jump['status'] == 'created' else '⚠'
            ))
