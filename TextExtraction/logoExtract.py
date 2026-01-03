"""
PDF Logo Extractor using Open-Source AI
Uses YOLOv8 for object detection + EasyOCR for text filtering
No paid APIs required!
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image
from pdf2image import convert_from_path
import easyocr
from ultralytics import YOLO


class OpenSourceLogoExtractor:
    def __init__(self, model_size: str = 'yolov8n'):
        """
        Initialize with open-source models
        
        Args:
            model_size: 'yolov8n' (nano, fastest), 'yolov8s' (small), 
                       'yolov8m' (medium), 'yolov8l' (large)
        """
        print("Loading AI models (this may take a moment)...")
        
        # Load YOLO model for object detection
        self.yolo = YOLO(f'{model_size}.pt')
        print(f"✓ Loaded {model_size} model")
        
        # Load EasyOCR for text detection (to filter it out)
        self.text_detector = easyocr.Reader(['en'], gpu=True)
        print("✓ Loaded EasyOCR text detector")
        
        # Logo-like object classes from COCO dataset
        self.logo_classes = {
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
            'bird', 'cat', 'dog', 'horse', 'bear', 'elephant', 'zebra', 'giraffe',
            'sports ball', 'kite', 'baseball bat', 'skateboard', 'surfboard',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
            'clock', 'vase', 'scissors', 'teddy bear', 'book'
        }
        
        print("✓ Ready to extract logos!\n")
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        """Convert PDF to high-resolution images"""
        print(f"Converting PDF to images (DPI: {dpi})...")
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"✓ Converted {len(images)} page(s)\n")
        return images
    
    def detect_objects_yolo(self, image: Image.Image, 
                           confidence: float = 0.3) -> List[Dict]:
        """
        Detect objects using YOLOv8
        
        Args:
            image: PIL Image
            confidence: Detection confidence threshold
            
        Returns:
            List of detected objects with bounding boxes
        """
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run YOLO detection
        results = self.yolo(img_array, conf=confidence, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = result.names[cls]
                
                detections.append({
                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    'confidence': conf,
                    'class': class_name,
                    'method': 'yolo'
                })
        
        return detections
    
    def detect_logo_regions(self, image: Image.Image) -> List[Dict]:
        """
        Detect potential logo regions using multiple methods
        """
        print("Detecting logo regions...")
        
        all_detections = []
        
        # Method 1: YOLO object detection
        yolo_dets = self.detect_objects_yolo(image, confidence=0.25)
        all_detections.extend(yolo_dets)
        print(f"  → YOLO found {len(yolo_dets)} object(s)")
        
        # Method 2: Detect regions in top 25% of image (where logos usually are)
        top_regions = self._extract_top_regions(image)
        all_detections.extend(top_regions)
        print(f"  → Top regions: {len(top_regions)}")
        
        # Method 3: Color-based region detection
        color_regions = self._detect_color_regions(image)
        all_detections.extend(color_regions)
        print(f"  → Color regions: {len(color_regions)}")
        
        return all_detections
    
    def _extract_top_regions(self, image: Image.Image, 
                            num_segments: int = 5) -> List[Dict]:
        """Extract top regions where logos are commonly placed"""
        width, height = image.size
        top_height = height // 4  # Top 25%
        
        regions = []
        segment_width = width // num_segments
        
        for i in range(num_segments):
            x1 = i * segment_width
            x2 = (i + 1) * segment_width if i < num_segments - 1 else width
            
            regions.append({
                'bbox': (x1, 0, x2, top_height),
                'confidence': 0.4,
                'class': f'top_region_{i+1}',
                'method': 'region'
            })
        
        return regions
    
    def _detect_color_regions(self, image: Image.Image) -> List[Dict]:
        """
        Detect regions with distinct colors (logos have brand colors)
        """
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for common logo colors
        color_ranges = [
            # Blue
            ([100, 50, 50], [130, 255, 255]),
            # Red
            ([0, 50, 50], [10, 255, 255]),
            # Green
            ([40, 50, 50], [80, 255, 255]),
            # Yellow
            ([20, 50, 50], [40, 255, 255]),
            # Orange
            ([10, 50, 50], [20, 255, 255]),
        ]
        
        regions = []
        
        for lower, upper in color_ranges:
            # Create mask for this color
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                          cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area (avoid noise)
                if 1000 < area < 100000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    regions.append({
                        'bbox': (x, y, x + w, y + h),
                        'confidence': 0.5,
                        'class': 'colored_region',
                        'method': 'color'
                    })
        
        return regions
    
    def detect_text_regions(self, image: Image.Image) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions using EasyOCR (to filter them out)
        
        Returns:
            List of bounding boxes containing text
        """
        img_array = np.array(image)
        
        # Detect text
        results = self.text_detector.detect(img_array)
        
        text_boxes = []
        if results and results[0]:
            for bbox in results[0]:
                # EasyOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x1, y1 = int(min(x_coords)), int(min(y_coords))
                x2, y2 = int(max(x_coords)), int(max(y_coords))
                
                text_boxes.append((x1, y1, x2, y2))
        
        return text_boxes
    
    def is_visual_logo(self, image: Image.Image, 
                      text_boxes: List[Tuple]) -> Tuple[bool, str]:
        """
        Check if region is a visual logo (not pure text)
        
        Args:
            image: Extracted region
            text_boxes: List of text bounding boxes from full page
            
        Returns:
            (is_logo, reason)
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        img_array = np.array(image)
        
        # Rule 1: Size check
        if width < 40 or height < 40:
            return False, f"Too small ({width}x{height})"
        
        # Rule 2: Aspect ratio
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 8:
            return False, f"Too elongated ({aspect_ratio:.1f}:1)"
        
        # Rule 3: Color diversity
        pixels = img_array.reshape(-1, 3)
        unique_colors = len(np.unique(pixels, axis=0))
        
        if unique_colors < 5:
            return False, f"Too few colors ({unique_colors})"
        
        # Rule 4: Color variance
        color_std = np.std(pixels, axis=0).mean()
        if color_std < 10:
            return False, f"Low color variance ({color_std:.1f})"
        
        # Rule 5: Check for actual graphics (edge detection)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (width * height)
        
        if edge_density < 0.01:
            return False, f"No defined shapes ({edge_density:.3f})"
        
        # Rule 6: Color saturation (logos have vibrant colors)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = hsv[:, :, 1].mean()
        
        if saturation < 20:
            return False, f"Grayscale/low saturation ({saturation:.1f})"
        
        # Rule 7: Spatial complexity
        # Divide into quadrants and check variance
        h_mid, w_mid = height // 2, width // 2
        quadrants = [
            img_array[:h_mid, :w_mid],
            img_array[:h_mid, w_mid:],
            img_array[h_mid:, :w_mid],
            img_array[h_mid:, w_mid:]
        ]
        
        quad_means = [q.mean() for q in quadrants]
        spatial_var = np.var(quad_means)
        
        if spatial_var < 5:
            return False, f"Low spatial complexity ({spatial_var:.1f})"
        
        # Calculate visual score
        score = (
            min(unique_colors / 20, 1.0) * 25 +
            min(color_std / 40, 1.0) * 20 +
            min(edge_density / 0.05, 1.0) * 20 +
            min(saturation / 100, 1.0) * 15 +
            min(spatial_var / 50, 1.0) * 20
        )
        
        return True, f"Visual logo (score: {score:.0f}/100)"
    
    def remove_duplicates(self, detections: List[Dict]) -> List[Dict]:
        """Remove overlapping detections using NMS"""
        if not detections:
            return []
        
        # Sort by confidence
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        unique = []
        for det in sorted_dets:
            is_dup = False
            for existing in unique:
                iou = self._calc_iou(det['bbox'], existing['bbox'])
                if iou > 0.5:
                    is_dup = True
                    break
            
            if not is_dup:
                unique.append(det)
        
        return unique
    
    def _calc_iou(self, box1, box2):
        """Calculate Intersection over Union"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        xi1, yi1 = max(x1_1, x1_2), max(y1_1, y1_2)
        xi2, yi2 = min(x2_1, x2_2), min(y2_1, y2_2)
        
        if xi2 < xi1 or yi2 < yi1:
            return 0.0
        
        inter = (xi2 - xi1) * (yi2 - yi1)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - inter
        
        return inter / union if union > 0 else 0.0
    
    def extract_region(self, image: Image.Image, bbox: Tuple, 
                      padding: int = 15) -> Image.Image:
        """Extract region with padding"""
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.width, x2 + padding)
        y2 = min(image.height, y2 + padding)
        
        return image.crop((x1, y1, x2, y2))
    
    def process_pdf(self, pdf_path: str, output_dir: str = "extracted_logos_opensource",
                   dpi: int = 300) -> List[str]:
        """
        Extract visual logos from PDF using open-source AI
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        pages = self.pdf_to_images(pdf_path, dpi=dpi)
        saved_logos = []
        pdf_name = Path(pdf_path).stem
        
        for page_num, page_img in enumerate(pages, start=1):
            print(f"\n{'='*70}")
            print(f"PAGE {page_num}")
            print(f"{'='*70}\n")
            
            # Detect text regions first (to filter them out)
            print("Detecting text regions to filter out...")
            text_boxes = self.detect_text_regions(page_img)
            print(f"✓ Found {len(text_boxes)} text region(s)\n")
            
            # Detect logo regions
            detections = self.detect_logo_regions(page_img)
            
            # Remove duplicates
            unique_dets = self.remove_duplicates(detections)
            print(f"\n✓ {len(unique_dets)} unique detection(s) after deduplication\n")
            
            print(f"{'-'*70}")
            print("Analyzing detections...")
            print(f"{'-'*70}\n")
            
            # Process each detection
            for idx, det in enumerate(unique_dets, start=1):
                try:
                    # Extract region
                    logo_img = self.extract_region(page_img, det['bbox'])
                    
                    # Check if it overlaps with text
                    det_bbox = det['bbox']
                    overlaps_text = any(
                        self._calc_iou(det_bbox, text_box) > 0.7
                        for text_box in text_boxes
                    )
                    
                    if overlaps_text:
                        print(f"[{idx}] ✗ FILTERED: Pure text region")
                        continue
                    
                    # Check if it's a visual logo
                    is_logo, reason = self.is_visual_logo(logo_img, text_boxes)
                    
                    if not is_logo:
                        print(f"[{idx}] ✗ FILTERED: {det['class']}")
                        print(f"    Reason: {reason}")
                        continue
                    
                    # Save the logo
                    class_name = det['class'].replace(' ', '_').lower()[:30]
                    method = det['method']
                    conf = int(det['confidence'] * 100)
                    
                    filename = f"{pdf_name}_p{page_num}_{idx}_{class_name}_{method}_{conf}.png"
                    filepath = os.path.join(output_dir, filename)
                    
                    logo_img.save(filepath, 'PNG', quality=95)
                    saved_logos.append(filepath)
                    
                    print(f"[{idx}] ✓ SAVED: {det['class']}")
                    print(f"    {reason}")
                    print(f"    Size: {logo_img.width}x{logo_img.height} | Method: {method}")
                    
                except Exception as e:
                    print(f"[{idx}] ✗ ERROR: {e}")
        
        print(f"\n{'='*70}")
        print("EXTRACTION COMPLETE")
        print(f"{'='*70}")
        print(f"Total visual logos: {len(saved_logos)}")
        print(f"Output directory: {output_dir}/")
        print(f"{'='*70}\n")
        
        return saved_logos


def main():
    """Example usage"""
    PDF_PATH = "degree.pdf"
    OUTPUT_DIR = "logos_opensource"
    
    try:
        print("="*70)
        print("OPEN-SOURCE AI LOGO EXTRACTOR")
        print("="*70)
        print("Using:")
        print("  • YOLOv8 for object detection")
        print("  • EasyOCR for text filtering")
        print("  • OpenCV for color/edge analysis")
        print("  • No paid APIs required!")
        print("="*70 + "\n")
        
        # Initialize extractor
        extractor = OpenSourceLogoExtractor(model_size='yolov8n')
        
        # Extract logos
        logos = extractor.process_pdf(
            pdf_path=PDF_PATH,
            output_dir=OUTPUT_DIR,
            dpi=300
        )
        
        if logos:
            print("\nExtracted Logos:")
            for i, path in enumerate(logos, 1):
                print(f"  {i}. {Path(path).name}")
        else:
            print("\n⚠ No visual logos found")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nInstall dependencies:")
        print("  pip install pdf2image pillow ultralytics easyocr opencv-python numpy")
        print("\nSystem requirements:")
        print("  • Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("  • macOS: brew install poppler")


if __name__ == "__main__":
    main()