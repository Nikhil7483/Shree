# Bilingual PDF Receipt Generation Pipeline

**Shree Shanishwara Swamy Temple Website**  
**Module:** `backend/app/utils/pdf_receipt.py` & `backend/app/receipts/`

---

## 1. Problem Statement & Kannada Ligature Challenges

Standard PDF engines (such as default ReportLab TrueType font rendering) draw Unicode Indic characters sequentially code-point by code-point. In Kannada:
- Conjuncts (`ಕ್ಷ`, `ಶ್ರೀ`, `ಸ್ವಾ`, `ನ್ನ`) require OpenType GSUB (Glyph Substitution) and GPOS (Glyph Positioning) tables.
- Vowel signs and viramas (halanta) must combine beneath or beside consonant bases into single or reordered glyphs.
- Without an OpenType layout engine, ReportLab renders broken characters like `ಶ ್ ರ ೀ` instead of `ಶ್ರೀ` or `ಕ ್ ಷ` instead of `ಕ್ಷ`.

---

## 2. Solution: HarfBuzz + FreeType + ReportLab Pipeline

To render flawless, publication-grade Kannada ligatures, our engine implements a hybrid rendering architecture:

```
[ Unicode Kannada Text (ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ) ]
                       |
                       v
         [ uharfbuzz OpenType Shaper ]
    (Uses GSUB / GPOS tables to resolve ligatures)
                       |
                       v
  [ Shaped Glyph IDs + Cluster Offsets (dx, dy, adv_x) ]
                       |
                       v
      [ freetype-py Glyph Outline Extraction ]
 (Converts TrueType outlines into Bezier curves & lines)
                       |
                       v
       [ ReportLab Canvas Vector Path Drawing ]
  (Emits native PDF vector paths: moveTo, lineTo, curveTo)
                       |
                       v
   [ Invisible Text Searchability Layer (RenderMode 3) ]
 (Renders underlying text in saveState() to keep PDF searchable)
```

### Key Technical Details

1. **HarfBuzz OpenType Shaping:**
   - Pre-loads font tables (`hb.Face` and `hb.Font`).
   - Configures script to `Knda` and language to `KAN`.
   - Shapes words into resolved glyph IDs and fractional x/y advances.

2. **FreeType Vector Path Decomposition:**
   - FreeType inspects each glyph outline and passes quadratic / cubic Bezier segments directly to ReportLab's `c.beginPath()`.
   - Native vectors are completely scalable, ultra-sharp, and print-ready at any DPI without pixelation.

3. **Searchable Text Layer:**
   - Because vector paths alone are not indexed by PDF search engines, an invisible text layer is rendered using ReportLab's `setTextRenderMode(3)`.
   - **Crucial Rule:** The render mode change is strictly isolated inside `c.saveState()` and `c.restoreState()` so it does not hide subsequent normal text.

4. **Multi-Page Prevention & Single-Page A4 Layout:**
   - Total canvas height: 841.89 points (Standard A4).
   - Coordinates are calculated mathematically from top to bottom with strict boundary enforcement to guarantee every receipt is exactly 1 page.
   - Long donor names (>32 characters) dynamically scale font size to prevent overlapping contact details or badges.

5. **Offline Vector QR Verification:**
   - Renders a native vector QR code using ReportLab's built-in `reportlab.graphics.barcode.qr.QrCodeWidget`.
   - Encodes receipt verification URL: `https://www.shreeshanitemple.com/verify?receipt=<RECEIPT_NUMBER>`.
   - Requires zero external web requests to generate, making it 100% offline-capable and reliable.
