"""
DeepFace Recognition System (Updated for Python 3.12)
Uses DeepFace (VGG-Face) for professional-grade accuracy.
Replaces manual pixel statistics with AI embeddings.
Fixes: JSON serialization errors by forcing Python types.
"""

import json
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import numpy as np

# Import DeepFace
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("❌ DeepFace not found! Please run: pip install -r requirements.txt")

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraSimpleFaceRecognition:
    """Professional Face Recognition using DeepFace embeddings"""
    
    def __init__(self, pinecone_api_key: str = None, pinecone_environment: str = None, index_name: str = "student-faces"):
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_environment = pinecone_environment
        self.index_name = index_name
        self.index = None
        
        # 1. Setup Pinecone (Vector Database)
        if pinecone_api_key:
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=self.pinecone_api_key)
                existing_indexes = [i.name for i in pc.list_indexes()]
                if self.index_name in existing_indexes:
                    self.index = pc.Index(self.index_name)
                    logger.info(f"✅ Connected to Pinecone index: {self.index_name}")
                else:
                    logger.warning(f"Index {self.index_name} not found in: {existing_indexes}")
            except Exception as e:
                logger.warning(f"⚠️ Pinecone connection failed: {e}")

        # 2. Setup Local Storage (Fallback)
        self.local_storage_path = Path("local_face_storage.json")
        self.local_storage = self._load_local_storage()
        
        # 3. Create directories
        self.student_images_path = Path("student_images")
        self.temp_upload_path = Path("temp_uploads")
        self.student_images_path.mkdir(exist_ok=True)
        self.temp_upload_path.mkdir(exist_ok=True)
        
        # 4. Validation
        if not DEEPFACE_AVAILABLE:
            logger.error("❌ CRITICAL: DeepFace library is missing.")
        else:
            logger.info("✅ DeepFace System initialized (VGG-Face model)")

    def _load_local_storage(self) -> Dict:
        if self.local_storage_path.exists():
            try:
                with open(self.local_storage_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_local_storage(self):
        try:
            with open(self.local_storage_path, 'w') as f:
                json.dump(self.local_storage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save local storage: {e}")

    def _extract_image_features(self, image_path: str) -> Optional[List[float]]:
        """
        Extracts AI embeddings using DeepFace.
        DeepFace handles detection, alignment, and resizing internally.
        """
        if not DEEPFACE_AVAILABLE:
            return None
            
        try:
            # DeepFace.represent automatically performs:
            # 1. Face Detection
            # 2. Alignment (rotating eyes to be horizontal)
            # 3. Normalization & Resizing
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name="VGG-Face",
                enforce_detection=False, # Process even if face is hard to detect
                detector_backend="opencv"
            )
            
            # Return the embedding of the first face found
            return embedding_objs[0]["embedding"]
            
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {e}")
            return None

    def enroll_student(self, roll_no: str, student_name: str, image_folder_path: str) -> bool:
        """Enroll a student by averaging embeddings from multiple images"""
        try:
            logger.info(f"Enrolling student: {student_name} ({roll_no})")
            
            # Get valid images
            image_folder = Path(image_folder_path)
            valid_exts = {'.jpg', '.jpeg', '.png', '.bmp'}
            image_files = [f for f in image_folder.iterdir() if f.suffix.lower() in valid_exts]
            
            if not image_files:
                logger.error("No image files found in folder")
                return False

            # Extract embeddings for ALL images
            all_embeddings = []
            for img_path in image_files:
                embedding = self._extract_image_features(str(img_path))
                if embedding:
                    all_embeddings.append(embedding)

            if not all_embeddings:
                logger.error("Could not find faces in any uploaded images")
                return False

            # Calculate AVERAGE embedding (improves accuracy)
            avg_embedding = np.mean(all_embeddings, axis=0).tolist()
            
            student_data = {
                "roll_no": roll_no,
                "name": student_name,
                "features": avg_embedding,
                "enrolled_at": datetime.now().isoformat(),
                "images_processed": len(all_embeddings)
            }

            # Save to Pinecone or Local
            if self.index:
                try:
                    self.index.upsert(vectors=[(roll_no, avg_embedding, {
                        "roll_no": roll_no,
                        "name": student_name,
                        "enrolled_at": student_data["enrolled_at"]
                    })])
                    logger.info("✅ Stored in Pinecone")
                except Exception as e:
                    logger.error(f"Pinecone error: {e}")
            
            # Always save local backup
            self.local_storage[roll_no] = student_data
            self._save_local_storage()
            
            return True

        except Exception as e:
            logger.error(f"❌ Error enrolling student: {e}")
            return False

    def recognize_student(self, image_path: str, top_k: int = 3) -> List[Dict]:
        """Recognize student using Cosine Similarity on AI embeddings"""
        try:
            # 1. Get embedding for the new image
            query_embedding = self._extract_image_features(image_path)
            if not query_embedding:
                return []

            matches = []

            # 2. Try Pinecone Search
            if self.index:
                try:
                    results = self.index.query(
                        vector=query_embedding,
                        top_k=top_k,
                        include_metadata=True
                    )
                    
                    for match in results['matches']:
                        # Force conversion to standard python float
                        confidence = float(match['score'] * 100)
                        matches.append({
                            "roll_no": match['metadata']['roll_no'],
                            "name": match['metadata']['name'],
                            "confidence": confidence,
                            "is_match": bool(confidence > 65), # Force conversion to python bool
                            "method": "pinecone"
                        })
                    return matches
                except Exception as e:
                    logger.warning(f"Pinecone query failed: {e}")

            # 3. Fallback to Local Search (Manual Cosine Similarity)
            query_vec = np.array(query_embedding)
            norm_q = np.linalg.norm(query_vec)

            for roll_no, data in self.local_storage.items():
                stored_vec = np.array(data["features"])
                norm_s = np.linalg.norm(stored_vec)
                
                # Cosine Similarity Formula
                if norm_q > 0 and norm_s > 0:
                    similarity = np.dot(query_vec, stored_vec) / (norm_q * norm_s)
                    
                    # ⚠️ CRITICAL FIX: Explicitly cast numpy types to Python types
                    confidence = float(similarity * 100)
                    is_match_val = bool(confidence > 65)
                    
                    matches.append({
                        "roll_no": data["roll_no"],
                        "name": data["name"],
                        "confidence": confidence,
                        "is_match": is_match_val,
                        "method": "local"
                    })

            # Sort by confidence
            matches.sort(key=lambda x: x['confidence'], reverse=True)
            return matches[:top_k]

        except Exception as e:
            logger.error(f"❌ Recognition error: {e}")
            return []

    def delete_student(self, roll_no: str) -> bool:
        """Delete student from database"""
        try:
            if self.index:
                try:
                    self.index.delete(ids=[roll_no])
                except:
                    pass
            
            if roll_no in self.local_storage:
                del self.local_storage[roll_no]
                self._save_local_storage()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting student: {str(e)}")
            return False

    def get_system_stats(self):
        return {
            "status": "operational",
            "backend": "DeepFace (VGG-Face)",
            "students_enrolled": len(self.local_storage),
            "storage_method": "pinecone" if self.index else "local"
        }

# Factory function
def create_ultra_simple_face_system(pinecone_api_key=None, pinecone_environment=None):
    return UltraSimpleFaceRecognition(pinecone_api_key, pinecone_environment)