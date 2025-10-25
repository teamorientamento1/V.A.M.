"""
Interfaccia Grafica Principale - UI con Tab
"""
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

# Import core
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import *
from core.knowledge_base import KnowledgeBase
from core.document_analyzer import WordAnalyzer
from modules.jump_manager.jump_creator import JumpManager
from modules.symbol_dictionary.symbol_manager import SymbolDictionary


class AccessibleDocsUI:
    """
    Interfaccia grafica principale del sistema
    
    Struttura:
    - Tab 1: Caricamento documento
    - Tab 2: Analisi risultati
    - Tab 3: Jump Manager
    - Tab 4: Dizionario Simboli
    - Tab 5: Editor Formule
    - Tab 6: Esportazione
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        
        # Inizializza componenti backend
        self.kb = KnowledgeBase()
        self.analyzer = None
        self.jump_manager = None
        self.symbol_dict = SymbolDictionary(self.kb)
        
        # Dati correnti
        self.current_document = None
        self.current_analysis = None
        self.current_discipline = "generic"
        
        # Setup UI
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Log iniziale
        self.log_message("Sistema avviato. Pronto per caricare documenti.")
        self._update_statistics()
    
    def _create_menu(self):
        """Crea menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Carica Documento", command=self.load_document)
        file_menu.add_command(label="Salva Progetto", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.quit_app)
        
        # Knowledge Base menu
        kb_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Knowledge Base", menu=kb_menu)
        kb_menu.add_command(label="Statistiche", command=self.show_kb_stats)
        kb_menu.add_command(label="Crea Backup", command=self.create_backup)
        kb_menu.add_command(label="Ripristina Backup", command=self.restore_backup)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Guida", command=self.show_help)
        help_menu.add_command(label="Info", command=self.show_about)
    
    def _create_main_layout(self):
        """Crea layout principale con notebook (tabs)"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Notebook (tab container)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Crea tabs
        self._create_load_tab()
        self._create_analysis_tab()
        self._create_jump_tab()
        self._create_dictionary_tab()
        self._create_formula_tab()
        self._create_export_tab()
    
    def _create_load_tab(self):
        """Tab 1: Caricamento Documento"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="📁 Carica Documento")
        
        # Title
        title = ttk.Label(tab, text="Carica Documento Word", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=20)
        
        # Discipline selection
        discipline_frame = ttk.LabelFrame(tab, text="Disciplina", padding="10")
        discipline_frame.pack(fill=tk.X, pady=10)
        
        self.discipline_var = tk.StringVar(value="generic")
        for discipline in SUPPORTED_DISCIPLINES:
            ttk.Radiobutton(discipline_frame, text=discipline.replace('_', ' ').title(), 
                          variable=self.discipline_var, value=discipline).pack(anchor=tk.W)
        
        # Load button
        load_btn = ttk.Button(tab, text="Carica Documento Word (.docx)", 
                            command=self.load_document, width=40)
        load_btn.pack(pady=20)
        
        # Status
        self.load_status_var = tk.StringVar(value="Nessun documento caricato")
        status_label = ttk.Label(tab, textvariable=self.load_status_var, 
                               font=('Arial', 10, 'italic'))
        status_label.pack(pady=10)
        
        # Analyze button (disabled initially)
        self.analyze_btn = ttk.Button(tab, text="Analizza Documento", 
                                     command=self.analyze_document, 
                                     state=tk.DISABLED, width=40)
        self.analyze_btn.pack(pady=10)
        
        # Instructions
        instructions = """
Istruzioni:
1. Seleziona la disciplina del documento
2. Carica un file Word (.docx)
3. Clicca "Analizza Documento" per estrarre contenuti
4. Vai alle altre tab per le funzioni specifiche
        """
        ttk.Label(tab, text=instructions, justify=tk.LEFT, 
                 foreground='gray').pack(pady=20)
    
    def _create_analysis_tab(self):
        """Tab 2: Risultati Analisi"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="🔍 Analisi")
        
        # Title
        ttk.Label(tab, text="Risultati Analisi", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(tab, text="Statistiche", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.analysis_text = scrolledtext.ScrolledText(stats_frame, height=20, 
                                                       wrap=tk.WORD, font=('Courier', 10))
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Aggiungi a Knowledge Base", 
                  command=self.learn_from_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Esporta Report", 
                  command=self.export_analysis_report).pack(side=tk.LEFT, padx=5)
    
    def _create_jump_tab(self):
        """Tab 3: Jump Manager"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="🔗 Jump Manager")
        
        ttk.Label(tab, text="Gestione Collegamenti Ipertestuali", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # TODO: Implementare UI per jump manager
        ttk.Label(tab, text="[Funzionalità in sviluppo]", 
                 font=('Arial', 12, 'italic'), foreground='gray').pack(pady=20)
        
        # Placeholder buttons
        ttk.Button(tab, text="Crea Jump per Immagini").pack(pady=5)
        ttk.Button(tab, text="Scansiona Riferimenti").pack(pady=5)
        ttk.Button(tab, text="Valida Collegamenti").pack(pady=5)
    
    def _create_dictionary_tab(self):
        """Tab 4: Dizionario Simboli"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="📖 Dizionario")
        
        ttk.Label(tab, text="Dizionario Simboli e Pronuncia", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Symbol list
        list_frame = ttk.LabelFrame(tab, text="Simboli Trovati", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview for symbols
        columns = ('Simbolo', 'Categoria', 'Pronuncia', 'Occorrenze')
        self.symbols_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.symbols_tree.heading(col, text=col)
            self.symbols_tree.column(col, width=150)
        
        self.symbols_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                 command=self.symbols_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.symbols_tree.configure(yscrollcommand=scrollbar.set)
        
        # Edit pronunciation button
        ttk.Button(tab, text="Modifica Pronuncia", 
                  command=self.edit_pronunciation).pack(pady=10)
    
    def _create_formula_tab(self):
        """Tab 5: Editor Formule"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="∑ Formule")
        
        ttk.Label(tab, text="Gestione Formule Matematiche", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # TODO: Implementare UI per formule
        ttk.Label(tab, text="[Funzionalità in sviluppo]", 
                 font=('Arial', 12, 'italic'), foreground='gray').pack(pady=20)
    
    def _create_export_tab(self):
        """Tab 6: Esportazione"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="💾 Esporta")
        
        ttk.Label(tab, text="Esportazione Documento", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Export options
        options_frame = ttk.LabelFrame(tab, text="Opzioni", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        self.export_with_jumps = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Includi Jump", 
                       variable=self.export_with_jumps).pack(anchor=tk.W)
        
        self.export_with_descriptions = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Includi Descrizioni", 
                       variable=self.export_with_descriptions).pack(anchor=tk.W)
        
        # Export button
        ttk.Button(tab, text="Esporta Documento Elaborato", 
                  command=self.export_document, width=40).pack(pady=20)
    
    def _create_status_bar(self):
        """Crea barra di stato in basso"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # KB stats in status bar
        self.kb_stats_var = tk.StringVar(value="KB: 0 pattern")
        kb_label = ttk.Label(status_frame, textvariable=self.kb_stats_var)
        kb_label.pack(side=tk.RIGHT, padx=5)
    
    # ========== EVENT HANDLERS ==========
    
    def load_document(self):
        """Carica documento Word"""
        filepath = filedialog.askopenfilename(
            title="Seleziona documento Word",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        self.current_document = Path(filepath)
        self.current_discipline = self.discipline_var.get()
        
        # Create analyzer
        self.analyzer = WordAnalyzer(self.kb)
        
        if self.analyzer.load_document(self.current_document):
            self.load_status_var.set(f"Caricato: {self.current_document.name}")
            self.analyze_btn.config(state=tk.NORMAL)
            self.log_message(f"Documento caricato: {self.current_document}")
        else:
            messagebox.showerror("Errore", "Impossibile caricare il documento")
    
    def analyze_document(self):
        """Analizza documento caricato"""
        if not self.analyzer:
            messagebox.showwarning("Attenzione", "Carica prima un documento")
            return
        
        self.status_var.set("Analisi in corso...")
        self.root.update()
        
        try:
            # Run analysis
            self.current_analysis = self.analyzer.analyze(self.current_discipline)
            
            # Show results
            report = self.analyzer.generate_report()
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(1.0, report)
            
            # Switch to analysis tab
            self.notebook.select(1)
            
            self.status_var.set("Analisi completata")
            self.log_message("Analisi documento completata")
            
            # Update symbols tab if any equations found
            if self.current_analysis.get('equations'):
                self._update_symbols_list()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'analisi: {e}")
            self.status_var.set("Errore analisi")
    
    def learn_from_analysis(self):
        """Impara dall'analisi e aggiorna KB"""
        if not self.current_analysis:
            messagebox.showwarning("Attenzione", "Esegui prima l'analisi")
            return
        
        self.status_var.set("Apprendimento in corso...")
        self.root.update()
        
        try:
            patterns_added = self.analyzer.learn_from_analysis(self.current_discipline)
            
            messagebox.showinfo("Successo", 
                              f"Aggiunti {patterns_added} pattern al Knowledge Base")
            self.log_message(f"Aggiunti {patterns_added} pattern al KB")
            self._update_statistics()
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'apprendimento: {e}")
        
        self.status_var.set("Pronto")
    
    def _update_symbols_list(self):
        """Aggiorna lista simboli nella tab dizionario"""
        # Clear existing
        for item in self.symbols_tree.get_children():
            self.symbols_tree.delete(item)
        
        # Scan symbols
        symbols = self.symbol_dict.scan_document_symbols(self.current_analysis)
        
        # Populate treeview
        for symbol, data in symbols.items():
            self.symbols_tree.insert('', tk.END, values=(
                symbol,
                'Math',  # TODO: Determinare categoria
                data['current_pronunciation'],
                data['count']
            ))
    
    def edit_pronunciation(self):
        """Modifica pronuncia simbolo selezionato"""
        selection = self.symbols_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un simbolo")
            return
        
        # Get selected symbol
        item = self.symbols_tree.item(selection[0])
        symbol = item['values'][0]
        current_pronunciation = item['values'][2]
        
        # TODO: Aprire dialog per modificare pronuncia
        new_pronunciation = tk.simpledialog.askstring(
            "Modifica Pronuncia",
            f"Pronuncia per '{symbol}':",
            initialvalue=current_pronunciation
        )
        
        if new_pronunciation:
            self.symbol_dict.set_pronunciation(symbol, new_pronunciation)
            self._update_symbols_list()
            self.log_message(f"Pronuncia aggiornata: {symbol} → {new_pronunciation}")
    
    def export_analysis_report(self):
        """Esporta report analisi"""
        if not self.current_analysis:
            messagebox.showwarning("Attenzione", "Nessuna analisi disponibile")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if filepath:
            report = self.analyzer.generate_report()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            self.log_message(f"Report esportato: {filepath}")
            messagebox.showinfo("Successo", "Report esportato")
    
    def export_document(self):
        """Esporta documento elaborato"""
        # TODO: Implementare export completo
        messagebox.showinfo("Info", "Funzione in sviluppo")
    
    def create_backup(self):
        """Crea backup del KB"""
        try:
            backup_path = self.kb.create_backup('full')
            messagebox.showinfo("Successo", f"Backup creato:\n{backup_path}")
            self.log_message(f"Backup creato: {backup_path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante backup: {e}")
    
    def restore_backup(self):
        """Ripristina backup"""
        filepath = filedialog.askopenfilename(
            title="Seleziona backup",
            filetypes=[("Database Files", "*.db"), ("All Files", "*.*")],
            initialdir=BACKUP_DIR
        )
        
        if filepath:
            if messagebox.askyesno("Conferma", 
                                   "Ripristinare questo backup? Il KB attuale verrà sostituito."):
                try:
                    self.kb.restore_backup(Path(filepath))
                    messagebox.showinfo("Successo", "Backup ripristinato")
                    self.log_message(f"Backup ripristinato: {filepath}")
                    self._update_statistics()
                except Exception as e:
                    messagebox.showerror("Errore", f"Errore durante ripristino: {e}")
    
    def show_kb_stats(self):
        """Mostra statistiche KB"""
        stats = self.kb.get_statistics()
        
        stats_text = "=== STATISTICHE KNOWLEDGE BASE ===\n\n"
        stats_text += f"Pattern per disciplina:\n"
        for disc, count in stats['patterns_by_discipline'].items():
            stats_text += f"  - {disc}: {count}\n"
        stats_text += f"\nSimboli totali: {stats['total_symbols']}\n"
        stats_text += f"Documenti analizzati: {stats['documents_analyzed']}\n"
        stats_text += f"\nTop pattern types:\n"
        for ptype, count in stats['top_pattern_types'].items():
            stats_text += f"  - {ptype}: {count}\n"
        
        messagebox.showinfo("Statistiche Knowledge Base", stats_text)
    
    def _update_statistics(self):
        """Aggiorna statistiche nella status bar"""
        stats = self.kb.get_statistics()
        total_patterns = sum(stats['patterns_by_discipline'].values())
        self.kb_stats_var.set(f"KB: {total_patterns} pattern, {stats['total_symbols']} simboli")
    
    def show_help(self):
        """Mostra guida"""
        help_text = """
GUIDA RAPIDA

1. CARICARE DOCUMENTO
   - Seleziona disciplina
   - Carica file .docx
   - Clicca "Analizza"

2. KNOWLEDGE BASE
   - Aggiungi pattern analizzati al KB
   - Il KB crescerà con ogni documento

3. JUMP MANAGER
   - Crea collegamenti per immagini
   - Gestisci riferimenti

4. DIZIONARIO
   - Personalizza pronuncia simboli
   - Gestisci apici/pedici

5. BACKUP
   - Backup automatici ogni ora
   - Manuale: Menu → KB → Crea Backup
        """
        messagebox.showinfo("Guida", help_text)
    
    def show_about(self):
        """Mostra info"""
        about_text = f"""
Accessible Docs System
Versione 1.0

Sistema per rendere accessibili documenti
scientifici a persone non vedenti.

Knowledge Base: {DATABASE_PATH}
Backup: ogni {AUTO_BACKUP_INTERVAL//60} minuti
        """
        messagebox.showinfo("Info", about_text)
    
    def save_project(self):
        """Salva progetto corrente"""
        # TODO: Implementare save/load progetto
        messagebox.showinfo("Info", "Funzione in sviluppo")
    
    def log_message(self, message: str):
        """Aggiunge messaggio al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def quit_app(self):
        """Chiude applicazione"""
        if messagebox.askyesno("Conferma", "Uscire dall'applicazione?"):
            self.kb.close()
            self.root.quit()


def main():
    """Entry point"""
    root = tk.Tk()
    app = AccessibleDocsUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
