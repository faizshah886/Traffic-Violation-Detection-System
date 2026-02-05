"""
Challan PDF/Image Generator
"""
import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import qrcode

class ChallanGenerator:
    def __init__(self, output_dir):
        """Initialize challan generator"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_qr_code(self, challan_id, output_path):
        """Generate QR code for challan"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_data = f"CHALLAN-{challan_id}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        return output_path
    
    def generate_pdf(self, challan_data):
        """
        Generate challan PDF
        Args:
            challan_data: Dictionary containing:
                - id: Challan ID
                - plate_number: Vehicle plate number
                - violation_type: Type of violation
                - fine_amount: Fine amount
                - timestamp: Violation timestamp
                - image_path: Path to violation image
                - plate_image_path: Path to plate image
        """
        challan_id = challan_data['id']
        output_path = self.output_dir / f"{challan_id}.pdf"
        
        # Create PDF
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 1*inch, "TRAFFIC CHALLAN")
        
        # Department info
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 1.5*inch, "Traffic Police Department")
        c.drawCentredString(width/2, height - 1.8*inch, "Smart Violation Detection System")
        
        # Horizontal line
        c.line(1*inch, height - 2*inch, width - 1*inch, height - 2*inch)
        
        # Challan details
        y_position = height - 2.5*inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, y_position, f"Challan No: {challan_id}")
        
        y_position -= 0.5*inch
        c.setFont("Helvetica", 12)
        
        # Details table
        details = [
            ("Plate Number:", challan_data.get('plate_number', 'N/A')),
            ("Violation Type:", challan_data['violation_type'].replace('_', ' ').title()),
            ("Fine Amount:", f"Rs. {challan_data['fine_amount']}"),
            ("Date & Time:", challan_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))),
            ("Status:", challan_data.get('status', 'Unpaid').upper())
        ]
        
        for label, value in details:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(1*inch, y_position, label)
            c.setFont("Helvetica", 11)
            c.drawString(2.5*inch, y_position, str(value))
            y_position -= 0.3*inch
        
        # Images section
        y_position -= 0.5*inch
        
        # Violation image
        if challan_data.get('image_path') and os.path.exists(challan_data['image_path']):
            try:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(1*inch, y_position, "Violation Evidence:")
                y_position -= 0.3*inch
                
                img = ImageReader(challan_data['image_path'])
                c.drawImage(img, 1*inch, y_position - 2.5*inch, 
                          width=4*inch, height=2*inch, preserveAspectRatio=True)
                y_position -= 2.7*inch
            except Exception as e:
                print(f"Error adding violation image: {e}")
        
        # Plate image
        if challan_data.get('plate_image_path') and os.path.exists(challan_data['plate_image_path']):
            try:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(1*inch, y_position, "Number Plate:")
                y_position -= 0.3*inch
                
                plate_img = ImageReader(challan_data['plate_image_path'])
                c.drawImage(plate_img, 1*inch, y_position - 1*inch, 
                          width=2*inch, height=0.8*inch, preserveAspectRatio=True)
                y_position -= 1.2*inch
            except Exception as e:
                print(f"Error adding plate image: {e}")
        
        # QR Code
        try:
            qr_path = self.output_dir / f"qr_{challan_id}.png"
            self.generate_qr_code(challan_id, qr_path)
            
            if y_position > 2*inch:
                c.drawImage(str(qr_path), width - 2.5*inch, 1*inch, 
                          width=1.5*inch, height=1.5*inch)
        except Exception as e:
            print(f"Error generating QR code: {e}")
        
        # Footer
        c.setFont("Helvetica", 9)
        c.drawCentredString(width/2, 0.8*inch, 
                          "Please pay the fine within 15 days to avoid additional penalties")
        c.drawCentredString(width/2, 0.5*inch, 
                          "For queries, visit www.trafficpolice.gov or call 1234-5678")
        
        c.save()
        print(f"Challan PDF generated: {output_path}")
        return output_path
    
    def generate_image(self, challan_data):
        """Generate challan as image (alternative to PDF)"""
        import cv2
        import numpy as np
        
        challan_id = challan_data['id']
        output_path = self.output_dir / f"{challan_id}.jpg"
        
        # Create blank image
        img = np.ones((1200, 800, 3), dtype=np.uint8) * 255
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "TRAFFIC CHALLAN", (200, 50), font, 1.5, (0, 0, 0), 3)
        cv2.putText(img, f"Challan No: {challan_id}", (50, 120), font, 0.8, (0, 0, 0), 2)
        
        y_pos = 180
        details = [
            f"Plate: {challan_data.get('plate_number', 'N/A')}",
            f"Violation: {challan_data['violation_type']}",
            f"Fine: Rs. {challan_data['fine_amount']}",
            f"Time: {challan_data.get('timestamp', 'N/A')}"
        ]
        
        for detail in details:
            cv2.putText(img, detail, (50, y_pos), font, 0.7, (0, 0, 0), 2)
            y_pos += 40
        
        cv2.imwrite(str(output_path), img)
        return output_path
