"""
Receipt generation and visual validation script.
Generates PDFs and renders them to PNGs for visual review.
"""

import asyncio
import io
import os
from datetime import datetime, timezone
import pypdf
import pypdfium2 as pdfium

from app.db.init_db import init_db
from app.domain.donations.models import Donation
from app.utils.pdf_receipt import generate_receipt_pdf, generate_donations_report_pdf


def render_pdf_to_png(pdf_bytes: bytes, output_png_path: str):
    pdf = pdfium.PdfDocument(pdf_bytes)
    page = pdf[0]
    # Render at 2x scale (144 DPI) for crisp visual inspection
    bitmap = page.render(scale=2.0)
    pil_image = bitmap.to_pil()
    pil_image.save(output_png_path)
    print(f"Rendered image saved to {output_png_path}")


async def main():
    await init_db()

    # 1. Real DB Donation
    d_real = await Donation.find_one(Donation.receipt_number == "SHANI-20260927-DA0BBE")
    if not d_real:
        d_real = await Donation.find_one()

    print(f"--- Testing Real DB Donation: {d_real.receipt_number} ---")
    pdf_real = generate_receipt_pdf(d_real)
    with open("receipt_real.pdf", "wb") as f:
        f.write(pdf_real)
    render_pdf_to_png(pdf_real, "receipt_real.png")

    reader_real = pypdf.PdfReader(io.BytesIO(pdf_real))
    text_real = reader_real.pages[0].extract_text()
    with open("receipt_real_text.txt", "w", encoding="utf-8") as f:
        f.write(text_real)
    print("Real receipt text extracted to receipt_real_text.txt")

    # 2. Edge Case Donation:
    # Long Devotee Name, Long Address, Annadanam seva, Anonymous false, missing razorpay_order_id
    d_edge = Donation(
        user_id="user_test_edge",
        donor_name="Sri Dharmadhikari Vinay Kumar Gurudatta Sharma",
        donor_email="vinay.dharmadhikari@shreeshanitemple.org",
        donor_mobile="9741943965",
        donor_address="Kuvempu Road, Near Ganesha Temple, 4th Cross, Koduru Post, Hosanagara Taluk, Shimoga District, Karnataka - 577418",
        amount=500000,  # Rs. 5,000
        donation_type="annadanam",
        is_anonymous=False,
        razorpay_order_id=None,
        razorpay_payment_id="pay_test_9988776655",
        status="completed",
        receipt_number="SHANI-20261017-TESTEDGE",
        created_at=datetime.now(timezone.utc),
    )

    print("\n--- Testing Edge Case Donation ---")
    pdf_edge = generate_receipt_pdf(d_edge)
    with open("receipt_edge.pdf", "wb") as f:
        f.write(pdf_edge)
    render_pdf_to_png(pdf_edge, "receipt_edge.png")

    # 3. Missing Fields Donation (Empty address, empty mobile, empty email, anonymous)
    d_missing = Donation(
        user_id="user_missing",
        donor_name="Devotee Anonymous",
        donor_email="",
        donor_mobile="",
        donor_address="",
        amount=100000,  # Rs. 1,000
        donation_type="goshala",
        is_anonymous=True,
        razorpay_order_id=None,
        razorpay_payment_id="pay_anon_11223344",
        status="completed",
        receipt_number="SHANI-20261017-ANON",
        created_at=datetime.now(timezone.utc),
    )

    print("\n--- Testing Anonymous & Missing Fields Donation ---")
    pdf_missing = generate_receipt_pdf(d_missing)
    with open("receipt_missing.pdf", "wb") as f:
        f.write(pdf_missing)
    render_pdf_to_png(pdf_missing, "receipt_missing.png")

    # 4. Multi-page landscape donations summary report
    all_donations = await Donation.find_all().to_list()
    print(f"\n--- Testing Donations Report ({len(all_donations)} records) ---")
    pdf_report = generate_donations_report_pdf(all_donations)
    with open("donations_report.pdf", "wb") as f:
        f.write(pdf_report)
    render_pdf_to_png(pdf_report, "donations_report_page1.png")
    print("Report PDF generated successfully")


if __name__ == "__main__":
    asyncio.run(main())
