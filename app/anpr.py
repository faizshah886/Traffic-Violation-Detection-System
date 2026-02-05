"""
Automatic Number Plate Recognition (ANPR) module
"""
import cv2
import numpy as np
from pathlib import Path
from utils import clean_plate_text

class ANPR:
    def __init__(self, use_easyocr=False):
        """Initialize OCR engine"""
        self.use_easyocr = use_easyocr
        
        if use_easyocr:
            try:
                import easyocr
                self.reader = easyocr.Reader(['en'], gpu=False)
                print("EasyOCR initialized")
            except Exception as e:
                print(f"EasyOCR not available ({e}), falling back to Tesseract")
                self.use_easyocr = False
                self._init_tesseract()
        else:
            self._init_tesseract()
    
    def _init_tesseract(self):
        """Initialize Tesseract OCR"""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            print("Tesseract initialized")
        except ImportError:
            print("Warning: Neither EasyOCR nor Tesseract available")
            self.pytesseract = None
    
    def preprocess_plate(self, plate_image):
        """Preprocess plate image for better OCR"""
        # Convert to grayscale
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image
        
        # Apply bilateral filter to reduce noise
        denoised = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Resize for better recognition
        height, width = thresh.shape
        if height < 50:
            scale = 50 / height
            new_width = int(width * scale)
            thresh = cv2.resize(thresh, (new_width, 50))
        
        return thresh
    
    def extract_text_easyocr(self, plate_image):
        """Extract text using EasyOCR"""
        try:
            results = self.reader.readtext(plate_image)
            if results:
                # Combine all detected text
                text = ' '.join([result[1] for result in results])
                return clean_plate_text(text)
        except Exception as e:
            print(f"EasyOCR error: {e}")
        return None
    
    def extract_text_tesseract(self, plate_image):
        """Extract text using Tesseract"""
        if not self.pytesseract:
            return None
        
        try:
            # Configure Tesseract for license plate
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            text = self.pytesseract.image_to_string(plate_image, config=custom_config)
            return clean_plate_text(text)
        except Exception as e:
            print(f"Tesseract error: {e}")
        return None
    
    def read_plate(self, frame, plate_bbox):
        """
        Read number plate from frame
        Args:
            frame: Original frame
            plate_bbox: Bounding box (x1, y1, x2, y2)
        Returns:
            plate_text: Extracted text or None
        """
        # Extract plate region
        x1, y1, x2, y2 = plate_bbox
        plate_image = frame[int(y1):int(y2), int(x1):int(x2)]
        
        if plate_image.size == 0:
            return None
        
        # Preprocess
        processed = self.preprocess_plate(plate_image)
        
        # Extract text
        if self.use_easyocr:
            text = self.extract_text_easyocr(processed)
        else:
            text = self.extract_text_tesseract(processed)
        
        # Validate text
        if text and len(text) >= 4:  # Minimum plate length
            return text
        
        return None
    
    def save_plate_image(self, frame, plate_bbox, output_path):
        """Save cropped plate image"""
        x1, y1, x2, y2 = plate_bbox
        plate_image = frame[int(y1):int(y2), int(x1):int(x2)]
        cv2.imwrite(str(output_path), plate_image)
        return output_path
