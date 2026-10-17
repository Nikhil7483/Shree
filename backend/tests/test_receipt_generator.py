"""
Unit tests for ReportLab and HarfBuzz bilingual PDF receipt generation.
"""

import io
import pypdf
import pytest
from app.domain.donations.models import Donation
from app.utils.pdf_receipt import generate_receipt_pdf, generate_donations_report_pdf


def test_standard_donation_receipt():
    donation = Donation(
        user_id="test_user_001",
        donor_name="Dr. Suresh Rao",
        donor_email="suresh.rao@example.com",
        donor_mobile="9876543210",
        donor_address="Basavanagudi, Bengaluru, Karnataka - 560004",
        amount=100000,  # Rs. 1,000 in paise
        donation_type="general",
        is_anonymous=False,
        status="completed",
        receipt_number="SHANI-TEST-STD001",
        razorpay_payment_id="pay_std_12345678",
    )

    pdf_bytes = generate_receipt_pdf(donation)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page_text = reader.pages[0].extract_text()
    assert "SHANI-TEST-STD001" in page_text
    assert "Dr. Suresh Rao" in page_text
    assert "1,000" in page_text


def test_edge_case_donation_receipt():
    donation = Donation(
        user_id="test_user_edge",
        donor_name="Sri Dharmadhikari Vinay Kumar Gurudatta Sharma of Siddhagiri Kshetra",
        donor_email="vinay.dharmadhikari@shreeshanitemple.org",
        donor_mobile="9741943965",
        donor_address="Kuvempu Road, Near Ganesha Temple, 4th Cross, Koduru Post, Hosanagara Taluk, Shimoga District, Karnataka - 577418",
        amount=500000,  # Rs. 5,000
        donation_type="annadanam",
        is_anonymous=False,
        status="completed",
        receipt_number="SHANI-TEST-EDGE002",
        razorpay_payment_id="pay_edge_87654321",
    )

    pdf_bytes = generate_receipt_pdf(donation)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page_text = reader.pages[0].extract_text()
    assert "SHANI-TEST-EDGE002" in page_text
    assert "5,000" in page_text


def test_donations_report_pdf():
    donations = [
        Donation(
            user_id="user_rep_001",
            donor_name="Donor One",
            donor_email="d1@example.com",
            donor_mobile="9876543211",
            amount=50000,
            donation_type="pooja",
            receipt_number="SHANI-REP-001",
            status="completed",
        ),
        Donation(
            user_id="user_rep_002",
            donor_name="Donor Two",
            donor_email="d2@example.com",
            donor_mobile="9876543212",
            amount=150000,
            donation_type="annadanam",
            receipt_number="SHANI-REP-002",
            status="completed",
        ),
    ]
    report_bytes = generate_donations_report_pdf(donations, "All Time Test Donations")
    assert isinstance(report_bytes, bytes)
    assert report_bytes.startswith(b"%PDF-")
    reader = pypdf.PdfReader(io.BytesIO(report_bytes))
    assert len(reader.pages) >= 1
