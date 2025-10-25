# Accessible Docs System

Sistema modulare per rendere accessibili documenti scientifici a persone non vedenti o con problemi alla vista.

## 🎯 Obiettivi

1. **Convertire PDF matematici in Word** con equazioni Office Math
2. **Creare collegamenti ipertestuali (jump)** da immagini a descrizioni
3. **Gestire dizionario simboli** per personalizzare sintesi vocale
4. **Costruire archivio conoscenze** multidisciplinare che migliora nel tempo

## 🏗️ Architettura

```
accessible-docs-system/
├── core/                   # Motore principale
│   ├── knowledge_base.py   # Database con backup automatico
│   ├── document_analyzer.py # Analisi Word
│   └── database_schema.py  # Schema DB multidisciplinare
│
├── modules/                # Funzionalità modulari
│   ├── jump_manager/       # Collegamenti ipertestuali
│   ├── symbol_dictionary/  # Dizionario simboli/pronuncia
│   ├── content_processor/  # Elaborazione contenuti
│   └── pdf_converter/      # Conversione PDF → Word (futuro)
│
├── ui/                     # Interfaccia grafica
│   ├── main_window.py      # Finestra principale con tab
│   ├── tabs/               # Tab specifiche
│   └── widgets/            # Componenti riutilizzabili
│
├── data/                   # Dati persistenti
│   ├── knowledge_base/     # Database SQLite
│   ├── backups/            # Backup automatici
│   └── user_data/          # Preferenze utente
│
└── config/                 # Configurazione
    └── settings.py         # Impostazioni globali
```

## 🚀 Quick Start

### Installazione

```bash
# Clone o download del progetto
cd accessible-docs-system

# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python ui/main_window.py
```

### Primo Utilizzo

1. **Carica documento Word**
   - Tab "Carica Documento"
   - Seleziona disciplina
   - Carica file .docx
   - Clicca "Analizza"

2. **Costruisci Knowledge Base**
   - Tab "Analisi"
   - Rivedi risultati
   - Clicca "Aggiungi a Knowledge Base"
   - Il sistema impara dai tuoi documenti!

3. **Gestisci simboli**
   - Tab "Dizionario"
   - Personalizza pronuncia simboli
   - Salva preferenze studente

## 📊 Knowledge Base

### Struttura Multidisciplinare

Il Knowledge Base supporta:
- **Matematica**: formule, teoremi, dimostrazioni
- **Fisica**: leggi, costanti, unità di misura
- **Chimica**: formule molecolari, reazioni
- **Biologia**: nomenclatura, processi
- **Ingegneria**: calcoli, schemi
- **Informatica**: algoritmi, pseudocodice
- **Statistica**: distribuzioni, test
- **Generic**: contenuti non specifici

### Apprendimento Progressivo

Il sistema impara in **due fasi**:

#### FASE 1: Costruzione (da Word editati)
```
Word con equazioni → Analisi → Estrazione pattern → Salva in KB
```
- Estrae tutte le equazioni Office Math
- Analizza struttura (frazioni, integrali, matrici)
- Salva contesto testuale
- Cataloga simboli usati

#### FASE 2: Riconoscimento (da PDF nuovi)
```
PDF → OCR matematico → Consulta KB → Match pattern → Word output
```
- OCR specializzato per matematica
- Cerca pattern simili nel KB
- Migliora riconoscimento con esperienza
- Converte in equazioni Word

### Backup Automatico

- **Backup automatici** ogni ora (configurabile)
- **Backup incrementali** per efficienza
- **Retention**: 30 giorni (configurabile)
- **Checksum** per integrità
- **Ripristino** da UI

```python
# Manuale
kb.create_backup('full')  # Backup completo
kb.create_backup('incremental')  # Solo cambiamenti

# Ripristino
kb.restore_backup(backup_path)
```

## 🔧 Moduli Principali

### 1. Document Analyzer

Estrae da Word:
- ✅ Equazioni matematiche (Office Math)
- ✅ Immagini e figure
- ✅ Tabelle
- ✅ Riferimenti (Fig.X, Eq.Y)
- ✅ Struttura testo (headings, paragrafi)

```python
from core.document_analyzer import WordAnalyzer

analyzer = WordAnalyzer(knowledge_base)
analyzer.load_document("documento.docx")
analysis = analyzer.analyze(discipline="mathematics")

# Impara e aggiungi al KB
patterns_added = analyzer.learn_from_analysis()
```

### 2. Jump Manager

Crea collegamenti ipertestuali:
- Da immagini a descrizioni
- Da riferimenti nel testo agli elementi
- Link di ritorno con blocco TTS

```python
from modules.jump_manager.jump_creator import JumpManager

jump_mgr = JumpManager(document)
jump_mgr.create_image_jumps(images, descriptions)
jump_mgr.scan_and_create_reference_jumps(references)
```

**Funzionalità**:
- Trova automaticamente label (Fig.2.5)
- Scansiona contesto per altri riferimenti
- Crea sezione descrizioni alla fine
- Aggiunge link ritorno con tag TTS-block

### 3. Symbol Dictionary

Gestisce pronuncia simboli per TTS:
- Dizionario default (simboli comuni)
- Personalizzazione per studente
- Pronuncia context-aware
- Gestione apici/pedici

```python
from modules.symbol_dictionary.symbol_manager import SymbolDictionary

symbol_dict = SymbolDictionary(knowledge_base)

# Scansiona documento
symbols = symbol_dict.scan_document_symbols(analysis)

# Personalizza
symbol_dict.set_pronunciation("α", "alfa", context="velocità")
symbol_dict.set_pronunciation("d", "differenziale", context="dx")
```

### 4. Knowledge Base

Database centrale con:
- Pattern multidisciplinari
- Simboli catalogati
- Contesti di apprendimento
- Relazioni tra pattern
- Change log per audit
- Sistema backup integrato

```python
from core.knowledge_base import KnowledgeBase

with KnowledgeBase() as kb:
    # Aggiungi pattern
    pattern_id = kb.add_pattern(
        discipline="mathematics",
        pattern_type="definite_integral",
        latex="\\int_{a}^{b} f(x) dx",
        mathml="...",
        context_words=["area", "curva"]
    )
    
    # Cerca simili
    matches = kb.find_similar_patterns(
        latex="integral",
        discipline="mathematics"
    )
    
    # Statistiche
    stats = kb.get_statistics()
```

## ⚙️ Configurazione

Modifica `config/settings.py`:

```python
# Backup
AUTO_BACKUP_INTERVAL = 3600  # secondi
BACKUP_RETENTION_DAYS = 30

# Analisi
CONTEXT_RADIUS = 150  # caratteri contesto
MIN_PATTERN_FREQUENCY = 3

# Jump
JUMP_PREFIX = "DESC_"
RETURN_TEXT = "↑ Torna al testo"
BLOCK_TTS_TAG = "<!--TTS:SKIP-->"

# OCR (futuro)
USE_MATHPIX = False
MATHPIX_API_KEY = None
```

## 🎨 Interfaccia Utente

### Tab 1: Carica Documento
- Selezione disciplina
- Caricamento .docx
- Pulsante analisi

### Tab 2: Analisi
- Statistiche documento
- Elementi trovati
- Report dettagliato
- Aggiungi a KB

### Tab 3: Jump Manager
- Gestione collegamenti
- Validazione jump
- Creazione descrizioni

### Tab 4: Dizionario
- Lista simboli trovati
- Modifica pronuncia
- Salva preferenze

### Tab 5: Formule
- Editor formule
- Conversione LaTeX
- Preview rendering

### Tab 6: Esporta
- Opzioni export
- Salva elaborato
- Formati disponibili

## 🔮 Sviluppi Futuri

### PDF Converter (Priorità Alta)
```python
# modules/pdf_converter/pdf_to_word.py
from modules.pdf_converter import PDFConverter

converter = PDFConverter(knowledge_base)
word_doc = converter.convert_pdf("matematica.pdf", discipline="mathematics")
```

**Features**:
- OCR matematico (Mathpix/Tesseract+)
- Layout analysis per identificare aree matematiche
- Consulta KB per pattern matching
- Confidence scoring
- Richiesta conferma utente per pattern incerti

### Funzionalità Avanzate
- [ ] Vector search per similarity (FAISS/ChromaDB)
- [ ] ML per riconoscimento pattern
- [ ] Export multi-formato (EPUB, HTML accessibile)
- [ ] Integrazione con screen reader
- [ ] API REST per automazione
- [ ] Plugin per Word/LibreOffice

### Miglioramenti UI
- [ ] PyQt6 per UI professionale
- [ ] Preview in tempo reale
- [ ] Drag & drop
- [ ] Batch processing
- [ ] Progress bars dettagliate

## 📝 Workflow Completo

```
1. FASE COSTRUZIONE KB
   ┌─────────────┐
   │ Word editati│ (già con equazioni corrette)
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  ANALIZZA   │ WordAnalyzer
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ AGGIUNGI KB │ learn_from_analysis()
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   ARCHIVIO  │ Pattern, simboli, contesti
   └─────────────┘

2. FASE UTILIZZO
   ┌─────────────┐
   │  PDF nuovo  │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ OCR + KB    │ PDFConverter consulta archivio
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Word output │ Con equazioni Office Math
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ ELABORA     │ Jump + Dizionario + Edit
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  ACCESSIBILE│ Pronto per studente
   └─────────────┘
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Con coverage
pytest --cov=core --cov=modules tests/
```

## 📄 Licenza

[Da definire]

## 👥 Contributi

Progetto modulare aperto a estensioni. Per aggiungere funzionalità:
1. Crea nuovo modulo in `modules/`
2. Implementa interfaccia standard
3. Aggiungi tab UI se necessario
4. Aggiorna documentazione

## 🆘 Supporto

Per problemi o domande:
- Controlla documentazione in `docs/`
- Verifica log in `logs/system.log`
- Issues/PR su repository

---

**Note**: Sistema in sviluppo attivo. Molte funzionalità (PDF converter, editor formule avanzato) sono in fase di implementazione. Lo scheletro modulare permette sviluppo incrementale.
