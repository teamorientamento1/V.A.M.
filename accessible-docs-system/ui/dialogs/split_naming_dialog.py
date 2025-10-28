"""
Dialog per nominare parti dopo split immagine
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QGroupBox, QScrollArea,
                             QWidget, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QImage
from PIL import Image
from typing import List
import io


class SplitNamingDialog(QDialog):
    """Dialog per assegnare nomi alle parti divise"""
    
    def __init__(self, parts: List[Image.Image], original_label: str, parent=None):
        """
        Args:
            parts: Lista immagini divise
            original_label: Nome originale (es. "Fig. 2.5")
            parent: Parent widget
        """
        super().__init__(parent)
        self.parts = parts
        self.original_label = original_label
        self.part_names = []
        
        self.setWindowTitle("✂️ Nomina Parti Divise")
        self.setMinimumSize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Titolo
        title = QLabel(f"✂️ Immagine divisa in {len(self.parts)} parti")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        info = QLabel(f"Originale: {self.original_label}\nAssegna un nome a ciascuna parte:")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Scroll area per le parti
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        container_layout = QVBoxLayout()
        
        self.name_inputs = []
        
        # Genera nomi suggeriti
        suggested_names = self._generate_suggested_names()
        
        for i, (part, suggested) in enumerate(zip(self.parts, suggested_names)):
            part_group = self._create_part_widget(i, part, suggested)
            container_layout.addWidget(part_group)
        
        container.setLayout(container_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Pulsanti
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _generate_suggested_names(self) -> List[str]:
        """Genera nomi suggeriti per le parti"""
        base = self.original_label
        num_parts = len(self.parts)
        
        # Rimuovi "Fig.", "Figura", etc.
        import re
        match = re.search(r'(\d+\.?\d*)', base)
        if match:
            number = match.group(1)
        else:
            number = "1"
        
        # Genera nomi con lettere
        suggestions = []
        for i in range(num_parts):
            letter = chr(ord('a') + i)  # a, b, c, ...
            suggestions.append(f"Fig. {number}{letter}")
        
        return suggestions
    
    def _create_part_widget(self, index: int, image: Image.Image, 
                           suggested_name: str) -> QGroupBox:
        """Crea widget per una parte"""
        group = QGroupBox(f"Parte {index + 1}")
        layout = QHBoxLayout()
        
        # Preview immagine (thumbnail)
        preview_label = QLabel()
        pixmap = self._pil_to_qpixmap(image)
        preview_label.setPixmap(pixmap.scaled(200, 150, 
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
        preview_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        layout.addWidget(preview_label)
        
        # Input nome
        input_layout = QVBoxLayout()
        
        label = QLabel("Nome:")
        label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        input_layout.addWidget(label)
        
        name_input = QLineEdit()
        name_input.setText(suggested_name)
        name_input.setPlaceholderText("Es: Fig. 2.5a")
        input_layout.addWidget(name_input)
        
        size_label = QLabel(f"Dimensioni: {image.width}x{image.height}px")
        size_label.setStyleSheet("color: #666; font-size: 9pt;")
        input_layout.addWidget(size_label)
        
        input_layout.addStretch()
        
        layout.addLayout(input_layout)
        
        group.setLayout(layout)
        
        self.name_inputs.append(name_input)
        
        return group
    
    def _pil_to_qpixmap(self, pil_image: Image.Image) -> QPixmap:
        """Converte PIL Image a QPixmap"""
        # Converti in RGB se necessario
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Converti a bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        
        # Carica in QPixmap
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        return QPixmap.fromImage(qimage)
    
    def get_part_names(self) -> List[str]:
        """Ritorna i nomi assegnati alle parti"""
        return [input_field.text().strip() for input_field in self.name_inputs]
    
    def validate_names(self) -> bool:
        """Valida che tutti i nomi siano univoci e non vuoti"""
        names = self.get_part_names()
        
        # Controlla vuoti
        if any(not name for name in names):
            return False
        
        # Controlla duplicati
        if len(names) != len(set(names)):
            return False
        
        return True
    
    def accept(self):
        """Override accept per validazione"""
        if not self.validate_names():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Nomi non Validi",
                "Assicurati che:\n"
                "• Tutti i campi siano compilati\n"
                "• Non ci siano nomi duplicati"
            )
            return
        
        super().accept()


def test_split_naming_dialog():
    """Test del dialog"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    print("=== TEST SPLIT NAMING DIALOG ===\n")
    
    app = QApplication(sys.argv)
    
    # Crea immagini test
    test_parts = []
    for i in range(3):
        img = Image.new('RGB', (400, 300), color=(100 + i*50, 100, 150))
        test_parts.append(img)
    
    dialog = SplitNamingDialog(test_parts, "Fig. 2.5")
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        names = dialog.get_part_names()
        print(f"✓ Nomi assegnati: {names}")
    else:
        print("✗ Dialog annullato")
    
    print("\n✅ Test completato")


if __name__ == "__main__":
    test_split_naming_dialog()
