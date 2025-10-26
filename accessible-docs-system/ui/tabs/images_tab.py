from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QPushButton, QTextEdit, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import io
from PIL import Image


class ImagesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.images_data = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("Immagini nel documento:"))
        self.images_list = QListWidget()
        self.images_list.itemClicked.connect(self.on_image_selected)
        left_layout.addWidget(self.images_list)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.image_preview = QLabel("Seleziona un'immagine")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(400, 300)
        self.image_preview.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
        preview_layout.addWidget(self.image_preview)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        info_group = QGroupBox("Informazioni")
        info_layout = QVBoxLayout()
        self.image_info = QTextEdit()
        self.image_info.setReadOnly(True)
        self.image_info.setMaximumHeight(100)
        info_layout.addWidget(self.image_info)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        btn_layout = QHBoxLayout()
        self.btn_save_image = QPushButton("Salva Immagine")
        self.btn_save_image.clicked.connect(self.on_save_image)
        self.btn_save_all = QPushButton("Salva Tutte")
        self.btn_delete = QPushButton("Elimina Immagine")
        self.btn_delete.clicked.connect(self.on_delete_image)
        btn_layout.addWidget(self.btn_save_image)
        btn_layout.addWidget(self.btn_save_all)
        btn_layout.addWidget(self.btn_delete)
        right_layout.addLayout(btn_layout)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def load_images(self, images):
        self.images_list.clear()
        self.images_data = images
        
        for img in images:
            label = img.get('label', 'Senza label')
            self.images_list.addItem(f"{label} - Paragrafo {img['paragraph_index']}")
    
    def on_image_selected(self, item):
        index = self.images_list.row(item)
        if index >= len(self.images_data):
            return
            
        img_data = self.images_data[index]
        
        try:
            if 'image_part' in img_data and img_data['image_part']:
                image_bytes = img_data['image_part'].blob
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                pil_image.thumbnail((400, 300), Image.Resampling.LANCZOS)
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                
                pixmap = QPixmap()
                pixmap.loadFromData(img_byte_arr.getvalue())
                self.image_preview.setPixmap(pixmap)
            else:
                self.image_preview.setText("Preview non disponibile")
        except Exception as e:
            self.image_preview.setText(f"Errore: {str(e)}")
        
        # Context come lista
        context_before = img_data.get('context_before', [])
        context_after = img_data.get('context_after', [])
        
        if isinstance(context_before, list):
            before_text = '\n'.join(context_before)
        else:
            before_text = str(context_before)
        
        if isinstance(context_after, list):
            after_text = '\n'.join(context_after)
        else:
            after_text = str(context_after)
        
        info = f"""Label: {img_data.get('label', 'N/A')}
Tipo: {img_data.get('content_type', 'N/A')}
Posizione: Paragrafo {img_data.get('paragraph_index', 'N/A')}

Contesto prima:
{before_text[:100]}...

Contesto dopo:
{after_text[:100]}...
"""
        self.image_info.setText(info)
    
    def on_save_image(self):
        # TODO: implementare salvataggio
        pass
    
    def on_delete_image(self):
        """Elimina immagine e marca dirty"""
        index = self.images_list.currentRow()
        if index >= 0:
            # Rimuovi dalla lista
            del self.images_data[index]
            self.images_list.takeItem(index)
            
            # Marca dirty per sync
            self.main_window.sync_manager.mark_dirty('images')
