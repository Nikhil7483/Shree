"""
PDF Receipt generation using ReportLab.
Generates an official, beautifully formatted bilingual (English & Kannada)
donation receipt with temple branding, vector logo, native QR code,
HarfBuzz-shaped Kannada typography, and accurate data mapping.
"""

import os
from io import BytesIO
from datetime import datetime
from PIL import Image

import uharfbuzz as hb
import freetype
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from app.domain.donations.models import Donation

# ============================================================
# Font Detection & Registration
# ============================================================

font_dir = os.path.dirname(os.path.abspath(__file__))
noto_path = os.path.join(font_dir, "NotoSansKannada.ttf")
noto_reg_path = os.path.join(font_dir, "NotoSansKannada-Regular.ttf")
noto_bold_path = os.path.join(font_dir, "NotoSansKannada-Bold.ttf")
nirmala_path = "C:/Windows/Fonts/Nirmala.ttc"

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

KANNADA_FONT_REGULAR = None
KANNADA_FONT_BOLD = None
KANNADA_FONT_INDEX_REG = 0
KANNADA_FONT_INDEX_BOLD = 0

if os.path.exists(nirmala_path):
    # Windows native Nirmala UI provides comprehensive Indic + Latin + Rupee glyphs
    pdfmetrics.registerFont(TTFont("TempleFont", nirmala_path, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("TempleFont-Bold", nirmala_path, subfontIndex=1))
    FONT_REGULAR = "TempleFont"
    FONT_BOLD = "TempleFont-Bold"
    pdfmetrics.registerFont(TTFont("NotoSansKannada", nirmala_path, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("NotoSansKannada-Bold", nirmala_path, subfontIndex=1))
    KANNADA_FONT_REGULAR = nirmala_path
    KANNADA_FONT_BOLD = nirmala_path
    KANNADA_FONT_INDEX_REG = 0
    KANNADA_FONT_INDEX_BOLD = 1
elif os.path.exists(noto_path):
    # NotoSansKannada with Latin + Kannada + Rupee
    pdfmetrics.registerFont(TTFont("TempleFont", noto_path))
    pdfmetrics.registerFont(TTFont("TempleFont-Bold", noto_path))
    FONT_REGULAR = "TempleFont"
    FONT_BOLD = "TempleFont-Bold"
    pdfmetrics.registerFont(TTFont("NotoSansKannada", noto_path))
    pdfmetrics.registerFont(TTFont("NotoSansKannada-Bold", noto_path))
    KANNADA_FONT_REGULAR = noto_path
    KANNADA_FONT_BOLD = noto_path
elif os.path.exists(noto_reg_path):
    pdfmetrics.registerFont(TTFont("NotoSansKannada", noto_reg_path))
    KANNADA_FONT_REGULAR = noto_reg_path
    if os.path.exists(noto_bold_path):
        pdfmetrics.registerFont(TTFont("NotoSansKannada-Bold", noto_bold_path))
        KANNADA_FONT_BOLD = noto_bold_path
    else:
        KANNADA_FONT_BOLD = noto_reg_path

if KANNADA_FONT_REGULAR is None and os.path.exists(noto_path):
    KANNADA_FONT_REGULAR = noto_path
    KANNADA_FONT_BOLD = noto_path

# Pre-load HarfBuzz & FreeType font data for zero-latency rendering
_HB_FACE_REG = None
_HB_FONT_REG = None
_FT_FACE_REG = None
_HB_FACE_BOLD = None
_HB_FONT_BOLD = None
_FT_FACE_BOLD = None

if KANNADA_FONT_REGULAR and os.path.exists(KANNADA_FONT_REGULAR):
    try:
        with open(KANNADA_FONT_REGULAR, "rb") as _f:
            _reg_data = _f.read()
        _HB_FACE_REG = hb.Face(_reg_data, index=KANNADA_FONT_INDEX_REG)
        _HB_FONT_REG = hb.Font(_HB_FACE_REG)
        _FT_FACE_REG = freetype.Face(KANNADA_FONT_REGULAR, index=KANNADA_FONT_INDEX_REG)
    except Exception as e:
        print(f"Warning: Failed to load regular Kannada font for shaping: {e}")

if KANNADA_FONT_BOLD and os.path.exists(KANNADA_FONT_BOLD):
    try:
        with open(KANNADA_FONT_BOLD, "rb") as _f:
            _bold_data = _f.read()
        _HB_FACE_BOLD = hb.Face(_bold_data, index=KANNADA_FONT_INDEX_BOLD)
        _HB_FONT_BOLD = hb.Font(_HB_FACE_BOLD)
        _FT_FACE_BOLD = freetype.Face(KANNADA_FONT_BOLD, index=KANNADA_FONT_INDEX_BOLD)
    except Exception as e:
        _HB_FACE_BOLD = _HB_FACE_REG
        _HB_FONT_BOLD = _HB_FONT_REG
        _FT_FACE_BOLD = _FT_FACE_REG
else:
    _HB_FACE_BOLD = _HB_FACE_REG
    _HB_FONT_BOLD = _HB_FONT_REG
    _FT_FACE_BOLD = _FT_FACE_REG

# In-memory image cache for shaped phrases (avoids re-rendering identical texts)
_SHAPED_IMAGE_CACHE = {}


def has_kannada(text: str) -> bool:
    """Check if the string contains any Kannada Unicode characters."""
    return any(0x0C80 <= ord(ch) <= 0x0CFF for ch in text)


def render_shaped_text(text: str, font_size: float, color_rgb: tuple, bold: bool = False, scale: float = 3.0):
    """
    Render complex Kannada / bilingual text using HarfBuzz text shaping and FreeType rasterization.
    Returns (ImageReader, width_pt, height_pt, descent_pt).
    """
    cache_key = (text, font_size, color_rgb, bold, scale)
    if cache_key in _SHAPED_IMAGE_CACHE:
        return _SHAPED_IMAGE_CACHE[cache_key]

    hb_font = _HB_FONT_BOLD if bold else _HB_FONT_REG
    ft_face = _FT_FACE_BOLD if bold else _FT_FACE_REG

    if not hb_font or not ft_face:
        return None, 0, 0, 0

    hb_font.scale = (int(font_size * scale * 64), int(font_size * scale * 64))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)

    ft_size = int(font_size * scale * 64)
    ft_face.set_char_size(ft_size, ft_size, 72, 72)

    positions = buf.glyph_positions
    infos = buf.glyph_infos

    total_w_px = sum(pos.x_advance for pos in positions) >> 6
    ascent_px = ft_face.size.ascender >> 6
    descent_px = ft_face.size.descender >> 6  # negative in FreeType
    total_h_px = ascent_px - descent_px + int(4 * scale)

    width_px = max(total_w_px + int(6 * scale), 4)
    height_px = max(total_h_px, 4)

    img = Image.new("RGBA", (width_px, height_px), (255, 255, 255, 0))
    x_px = int(2 * scale)
    y_px = ascent_px + int(2 * scale)

    for info, pos in zip(infos, positions):
        ft_face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        slot = ft_face.glyph
        bmp = slot.bitmap
        bx = x_px + (pos.x_offset >> 6) + slot.bitmap_left
        by = y_px - (pos.y_offset >> 6) - slot.bitmap_top
        if bmp.width > 0 and bmp.rows > 0:
            glyph_data = bytes(bmp.buffer)
            g = Image.frombytes("L", (bmp.width, bmp.rows), glyph_data)
            tint = Image.new("RGBA", (bmp.width, bmp.rows), color_rgb + (255,))
            img.paste(tint, (bx, by), g)
        x_px += (pos.x_advance >> 6)
        y_px -= (pos.y_advance >> 6)

    width_pt = total_w_px / scale
    height_pt = total_h_px / scale
    descent_pt = (-descent_px + int(2 * scale)) / scale

    img_reader = ImageReader(img)
    res = (img_reader, width_pt, height_pt, descent_pt)
    _SHAPED_IMAGE_CACHE[cache_key] = res
    return res


def draw_styled_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    font_size: float,
    color: HexColor,
    bold: bool = False,
    align: str = "left",
):
    """
    Draw text with automatic HarfBuzz shaping for Kannada text,
    and fast native drawing for purely Latin/English text.
    Correctly aligns the baseline so English and Kannada text sit on the same line.
    """
    if not text:
        return 0

    if has_kannada(text) and _HB_FONT_REG:
        r = int(color.red * 255)
        g = int(color.green * 255)
        b = int(color.blue * 255)

        img_reader, width_pt, height_pt, descent_pt = render_shaped_text(
            text, font_size, (r, g, b), bold=bold
        )

        draw_x = x
        if align == "center":
            draw_x = x - (width_pt / 2.0)
        elif align == "right":
            draw_x = x - width_pt

        draw_y = y - descent_pt
        c.drawImage(
            img_reader,
            draw_x,
            draw_y,
            width=width_pt,
            height=height_pt,
            mask="auto",
        )

        try:
            c.saveState()
            t = c.beginText(draw_x, y)
            t.setTextRenderMode(3)  # Invisible
            t.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
            t.textOut(text)
            c.drawText(t)
            c.restoreState()
        except Exception:
            pass

        return width_pt
    else:
        # Standard Latin / ASCII / Numbers / Rupee
        c.setFont(FONT_BOLD if bold else FONT_REGULAR, font_size)
        c.setFillColor(color)
        if align == "center":
            c.drawCentredString(x, y, text)
        elif align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)
        return c.stringWidth(text, FONT_BOLD if bold else FONT_REGULAR, font_size)


# Design Colors
PRIMARY_GREEN = HexColor("#0B3D2E")
SECONDARY_GREEN = HexColor("#145A32")
GOLD = HexColor("#D4AF37")
LIGHT_GOLD = HexColor("#F5EACB")
CREAM = HexColor("#FCFBF7")
WHITE = HexColor("#FFFFFF")
TEXT_DARK = HexColor("#0F172A")
TEXT_MUTED = HexColor("#475569")
TEXT_LIGHT = HexColor("#64748B")
BORDER_LIGHT = HexColor("#E2E8F0")
BORDER_GREEN = HexColor("#BDD4B3")
AMOUNT_BOX_BG = HexColor("#EDF6EE")
SUCCESS_GREEN = HexColor("#166534")

# Donation categories with clean bilingual names and descriptions (no leading/inline slashes)
DONATION_TYPES_INFO = {
    "general": {
        "name_en": "General Donation",
        "name_kn": "ಸಾಮಾನ್ಯ ದೇಣಿಗೆ",
        "desc_en": "Temple Daily Poojas, Maintenance & Devotee Welfare",
        "desc_kn": "ದೇವಸ್ಥಾನದ ನಿತ್ಯ ಪೂಜೆ, ನಿರ್ವಹಣೆ ಹಾಗೂ ಭಕ್ತರ ಕಲ್ಯಾಣ ಕಾರ್ಯಗಳಿಗಾಗಿ",
    },
    "annadanam": {
        "name_en": "Annadanam Seva",
        "name_kn": "ನಿತ್ಯ ಅನ್ನದಾನ ಸೇವೆ",
        "desc_en": "Sacred Food Prasada Offering to Visiting Devotees",
        "desc_kn": "ಕ್ಷೇತ್ರಕ್ಕೆ ಆಗಮಿಸುವ ಭಕ್ತಾದಿಗಳಿಗೆ ನಿತ್ಯ ಮಹಾಪ್ರಸಾದ ಅನ್ನದಾಸೋಹ ಸೇವೆ",
    },
    "temple_development": {
        "name_en": "Temple Development Fund",
        "name_kn": "ದೇವಸ್ಥಾನ ಅಭಿವೃದ್ಧಿ ನಿಧಿ",
        "desc_en": "Sanctum Renovation, Gopuram & Infrastructure Expansion",
        "desc_kn": "ಗರ್ಭಗುಡಿ ಜೀರ್ಣೋದ್ಧಾರ, ರಾಜಗೋಪುರ ಹಾಗೂ ಕ್ಷೇತ್ರಾಭಿವೃದ್ಧಿ ಯೋಜನೆಗಳು",
    },
    "festival": {
        "name_en": "Special Festival Seva",
        "name_kn": "ವಿಶೇಷ ಹಬ್ಬ ಹಾಗೂ ಜಾತ್ರಾ ಸೇವೆ",
        "desc_en": "Shani Amavasya, Navaratri & Special Utsava Celebrations",
        "desc_kn": "ಶನಿ ಅಮಾವಾಸ್ಯೆ, ದಸರಾ ನವರಾತ್ರಿ ಹಾಗೂ ವಾರ್ಷಿಕ ಜಾತ್ರಾ ಮಹೋತ್ಸವ ಸೇವೆ",
    },
    "goshala": {
        "name_en": "Goshala Seva",
        "name_kn": "ಗೋಸಂರಕ್ಷಣಾ ಸೇವೆ",
        "desc_en": "Care, Fodder & Sacred Protection of Temple Cows",
        "desc_kn": "ದೇವಸ್ಥಾನದ ದೇಸಿ ಗೋವುಗಳ ಪಾಲನೆ, ಪೋಷಣೆ ಮತ್ತು ಮೇವು ಸಂರಕ್ಷಣೆ",
    },
}

# Legacy mapping compatibility
DONATION_TYPES = {
    k: f"{v['name_en']} / {v['name_kn']}" for k, v in DONATION_TYPES_INFO.items()
}


def draw_temple_logo(c: canvas.Canvas, x: float, y: float):
    """Draw South Indian Gopuram & Deepa Logo using precise vector shapes."""
    c.setFillColor(PRIMARY_GREEN)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.circle(x, y, 28, fill=True, stroke=True)

    c.setFillColor(GOLD)
    c.setStrokeColor(PRIMARY_GREEN)
    c.setLineWidth(0.5)

    # Top spire (Kalasa)
    p = c.beginPath()
    p.moveTo(x - 2.5, y + 17)
    p.lineTo(x, y + 24)
    p.lineTo(x + 2.5, y + 17)
    p.close()
    c.drawPath(p, fill=True, stroke=False)

    # Gopuram tiers
    c.rect(x - 5, y + 12, 10, 4.5, fill=True, stroke=True)
    c.rect(x - 8, y + 5, 16, 6, fill=True, stroke=True)
    c.rect(x - 11, y - 4, 22, 8, fill=True, stroke=True)

    # Pillar arch gateway
    c.rect(x - 13, y - 16, 26, 11, fill=True, stroke=True)
    c.setFillColor(PRIMARY_GREEN)
    c.rect(x - 8.5, y - 16, 17, 8.5, fill=True, stroke=True)

    # Oil lamp (Deepa) inside
    c.setFillColor(HexColor("#FF8C00"))
    p2 = c.beginPath()
    p2.moveTo(x, y - 14)
    p2.curveTo(x - 2.5, y - 11, x - 2.5, y - 8, x, y - 6)
    p2.curveTo(x + 2.5, y - 8, x + 2.5, y - 11, x, y - 14)
    p2.close()
    c.drawPath(p2, fill=True, stroke=False)

    # Inner flame glow
    c.setFillColor(HexColor("#FFD700"))
    p3 = c.beginPath()
    p3.moveTo(x, y - 12)
    p3.curveTo(x - 1.2, y - 10, x - 1.2, y - 8, x, y - 7)
    p3.curveTo(x + 1.2, y - 8, x + 1.2, y - 10, x, y - 12)
    p3.close()
    c.drawPath(p3, fill=True, stroke=False)

    # Base Pedestal
    c.setFillColor(GOLD)
    c.rect(x - 15, y - 19, 30, 2.5, fill=True, stroke=False)


def draw_vector_star(c: canvas.Canvas, cx: float, cy: float, r_outer: float = 4.5, r_inner: float = 2.0):
    """Draw a clean 5-pointed star using vector paths (no missing font glyphs)."""
    import math
    p = c.beginPath()
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    c.drawPath(p, fill=True, stroke=False)


def amount_to_words(n: int) -> str:
    """Convert an amount in rupees to clean English words."""
    units = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen",
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
    ]
    if n == 0:
        return "Zero Rupees Only"

    def helper(num):
        if num < 20:
            return units[num]
        elif num < 100:
            return tens[num // 10] + (" " + units[num % 10] if num % 10 else "")
        elif num < 1000:
            return units[num // 100] + " Hundred" + (" " + helper(num % 100) if num % 100 else "")
        elif num < 100000:
            return helper(num // 1000) + " Thousand" + (" " + helper(num % 1000) if num % 1000 else "")
        elif num < 10000000:
            return helper(num // 100000) + " Lakh" + (" " + helper(num % 100000) if num % 100000 else "")
        else:
            return helper(num // 10000000) + " Crore" + (" " + helper(num % 10000000) if num % 10000000 else "")

    return helper(n) + " Rupees Only"


def generate_receipt_pdf(donation: Donation) -> bytes:
    """
    Generate an official, professional single-page A4 donation receipt.
    Clean typography, balanced margins, zero stray slashes, embedded Unicode fonts,
    HarfBuzz shaped Kannada text, offline vector QR code, verified trust seal, and accurate data mapping.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 1. Background & Double Border
    c.setFillColor(CREAM)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # Outer Forest Green Border
    c.setStrokeColor(PRIMARY_GREEN)
    c.setLineWidth(2.0)
    c.rect(22, 22, width - 44, height - 44, fill=False, stroke=True)

    # Inner Gold Border
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.rect(26, 26, width - 52, height - 52, fill=False, stroke=True)

    # Subtle Corner Ornaments
    for cx, cy in [(32, height - 32), (width - 32, height - 32), (32, 32), (width - 32, 32)]:
        c.setFillColor(GOLD)
        c.rect(cx - 2, cy - 2, 4, 4, fill=True, stroke=False)

    # 2. Header Panel Card
    header_top = height - 36
    header_height = 88
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(34, header_top - header_height, width - 68, header_height, 6, fill=True, stroke=True)

    # Vector Logo (centered vertically in header card)
    draw_temple_logo(c, 74, header_top - 44)

    # Temple Titles & Details
    text_x = 118
    # Kannada Main Heading with HarfBuzz shaping
    draw_styled_text(
        c,
        "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) • ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ",
        text_x,
        header_top - 20,
        font_size=12.5,
        color=PRIMARY_GREEN,
        bold=True,
    )

    # English Title
    draw_styled_text(
        c,
        "SHREE SHANISHWARA SWAMY TEMPLE (R.) — SIDDAGIRI KSHETRA",
        text_x,
        header_top - 36,
        font_size=9.5,
        color=SECONDARY_GREEN,
        bold=True,
    )

    # Address & Trust Details
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(text_x, header_top - 50, "Kusugundi Village, Koduru Post, Hosanagara Taluk, Shimoga District, Karnataka – 577418")
    c.drawString(text_x, header_top - 63, "Registered Public Religious & Charitable Trust • Reg. No: DRSH/SOR/637/2023-24")
    c.drawString(text_x, header_top - 75, "Phone: +91 9741943965  |  Email: info@shreeshani.com  |  Website: www.shreeshanitemple.com")

    # 3. Receipt Title & Status Banner
    banner_y = header_top - header_height - 28
    banner_height = 26
    c.setFillColor(PRIMARY_GREEN)
    c.roundRect(34, banner_y, width - 68, banner_height, 4, fill=True, stroke=False)

    # Gold accent line on banner bottom
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(34, banner_y, width - 34, banner_y)

    # Banner Title (Shaped Kannada + English)
    draw_styled_text(
        c,
        "DONATION RECEIPT   •   ಅಧಿಕೃತ ದೇಣಿಗೆ ರಸೀದಿ",
        48,
        banner_y + 8,
        font_size=10.5,
        color=WHITE,
        bold=True,
    )

    # Banner Subtitle
    draw_styled_text(
        c,
        "ORIGINAL DEVOTEE COPY",
        width - 48,
        banner_y + 9,
        font_size=8,
        color=LIGHT_GOLD,
        bold=True,
        align="right",
    )

    # 4. Section 1: Transaction & Receipt Metadata Grid
    meta_y = banner_y - 62
    meta_height = 56
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(34, meta_y, width - 68, meta_height, 6, fill=True, stroke=True)

    # 4 Columns Grid
    # Col 1: Receipt Number
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(46, meta_y + 41, "RECEIPT NUMBER")
    draw_styled_text(c, "ರಸೀದಿ ಸಂಖ್ಯೆ", 46, meta_y + 31, 6.5, TEXT_LIGHT)
    c.setFont(FONT_BOLD, 9.5)
    c.setFillColor(PRIMARY_GREEN)
    c.drawString(46, meta_y + 14, donation.receipt_number or "N/A")

    # Vertical divider 1
    c.setStrokeColor(BORDER_LIGHT)
    c.line(174, meta_y + 8, 174, meta_y + 48)

    # Col 2: Date & Time
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(184, meta_y + 41, "DATE & TIME")
    draw_styled_text(c, "ದಿನಾಂಕ ಮತ್ತು ಸಮಯ", 184, meta_y + 31, 6.5, TEXT_LIGHT)
    c.setFont(FONT_BOLD, 8.5)
    c.setFillColor(TEXT_DARK)
    date_str = donation.created_at.strftime("%d-%m-%Y")
    time_str = donation.created_at.strftime("%I:%M %p")
    c.drawString(184, meta_y + 14, f"{date_str}, {time_str}")

    # Vertical divider 2
    c.line(310, meta_y + 8, 310, meta_y + 48)

    # Col 3: Payment ID
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(320, meta_y + 41, "PAYMENT ID / TRANSACTION REF")
    draw_styled_text(c, "ಪಾವತಿ ಐಡಿ", 320, meta_y + 31, 6.5, TEXT_LIGHT)
    c.setFont(FONT_BOLD, 8)
    c.setFillColor(TEXT_DARK)
    c.drawString(320, meta_y + 14, donation.razorpay_payment_id or "Online Payment")

    # Vertical divider 3
    c.line(442, meta_y + 8, 442, meta_y + 48)

    # Col 4: Order ID / Channel
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(452, meta_y + 41, "ORDER ID / MODE")
    draw_styled_text(c, "ಆರ್ಡರ್ ಐಡಿ / ವಿಧಾನ", 452, meta_y + 31, 6.5, TEXT_LIGHT)
    c.setFont(FONT_BOLD, 8)
    c.setFillColor(TEXT_DARK)
    order_val = donation.razorpay_order_id or "Direct Online"
    c.drawString(452, meta_y + 14, order_val[:14] if len(order_val) > 14 else order_val)

    # 5. Section 2: Donor Details Card (Spacious 4-row layout)
    donor_title_y = meta_y - 15
    donor_card_top = meta_y - 28
    donor_height = 92
    donor_y = donor_card_top - donor_height

    # Section Title drawn comfortably ABOVE card
    draw_styled_text(
        c,
        "DONOR INFORMATION   •   ದಾನಿಯ ವಿವರಗಳು",
        36,
        donor_title_y,
        font_size=8.5,
        color=PRIMARY_GREEN,
        bold=True,
    )

    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(34, donor_y, width - 68, donor_height, 6, fill=True, stroke=True)

    # Row 1: Donor Name across full width (no collision with other fields!)
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, donor_y + 70, "Donor Name:")
    draw_styled_text(c, "(ದಾನಿಯ ಹೆಸರು)", 98, donor_y + 70, 7, TEXT_LIGHT)

    if donation.is_anonymous:
        draw_styled_text(c, "Anonymous Devotee (ಅನಾಮಧೇಯ ಭಕ್ತರು)", 175, donor_y + 69, 9.5, TEXT_DARK, bold=True)
    else:
        donor_name = (donation.donor_name or "Devotee").strip()
        draw_styled_text(c, donor_name, 175, donor_y + 69, 9.5, TEXT_DARK, bold=True)

    # Row 2: Mobile Number & Email Address side by side
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, donor_y + 48, "Mobile:")
    draw_styled_text(c, "(ಮೊಬೈಲ್)", 84, donor_y + 48, 7, TEXT_LIGHT)
    c.setFont(FONT_BOLD, 9)
    c.setFillColor(TEXT_DARK)
    c.drawString(175, donor_y + 48, donation.donor_mobile or "Not provided")

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(320, donor_y + 48, "Email:")
    draw_styled_text(c, "(ಇಮೇಲ್)", 352, donor_y + 48, 7, TEXT_LIGHT)
    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColor(TEXT_DARK)
    c.drawString(405, donor_y + 48, donation.donor_email or "Not provided")

    # Row 3: Category & Payment Mode
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, donor_y + 27, "Category:")
    draw_styled_text(c, "(ವರ್ಗ)", 94, donor_y + 27, 7, TEXT_LIGHT)
    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColor(TEXT_DARK)
    c.drawString(175, donor_y + 27, "Devotee")
    draw_styled_text(c, "(ಭಕ್ತರು)", 218, donor_y + 27, 7.5, TEXT_DARK)

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(320, donor_y + 27, "Channel:")
    draw_styled_text(c, "(ವಿಧಾನ)", 360, donor_y + 27, 7, TEXT_LIGHT)
    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(TEXT_DARK)
    c.drawString(405, donor_y + 27, "Online")
    draw_styled_text(c, "(ಆನ್‌ಲೈನ್ ಪಾವತಿ)", 438, donor_y + 27, 7.5, TEXT_DARK)

    # Row 4: Address
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, donor_y + 9, "Address:")
    draw_styled_text(c, "(ವಿಳಾಸ)", 86, donor_y + 9, 7, TEXT_LIGHT)

    addr_style = ParagraphStyle(
        "AddrStyle",
        fontName=FONT_REGULAR,
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_DARK,
    )
    raw_addr = (donation.donor_address or "").strip()
    if not raw_addr:
        addr_text = "Not provided"
        c.setFont(FONT_REGULAR, 8)
        c.setFillColor(TEXT_MUTED)
        c.drawString(175, donor_y + 9, addr_text)
        draw_styled_text(c, "(ವಿಳಾಸ ಲಭ್ಯವಿಲ್ಲ)", 232, donor_y + 9, 7.5, TEXT_MUTED)
    else:
        addr_p = Paragraph(raw_addr, addr_style)
        pw, ph = addr_p.wrap(width - 68 - 190, 22)
        addr_p.drawOn(c, 175, donor_y + 9 - (ph - 7))

    # 6. Section 3: Seva & Contribution Details
    seva_title_y = donor_y - 15
    seva_card_top = donor_y - 28
    seva_height = 114
    seva_y = seva_card_top - seva_height

    # Section Title drawn ABOVE card
    draw_styled_text(
        c,
        "SEVA & CONTRIBUTION DETAILS   •   ದೇಣಿಗೆ ಹಾಗೂ ಸೇವಾ ವಿವರಗಳು",
        36,
        seva_title_y,
        font_size=8.5,
        color=PRIMARY_GREEN,
        bold=True,
    )

    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(34, seva_y, width - 68, seva_height, 6, fill=True, stroke=True)

    # Seva Info Lookup
    type_info = DONATION_TYPES_INFO.get(
        donation.donation_type,
        {
            "name_en": donation.donation_type.replace("_", " ").title(),
            "name_kn": "ದೇವಸ್ಥಾನ ಸೇವಾ ದೇಣಿಗೆ",
            "desc_en": "General Devotional Contribution for Temple Welfare",
            "desc_kn": "ದೇವಸ್ಥಾನದ ಧಾರ್ಮಿಕ ಮತ್ತು ನಿತ್ಯ ಸೇವಾ ಕಾರ್ಯಗಳಿಗಾಗಿ",
        },
    )

    # Row 1: Seva Name & Description
    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, seva_y + 92, "Devotion Seva:")
    draw_styled_text(c, "(ಸೇವೆ)", 110, seva_y + 92, 7, TEXT_LIGHT)

    # Bilingual Seva Name
    c.setFont(FONT_BOLD, 9.5)
    c.setFillColor(PRIMARY_GREEN)
    c.drawString(175, seva_y + 92, type_info["name_en"])
    en_len = c.stringWidth(type_info["name_en"], FONT_BOLD, 9.5)
    draw_styled_text(c, f"({type_info['name_kn']})", 175 + en_len + 8, seva_y + 92, 9, PRIMARY_GREEN, bold=True)

    # Description
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(175, seva_y + 79, type_info["desc_en"] + "  •  ")
    desc_en_len = c.stringWidth(type_info["desc_en"] + "  •  ", FONT_REGULAR, 7)
    draw_styled_text(c, type_info["desc_kn"], 175 + desc_en_len, seva_y + 79, 7, TEXT_MUTED)

    # Row 2: Prominent Amount Banner
    amt_box_y = seva_y + 10
    amt_box_height = 56
    c.setFillColor(AMOUNT_BOX_BG)
    c.setStrokeColor(BORDER_GREEN)
    c.setLineWidth(1)
    c.roundRect(44, amt_box_y, width - 88, amt_box_height, 4, fill=True, stroke=True)

    amount_rs = donation.amount // 100
    words_str = amount_to_words(amount_rs)

    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(58, amt_box_y + 38, "TOTAL AMOUNT PAID")
    draw_styled_text(c, "(ಪಾವತಿಸಿದ ಒಟ್ಟು ಮೊತ್ತ)", 148, amt_box_y + 38, 6.5, TEXT_LIGHT)

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(PRIMARY_GREEN)
    c.drawString(58, amt_box_y + 18, words_str)

    # Amount Value in Large Bold Numbers with clean Rupee symbol
    amt_display = f"₹{amount_rs:,}.00"
    draw_styled_text(c, amt_display, width - 58, amt_box_y + 26, 17, PRIMARY_GREEN, bold=True, align="right")

    # Payment Status Badge
    c.setFont(FONT_BOLD, 7)
    c.setFillColor(SUCCESS_GREEN)
    c.drawRightString(width - 150, amt_box_y + 12, "● PAYMENT VERIFIED & COMPLETED")
    draw_styled_text(c, "(ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ)", width - 58, amt_box_y + 12, 7, SUCCESS_GREEN, bold=True, align="right")

    # 7. Section 4: Authentication, Blessing & Signature
    auth_y = seva_y - 124
    auth_height = 114

    # 7A. Official Digital Temple Trust Seal (Left)
    seal_x = 94
    seal_y = auth_y + 54
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.6)
    c.circle(seal_x, seal_y, 34, fill=False, stroke=True)
    c.setLineWidth(0.7)
    c.circle(seal_x, seal_y, 31, fill=False, stroke=True)

    c.setFont(FONT_BOLD, 5.5)
    c.setFillColor(SECONDARY_GREEN)
    c.drawCentredString(seal_x, seal_y + 19, "SHREE SHANISHWARA SWAMY")
    c.drawCentredString(seal_x, seal_y + 12, "TEMPLE TRUST (R.)")

    # Center emblem in seal
    c.setFillColor(HexColor("#FF8C00"))
    draw_vector_star(c, seal_x - 14, seal_y - 2, 2.5, 1)
    draw_vector_star(c, seal_x + 14, seal_y - 2, 2.5, 1)
    c.setFillColor(PRIMARY_GREEN)
    c.setFont(FONT_BOLD, 7)
    c.drawCentredString(seal_x, seal_y - 2, "OFFICIAL")
    c.drawCentredString(seal_x, seal_y - 10, "SEAL")

    c.setFont(FONT_REGULAR, 5.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(seal_x, seal_y - 20, "SIDDAGIRI KSHETRA")

    # 7B. Divine Blessings Card (Center)
    bless_x = 144
    bless_w = 268
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.roundRect(bless_x, auth_y + 4, bless_w, auth_height - 4, 6, fill=True, stroke=True)

    # Blessings Title
    draw_styled_text(
        c,
        "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿಯ ಕೃಪಾಶೀರ್ವಾದಗಳು   •   DIVINE BLESSINGS",
        bless_x + bless_w / 2,
        auth_y + auth_height - 18,
        font_size=7.5,
        color=PRIMARY_GREEN,
        bold=True,
        align="center",
    )

    # Kannada Sacred Blessing (Clean 3-line centered layout completely within card)
    center_bless = bless_x + bless_w / 2
    draw_styled_text(c, "“ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿಯು ನಿಮಗೆ ಹಾಗೂ ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ", center_bless, auth_y + auth_height - 35, 7.5, SECONDARY_GREEN, align="center")
    draw_styled_text(c, "ಸಕಲ ಕಷ್ಟಗಳನ್ನು ನಿವಾರಿಸಿ, ಆಯುರಾರೋಗ್ಯ, ಶಾಂತಿ,", center_bless, auth_y + auth_height - 47, 7.5, SECONDARY_GREEN, align="center")
    draw_styled_text(c, "ನೆಮ್ಮದಿ ಹಾಗೂ ಸಕಲ ಸನ್ಮಂಗಳಗಳನ್ನು ಕರುಣಿಸಲಿ.”", center_bless, auth_y + auth_height - 59, 7.5, SECONDARY_GREEN, align="center")

    # English Blessing (Clean 2-line layout)
    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(
        center_bless,
        auth_y + auth_height - 75,
        "“May Lord Shanishwara Swamy dispel all obstacles and bestow",
    )
    c.drawCentredString(
        center_bless,
        auth_y + auth_height - 85,
        "divine grace, peace, good health and prosperity upon your family.”",
    )

    # 7C. Offline Native Vector QR Code (Right)
    qr_x = 450
    qr_y = auth_y + 36
    qr_size = 58

    qr_target = f"https://www.shreeshanitemple.com/verify?receipt={donation.receipt_number}"
    qr_widget = qr.QrCodeWidget(qr_target)
    bounds = qr_widget.getBounds()
    qw = bounds[2] - bounds[0]
    qh = bounds[3] - bounds[1]
    d = Drawing(qr_size, qr_size, transform=[qr_size / qw, 0, 0, qr_size / qh, 0, 0])
    d.add(qr_widget)
    renderPDF.draw(d, c, qr_x, qr_y)

    c.setFont(FONT_BOLD, 6.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size + 4, "Scan to Verify Receipt")
    draw_styled_text(c, "ಪರಿಶೀಲಿಸಲು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ", qr_x + qr_size / 2, qr_y - 8, 6, TEXT_MUTED, align="center")

    # Authorized Signatory Line
    c.setStrokeColor(BORDER_LIGHT)
    c.setLineWidth(0.8)
    c.line(428, auth_y + 8, width - 44, auth_y + 8)

    # Signatory Label (clean single bilingual line)
    sig_center_x = (428 + width - 44) / 2
    draw_styled_text(
        c,
        "Authorized Signatory (ಅಧಿಕೃತ ಸಹಿದಾರರು)",
        sig_center_x,
        auth_y - 3,
        font_size=6.5,
        color=PRIMARY_GREEN,
        bold=True,
        align="center",
    )

    # 8. Computer-Generated Disclaimer Footer
    footer_y = 50
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(34, footer_y + 24, width - 34, footer_y + 24)

    # Kannada Disclaimer (Concise, perfectly centered within margins)
    draw_styled_text(
        c,
        "ಗಮನಿಸಿ: ಇದು ಗಣಕಯಂತ್ರದಿಂದ ರಚಿಸಲಾದ ಅಧಿಕೃತ ರಸೀದಿಯಾಗಿದ್ದು ಸಹಿಯ ಅಗತ್ಯವಿರುವುದಿಲ್ಲ.",
        width / 2,
        footer_y + 14,
        font_size=7,
        color=TEXT_MUTED,
        align="center",
    )

    # English Disclaimer
    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(
        width / 2,
        footer_y + 4,
        "Note: This is a computer-generated official receipt and requires no physical signature. Dedicated to temple welfare.",
    )

    # Canonical Temple Title
    draw_styled_text(
        c,
        "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ — Shree Shanishwara Swamy Temple (R.), Kusugundi, Shimoga",
        width / 2,
        footer_y - 7,
        font_size=7.5,
        color=PRIMARY_GREEN,
        bold=True,
        align="center",
    )

    c.save()
    return buffer.getvalue()


# ============================================================
# Multi-Page Landscape Donations Summary Report
# ============================================================

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
            draw_styled_text(
                self,
                "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) — DONATIONS REPORT (Continued)",
                32,
                h - 35,
                font_size=8,
                color=PRIMARY_GREEN,
                bold=True,
            )
            self.setFont(FONT_BOLD, 8)
            self.setFillColor(PRIMARY_GREEN)
            self.drawRightString(w - 32, h - 35, "Shree Shanishwara Swamy Temple (R.)")
            self.setStrokeColor(BORDER_GREEN)
            self.setLineWidth(0.5)
            self.line(32, h - 38, w - 32, h - 38)

        # Footer divider line
        self.setStrokeColor(BORDER_GREEN)
        self.setLineWidth(0.75)
        self.line(30, 36, w - 30, 36)

        # Footer text
        draw_styled_text(
            self,
            "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ — Shree Shanishwara Swamy Temple (R.)",
            32,
            26,
            font_size=7.5,
            color=HexColor("#4A5568"),
        )
        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(HexColor("#4A5568"))
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
        bottomMargin=45,
    )

    w, h = landscape(A4)
    content_width = w - 64
    elements = []

    # Typography styles
    style_th = ParagraphStyle('TH', fontName=FONT_BOLD, fontSize=8.5, textColor=WHITE, alignment=1)
    style_td = ParagraphStyle('TD', fontName=FONT_REGULAR, fontSize=8, textColor=TEXT_DARK)
    style_td_center = ParagraphStyle('TDC', fontName=FONT_REGULAR, fontSize=8, textColor=TEXT_DARK, alignment=1)
    style_td_bold = ParagraphStyle('TDB', fontName=FONT_BOLD, fontSize=8, textColor=TEXT_DARK)
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
        ParagraphStyle('HeaderLeft', leading=13),
    )

    header_cell_right = Paragraph(
        f"<font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>DONATIONS REPORT</b></font><br/>"
        f"<font fontName='{FONT_BOLD}' size='9.5' color='#D4AF37'>ದೇಣಿಗೆ ವರದಿ</font><br/>"
        f"<font fontName='{FONT_REGULAR}' size='7.5' color='#4A5568'>Generated: {now_str}<br/>{filter_text}</font>",
        ParagraphStyle('HeaderRight', leading=12, alignment=2),
    )

    header_table = Table(
        [[header_cell_left, header_cell_right]],
        colWidths=[content_width * 0.65, content_width * 0.35],
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
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Total Donations (ಒಟ್ಟು)</font><br/><font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>{total_count}</b></font>", ParagraphStyle('S1', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Total Value (ಒಟ್ಟು ಮೊತ್ತ)</font><br/><font fontName='{FONT_BOLD}' size='12' color='#0B3D2E'><b>₹{total_amount_rs:,}</b></font>", ParagraphStyle('S2', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Completed (ಯಶಸ್ವಿ)</font><br/><font fontName='{FONT_BOLD}' size='12' color='#1B5E20'><b>{completed_count} (₹{completed_amount_rs:,})</b></font>", ParagraphStyle('S3', alignment=1)),
            Paragraph(f"<font fontName='{FONT_REGULAR}' size='7.5' color='#555'>Pending (ಬಾಕಿ)</font><br/><font fontName='{FONT_BOLD}' size='12' color='#E65100'><b>{pending_count}</b></font>", ParagraphStyle('S4', alignment=1)),
        ]
    ]
    stat_table = Table(stat_data, colWidths=[stat_cols] * 4)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor("#EBF3EC")),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_GREEN),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(stat_table)
    elements.append(Spacer(1, 10))

    # 3. Main Donations Table
    col_widths = [28, 120, 150, 75, 110, 65, 135, 95]

    headers = [
        Paragraph("#", style_th),
        Paragraph("Donor Name (ಹೆಸರು)", style_th),
        Paragraph("Email / Mobile", style_th),
        Paragraph("Amount (ಮೊತ್ತ)", style_th),
        Paragraph("Donation Type (ಸೇವೆ)", style_th),
        Paragraph("Status (ಸ್ಥಿತಿ)", style_th),
        Paragraph("Receipt Number (ರಸೀದಿ)", style_th),
        Paragraph("Date & Time (ದಿನಾಂಕ)", style_th),
    ]

    table_data = [headers]

    for idx, d in enumerate(donations, 1):
        amt_rs = d.amount // 100
        t_info = DONATION_TYPES_INFO.get(d.donation_type, {"name_en": d.donation_type.title(), "name_kn": ""})
        type_str = f"{t_info['name_en']} ({t_info['name_kn']})" if t_info.get("name_kn") else t_info['name_en']
        date_str = d.created_at.strftime("%d-%m-%Y %I:%M %p") if hasattr(d.created_at, 'strftime') else str(d.created_at)[:16]

        if d.status == "completed":
            status_p = Paragraph("COMPLETED", style_td_status_ok)
        elif d.status == "pending":
            status_p = Paragraph("PENDING", style_td_status_pending)
        else:
            status_p = Paragraph(d.status.upper(), style_td_status_failed)

        donor_display = "Anonymous Devotee" if d.is_anonymous else d.donor_name
        contact_p = Paragraph(
            f"<font size='7.5'>{d.donor_email or '—'}</font><br/><font size='7' color='#555'>{d.donor_mobile or '—'}</font>",
            ParagraphStyle('Contact', leading=9),
        )

        row = [
            Paragraph(str(idx), style_td_center),
            Paragraph(f"<b>{donor_display}</b>", style_td_bold),
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
        Paragraph("<b>GRAND TOTAL (ಒಟ್ಟು ಮೊತ್ತ):</b>", ParagraphStyle('GT', fontName=FONT_BOLD, fontSize=8.5, textColor=PRIMARY_GREEN, alignment=2)),
        "", "",
        Paragraph(f"<b>₹{total_amount_rs:,}</b>", style_td_amount),
        Paragraph(f"<b>{completed_count} Successful</b>", ParagraphStyle('GTS', fontName=FONT_BOLD, fontSize=8, textColor=HexColor("#1B5E20"))),
        "", "", "",
    ]
    table_data.append(total_row)

    donations_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_GREEN),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, GOLD),
        ('INNERGRID', (0, 0), (-1, -2), 0.5, HexColor("#E2E8F0")),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
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
