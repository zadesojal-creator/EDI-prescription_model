"""
Multi-Line Prescription Line Segmenter Module.
Detects full prescription sheets, counts total prescribed medicine lines,
and crops individual line segment images for downstream ML model inference.
"""

import cv2
import uuid
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

class PrescriptionLineSegmenter:
    """
    Segmentation engine for detecting handwritten medicine lines on full prescription pages.
    """

    def __init__(self, segments_dir: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.segments_dir = Path(segments_dir) if segments_dir else project_root / "data" / "uploads" / "segments"
        self.segments_dir.mkdir(parents=True, exist_ok=True)

    def is_single_word_crop(self, img: np.ndarray) -> bool:
        """
        Determines if an image is already a single cropped medicine word vs a full page.
        """
        h, w = img.shape[:2]
        aspect_ratio = w / float(h)
        return h < 150 or aspect_ratio > 3.8

    def segment_prescription_lines(self, image_path: str) -> Dict:
        """
        Processes a prescription image:
        - If single word crop, returns 1 medicine count.
        - If full prescription page, segments all medicine lines via Y-center clustering,
          crops segment images, and returns total medicine count.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Prescription image not found at '{image_path}'")

        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Could not load image file from '{image_path}'")

        h, w = img.shape[:2]

        # 1. Single Word Check
        if self.is_single_word_crop(img):
            return {
                "is_multi_line": False,
                "total_medicines_detected": 1,
                "segments": [
                    {
                        "line_number": 1,
                        "bounding_box": {"x": 0, "y": 0, "width": w, "height": h},
                        "cropped_image_path": str(img_path)
                    }
                ]
            }

        # 2. Multi-Line Prescription Segmentation
        body_top = int(h * 0.18)
        body_bottom = int(h * 0.98)
        body_left = int(w * 0.03)
        body_right = int(w * 0.95)

        body = img[body_top:body_bottom, body_left:body_right]
        bh_total, bw_total = body.shape[:2]

        gray = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Subtract long vertical margin lines
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
        vert_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vert_kernel)
        thresh_clean = cv2.subtract(thresh, vert_lines)

        # Apply narrow-height horizontal morphological dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        dilated = cv2.dilate(thresh_clean, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_boxes = []
        for c in contours:
            bx, by, bw_box, bh_box = cv2.boundingRect(c)
            # Filter tiny dots and header noise
            if bw_box > 45 and bh_box > 12 and bh_box < int(bh_total * 0.35):
                full_x = bx + body_left
                full_y = by + body_top
                raw_boxes.append((full_x, full_y, bw_box, bh_box))

        # Sort top-to-bottom
        raw_boxes = sorted(raw_boxes, key=lambda b: b[1])

        # Cluster boxes into distinct medicine line bands based on Y center
        line_clusters = []
        for b in raw_boxes:
            bx, by, bw_box, bh_box = b
            y_center = by + bh_box / 2.0
            matched = False
            for cluster in line_clusters:
                cluster_y_center = np.mean([cb[1] + cb[3]/2.0 for cb in cluster])
                if abs(y_center - cluster_y_center) < 38:
                    cluster.append(b)
                    matched = True
                    break
            if not matched:
                line_clusters.append([b])

        # Convert line clusters to merged bounding boxes
        merged_boxes = []
        for cluster in line_clusters:
            min_x = min(b[0] for b in cluster)
            min_y = min(b[1] for b in cluster)
            max_x = max(b[0] + b[2] for b in cluster)
            max_y = max(b[1] + b[3] for b in cluster)
            bw_merged = max_x - min_x
            bh_merged = max_y - min_y

            # Keep only line bands that have substantial width (> 80px)
            if bw_merged > 80:
                merged_boxes.append((min_x, min_y, bw_merged, bh_merged))

        # Fallback if no lines matched: treat entire body as 1 line
        if not merged_boxes:
            merged_boxes = [(body_left, body_top, bw_total, bh_total)]

        # Crop and save individual line segment images
        segments = []
        task_uuid = uuid.uuid4().hex[:8]

        for idx, (bx, by, bw_box, bh_box) in enumerate(merged_boxes, 1):
            # Pad crop box by 12px safely
            pad_y1 = max(0, by - 12)
            pad_y2 = min(h, by + bh_box + 12)
            pad_x1 = max(0, bx - 12)
            pad_x2 = min(w, bx + bw_box + 12)

            crop = img[pad_y1:pad_y2, pad_x1:pad_x2]
            seg_filename = f"segment_{task_uuid}_line{idx}.png"
            seg_path = self.segments_dir / seg_filename

            cv2.imwrite(str(seg_path), crop)

            segments.append({
                "line_number": idx,
                "bounding_box": {"x": bx, "y": by, "width": bw_box, "height": bh_box},
                "cropped_image_path": str(seg_path),
                "segment_filename": seg_filename
            })

        return {
            "is_multi_line": len(segments) > 1,
            "total_medicines_detected": len(segments),
            "segments": segments
        }
