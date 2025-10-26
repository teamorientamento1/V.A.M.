"""
DLMF Importer - FIXED VERSION
Importa formule dal DLMF (Digital Library of Mathematical Functions)
https://dlmf.nist.gov/

FIX: Parsing HTML migliorato per estrarre LaTeX da MathML/alttext
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from pathlib import Path
import json
import time
from urllib.parse import urljoin


class DLMFImporter:
    """Importa formule dal DLMF con parsing migliorato"""
    
    BASE_URL = "https://dlmf.nist.gov"
    
    # Mapping capitoli DLMF a categorie
    CHAPTER_MAPPING = {
        '1': ('algebra', 'misc', 'Algebraic and Analytic Methods'),
        '4': ('calculus', 'series', 'Elementary Functions'),
        '5': ('special_functions', 'gamma', 'Gamma Function'),
        '6': ('special_functions', 'exponential', 'Exponential, Logarithmic'),
        '7': ('special_functions', 'misc', 'Error Functions'),
        '8': ('calculus', 'integral', 'Incomplete Gamma'),
        '9': ('special_functions', 'misc', 'Airy and Related Functions'),
        '10': ('special_functions', 'bessel', 'Bessel Functions'),
        '13': ('special_functions', 'misc', 'Confluent Hypergeometric'),
        '14': ('special_functions', 'misc', 'Legendre and Related Functions'),
        '15': ('special_functions', 'hypergeometric', 'Hypergeometric Function'),
        '18': ('special_functions', 'misc', 'Orthogonal Polynomials'),
        '25': ('special_functions', 'misc', 'Zeta and Related Functions'),
    }
    
    def __init__(self, cache_dir: str = "dlmf_cache"):
        """
        Inizializza importer
        
        Args:
            cache_dir: Directory per cache HTML scaricate
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Formula Database)'
        })
    
    def _get_cache_path(self, url: str) -> Path:
        """Genera path cache per URL"""
        url_hash = str(abs(hash(url)))
        return self.cache_dir / f"{url_hash}.html"
    
    def _fetch_page(self, url: str, use_cache: bool = True) -> Optional[str]:
        """
        Scarica pagina HTML con caching
        
        Args:
            url: URL da scaricare
            use_cache: Se usare cache locale
            
        Returns:
            HTML della pagina o None se errore
        """
        cache_path = self._get_cache_path(url)
        
        # Controlla cache
        if use_cache and cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        # Scarica
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html = response.text
            
            # Salva in cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Rate limiting
            time.sleep(1)
            
            return html
            
        except requests.RequestException as e:
            print(f"Errore scaricamento {url}: {e}")
            return None
    
    def _extract_latex_from_html(self, html: str) -> List[str]:
        """
        Estrae LaTeX da HTML usando multiple strategie
        
        Strategie:
        1. Cerca alttext in tag math
        2. Cerca annotation encoding="application/x-tex"
        3. Cerca pattern LaTeX direttamente nel testo
        """
        soup = BeautifulSoup(html, 'html.parser')
        formulas = []
        
        # Strategia 1: alttext attribute
        math_tags = soup.find_all('math')
        for math_tag in math_tags:
            alttext = math_tag.get('alttext')
            if alttext and len(alttext) > 5:
                formulas.append(alttext)
        
        # Strategia 2: annotation tag con LaTeX
        annotations = soup.find_all('annotation', {'encoding': re.compile(r'.*tex.*', re.I)})
        for ann in annotations:
            latex = ann.get_text(strip=True)
            if latex and len(latex) > 5:
                formulas.append(latex)
        
        # Strategia 3: Cerca img con alt attribute contenente LaTeX
        img_tags = soup.find_all('img', class_=re.compile(r'.*math.*', re.I))
        for img in img_tags:
            alt = img.get('alt', '')
            if alt and len(alt) > 5 and ('\\' in alt or '{' in alt):
                formulas.append(alt)
        
        # Strategia 4: Cerca script tag con LaTeX (MathJax)
        scripts = soup.find_all('script', {'type': re.compile(r'.*tex.*', re.I)})
        for script in scripts:
            latex = script.string
            if latex:
                # Rimuovi delimitatori MathJax
                latex = re.sub(r'^\s*\\\[|\\\]\s*$', '', latex)
                latex = re.sub(r'^\s*\$\$|\$\$\s*$', '', latex)
                if len(latex) > 5:
                    formulas.append(latex.strip())
        
        # Rimuovi duplicati mantenendo ordine
        seen = set()
        unique = []
        for f in formulas:
            if f not in seen:
                seen.add(f)
                unique.append(f)
        
        return unique
    
    def _extract_formulas_from_page(self, html: str, chapter: str) -> List[Dict]:
        """
        Estrae formule da pagina HTML DLMF
        
        Args:
            html: HTML della pagina
            chapter: Numero capitolo
            
        Returns:
            Lista dict con formule estratte
        """
        # Estrai LaTeX
        latex_formulas = self._extract_latex_from_html(html)
        
        # Categoria basata su capitolo
        category_info = self.CHAPTER_MAPPING.get(
            chapter, 
            ('other', 'misc', 'Unknown')
        )
        
        formulas = []
        for i, latex in enumerate(latex_formulas):
            # Pulisci LaTeX
            latex = self._clean_latex(latex)
            
            if not latex or len(latex) < 5:
                continue
            
            formula = {
                'latex': latex,
                'name': f"DLMF {chapter}.{i+1}",
                'description': f"Formula from DLMF Chapter {chapter}: {category_info[2]}",
                'category': category_info[0],
                'subcategory': category_info[1],
                'source': 'DLMF',
                'source_url': f"{self.BASE_URL}/{chapter}",
                'tags': ['DLMF', category_info[2]],
                'chapter': chapter,
            }
            
            formulas.append(formula)
        
        return formulas
    
    def _clean_latex(self, latex: str) -> str:
        """Pulisce e normalizza LaTeX"""
        # Rimuovi spazi multipli
        latex = ' '.join(latex.split())
        
        # Rimuovi delimitatori esterni comuni
        latex = re.sub(r'^\$+|\$+$', '', latex)
        latex = re.sub(r'^\\[\[\(]|\\[\]\)]$', '', latex)
        
        # Rimuovi label
        latex = re.sub(r'\\label\{[^}]*\}', '', latex)
        
        # Trim
        latex = latex.strip()
        
        return latex
    
    def import_chapter(self, chapter: str) -> List[Dict]:
        """
        Importa tutte le formule da un capitolo DLMF
        
        Args:
            chapter: Numero capitolo (es. '5' per Gamma Function)
            
        Returns:
            Lista formule estratte
        """
        url = f"{self.BASE_URL}/{chapter}"
        print(f"Importando capitolo {chapter} da {url}...")
        
        html = self._fetch_page(url)
        if not html:
            return []
        
        formulas = self._extract_formulas_from_page(html, chapter)
        print(f"Estratte {len(formulas)} formule dal capitolo {chapter}")
        
        return formulas
    
    def import_chapters(self, chapters: List[str]) -> List[Dict]:
        """
        Importa formule da multipli capitoli
        
        Args:
            chapters: Lista numeri capitoli
            
        Returns:
            Lista tutte formule estratte
        """
        all_formulas = []
        
        for chapter in chapters:
            formulas = self.import_chapter(chapter)
            all_formulas.extend(formulas)
            print(f"Totale formule: {len(all_formulas)}")
        
        return all_formulas
    
    def import_special_functions(self) -> List[Dict]:
        """Importa capitoli funzioni speciali comuni"""
        # Usa solo capitoli che sappiamo funzionare meglio
        chapters = ['5', '6', '7', '10', '15', '25']
        return self.import_chapters(chapters)
    
    def export_to_json(self, formulas: List[Dict], output_file: str):
        """Esporta formule in JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formulas, f, indent=2, ensure_ascii=False)
        print(f"Esportate {len(formulas)} formule in {output_file}")
    
    def import_to_database(self, formulas: List[Dict], db) -> int:
        """
        Importa formule nel database
        
        Args:
            formulas: Lista formule da importare
            db: Istanza FormulaDatabase
            
        Returns:
            Numero formule importate con successo
        """
        count = 0
        duplicates = 0
        
        for formula in formulas:
            formula_id = db.add_formula(
                latex=formula['latex'],
                name=formula.get('name'),
                description=formula.get('description'),
                category=formula['category'],
                subcategory=formula['subcategory'],
                source=formula['source'],
                source_url=formula['source_url'],
                tags=formula.get('tags'),
                verified=True  # DLMF è fonte verificata
            )
            
            if formula_id:
                count += 1
            else:
                duplicates += 1
        
        print(f"Importate: {count}, Duplicate: {duplicates}")
        return count


class WikipediaFormulaImporter:
    """Importa formule da Wikipedia (liste di formule matematiche)"""
    
    BASE_URL = "https://en.wikipedia.org"
    
    # Pagine Wikipedia con liste formule
    FORMULA_PAGES = {
        'calculus': '/wiki/Lists_of_integrals',
        'trig': '/wiki/List_of_trigonometric_identities',
        'series': '/wiki/List_of_mathematical_series',
        'derivatives': '/wiki/Table_of_derivatives'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Formula Database)'
        })
    
    def _extract_latex_from_wiki(self, html: str) -> List[str]:
        """Estrae formule LaTeX da pagina Wikipedia"""
        soup = BeautifulSoup(html, 'html.parser')
        formulas = []
        
        # Wikipedia usa img con class "mwe-math-fallback-image-inline"
        math_imgs = soup.find_all('img', class_=re.compile(r'.*math.*', re.I))
        
        for img in math_imgs:
            latex = img.get('alt', '')
            if latex and len(latex) > 5:
                # Pulisci LaTeX
                latex = latex.strip()
                # Rimuovi delimitatori esterni
                latex = re.sub(r'^\$+|\$+$', '', latex)
                latex = re.sub(r'^\\[\[\(]|\\[\]\)]$', '', latex)
                if len(latex) > 5:
                    formulas.append(latex)
        
        return formulas
    
    def import_from_page(self, page_key: str) -> List[Dict]:
        """Importa formule da pagina Wikipedia"""
        if page_key not in self.FORMULA_PAGES:
            print(f"Pagina {page_key} non trovata")
            return []
        
        url = self.BASE_URL + self.FORMULA_PAGES[page_key]
        print(f"Importando da {url}...")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as e:
            print(f"Errore scaricamento: {e}")
            return []
        
        latex_formulas = self._extract_latex_from_wiki(html)
        
        # Mappa a categoria
        category_map = {
            'calculus': ('calculus', 'integral'),
            'trig': ('geometry', 'trigonometry'),
            'series': ('calculus', 'series'),
            'derivatives': ('calculus', 'derivative')
        }
        
        category, subcategory = category_map.get(page_key, ('other', 'misc'))
        
        formulas = []
        for latex in latex_formulas:
            formulas.append({
                'latex': latex,
                'category': category,
                'subcategory': subcategory,
                'source': 'Wikipedia',
                'source_url': url,
                'tags': ['Wikipedia', page_key]
            })
        
        print(f"Estratte {len(formulas)} formule da Wikipedia")
        return formulas


def test_dlmf_fix():
    """Test importer DLMF fixato"""
    print("=== TEST DLMF IMPORTER FIXATO ===\n")
    
    importer = DLMFImporter()
    
    # Test capitolo 5 (Gamma)
    print("Test capitolo 5 (Gamma Function)...")
    formulas = importer.import_chapter('5')
    
    if formulas:
        print(f"✅ Successo! Estratte {len(formulas)} formule")
        print("\nPrime 3 formule:")
        for i, f in enumerate(formulas[:3], 1):
            print(f"{i}. {f['latex'][:60]}...")
    else:
        print("⚠️ Nessuna formula estratta")
        print("DLMF potrebbe aver cambiato struttura HTML")
        print("Usa Wikipedia come fonte principale (già funzionante)")


if __name__ == "__main__":
    test_dlmf_fix()
