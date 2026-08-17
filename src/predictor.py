import os
import pickle
import numpy as np
from pathlib import Path
from PIL import Image
import tensorflow as tf

from src.confidence import evaluate_confidence
from src.medicine_mapping import GenericMedicineMapper

class MedicinePredictor:
    """
    Standalone Production Predictor for Handwritten Medicine Recognition using EfficientNetB0.
    Handles image loading, white-canvas letterboxing, model inference, brand-to-generic mapping, and top-k candidate generation.
    """

    def __init__(self, model_path: str = None, label_encoder_path: str = None, mapping_csv_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.model_path = Path(model_path) if model_path else project_root / "models" / "efficientnetb0_best.keras"
        self.label_encoder_path = Path(label_encoder_path) if label_encoder_path else project_root / "models" / "v3_label_encoder.pkl"
        self.mapping_csv_path = mapping_csv_path

        self._load_model_and_encoder()
        self.mapper = GenericMedicineMapper(mapping_csv_path=self.mapping_csv_path)

    def _load_model_and_encoder(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        if not self.label_encoder_path.exists():
            raise FileNotFoundError(f"Label encoder not found at {self.label_encoder_path}")

        # Load Keras Model
        self.model = tf.keras.models.load_model(self.model_path)

        # Load Label Encoder
        with open(self.label_encoder_path, "rb") as f:
            self.label_encoder = pickle.load(f)

        self.class_names = list(self.label_encoder.classes_)
        self.num_classes = len(self.class_names)

    def preprocess_image(self, image_input) -> np.ndarray:
        """
        Letterbox any input image (file path, PIL Image, or numpy array) onto a 224x224 square white canvas.
        Preserves original handwriting aspect ratio without stretching.
        Returns a float32 tensor of shape (1, 224, 224, 3) in range [0, 255].
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert('RGB')
        elif isinstance(image_input, Image.Image):
            img = image_input.convert('RGB')
        elif isinstance(image_input, np.ndarray):
            img = Image.fromarray(image_input.astype(np.uint8)).convert('RGB')
        else:
            raise ValueError("Unsupported image input type. Provide a file path, PIL Image, or numpy array.")

        W, H = img.size
        max_dim = max(W, H)
        canvas = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
        canvas.paste(img, ((max_dim - W) // 2, (max_dim - H) // 2))

        resized = canvas.resize((224, 224), Image.LANCZOS)
        img_array = np.array(resized, dtype=np.float32)
        return np.expand_dims(img_array, axis=0)

    def predict(self, image_input, top_k: int = 3) -> dict:
        """
        Execute prediction on an input image.
        Returns a clean dictionary containing top_brand, confidence, and top_k candidates.
        """
        preprocessed_tensor = self.preprocess_image(image_input)
        raw_probs = self.model.predict(preprocessed_tensor, verbose=0)[0]

        top_k_indices = np.argsort(raw_probs)[-top_k:][::-1]

        candidates = []
        for idx in top_k_indices:
            b_name = self.class_names[idx]
            g_info = self.mapper.get_generic_mapping(b_name)
            candidates.append({
                "class_index": int(idx),
                "brand_name": b_name,
                "generic_name": g_info["generic_name"],
                "mapping_status": g_info["mapping_status"],
                "confidence": float(raw_probs[idx])
            })

        top_1 = candidates[0]
        conf_eval = evaluate_confidence(top_1["confidence"])
        display_brand = top_1["brand_name"] if conf_eval["is_definitive_display"] else "Unknown"
        display_generic = top_1["generic_name"] if conf_eval["is_definitive_display"] else None
        display_mapping_status = top_1["mapping_status"] if conf_eval["is_definitive_display"] else "UNVERIFIED"

        return {
            "top_brand": display_brand,
            "generic_name": display_generic,
            "mapping_status": display_mapping_status,
            "top_confidence": top_1["confidence"],
            "top_candidates": candidates,
            "status": conf_eval["status"],
            "doctor_feedback_required": conf_eval["doctor_feedback_required"],
            "doctor_verification_required": conf_eval["doctor_verification_required"],
            "review_priority": conf_eval["review_priority"],
            "user_message": conf_eval["user_message"],
            "is_definitive_display": conf_eval["is_definitive_display"],
            "raw_probabilities": raw_probs.tolist()
        }


