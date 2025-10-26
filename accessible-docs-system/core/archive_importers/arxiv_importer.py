"""
arXiv Importer
Estrae formule matematiche da paper arXiv in formato LaTeX source
"""

import re
import requests
import tarfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Set
import time
from collections import Counter


class ArxivImporter:
    """Importa formule da paper arXiv"""
    
    BASE_URL = "https://arxiv.org"
    EXPORT_URL = "https://export.arxiv.org/e-print"
    
    # Categorie arXiv matematiche
    MATH_CATEGORIES = {
        'math.CA': ('calculus', 'misc', 'Classical Analysis'),
        'math.FA': ('calculus', 'misc', 'Functional Analysis'),
        'math.OA': ('algebra', 'misc', 'Operator Algebras'),
        'math.PR': ('statistics', 'probability', 'Probability'),
        'math.ST': ('statistics', 'descriptive', 'Statistics Theory'),
        'math.NT': ('number_theory', 'misc', 'Number Theory'),
        'math.AG': ('geometry', 'misc', 'Algebraic Geometry'),
        'math.DG': ('geometry', 'differential', 'Differential Geometry'),
        'math.GT': ('geometry', 'misc', 'Geometric Topology'),
        'math.GR': ('algebra', 'misc', 'Group Theory'),
        'math.NA': ('calculus', 'misc', 'Numerical Analysis'),
        'math.AP': ('calculus', 'differential', 'Analysis of PDEs'),
        'math-ph': ('physics', 'misc', 'Mathematical Physics'),
        'quant-ph': ('physics', 'quantum', 'Quantum Physics'),
    }
    
    def __init__(self, cache_dir: str = "arxiv_cache"):
        """
        Inizializza importer
        
        Args:
            cache_dir: Directory cache paper scaricati
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Formula Database)'
        })
    
    def _download_source(self, arxiv_id: str) -> Optional[Path]:
        """
        Scarica sorgente LaTeX paper arXiv
        
        Args:
            arxiv_id: ID paper (es. '2301.12345' o 'math/0601001')
            
        Returns:
            Path tar.gz scaricato o None se errore
        """
        # Rimuovi versione se presente (es. v1, v2)
        arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
        
        cache_file = self.cache_dir / f"{arxiv_id.replace('/', '_')}.tar.gz"
        
        # Controlla cache
        if cache_file.exists():
            print(f"Usando cache per {arxiv_id}")
            return cache_file
        
        # Scarica
        url = f"{self.EXPORT_URL}/{arxiv_id}"
        print(f"Scaricando {url}...")
        
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(cache_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Rate limiting
            time.sleep(3)
            
            return cache_file
            
        except requests.RequestException as e:
            print(f"Errore download {arxiv_id}: {e}")
            return None
    
    def _extract_tar(self, tar_path: Path) -> Optional[Path]:
        """Estrae tar.gz in directory temporanea"""
        extract_dir = tempfile.mkdtemp(prefix="arxiv_")
        extract_path = Path(extract_dir)
        
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(extract_path)
            return extract_path
        except Exception as e:
            print(f"Errore estrazione tar: {e}")
            return None
    
    def _find_main_tex(self, extract_dir: Path) -> Optional[Path]:
        """Trova file .tex principale"""
        tex_files = list(extract_dir.glob("*.tex"))
        
        if not tex_files:
            return None
        
        if len(tex_files) == 1:
            return tex_files[0]
        
        # Cerca file main/paper comune
        for name in ['main.tex', 'paper.tex', 'article.tex', 'ms.tex']:
            candidate = extract_dir / name
            if candidate.exists():
                return candidate
        
        # Fallback: file più grande
        return max(tex_files, key=lambda f: f.stat().st_size)
    
    def _extract_equations(self, tex_content: str) -> List[str]:
        """
        Estrae equazioni da contenuto LaTeX
        
        Riconosce:
        - equation environment
        - align, gather, multline
        - $...$ e $$...$$
        - \[...\]
        """
        equations = []
        
        # equation environment
        equation_pattern = r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}'
        equations.extend(re.findall(equation_pattern, tex_content, re.DOTALL))
        
        # align environment
        align_pattern = r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}'
        equations.extend(re.findall(align_pattern, tex_content, re.DOTALL))
        
        # gather environment
        gather_pattern = r'\\begin\{gather\*?\}(.*?)\\end\{gather\*?\}'
        equations.extend(re.findall(gather_pattern, tex_content, re.DOTALL))
        
        # multline environment
        multline_pattern = r'\\begin\{multline\*?\}(.*?)\\end\{multline\*?\}'
        equations.extend(re.findall(multline_pattern, tex_content, re.DOTALL))
        
        # displaymath \[...\]
        displaymath_pattern = r'\\\[(.*?)\\\]'
        equations.extend(re.findall(displaymath_pattern, tex_content, re.DOTALL))
        
        # $$...$$ (evita $ singolo inline)
        double_dollar_pattern = r'\$\$(.*?)\$\$'
        equations.extend(re.findall(double_dollar_pattern, tex_content, re.DOTALL))
        
        # Pulisci equazioni
        cleaned = []
        for eq in equations:
            # Rimuovi label
            eq = re.sub(r'\\label\{[^}]*\}', '', eq)
            # Rimuovi spazi multipli e newline
            eq = ' '.join(eq.split())
            eq = eq.strip()
            
            # Filtra equazioni troppo corte o vuote
            if len(eq) > 5:
                cleaned.append(eq)
        
        return cleaned
    
    def _get_paper_metadata(self, arxiv_id: str) -> Dict:
        """Recupera metadati paper da API arXiv"""
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            # Parse XML (semplificato)
            content = response.text
            
            # Estrae titolo
            title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else None
            
            # Estrae categoria
            category_match = re.search(r'<arxiv:primary_category.*?term="([^"]+)"', content)
            category = category_match.group(1) if category_match else None
            
            # Estrae abstract
            abstract_match = re.search(r'<summary>(.*?)</summary>', content, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else None
            
            return {
                'title': title,
                'category': category,
                'abstract': abstract
            }
            
        except Exception as e:
            print(f"Errore recupero metadata: {e}")
            return {}
    
    def import_from_arxiv(self, arxiv_id: str, max_formulas: int = 100) -> List[Dict]:
        """
        Importa formule da paper arXiv
        
        Args:
            arxiv_id: ID paper arXiv
            max_formulas: Numero massimo formule da estrarre
            
        Returns:
            Lista formule estratte
        """
        print(f"\n=== Importando {arxiv_id} ===")
        
        # Recupera metadata
        metadata = self._get_paper_metadata(arxiv_id)
        paper_title = metadata.get('title', arxiv_id)
        paper_category = metadata.get('category', 'unknown')
        
        print(f"Titolo: {paper_title}")
        print(f"Categoria: {paper_category}")
        
        # Scarica sorgente
        tar_path = self._download_source(arxiv_id)
        if not tar_path:
            return []
        
        # Estrai
        extract_dir = self._extract_tar(tar_path)
        if not extract_dir:
            return []
        
        # Trova main.tex
        main_tex = self._find_main_tex(extract_dir)
        if not main_tex:
            print("File .tex principale non trovato")
            return []
        
        print(f"Analizzando {main_tex.name}...")
        
        # Leggi contenuto
        try:
            with open(main_tex, 'r', encoding='utf-8', errors='ignore') as f:
                tex_content = f.read()
        except Exception as e:
            print(f"Errore lettura .tex: {e}")
            return []
        
        # Estrai equazioni
        equations = self._extract_equations(tex_content)
        print(f"Trovate {len(equations)} equazioni")
        
        # Limita numero
        if len(equations) > max_formulas:
            equations = equations[:max_formulas]
            print(f"Limitato a {max_formulas} formule")
        
        # Mappa categoria arXiv a categoria database
        category_info = self.MATH_CATEGORIES.get(
            paper_category,
            ('other', 'misc', 'Unknown')
        )
        
        # Crea dict formule
        formulas = []
        for i, latex in enumerate(equations, 1):
            formulas.append({
                'latex': latex,
                'name': f"{arxiv_id} - Eq {i}",
                'description': f"From paper: {paper_title}",
                'category': category_info[0],
                'subcategory': category_info[1],
                'source': 'arXiv',
                'source_url': f"https://arxiv.org/abs/{arxiv_id}",
                'tags': ['arXiv', paper_category, category_info[2]],
                'arxiv_id': arxiv_id,
                'paper_title': paper_title
            })
        
        return formulas
    
    def import_multiple_papers(self, arxiv_ids: List[str]) -> List[Dict]:
        """Importa formule da multipli paper"""
        all_formulas = []
        
        for arxiv_id in arxiv_ids:
            formulas = self.import_from_arxiv(arxiv_id)
            all_formulas.extend(formulas)
            print(f"Totale formule: {len(all_formulas)}\n")
        
        return all_formulas
    
    def search_and_import(self, search_query: str, max_papers: int = 5) -> List[Dict]:
        """
        Cerca paper su arXiv e importa formule
        
        Args:
            search_query: Query di ricerca
            max_papers: Numero massimo paper da processare
            
        Returns:
            Lista formule estratte da tutti i paper
        """
        # Cerca paper
        api_url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&max_results={max_papers}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            # Estrae ID paper
            arxiv_ids = re.findall(r'<id>http://arxiv.org/abs/(.*?)</id>', response.text)
            
            if not arxiv_ids:
                print("Nessun paper trovato")
                return []
            
            print(f"Trovati {len(arxiv_ids)} paper")
            
            # Importa da ogni paper
            return self.import_multiple_papers(arxiv_ids)
            
        except Exception as e:
            print(f"Errore ricerca: {e}")
            return []


def demo_arxiv_import():
    """Demo importazione arXiv"""
    from formula_database import FormulaDatabase
    
    db = FormulaDatabase("arxiv_formulas.db")
    importer = ArxivImporter()
    
    # Esempio: paper famoso di matematica
    # 1. Paper sulle funzioni di Bessel
    arxiv_id = "math/0601001"  # Esempio
    
    # O cerca per topic
    print("Cercando paper su 'special functions'...")
    formulas = importer.search_and_import("special functions", max_papers=2)
    
    print(f"\nTrovate {len(formulas)} formule totali")
    
    # Importa in database
    if formulas:
        count = 0
        for formula in formulas:
            formula_id = db.add_formula(**formula, verified=False)
            if formula_id:
                count += 1
        
        print(f"Importate {count} formule nel database")
    
    db.close()


if __name__ == "__main__":
    demo_arxiv_import()
