"""
PDF Receipt generation using ReportLab.
Generates a branded donation receipt with temple details.
"""

from io import BytesIO
import urllib.request
import urllib.parse
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
import os

from app.domain.donations.models import Donation

# Register fonts
font_dir = os.path.dirname(os.path.abspath(__file__))
reg_font_path = os.path.join(font_dir, "NotoSansKannada-Regular.ttf")
bold_font_path = os.path.join(font_dir, "NotoSansKannada-Bold.ttf")

if os.path.exists(reg_font_path) and os.path.exists(bold_font_path):
    pdfmetrics.registerFont(TTFont('NotoSansKannada', reg_font_path))
    pdfmetrics.registerFont(TTFont('NotoSansKannada-Bold', bold_font_path))
    FONT_REGULAR = "NotoSansKannada"
    FONT_BOLD = "NotoSansKannada-Bold"
else:
    FONT_REGULAR = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# Design colors
PRIMARY_GREEN = HexColor("#0B3D2E")
SECONDARY_GREEN = HexColor("#145A32")
GOLD = HexColor("#D4AF37")
CREAM = HexColor("#FDFBF5")
WHITE = HexColor("#FFFFFF")
TEXT_PRIMARY = HexColor("#123524")
BORDER_COLOR = HexColor("#BDD4B3")

# Donation type labels (Bilingual)
DONATION_TYPES = {
    "general": "General Donation / ಸಾಮಾನ್ಯ ದೇಣಿಗೆ",
    "annadanam": "Annadanam Seva / ಅನ್ನದಾನ ಸೇವೆ",
    "temple_development": "Temple Development / ದೇವಸ್ಥಾನ ಅಭಿವೃದ್ಧಿ",
    "festival": "Festival Seva / ಹಬ್ಬದ ಸೇವೆ",
    "goshala": "Goshala Seva / ಗೋಶಾಲೆ ಸೇವೆ",
}

def draw_temple_logo(c, x, y):
    """Draw South Indian Gopuram & Deepa Logo using vector shapes."""
    # Outer circle shield
    c.setFillColor(HexColor("#0B3D2E"))
    c.setStrokeColor(HexColor("#D4AF37"))
    c.setLineWidth(2.5)
    c.circle(x, y, 32, fill=True, stroke=True)
    
    # Gopuram tower
    c.setFillColor(HexColor("#D4AF37"))
    c.setStrokeColor(HexColor("#0B3D2E"))
    c.setLineWidth(0.5)
    
    # Top spire (Kalasa)
    p = c.beginPath()
    p.moveTo(x - 3, y + 20)
    p.lineTo(x, y + 28)
    p.lineTo(x + 3, y + 20)
    p.close()
    c.drawPath(p, fill=True, stroke=False)
    
    # Gopuram tiers
    c.rect(x - 6, y + 14, 12, 5, fill=True, stroke=True)
    c.rect(x - 9, y + 6, 18, 7, fill=True, stroke=True)
    c.rect(x - 12, y - 4, 24, 9, fill=True, stroke=True)
    
    # Pillar arch gateway
    c.rect(x - 15, y - 18, 30, 13, fill=True, stroke=True)
    c.setFillColor(HexColor("#0B3D2E"))
    c.rect(x - 10, y - 18, 20, 10, fill=True, stroke=True)
    
    # Oil lamp (Deepa) inside
    c.setFillColor(HexColor("#FF8C00"))
    p2 = c.beginPath()
    p2.moveTo(x, y - 16)
    p2.curveTo(x - 3, y - 12, x - 3, y - 9, x, y - 7)
    p2.curveTo(x + 3, y - 9, x + 3, y - 12, x, y - 16)
    p2.close()
    c.drawPath(p2, fill=True, stroke=False)
    
    # Inner flame glow
    c.setFillColor(HexColor("#FFD700"))
    p3 = c.beginPath()
    p3.moveTo(x, y - 14)
    p3.curveTo(x - 1.5, y - 11, x - 1.5, y - 9, x, y - 8)
    p3.curveTo(x + 1.5, y - 9, x + 1.5, y - 11, x, y - 14)
    p3.close()
    c.drawPath(p3, fill=True, stroke=False)
    
    # Pedestal
    c.setFillColor(HexColor("#D4AF37"))
    c.rect(x - 18, y - 22, 36, 3, fill=True, stroke=False)


def generate_receipt_pdf(donation: Donation) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 1. Background borders & decorations
    c.setFillColor(CREAM)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Decorative green border
    c.setStrokeColor(PRIMARY_GREEN)
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40, fill=False, stroke=True)
    
    # Inner gold border
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.rect(25, 25, width - 50, height - 50, fill=False, stroke=True)

    # 2. Header Panel Card
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(1)
    c.roundRect(40, height - 160, width - 80, 115, 10, fill=True, stroke=True)
    
    # Draw Logo
    draw_temple_logo(c, 85, height - 102)
    
    # English Temple details
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 14)
    c.drawString(135, height - 72, "Shree Shanishwara Swamy Temple (R.)")
    
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(135, height - 86, "Shree Kshetra Siddagiri | www.shreeshanitemple.com")
    c.drawString(135, height - 100, "Kusugundi Village, Koduru Post, Hosanagara Taluk, Shimoga, Karnataka")
    c.drawString(135, height - 114, "Phone: +91 9741943965  |  Email: info@shreeshani.com")
    
    # Kannada translation below English in header card
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(SECONDARY_GREEN)
    c.drawString(135, height - 136, "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) - ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ")

    # 3. Gold Decorative Line
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(40, height - 175, width - 40, height - 175)

    # 4. Receipt Title centered
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 15)
    c.drawCentredString(width / 2, height - 198, "DONATION RECEIPT / ದೇಣಿಗೆ ರಸೀದಿ")
    
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(0.5)
    c.line(150, height - 206, width - 150, height - 206)

    # 5. Receipt Metadata Card
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(1)
    c.roundRect(40, height - 310, width - 80, 85, 8, fill=True, stroke=True)
    
    # Left column of Metadata
    y_meta = height - 250
    c.setFillColor(TEXT_PRIMARY)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_meta, "Receipt Number / ರಸೀದಿ ಸಂಖ್ಯೆ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_meta, donation.receipt_number)
    
    y_meta -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_meta, "Transaction ID / ಆರ್ಡರ್ ಐಡಿ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_meta, donation.razorpay_order_id or "N/A")
    
    y_meta -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_meta, "Payment ID / ಪಾವತಿ ಐಡಿ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_meta, donation.razorpay_payment_id or "N/A")
    
    # Right column of Metadata
    y_meta = height - 250
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(370, y_meta, "Date / ದಿನಾಂಕ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(450, y_meta, donation.created_at.strftime("%d-%m-%Y"))
    
    y_meta -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(370, y_meta, "Time / ಸಮಯ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(450, y_meta, donation.created_at.strftime("%I:%M %p"))
    
    y_meta -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(370, y_meta, "Method / ವಿಧಾನ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(450, y_meta, "Online / ಆನ್‌ಲೈನ್")

    # 6. Donor Details Card
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(40, height - 332, "Donor Details / ದಾನಿಯ ವಿವರಗಳು")
    
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_COLOR)
    c.roundRect(40, height - 455, width - 80, 105, 8, fill=True, stroke=True)
    
    y_donor = height - 370
    c.setFillColor(TEXT_PRIMARY)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_donor, "Donor Name / ದಾನಿಯ ಹೆಸರು:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_donor, donation.donor_name)
    
    y_donor -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_donor, "Email Address / ಇಮೇಲ್:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_donor, donation.donor_email)
    
    y_donor -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_donor, "Mobile Number / ಮೊಬೈಲ್ ಸಂಖ್ಯೆ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_donor, donation.donor_mobile)
    
    y_donor -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_donor, "Address / ವಿಳಾಸ:")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_donor, donation.donor_address or "Not Provided / ಒದಗಿಸಿಲ್ಲ")

    # 7. Donation Details Card
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(40, height - 477, "Donation Details / ದೇಣಿಗೆ ವಿವರಗಳು")
    
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_COLOR)
    c.roundRect(40, height - 590, width - 80, 95, 8, fill=True, stroke=True)
    
    y_done = height - 510
    c.setFillColor(TEXT_PRIMARY)
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_done, "Seva / Devotion Type (ದೇಣಿಗೆ ವಿಧ):")
    c.setFont(FONT_REGULAR, 9.5)
    c.drawString(240, y_done, DONATION_TYPES.get(donation.donation_type, donation.donation_type))
    
    y_done -= 20
    c.setFont(FONT_BOLD, 9.5)
    c.drawString(60, y_done, "Payment Status / ಪಾವತಿ ಸ್ಥಿತಿ:")
    c.setFont(FONT_BOLD, 9.5)
    if donation.status == "completed":
        c.setFillColor(HexColor("#2E7D32"))
        c.drawString(240, y_done, "SUCCESSFUL / ಪೂರ್ಣಗೊಂಡಿದೆ")
    else:
        c.setFillColor(HexColor("#C62828"))
        c.drawString(240, y_done, donation.status.upper())
        
    y_done -= 25
    c.setFillColor(TEXT_PRIMARY)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(60, y_done, "Amount Paid / ಪಾವತಿಸಿದ ಮೊತ್ತ:")
    
    # Highlight the amount in Gold & Green
    c.setFont(FONT_BOLD, 15)
    c.setFillColor(PRIMARY_GREEN)
    amount_rupees = donation.amount // 100
    c.drawString(240, y_done, f"INR ₹{amount_rupees:,}.00")
    
    # Subtle decorative line under the amount
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(240, y_done - 4, 380, y_done - 4)

    # 8. Digital Official Seal (Left)
    seal_x, seal_y = 120, 150
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.circle(seal_x, seal_y, 40, fill=False, stroke=True)
    c.circle(seal_x, seal_y, 37, fill=False, stroke=True)
    c.setFont(FONT_BOLD, 7)
    c.setFillColor(SECONDARY_GREEN)
    c.drawCentredString(seal_x, seal_y + 16, "OFFICIAL RECEIPT")
    c.setFont(FONT_REGULAR, 6.5)
    c.drawCentredString(seal_x, seal_y, "Shree Shanishwara Swamy")
    c.drawCentredString(seal_x, seal_y - 10, "Temple Trust")
    c.setFont(FONT_BOLD, 6.5)
    c.drawCentredString(seal_x, seal_y - 20, "★ VERIFIED ★")

    # 9. Dynamic QR Code (Right)
    qr_x = width - 120
    qr_y = 115
    data_str = f"Receipt: {donation.receipt_number}\nTxn: {donation.razorpay_order_id}\nWeb: www.shreeshanitemple.com"
    encoded_data = urllib.parse.quote(data_str)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded_data}"
    
    try:
        qr_data = urllib.request.urlopen(qr_url).read()
        qr_image = ImageReader(BytesIO(qr_data))
        c.drawImage(qr_image, qr_x, qr_y, width=70, height=70)
        
        # QR Code Verification label
        c.setFillColor(TEXT_PRIMARY)
        c.setFont(FONT_BOLD, 7.5)
        c.drawCentredString(qr_x + 35, qr_y - 12, "Scan to Verify Receipt")
        c.setFont(FONT_REGULAR, 7)
        c.drawCentredString(qr_x + 35, qr_y - 22, "ಪರಿಶೀಲಿಸಲು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ")
    except Exception as e:
        # Fallback placeholder frame
        c.setStrokeColor(BORDER_COLOR)
        c.setLineWidth(1)
        c.rect(qr_x, qr_y, 70, 70, fill=False, stroke=True)
        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(HexColor("#999999"))
        c.drawCentredString(qr_x + 35, qr_y + 30, "[ QR Code ]")

    # 10. Thank You & Blessings Message (Center)
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 10.5)
    c.drawCentredString(width / 2, 230, "Thank you for your generous contribution.")
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(width / 2, 214, "ನಿಮ್ಮ ಉದಾರ ದೇಣಿಗೆಗೆ ಧನ್ಯವಾದಗಳು.")
    
    c.setFillColor(TEXT_PRIMARY)
    c.setFont(FONT_REGULAR, 8.5)
    c.drawCentredString(width / 2, 194, "May Lord Shanishwara Swamy bless you and your family with peace and prosperity.")
    c.drawCentredString(width / 2, 180, "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿಯು ನಿಮಗೆ ಮತ್ತು ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ ಶಾಂತಿ, ನೆಮ್ಮದಿ ನೀಡಲಿ.")

    # 11. Computer Generated footer note
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(40, 85, width - 40, 85)
    
    c.setFillColor(HexColor("#777777"))
    c.setFont(FONT_REGULAR, 7.5)
    c.drawCentredString(width / 2, 70, "This is a computer-generated receipt and does not require a physical signature.")
    c.drawCentredString(width / 2, 58, "ಇದು ಗಣಕಯಂತ್ರದಿಂದ ರಚಿಸಲಾದ ಅಧಿಕೃತ ರಸೀದಿಯಾಗಿದ್ದು ಸಹಿಯ ಅಗತ್ಯವಿರುವುದಿಲ್ಲ.")
    c.setFont(FONT_BOLD, 7.5)
    c.drawCentredString(width / 2, 42, "Shree Shanishwara Swamy Temple (R.), Shree Kshetra Siddagiri")

    c.save()
    return buffer.getvalue()


class NumberedReportCanvas(canvas.Canvas):
    """Two-pass canvas to calculate total page count and draw running header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        w, h = landscape(A4)

        # Outer decorative frame
        self.setStrokeColor(PRIMARY_GREEN)
        self.setLineWidth(1.5)
        self.rect(20, 20, w - 40, h - 40, fill=False, stroke=True)

        self.setStrokeColor(GOLD)
        self.setLineWidth(0.75)
        self.rect(23, 23, w - 46, h - 46, fill=False, stroke=True)

        # Header running line on pages > 1
        if self._pageNumber > 1:
            self.setFont(FONT_BOLD, 8)
            self.setFillColor(PRIMARY_GREEN)
            self.drawString(32, h - 35, "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) — DONATIONS REPORT (Continued)")
            self.drawRightString(w - 32, h - 35, "Shree Shanishwara Swamy Temple (R.)")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(32, h - 38, w - 32, h - 38)

        # Footer divider line
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.75)
        self.line(30, 36, w - 30, 36)

        # Footer text
        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(HexColor("#4A5568"))
        self.drawString(32, 26, "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ — Shree Shanishwara Swamy Temple (R.)")
        self.drawCentredString(w / 2, 26, "Official Admin Report • Confidential")
        self.drawRightString(w - 32, 26, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_donations_report_pdf(donations: list[Donation], query: str = "") -> bytes:
    """
    Generate an official landscape multi-page PDF report for donations.
    Includes temple branding, metrics summary, styled tabular data, and total summary.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=32,
        rightMargin=32,
        topMargin=35,
        bottomMargin=45
    )

    w, h = landscape(A4)
    content_width = w - 64  # 777.89 pt
    elements = []

    # Typography styles
    style_th = ParagraphStyle('TH', fontName=FONT_BOLD, fontSize=8.5, textColor=WHITE, alignment=1)
    style_td = ParagraphStyle('TD', fontName=FONT_REGULAR, fontSize=8, textColor=TEXT_PRIMARY)
    style_td_center = ParagraphStyle('TDC', fontName=FONT_REGULAR, fontSize=8, textColor=TEXT_PRIMARY, alignment=1)
    style_td_bold = ParagraphStyle('TDB', fontName=FONT_BOLD, fontSize=8, textColor=TEXT_PRIMARY)
    style_td_amount = ParagraphStyle('TDA', fontName=FONT_BOLD, fontSize=8.5, textColor=PRIMARY_GREEN, alignment=2)
    style_td_status_ok = ParagraphStyle('TDS_OK', fontName=FONT_BOLD, fontSize=8, textColor=HexColor("#1B5E20"), alignment=1)
    style_td_status_pending = ParagraphStyle('TDS_P', fontName=FONT_BOLD, fontSize=8, textColor=HexColor("#E65100"), alignment=1)
    style_td_status_failed = ParagraphStyle('TDS_F', fontName=FONT_BOLD, fontSize=8, textColor=HexColor("#B71C1C"), alignment=1)

    # 1. Header Table
    title_kn = "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) — ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ"
    title_en = "Shree Shanishwara Swamy Temple (R.) — Siddagiri Kshetra"
    address = "Kusugundi Village, Koduru Post, Hosanagara Taluk, Shimoga Dist, Karnataka • Phone: +91 9741943965"

    now_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
    filter_text = f"Filter: '{query}'" if query else "All Records"

    header_cell_left = Paragraph(
        f"<font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>{title_kn}</b></font><br/>"
        f"<font fontName='{FONT_BOLD}' size='10' color='#145A32'>{title_en}</font><br/>"
        f"<font fontName='{FONT_REGULAR}' size='7.5' color='#4A5568'>{address}</font>",
        ParagraphStyle('HeaderLeft', leading=13)
    )

    header_cell_right = Paragraph(
        f"<font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>DONATIONS REPORT</b></font><br/>"
        f"<font fontName='{FONT_BOLD}' size='9.5' color='#D4AF37'>ದೇಣಿಗೆ ವರದಿ</font><br/>"
        f"<font fontName='{FONT_REGULAR}' size='7.5' color='#4A5568'>Generated: {now_str}<br/>{filter_text}</font>",
        ParagraphStyle('HeaderRight', leading=12, alignment=2)
    )

    header_table = Table(
        [[header_cell_left, header_cell_right]],
        colWidths=[content_width * 0.65, content_width * 0.35]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))

    # 2. Metric Summary Cards
    total_count = len(donations)
    total_amount_paise = sum(d.amount for d in donations)
    total_amount_rs = total_amount_paise // 100

    completed_donations = [d for d in donations if d.status == "completed"]
    completed_count = len(completed_donations)
    completed_amount_rs = sum(d.amount for d in completed_donations) // 100
    pending_count = total_count - completed_count

    stat_cols = content_width / 4
    stat_data = [
        [
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Total Donations / ಒಟ್ಟು</font><br/><font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>{total_count}</b></font>", ParagraphStyle('S1', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Total Value / ಒಟ್ಟು ಮೊತ್ತ</font><br/><font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>₹{total_amount_rs:,}</b></font>", ParagraphStyle('S2', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Completed / ಯಶಸ್ವಿ</font><br/><font fontName='{FONT_BOLD}' size='12' color='#1B5E20'><b>{completed_count} (₹{completed_amount_rs:,})</b></font>", ParagraphStyle('S3', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Pending / ಬಾಕಿ</font><br/><font fontName='{FONT_BOLD}' size='12' color='#E65100'><b>{pending_count}</b></font>", ParagraphStyle('S4', alignment=1)),
        ]
    ]
    stat_table = Table(stat_data, colWidths=[stat_cols] * 4)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#EBF3EC")),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(stat_table)
    elements.append(Spacer(1, 10))

    # 3. Main Donations Table
    # Col widths sum to 778
    col_widths = [28, 120, 150, 75, 110, 65, 135, 95]

    headers = [
        Paragraph("#", style_th),
        Paragraph("Donor Name / ಹೆಸರು", style_th),
        Paragraph("Email / Mobile", style_th),
        Paragraph("Amount / ಮೊತ್ತ", style_th),
        Paragraph("Donation Type / ಸೇವೆ", style_th),
        Paragraph("Status / ಸ್ಥಿತಿ", style_th),
        Paragraph("Receipt Number / ರಸೀದಿ", style_th),
        Paragraph("Date & Time / ದಿನಾಂಕ", style_th),
    ]

    table_data = [headers]

    for idx, d in enumerate(donations, 1):
        amt_rs = d.amount // 100
        type_str = DONATION_TYPES.get(d.donation_type, d.donation_type.title())
        date_str = d.created_at.strftime("%d-%m-%Y %I:%M %p") if hasattr(d.created_at, 'strftime') else str(d.created_at)[:16]

        if d.status == "completed":
            status_p = Paragraph("COMPLETED", style_td_status_ok)
        elif d.status == "pending":
            status_p = Paragraph("PENDING", style_td_status_pending)
        else:
            status_p = Paragraph(d.status.upper(), style_td_status_failed)

        contact_p = Paragraph(
            f"<font size='7.5'>{d.donor_email or '—'}</font><br/><font size='7' color='#555'>{d.donor_mobile or '—'}</font>",
            ParagraphStyle('Contact', leading=9)
        )

        row = [
            Paragraph(str(idx), style_td_center),
            Paragraph(f"<b>{d.donor_name}</b>", style_td_bold),
            contact_p,
            Paragraph(f"₹{amt_rs:,}", style_td_amount),
            Paragraph(f"<font size='7.5'>{type_str}</font>", style_td),
            status_p,
            Paragraph(f"<font size='7.5' fontName='{FONT_BOLD}'>{d.receipt_number}</font>", style_td_center),
            Paragraph(f"<font size='7' color='#444'>{date_str}</font>", style_td_center),
        ]
        table_data.append(row)

    # Total Row
    total_row = [
        Paragraph("<b>GRAND TOTAL / ಒಟ್ಟು:</b>", ParagraphStyle('GT', fontName=FONT_BOLD, fontSize=8.5, textColor=PRIMARY_GREEN, alignment=2)),
        "", "",
        Paragraph(f"<b>₹{total_amount_rs:,}</b>", style_td_amount),
        Paragraph(f"<b>{completed_count} Successful</b>", ParagraphStyle('GTS', fontName=FONT_BOLD, fontSize=8, textColor=HexColor("#1B5E20"))),
        "", "", ""
    ]
    table_data.append(total_row)

    donations_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_GREEN),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, GOLD),
        ('INNERGRID', (0, 0), (-1, -2), 0.5, HexColor("#E2E8F0")),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Total row span and styling
        ('SPAN', (0, -1), (2, -1)),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor("#E2EFE4")),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, PRIMARY_GREEN),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
    ]

    for r in range(1, len(table_data) - 1):
        bg = WHITE if r % 2 != 0 else HexColor("#F7FAF7")
        t_style.append(('BACKGROUND', (0, r), (-1, r), bg))

    donations_table.setStyle(TableStyle(t_style))
    elements.append(donations_table)

    doc.build(elements, canvasmaker=NumberedReportCanvas)
    return buffer.getvalue()

