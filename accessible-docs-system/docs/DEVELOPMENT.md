# Guida Sviluppo - Accessible Docs System

## 🎯 Stato Attuale

### ✅ Completato

1. **Architettura Modulare**
   - Struttura directory completa
   - Separazione concerns (core/modules/ui)
   - Package system con __init__.py

2. **Knowledge Base**
   - Database SQLite con schema multidisciplinare
   - Sistema backup automatico (ogni ora)
   - Change log per audit
   - Gestione discipline multiple
   - CRUD pattern completo
   - Statistics e query

3. **Document Analyzer (Word)**
   - Caricamento documenti .docx
   - Estrazione equazioni (Office Math)
   - Rilevamento immagini (stub)
   - Estrazione tabelle
   - Find references (Fig.X, Eq.Y)
   - Analisi struttura testo
   - Learn from analysis (salva in KB)

4. **Symbol Dictionary**
   - Dizionario default simboli comuni
   - Scan simboli da documento
   - Gestione pronuncia personalizzata
   - User preferences
   - Export mapping TTS

5. **Jump Manager (stub)**
   - Struttura classi
   - Metodi placeholder
   - Scan context for references

6. **UI (Tkinter)**
   - Finestra principale con 6 tab
   - Menu bar completo
   - Status bar con stats KB
   - Tab Caricamento
   - Tab Analisi con scrolled text
   - Tab Dizionario con treeview
   - Altre tab placeholder

## 🚧 Da Completare (Priorità)

### PRIORITÀ 1 - Funzionalità Core

#### 1.1 Document Analyzer - Completare Estrazione

**File**: `core/document_analyzer.py`

```python
def _extract_images(self) -> List[Dict]:
    """COMPLETARE: Estrazione immagini vere"""
    # TODO: Usare python-docx per accedere a w:drawing elements
    # TODO: Estrarre:
    #   - Image data (bytes)
    #   - Position nel documento
    #   - Dimensioni
    #   - Caption se presente
    #   - Relazione con paragrafi circostanti
    pass

def _parse_equation(self, omath_elem, paragraph):
    """MIGLIORARE: Conversione MathML -> LaTeX completa"""
    # TODO: Implementare parser OMML -> LaTeX robusto
    # TODO: Gestire tutti gli elementi Office Math:
    #   - Frazioni (m:f)
    #   - Radici (m:rad)
    #   - Apici/pedici (m:sSup, m:sSub)
    #   - Integrali/Sommatorie
    #   - Matrici (m:m)
    #   - Delimiter (parentesi, brackets)
    # Riferimento: Office MathML spec
    pass
```

**Test**: Creare `tests/test_word_analyzer.py`

#### 1.2 Jump Manager - Implementare Funzioni

**File**: `modules/jump_manager/jump_creator.py`

```python
def create_hyperlink(self, paragraph, run_text, anchor_name):
    """IMPLEMENTARE: Creazione hyperlink via XML"""
    # Riferimenti:
    # https://github.com/python-openxml/python-docx/issues/74
    # 
    # Codice XML necessario:
    # <w:hyperlink w:anchor="bookmark_name">
    #   <w:r><w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>
    #     <w:t>link text</w:t>
    #   </w:r>
    # </w:hyperlink>
    pass

def create_bookmark(self, paragraph, bookmark_name):
    """IMPLEMENTARE: Creazione bookmark via XML"""
    # XML necessario:
    # <w:bookmarkStart w:id="0" w:name="bookmark_name"/>
    # <w:bookmarkEnd w:id="0"/>
    pass

# Poi completare tutti i metodi create_image_jumps(), etc.
```

**Test**: Creare documento test con immagini e verificare jump

#### 1.3 Symbol Dictionary - Pronuncia Context-Aware

**File**: `modules/symbol_dictionary/symbol_manager.py`

```python
def _get_pronunciation(self, symbol, context):
    """MIGLIORARE: Context-aware pronunciation"""
    # TODO: Implementare regole:
    # - 'd' in 'dx' -> 'differenziale di x'
    # - 'd' come variabile -> 'di'
    # - '∫' con estremi -> 'integrale da ... a ...'
    # - 'x²' -> 'x al quadrato' (non 'x alla seconda')
    # - 'xⁿ' -> 'x alla n-esima'
    # 
    # Usare regex patterns per context matching
    pass

def identify_subscripts_superscripts(self, text):
    """IMPLEMENTARE: Identificazione apici/pedici"""
    # Unicode subscript: ₀₁₂₃₄₅₆₇₈₉
    # Unicode superscript: ⁰¹²³⁴⁵⁶⁷⁸⁹
    # 
    # Ma anche da XML equazioni Office Math:
    # <m:sSup> per superscript
    # <m:sSub> per subscript
    pass
```

### PRIORITÀ 2 - PDF Converter (Il Cuore del Progetto)

**File**: `modules/pdf_converter/pdf_to_word.py` (DA CREARE)

```python
class PDFConverter:
    """
    Converte PDF in Word usando Knowledge Base
    """
    
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.ocr_engine = self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Setup OCR matematico"""
        # Opzione 1: Mathpix API (migliore, ma a pagamento)
        if USE_MATHPIX and MATHPIX_API_KEY:
            from mathpix import MathpixOCR
            return MathpixOCR(api_key=MATHPIX_API_KEY)
        
        # Opzione 2: Tesseract + post-processing
        else:
            import pytesseract
            # Setup tesseract con training data per matematica
            # https://github.com/tesseract-ocr/tessdata
            return pytesseract
    
    def convert_pdf_to_word(self, pdf_path, discipline="generic"):
        """IMPLEMENTARE: Conversione completa"""
        # 1. Extract pages as images
        pages = self._extract_pages(pdf_path)
        
        # 2. Per ogni pagina:
        for page in pages:
            # 2a. Layout analysis - identifica regioni
            regions = self._analyze_layout(page)
            #     - Text regions
            #     - Math regions (formule)
            #     - Image regions
            #     - Table regions
            
            # 2b. OCR per testo normale
            text_content = self._ocr_text(text_regions)
            
            # 2c. OCR matematico per formule
            for math_region in math_regions:
                # OCR -> LaTeX candidate
                latex = self._ocr_math(math_region)
                
                # 2d. CONSULTA KNOWLEDGE BASE
                matches = self.kb.find_similar_patterns(
                    latex=latex,
                    visual_signature=hash(math_region.image),
                    context=text_around_region,
                    discipline=discipline
                )
                
                # 2e. Score e selezione best match
                best_match = self._select_best_match(matches, latex)
                
                # 2f. Se confidence bassa -> chiedi conferma utente
                if best_match.confidence < THRESHOLD:
                    confirmed = self._ask_user_confirmation(
                        math_region.image,
                        best_match.latex,
                        alternatives=[m.latex for m in matches[:3]]
                    )
                
                # 2g. Converti in equazione Word
                word_equation = self._create_word_equation(best_match.mathml)
                
                # 2h. REINFORCEMENT: Aggiorna KB
                self.kb.update_pattern_frequency(best_match.id)
            
            # 2i. Ricostruisci layout in Word
            word_page = self._rebuild_layout(
                text_content, 
                word_equations, 
                images, 
                tables
            )
        
        # 3. Salva Word
        word_doc.save(output_path)
        
        return word_doc
    
    def _analyze_layout(self, page_image):
        """IMPLEMENTARE: Analisi layout pagina"""
        # Usa CV per identificare regioni
        # Opzioni:
        # - pdfplumber per bbox detection
        # - OpenCV per contour detection
        # - Modello ML pre-trained (LayoutParser)
        pass
    
    def _detect_math_regions(self, page_image):
        """IMPLEMENTARE: Rilevamento aree matematiche"""
        # Euristiche:
        # - Densità simboli speciali
        # - Font diverso (italic, symbol fonts)
        # - Presenza frazioni (linee orizzontali)
        # - Apici/pedici (bounding boxes offset)
        # - Parentesi annidate
        # - Allineamento centrato
        # 
        # ML approach:
        # - Train classifier su dataset di pagine miste
        # - Input: region features
        # - Output: probability(is_math)
        pass
    
    def _ocr_math(self, math_region):
        """IMPLEMENTARE: OCR matematico"""
        if isinstance(self.ocr_engine, MathpixOCR):
            # Mathpix API
            result = self.ocr_engine.latex(
                image=math_region.image,
                options={
                    'math_inline_delimiters': ['$', '$'],
                    'rm_spaces': True
                }
            )
            return result.latex
        else:
            # Tesseract + post-processing
            # Più complesso, serve molto lavoro
            pass
    
    def _select_best_match(self, matches, ocr_latex):
        """IMPLEMENTARE: Selezione best match"""
        # Scoring basato su:
        # - LaTeX similarity (edit distance)
        # - Visual similarity (se disponibile)
        # - Context match
        # - Frequency nel KB (pattern più usati = più probabili)
        # - Confidence OCR
        # 
        # Formula esempio:
        # score = 0.4 * latex_sim + 0.3 * visual_sim + 
        #         0.2 * context_sim + 0.1 * log(frequency)
        pass
    
    def _create_word_equation(self, mathml):
        """IMPLEMENTARE: Conversione MathML -> Word Equation"""
        # Office Math usa OMML (Office MathML)
        # Conversione LaTeX -> OMML:
        # 1. LaTeX -> MathML standard (usando latex2mathml)
        # 2. MathML -> OMML (transformazione XML)
        # 
        # Inserire in documento:
        # paragraph._element.append(omml_element)
        pass
```

**Dipendenze Aggiuntive**:
```
pip install pdfplumber pymupdf mathpix Pillow opencv-python
```

**Tests**: Creare suite test con PDF campione

### PRIORITÀ 3 - UI Miglioramenti

#### 3.1 PyQt Migration (Opzionale ma Consigliato)

Tkinter è limitato. PyQt6 offre:
- UI più professionale
- Widget avanzati
- Styling completo (CSS-like)
- Threading migliore
- WebView (per preview)

**Se si migra**: Creare `ui/qt_main_window.py`

#### 3.2 Preview Features

```python
# ui/widgets/equation_preview.py
class EquationPreview(ttk.Frame):
    """Widget per preview equazioni"""
    # Opzioni:
    # 1. Render LaTeX to image (matplotlib)
    # 2. MathJax in webview
    # 3. Office Math rendering (se disponibile)
```

#### 3.3 Batch Processing

```python
# ui/tabs/batch_tab.py
class BatchProcessingTab:
    """Tab per elaborazione batch di documenti"""
    def process_folder(self, folder_path):
        # Processa tutti i .docx o .pdf in una cartella
        # Progress bar
        # Log risultati
        pass
```

## 📋 Checklist Implementazione

### Fase 1: Completare Analyzer
- [ ] Estrazione immagini completa
- [ ] Parser OMML->LaTeX robusto
- [ ] Estrazione caption/label immagini
- [ ] Test con documenti reali

### Fase 2: Jump Manager Funzionante
- [ ] Implementare hyperlink XML
- [ ] Implementare bookmark XML
- [ ] Create image jumps
- [ ] Scan e link riferimenti
- [ ] TTS block markers
- [ ] Test validazione

### Fase 3: PDF Converter
- [ ] Setup OCR (Mathpix o Tesseract)
- [ ] Layout analysis
- [ ] Math region detection
- [ ] OCR matematico
- [ ] KB pattern matching
- [ ] User confirmation UI
- [ ] LaTeX->OMML conversion
- [ ] Word reconstruction
- [ ] Test con vari PDF

### Fase 4: Polish & Features
- [ ] Symbol context-aware pronunciation
- [ ] Batch processing
- [ ] Export formats (EPUB, HTML)
- [ ] Vector search (FAISS)
- [ ] ML pattern recognition
- [ ] API REST

## 🔬 Test Strategy

### Unit Tests
Creare in `tests/`:
- `test_knowledge_base.py` ✅
- `test_word_analyzer.py`
- `test_jump_manager.py`
- `test_symbol_dictionary.py`
- `test_pdf_converter.py`

### Integration Tests
- End-to-end: PDF -> Analysis -> KB -> Word output
- UI tests con pytest-qt

### Test Data
Creare `tests/data/`:
- `sample_math.docx` - Documento con equazioni
- `sample_physics.docx` - Fisica con formule
- `sample_math.pdf` - PDF da convertire
- `sample_with_images.docx` - Con figure

## 📚 Risorse Utili

### Office Math (OMML)
- [Office MathML Spec](https://docs.microsoft.com/en-us/openspecs/office_standards/ms-omml/4b43d0e8-d8ca-4f7f-9842-9a43c62d66e1)
- [python-docx issues on math](https://github.com/python-openxml/python-docx/issues)

### OCR Matematico
- [Mathpix API](https://mathpix.com/ocr)
- [LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) - Open source alternative
- [InftyReader](http://www.inftyproject.org/) - Commercial

### LaTeX/MathML
- [latex2mathml](https://github.com/roniemartinez/latex2mathml)
- [MathJax](https://www.mathjax.org/)
- [KaTeX](https://katex.org/)

### Layout Analysis
- [LayoutParser](https://github.com/Layout-Parser/layout-parser)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [PyMuPDF](https://pymupdf.readthedocs.io/)

### Accessibility
- [NVDA Screen Reader](https://www.nvaccess.org/)
- [JAWS](https://www.freedomscientific.com/products/software/jaws/)
- [MathPlayer](https://www.dessci.com/en/products/mathplayer/) - Math TTS

## 🎓 Best Practices

### Code Style
```bash
# Format code
black .

# Lint
flake8 --max-line-length=100 core/ modules/ ui/

# Type hints
mypy core/ modules/
```

### Commit Messages
```
feat: Add PDF layout analysis
fix: Correct OMML to LaTeX conversion
docs: Update README with PDF converter guide
test: Add tests for symbol dictionary
refactor: Improve KB pattern matching
```

### Branch Strategy
```
main          - Stable releases
develop       - Integration branch
feature/*     - New features
bugfix/*      - Bug fixes
release/*     - Release preparation
```

## 💡 Tips & Tricks

### Debug OMML/XML
```python
# Pretty print XML
from xml.dom import minidom
xml_str = element.xml
pretty_xml = minidom.parseString(xml_str).toprettyxml()
print(pretty_xml)
```

### Test OCR Locally
```python
# Quick test Mathpix
from mathpix import MathpixOCR
ocr = MathpixOCR(api_key="your_key")
result = ocr.latex("equation_image.png")
print(result)
```

### Profile Performance
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)
```

## 🚀 Deployment

### Packaging
```bash
# PyInstaller per exe standalone
pip install pyinstaller
pyinstaller --onefile --windowed main.py

# O setuptools
python setup.py sdist bdist_wheel
```

### Distribution
- GitHub Releases
- PyPI (se si fa package)
- Docker image

---

**Ultima revisione**: 2024
**Versione**: 1.0.0-alpha
**Stato**: In sviluppo attivo
