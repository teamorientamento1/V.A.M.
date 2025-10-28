"""
Image Editor - Operazioni base di editing su immagini
Supporta crop, rotate, flip, resize
"""

from PIL import Image, ImageDraw
from typing import Tuple, Optional, List
import io


class ImageEditor:
    """Gestisce operazioni di editing base su immagini"""
    
    def __init__(self, image: Image.Image):
        """
        Args:
            image: Immagine PIL da editare
        """
        self.original_image = image.copy()
        self.current_image = image.copy()
        self.history = [image.copy()]  # History per undo
        self.history_index = 0
    
    def get_current_image(self) -> Image.Image:
        """Ritorna l'immagine corrente"""
        return self.current_image.copy()
    
    def get_image_size(self) -> Tuple[int, int]:
        """Ritorna dimensioni immagine corrente (width, height)"""
        return self.current_image.size
    
    def crop(self, box: Tuple[int, int, int, int]) -> Image.Image:
        """
        Ritaglia immagine
        
        Args:
            box: (left, top, right, bottom)
            
        Returns:
            Immagine ritagliata
        """
        self.current_image = self.current_image.crop(box)
        self._add_to_history()
        return self.current_image.copy()
    
    def rotate(self, angle: int, expand: bool = True) -> Image.Image:
        """
        Ruota immagine
        
        Args:
            angle: Angolo di rotazione (90, 180, 270)
            expand: Se True, espande canvas per contenere immagine ruotata
            
        Returns:
            Immagine ruotata
        """
        self.current_image = self.current_image.rotate(-angle, expand=expand)
        self._add_to_history()
        return self.current_image.copy()
    
    def flip_horizontal(self) -> Image.Image:
        """Ribalta immagine orizzontalmente"""
        self.current_image = self.current_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        self._add_to_history()
        return self.current_image.copy()
    
    def flip_vertical(self) -> Image.Image:
        """Ribalta immagine verticalmente"""
        self.current_image = self.current_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self._add_to_history()
        return self.current_image.copy()
    
    def resize(self, size: Tuple[int, int], keep_aspect: bool = True) -> Image.Image:
        """
        Ridimensiona immagine
        
        Args:
            size: (width, height) desiderati
            keep_aspect: Se True, mantiene aspect ratio
            
        Returns:
            Immagine ridimensionata
        """
        if keep_aspect:
            self.current_image.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            self.current_image = self.current_image.resize(size, Image.Resampling.LANCZOS)
        
        self._add_to_history()
        return self.current_image.copy()
    
    def auto_crop_whitespace(self, threshold: int = 250) -> Image.Image:
        """
        Rimuove automaticamente bordi bianchi
        
        Args:
            threshold: Valore RGB sopra il quale considerare "bianco" (0-255)
            
        Returns:
            Immagine con bordi rimossi
        """
        # Converti in RGB se necessario
        img = self.current_image
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Trova bounding box del contenuto
        bbox = img.getbbox()
        
        if bbox:
            # Trova area non-bianca
            pixels = img.load()
            width, height = img.size
            
            # Trova bounds
            left = width
            top = height
            right = 0
            bottom = 0
            
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y][:3]
                    # Se pixel non è bianco
                    if r < threshold or g < threshold or b < threshold:
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)
            
            if left < right and top < bottom:
                # Aggiungi piccolo margine
                margin = 5
                left = max(0, left - margin)
                top = max(0, top - margin)
                right = min(width, right + margin)
                bottom = min(height, bottom + margin)
                
                self.current_image = img.crop((left, top, right, bottom))
                self._add_to_history()
        
        return self.current_image.copy()
    
    def replace_image(self, new_image: Image.Image):
        """
        Sostituisce completamente l'immagine corrente
        
        Args:
            new_image: Nuova immagine
        """
        self.current_image = new_image.copy()
        self._add_to_history()
    
    def undo(self) -> Optional[Image.Image]:
        """
        Annulla ultima operazione
        
        Returns:
            Immagine precedente o None se già all'inizio
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            return self.current_image.copy()
        return None
    
    def redo(self) -> Optional[Image.Image]:
        """
        Ripristina operazione annullata
        
        Returns:
            Immagine successiva o None se già alla fine
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            return self.current_image.copy()
        return None
    
    def can_undo(self) -> bool:
        """Verifica se può fare undo"""
        return self.history_index > 0
    
    def can_redo(self) -> bool:
        """Verifica se può fare redo"""
        return self.history_index < len(self.history) - 1
    
    def reset(self):
        """Ripristina immagine originale"""
        self.current_image = self.original_image.copy()
        self.history = [self.original_image.copy()]
        self.history_index = 0
    
    def _add_to_history(self):
        """Aggiunge stato corrente alla history"""
        # Rimuovi eventuali stati futuri se siamo nel mezzo della history
        self.history = self.history[:self.history_index + 1]
        
        # Aggiungi nuovo stato
        self.history.append(self.current_image.copy())
        self.history_index += 1
        
        # Limita history a max 20 stati
        max_history = 20
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
            self.history_index = len(self.history) - 1
    
    def save_to_bytes(self, format: str = 'PNG') -> bytes:
        """
        Salva immagine corrente in bytes
        
        Args:
            format: Formato output (PNG, JPEG, etc.)
            
        Returns:
            Bytes dell'immagine
        """
        buffer = io.BytesIO()
        self.current_image.save(buffer, format=format)
        return buffer.getvalue()
    
    @staticmethod
    def from_bytes(image_bytes: bytes) -> 'ImageEditor':
        """
        Crea ImageEditor da bytes
        
        Args:
            image_bytes: Bytes dell'immagine
            
        Returns:
            Nuovo ImageEditor
        """
        image = Image.open(io.BytesIO(image_bytes))
        return ImageEditor(image)


def test_image_editor():
    """Test del modulo ImageEditor"""
    print("=== TEST IMAGE EDITOR ===\n")
    
    # Crea immagine test
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill='blue', outline='black', width=3)
    draw.text((150, 130), "TEST IMAGE", fill='white')
    
    editor = ImageEditor(img)
    print(f"✓ Editor creato - Dimensioni: {editor.get_image_size()}")
    
    # Test crop
    print("\n1. Test Crop:")
    editor.crop((100, 100, 300, 200))
    print(f"   Dopo crop: {editor.get_image_size()}")
    
    # Test rotate
    print("\n2. Test Rotate:")
    editor.rotate(90)
    print(f"   Dopo rotate 90°: {editor.get_image_size()}")
    
    # Test undo
    print("\n3. Test Undo:")
    editor.undo()
    print(f"   Dopo undo: {editor.get_image_size()}")
    print(f"   Can undo: {editor.can_undo()}, Can redo: {editor.can_redo()}")
    
    # Test history
    print("\n4. Test History:")
    print(f"   Stati in history: {len(editor.history)}")
    print(f"   Posizione corrente: {editor.history_index}")
    
    # Test reset
    print("\n5. Test Reset:")
    editor.reset()
    print(f"   Dopo reset: {editor.get_image_size()}")
    
    print("\n✅ Test completati")


if __name__ == "__main__":
    test_image_editor()
