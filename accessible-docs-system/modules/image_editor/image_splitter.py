"""
Image Splitter - Split immagini in più parti
Supporta: Verticale, Orizzontale, Griglia, Libero
"""

from PIL import Image
from typing import List, Tuple, Dict
import math


class ImageSplitter:
    """Gestisce lo split di immagini in più parti"""
    
    def __init__(self, image: Image.Image):
        """
        Args:
            image: Immagine PIL da dividere
        """
        self.image = image
        self.width, self.height = image.size
    
    def split_vertical(self, position_y: int) -> List[Image.Image]:
        """
        Divide immagine verticalmente (alto/basso)
        
        Args:
            position_y: Posizione Y dove dividere (in pixel)
            
        Returns:
            [immagine_sopra, immagine_sotto]
        """
        if position_y <= 0 or position_y >= self.height:
            raise ValueError(f"Posizione Y deve essere tra 0 e {self.height}")
        
        top = self.image.crop((0, 0, self.width, position_y))
        bottom = self.image.crop((0, position_y, self.width, self.height))
        
        return [top, bottom]
    
    def split_horizontal(self, position_x: int) -> List[Image.Image]:
        """
        Divide immagine orizzontalmente (sinistra/destra)
        
        Args:
            position_x: Posizione X dove dividere (in pixel)
            
        Returns:
            [immagine_sinistra, immagine_destra]
        """
        if position_x <= 0 or position_x >= self.width:
            raise ValueError(f"Posizione X deve essere tra 0 e {self.width}")
        
        left = self.image.crop((0, 0, position_x, self.height))
        right = self.image.crop((position_x, 0, self.width, self.height))
        
        return [left, right]
    
    def split_grid(self, rows: int, cols: int) -> List[Image.Image]:
        """
        Divide immagine in griglia regolare
        
        Args:
            rows: Numero di righe
            cols: Numero di colonne
            
        Returns:
            Lista di immagini (da sinistra a destra, dall'alto in basso)
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Righe e colonne devono essere > 0")
        
        cell_width = self.width // cols
        cell_height = self.height // rows
        
        parts = []
        
        for row in range(rows):
            for col in range(cols):
                x1 = col * cell_width
                y1 = row * cell_height
                
                # Ultima cella: prendi fino al bordo
                x2 = self.width if col == cols - 1 else (col + 1) * cell_width
                y2 = self.height if row == rows - 1 else (row + 1) * cell_height
                
                part = self.image.crop((x1, y1, x2, y2))
                parts.append(part)
        
        return parts
    
    def split_free(self, rectangles: List[Tuple[int, int, int, int]]) -> List[Image.Image]:
        """
        Divide immagine in parti custom definite da rettangoli
        
        Args:
            rectangles: Lista di (x1, y1, x2, y2) per ogni parte
            
        Returns:
            Lista di immagini ritagliate
        """
        parts = []
        
        for rect in rectangles:
            x1, y1, x2, y2 = rect
            
            # Valida coordinate
            if x1 < 0 or y1 < 0 or x2 > self.width or y2 > self.height:
                raise ValueError(f"Rettangolo {rect} fuori dai limiti dell'immagine")
            
            if x1 >= x2 or y1 >= y2:
                raise ValueError(f"Rettangolo {rect} ha dimensioni invalide")
            
            part = self.image.crop((x1, y1, x2, y2))
            parts.append(part)
        
        return parts
    
    def get_split_info(self, split_type: str, **kwargs) -> Dict:
        """
        Ottiene informazioni su uno split senza eseguirlo
        
        Args:
            split_type: 'vertical', 'horizontal', 'grid', o 'free'
            **kwargs: Parametri specifici per il tipo di split
            
        Returns:
            Dict con info: num_parts, dimensions, etc.
        """
        info = {
            'split_type': split_type,
            'original_size': (self.width, self.height)
        }
        
        if split_type == 'vertical':
            position_y = kwargs.get('position_y', self.height // 2)
            info['num_parts'] = 2
            info['parts'] = [
                {'index': 0, 'position': 'top', 'size': (self.width, position_y)},
                {'index': 1, 'position': 'bottom', 'size': (self.width, self.height - position_y)}
            ]
        
        elif split_type == 'horizontal':
            position_x = kwargs.get('position_x', self.width // 2)
            info['num_parts'] = 2
            info['parts'] = [
                {'index': 0, 'position': 'left', 'size': (position_x, self.height)},
                {'index': 1, 'position': 'right', 'size': (self.width - position_x, self.height)}
            ]
        
        elif split_type == 'grid':
            rows = kwargs.get('rows', 2)
            cols = kwargs.get('cols', 2)
            cell_w = self.width // cols
            cell_h = self.height // rows
            
            info['num_parts'] = rows * cols
            info['grid'] = {'rows': rows, 'cols': cols}
            info['cell_size'] = (cell_w, cell_h)
            info['parts'] = []
            
            for r in range(rows):
                for c in range(cols):
                    info['parts'].append({
                        'index': r * cols + c,
                        'position': f'row_{r}_col_{c}',
                        'grid_pos': (r, c)
                    })
        
        elif split_type == 'free':
            rectangles = kwargs.get('rectangles', [])
            info['num_parts'] = len(rectangles)
            info['parts'] = []
            
            for i, rect in enumerate(rectangles):
                x1, y1, x2, y2 = rect
                info['parts'].append({
                    'index': i,
                    'position': 'custom',
                    'bounds': rect,
                    'size': (x2 - x1, y2 - y1)
                })
        
        return info
    
    @staticmethod
    def suggest_split_lines(image: Image.Image, direction: str = 'vertical', 
                           num_parts: int = 2) -> List[int]:
        """
        Suggerisce posizioni ottimali per dividere l'immagine
        basandosi su analisi del contenuto (zone bianche, contrasto, etc.)
        
        Args:
            image: Immagine da analizzare
            direction: 'vertical' o 'horizontal'
            num_parts: Numero di parti desiderate
            
        Returns:
            Lista di posizioni suggerite
        """
        # Implementazione semplice: divide in parti uguali
        # TODO: Implementare analisi contenuto per split intelligente
        
        width, height = image.size
        
        if direction == 'vertical':
            step = height // num_parts
            return [step * i for i in range(1, num_parts)]
        else:  # horizontal
            step = width // num_parts
            return [step * i for i in range(1, num_parts)]
    
    @staticmethod
    def generate_part_names(base_label: str, num_parts: int, 
                           naming_style: str = 'letters') -> List[str]:
        """
        Genera nomi per le parti divise
        
        Args:
            base_label: Etichetta base (es: "Fig. 2.5")
            num_parts: Numero di parti
            naming_style: 'letters' (a,b,c) o 'numbers' (1,2,3) o 'sub' (.1,.2,.3)
            
        Returns:
            Lista di nomi generati
        """
        names = []
        
        if naming_style == 'letters':
            # Fig. 2.5 → Fig. 2.5a, Fig. 2.5b, ...
            for i in range(num_parts):
                letter = chr(ord('a') + i)
                names.append(f"{base_label}{letter}")
        
        elif naming_style == 'numbers':
            # Fig. 2.5 → Fig. 2.5-1, Fig. 2.5-2, ...
            for i in range(num_parts):
                names.append(f"{base_label}-{i+1}")
        
        elif naming_style == 'sub':
            # Fig. 2.5 → Fig. 2.5.1, Fig. 2.5.2, ...
            for i in range(num_parts):
                names.append(f"{base_label}.{i+1}")
        
        return names


def test_image_splitter():
    """Test del modulo ImageSplitter"""
    print("=== TEST IMAGE SPLITTER ===\n")
    
    # Crea immagine test 400x300
    from PIL import ImageDraw
    img = Image.new('RGB', (400, 300), color='lightgray')
    draw = ImageDraw.Draw(img)
    
    # Disegna 4 quadrati colorati
    colors = ['red', 'green', 'blue', 'yellow']
    positions = [(0, 0), (200, 0), (0, 150), (200, 150)]
    for i, (x, y) in enumerate(positions):
        draw.rectangle([x, y, x+200, y+150], fill=colors[i], outline='black', width=2)
    
    splitter = ImageSplitter(img)
    print(f"✓ Splitter creato - Dimensioni: {splitter.width}x{splitter.height}\n")
    
    # Test 1: Split Verticale
    print("1. Split Verticale (metà altezza):")
    parts_v = splitter.split_vertical(150)
    print(f"   Parti create: {len(parts_v)}")
    for i, part in enumerate(parts_v):
        print(f"   Parte {i}: {part.size}")
    
    # Test 2: Split Orizzontale
    print("\n2. Split Orizzontale (metà larghezza):")
    parts_h = splitter.split_horizontal(200)
    print(f"   Parti create: {len(parts_h)}")
    for i, part in enumerate(parts_h):
        print(f"   Parte {i}: {part.size}")
    
    # Test 3: Split Griglia
    print("\n3. Split Griglia (2x2):")
    parts_g = splitter.split_grid(2, 2)
    print(f"   Parti create: {len(parts_g)}")
    for i, part in enumerate(parts_g):
        print(f"   Parte {i}: {part.size}")
    
    # Test 4: Split Libero
    print("\n4. Split Libero (3 rettangoli custom):")
    rectangles = [
        (0, 0, 150, 150),     # Angolo top-left
        (150, 0, 400, 150),   # Top-right
        (0, 150, 400, 300)    # Bottom intero
    ]
    parts_f = splitter.split_free(rectangles)
    print(f"   Parti create: {len(parts_f)}")
    for i, part in enumerate(parts_f):
        print(f"   Parte {i}: {part.size}")
    
    # Test 5: Info Split
    print("\n5. Get Split Info (griglia 3x3):")
    info = splitter.get_split_info('grid', rows=3, cols=3)
    print(f"   Tipo: {info['split_type']}")
    print(f"   Numero parti: {info['num_parts']}")
    print(f"   Dimensione celle: {info['cell_size']}")
    
    # Test 6: Genera Nomi
    print("\n6. Genera Nomi Parti:")
    names_letters = ImageSplitter.generate_part_names("Fig. 2.5", 3, 'letters')
    print(f"   Letters: {names_letters}")
    names_numbers = ImageSplitter.generate_part_names("Fig. 2.5", 3, 'numbers')
    print(f"   Numbers: {names_numbers}")
    names_sub = ImageSplitter.generate_part_names("Fig. 2.5", 3, 'sub')
    print(f"   Sub: {names_sub}")
    
    print("\n✅ Test completati")


if __name__ == "__main__":
    test_image_splitter()
