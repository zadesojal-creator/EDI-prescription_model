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
        # If image height is small (< 150px) or aspect ratio is very wide, treat as single word
        return h < 150 or aspect_ratio > 3.8

    def segment_prescription_lines(self, image_path: str) -> Dict:
        """
        Processes a prescription image:
        - If single word, returns 1 medicine count.
        - If full prescription page, segments all medicine lines, crops segment images, and returns total medicine count.
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
        body_right = int(w * 0.90)

        body = img[body_top:body_bottom, body_left:body_right]
        bh_total, bw_total = body.shape[:2]

        gray = cv2.cvtColor(body, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Subtract long vertical lines (margins/doodles)
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(bh_total * 0.20)))
        vert_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vert_kernel)
        thresh_clean = cv2.subtract(thresh, vert_lines)

        # Horizontal dilation to merge words on the same line
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(bw_total * 0.08), 5))
        dilated = cv2.dilate(thresh_clean, horiz_kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_boxes = []
        for c in contours:
            x, y, bw_box, bh_box = cv2.boundingRect(c)
            # Filter header noise & tiny dots
            if bw_box > int(bw_total * 0.12) and bh_box > 15 and bh_box < int(bh_total * 0.35):
                full_x = x + body_left
                full_y = y + body_top
                raw_boxes.append((full_x, full_y, bw_box, bh_box))

        # Sort top-to-bottom
        raw_boxes = sorted(raw_boxes, key=lambda b: b[1])

        # Merge vertically overlapping bounding boxes (Y gap < 25px)
        merged_boxes = []
        for b in raw_boxes:
            if not merged_boxes:
                merged_boxes.append(b)
            else:
                prev_x, prev_y, prev_w, prev_h = merged_boxes[-1]
                curr_x, curr_y, curr_w, curr_h = b
                if abs(curr_y - prev_y) < 28:
                    new_x = min(prev_x, curr_x)
                    new_y = min(prev_y, curr_y)
                    new_w = max(prev_x + prev_w, curr_x + curr_w) - new_x
                    new_h = max(prev_y + prev_h, curr_y + curr_h) - new_y
                    merged_boxes[-1] = (new_x, new_y, new_w, new_h)
                else:
                    merged_boxes.append(b)

        # Fallback if no contours matched: treat entire body as 1 line
        if not merged_boxes:
            merged_boxes = [(body_left, body_top, bw_total, bh_total)]

        # Crop and save individual line segment images
        segments = []
        task_uuid = uuid.uuid4().hex[:8]

        for idx, (bx, by, bw_box, bh_box) in enumerate(merged_boxes, 1):
            # Pad crop box by 10px safely
            pad_y1 = max(0, by - 10)
            pad_y2 = min(h, by + bh_box + 10)
            pad_x1 = max(0, bx - 10)
            pad_x2 = min(w, bx + bw_box + 10)

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
