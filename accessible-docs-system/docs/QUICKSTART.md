# Quick Start Guide - Per Sviluppatori

Guida rapida per iniziare a lavorare sul progetto.

## Setup Iniziale (5 minuti)

```bash
# 1. Naviga nella directory
cd accessible-docs-system

# 2. Crea virtual environment (consigliato)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Installa dipendenze
pip install python-docx  # Minimo per iniziare

# Opzionale: tutte le dipendenze
pip install -r requirements.txt

# 4. Test sistema
python tests/test_system.py

# 5. Avvia UI
python main.py
```

## 🎯 Primo Compito: Completare Image Extraction

**Obiettivo**: Far funzionare l'estrazione immagini dal Word

**File**: `core/document_analyzer.py`

**Metodo da completare**: `_extract_images()`

### Step-by-step

```python
def _extract_images(self) -> List[Dict]:
    """Estrae immagini dal documento"""
    images = []
    image_index = 0
    
    # Usa python-docx per accedere alle immagini
    # Le immagini in .docx sono nelle "relationships"
    for rel in self.document.part.rels.values():
        if "image" in rel.target_ref:
            image_index += 1
            
            # Estrai dati immagine
            image_data = {
                'index': image_index,
                'filename': rel.target_ref.split('/')[-1],
                'content_type': rel.target_part.content_type,
                'image_data': rel.target_part.blob,  # bytes dell'immagine
                'paragraph_index': None,  # TODO: trovare dove si trova
                'label': None,  # TODO: cercare "Fig.X" vicino
                'has_caption': False
            }
            
            images.append(image_data)
    
    return images
```

### Test

```python
# In Python console
from core.knowledge_base import KnowledgeBase
from core.document_analyzer import WordAnalyzer

kb = KnowledgeBase()
analyzer = WordAnalyzer(kb)
analyzer.load_document("path/to/documento_con_immagini.docx")
result = analyzer.analyze()

print(f"Immagini trovate: {len(result['images'])}")
for img in result['images']:
    print(f"  - {img['filename']}")
```

## 🎯 Secondo Compito: Hyperlinks in Word

**Obiettivo**: Creare collegamenti ipertestuali funzionanti

**File**: `modules/jump_manager/jump_creator.py`

**Metodo da completare**: `create_hyperlink()`

### Codice di base

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def create_hyperlink(self, paragraph, run_text, anchor_name):
    """Crea hyperlink a bookmark"""
    
    # Crea elemento hyperlink
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('w:anchor'), anchor_name)
    
    # Crea run con testo
    new_run = OxmlElement('w:r')
    
    # Style come link
    rPr = OxmlElement('w:rPr')
    rStyle = OxmlElement('w:rStyle')
    rStyle.set(qn('w:val'), 'Hyperlink')
    rPr.append(rStyle)
    new_run.append(rPr)
    
    # Aggiungi testo
    text_elem = OxmlElement('w:t')
    text_elem.text = run_text
    new_run.append(text_elem)
    
    # Assembla
    hyperlink.append(new_run)
    paragraph._element.append(hyperlink)
    
    return hyperlink

def create_bookmark(self, paragraph, bookmark_name):
    """Crea bookmark in paragrafo"""
    
    # Bookmark start
    bookmark_start = OxmlElement('w:bookmarkStart')
    bookmark_start.set(qn('w:id'), '0')
    bookmark_start.set(qn('w:name'), bookmark_name)
    
    # Bookmark end
    bookmark_end = OxmlElement('w:bookmarkEnd')
    bookmark_end.set(qn('w:id'), '0')
    
    # Inserisci nel paragrafo
    paragraph._element.append(bookmark_start)
    paragraph._element.append(bookmark_end)
    
    return bookmark_start
```

### Test

```python
from docx import Document
from modules.jump_manager.jump_creator import JumpManager

doc = Document()

# Crea bookmark
para1 = doc.add_paragraph("Questo è il target")
jump_mgr = JumpManager(doc)
jump_mgr.create_bookmark(para1, "target_1")

# Crea link
para2 = doc.add_paragraph("Clicca qui: ")
jump_mgr.create_hyperlink(para2, "VAI AL TARGET", "target_1")

doc.save("test_jumps.docx")
# Apri in Word e testa!
```

## 🎯 Terzo Compito: Symbol Pronunciation Context-Aware

**Obiettivo**: Pronuncia intelligente basata su contesto

**File**: `modules/symbol_dictionary/symbol_manager.py`

**Metodo da migliorare**: `_get_pronunciation()`

### Esempio Implementazione

```python
def _get_pronunciation(self, symbol: str, context: Optional[str] = None) -> str:
    """Pronuncia context-aware"""
    
    # Context rules
    if context and symbol in self.context_rules:
        for rule in self.context_rules[symbol]:
            if rule['pattern'] in context:
                return rule['pronunciation']
    
    # Regole hard-coded comuni
    if symbol == 'd':
        # In 'dx', 'dy' -> differenziale
        if context and re.search(r'd[a-z]', context):
            return 'differenziale di'
        else:
            return 'di'
    
    if symbol == 'x' and context:
        # Cerca apici
        if '²' in context or '^2' in context:
            return 'x al quadrato'
        elif '³' in context or '^3' in context:
            return 'x al cubo'
    
    # User preferences
    if symbol in self.user_preferences:
        return self.user_preferences[symbol][0]['pronunciation']
    
    # Default
    return self.default_mappings.get(symbol, f"simbolo {symbol}")
```

### Test

```python
from core.knowledge_base import KnowledgeBase
from modules.symbol_dictionary.symbol_manager import SymbolDictionary

kb = KnowledgeBase()
sym_dict = SymbolDictionary(kb)

# Test pronuncia context-aware
print(sym_dict._get_pronunciation('d', context='dx'))  # "differenziale di"
print(sym_dict._get_pronunciation('d', context='variabile d'))  # "di"
print(sym_dict._get_pronunciation('x', context='x²'))  # "x al quadrato"
```

## 📦 Struttura Workflow

### 1. Mattina: Setup e comprensione

```bash
# Leggi documentazione
cat README.md
cat docs/DEVELOPMENT.md

# Esplora codice
ls -R core/ modules/ ui/

# Studia un modulo
cat core/document_analyzer.py
```

### 2. Pomeriggio: Implementazione

```bash
# Crea branch
git checkout -b feature/image-extraction

# Implementa feature
# Edit core/document_analyzer.py

# Test
python tests/test_system.py

# Commit
git add .
git commit -m "feat: Implement image extraction from Word"
```

### 3. Sera: Testing e refactoring

```bash
# Test su documenti reali
python -c "
from core.knowledge_base import KnowledgeBase
from core.document_analyzer import WordAnalyzer

kb = KnowledgeBase()
analyzer = WordAnalyzer(kb)
analyzer.load_document('test.docx')
result = analyzer.analyze()
print(result['statistics'])
"

# Run tutti i test
pytest tests/

# Cleanup code
black core/ modules/
```

## 🐛 Debug Tips

### Print XML di equazioni

```python
eq_elem = # ... ottieni elemento Office Math
print(eq_elem.xml)

# Pretty print
from xml.dom import minidom
pretty = minidom.parseString(eq_elem.xml).toprettyxml()
print(pretty)
```

### Inspect documento Word

```python
from docx import Document

doc = Document('file.docx')

# Lista tutti i paragrafi
for i, para in enumerate(doc.paragraphs):
    print(f"{i}: {para.text[:50]}")

# Lista relationships (per immagini)
for rel in doc.part.rels.values():
    print(f"{rel.target_ref} - {rel.reltype}")

# Accedi a elementi XML direttamente
for para in doc.paragraphs:
    for elem in para._element.iter():
        if 'oMath' in elem.tag:
            print("Found equation!")
```

### Database queries

```python
from core.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

# Query diretta SQL
cursor = kb.connection.cursor()
cursor.execute("SELECT * FROM content_patterns LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

# Statistiche
stats = kb.get_statistics()
print(stats)
```

## 📝 Coding Checklist

Prima di ogni commit:

- [ ] Codice funziona (testato manualmente)
- [ ] Docstrings aggiunti/aggiornati
- [ ] TODOs ridotti (o almeno descritti meglio)
- [ ] Print statements di debug rimossi
- [ ] Nessun import inutilizzato
- [ ] Nomi variabili chiari
- [ ] Errori gestiti con try/except dove necessario

## 🎓 Learning Path

### Settimana 1: Core
- [ ] Capire Knowledge Base
- [ ] Completare Document Analyzer
- [ ] Test con documenti veri

### Settimana 2: Modules
- [ ] Implementare Jump Manager
- [ ] Completare Symbol Dictionary
- [ ] Integrare tutto

### Settimana 3: PDF
- [ ] Setup OCR
- [ ] Layout analysis
- [ ] Prima versione PDF converter

### Settimana 4+: Polish
- [ ] UI improvements
- [ ] Batch processing
- [ ] Documentation
- [ ] Release 1.0

## 🚀 Quick Commands

```bash
# Run app
python main.py

# Run tests
python tests/test_system.py

# Interactive testing
python -i
>>> from core import *
>>> kb = KnowledgeBase()
>>> # ... play around

# Check code quality
black --check .
flake8 --max-line-length=100 core/ modules/

# Backup KB manualmente
python -c "from core import KnowledgeBase; kb = KnowledgeBase(); kb.create_backup('full')"
```

## 💬 Need Help?

1. Leggi i TODO nei file sorgente
2. Consulta docs/DEVELOPMENT.md
3. Cerca esempi simili nel codice esistente
4. Aggiungi print() per debug
5. Test su documenti semplici prima

## 🎉 Primo Milestone

**Goal**: Far funzionare il flusso completo Word → Analisi → KB → Jump

Quando riesci a:
1. Caricare un Word con equazioni
2. Analizzarlo e vedere risultati
3. Aggiungere pattern al KB
4. Creare jump funzionanti (anche se semplici)

...allora sei pronto per il PDF converter! 🚀

---

**Happy Coding!** 🎨✨
