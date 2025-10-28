"""
Project Manager - Gestisce salvataggio e caricamento progetti
"""

import zipfile
import json
import shutil
import base64
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from PIL import Image


class ProjectManager:
    """Gestisce progetti: salvataggio in ZIP e caricamento"""
    
    def __init__(self):
        self.project_version = "1.0"
    
    def save_project(self, output_path: str, document_path: str, 
                    analysis_results: Dict, jumps_created: list = None,
                    modifications: Dict = None) -> bool:
        """
        Salva progetto completo in ZIP
        
        Args:
            output_path: Percorso ZIP output
            document_path: Percorso documento originale
            analysis_results: Risultati analisi
            jumps_created: Lista jump creati
            modifications: Modifiche apportate
        
        Returns:
            True se successo
        """
        try:
            # Crea directory temporanea
            temp_dir = Path("temp_project")
            temp_dir.mkdir(exist_ok=True)
            
            # 1. Copia documento originale
            doc_name = Path(document_path).name
            shutil.copy(document_path, temp_dir / doc_name)
            
            # 2. Salva stato progetto
            project_state = {
                'version': self.project_version,
                'created_date': datetime.now().isoformat(),
                'document_name': doc_name,
                'analysis_results': self._serialize_analysis(analysis_results),
                'jumps_created': jumps_created or [],
                'modifications': modifications or {},
                'statistics': self._compute_statistics(analysis_results, jumps_created)
            }
            
            with open(temp_dir / 'project_state.json', 'w', encoding='utf-8') as f:
                json.dump(project_state, f, indent=2, ensure_ascii=False)
            
            # 3. Metadata
            metadata = {
                'project_name': Path(output_path).stem,
                'software_version': self.project_version,
                'save_date': datetime.now().isoformat(),
                'document_original': doc_name
            }
            
            with open(temp_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. Crea ZIP
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in temp_dir.iterdir():
                    zipf.write(file, file.name)
            
            # 5. Cleanup
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            print(f"Errore salvataggio progetto: {e}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
    
    def load_project(self, zip_path: str) -> Optional[Dict]:
        """
        Carica progetto da ZIP
        
        Args:
            zip_path: Percorso ZIP progetto
        
        Returns:
            Dict con dati progetto o None se errore
        """
        try:
            temp_dir = Path("temp_project_load")
            temp_dir.mkdir(exist_ok=True)
            
            # 1. Estrai ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 2. Carica project_state
            with open(temp_dir / 'project_state.json', 'r', encoding='utf-8') as f:
                project_state = json.load(f)
            
            # 3. Carica metadata
            with open(temp_dir / 'metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 4. Trova documento
            doc_name = project_state['document_name']
            doc_path = temp_dir / doc_name
            
            if not doc_path.exists():
                raise FileNotFoundError(f"Documento {doc_name} non trovato nel progetto")
            
            # 5. Prepara dati ritorno
            project_data = {
                'version': project_state['version'],
                'document_path': str(doc_path),
                'document_name': doc_name,
                'analysis_results': self._deserialize_analysis(project_state['analysis_results']),
                'jumps_created': project_state.get('jumps_created', []),
                'modifications': project_state.get('modifications', {}),
                'statistics': project_state.get('statistics', {}),
                'metadata': metadata,
                'temp_dir': temp_dir  # Per cleanup dopo
            }
            
            return project_data
            
        except Exception as e:
            print(f"Errore caricamento progetto: {e}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return None
    
    def cleanup_temp_project(self, temp_dir: Path):
        """Pulisce directory temporanea progetto"""
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    def _serialize_analysis(self, analysis_results: Dict) -> Dict:
        """Serializza risultati analisi per JSON"""
        serialized = {}
        
        for key, value in analysis_results.items():
            if key == 'images':
                # Converti immagini PIL in bytes per salvataggio
                serialized_images = []
                for img in value:
                    img_dict = {}
                    
                    # Copia tutti i metadati (tranne image_part che non è serializzabile)
                    for k, v in img.items():
                        if k not in ['image_part', 'image']:
                            img_dict[k] = v
                    
                    # Converti immagine PIL in bytes se presente
                    if 'image' in img and img['image'] is not None:
                        try:
                            # Converti PIL Image in bytes
                            pil_image = img['image']
                            img_buffer = io.BytesIO()
                            
                            # Salva come PNG (formato lossless)
                            pil_image.save(img_buffer, format='PNG')
                            img_bytes = img_buffer.getvalue()
                            
                            # Converti in base64 per JSON
                            img_dict['image_data'] = base64.b64encode(img_bytes).decode('utf-8')
                            
                            # Salva anche formato e dimensioni
                            img_dict['width'] = pil_image.width
                            img_dict['height'] = pil_image.height
                            img_dict['format'] = 'PNG'
                            
                        except Exception as e:
                            print(f"⚠ Errore conversione immagine: {e}")
                            # Se fallisce, almeno salva i metadati
                            pass
                    
                    serialized_images.append(img_dict)
                
                serialized[key] = serialized_images
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_analysis(self, serialized: Dict) -> Dict:
        """Deserializza risultati analisi"""
        deserialized = {}
        
        for key, value in serialized.items():
            if key == 'images':
                # Decodifica bytes immagini da base64
                deserialized_images = []
                for img_dict in value:
                    # Se ha image_data in base64, decodificalo
                    if 'image_data' in img_dict:
                        try:
                            # Decodifica da base64 a bytes
                            img_bytes = base64.b64decode(img_dict['image_data'])
                            
                            # Sostituisci la stringa base64 con i bytes puri
                            img_dict = img_dict.copy()
                            img_dict['image_data'] = img_bytes
                            
                        except Exception as e:
                            print(f"⚠ Errore decodifica immagine: {e}")
                    
                    deserialized_images.append(img_dict)
                
                deserialized[key] = deserialized_images
            else:
                deserialized[key] = value
        
        return deserialized
    
    def _compute_statistics(self, analysis_results: Dict, jumps_created: list) -> Dict:
        """Calcola statistiche progetto"""
        stats = {
            'total_images': len(analysis_results.get('images', [])),
            'total_tables': len(analysis_results.get('tables', [])),
            'total_equations': len(analysis_results.get('equations', [])),
            'total_references': len(analysis_results.get('references', [])),
            'jumps_created': len(jumps_created) if jumps_created else 0
        }
        
        return stats
    
    def get_project_info(self, zip_path: str) -> Optional[Dict]:
        """
        Ottiene info progetto senza caricarlo completamente
        
        Returns:
            Dict con metadata o None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                with zipf.open('metadata.json') as f:
                    metadata = json.load(f)
                
                with zipf.open('project_state.json') as f:
                    state = json.load(f)
                    stats = state.get('statistics', {})
            
            return {
                'metadata': metadata,
                'statistics': stats
            }
            
        except Exception as e:
            print(f"Errore lettura info progetto: {e}")
            return None
