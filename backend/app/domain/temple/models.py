"""
Temple document model for MongoDB via Beanie ODM.
"""

from datetime import datetime
from typing import List, Optional

from beanie import Document
from pydantic import BaseModel, Field


class PoojaTime(BaseModel):
    """Individual pooja timing entry."""
    name_en: str = ""
    name_kn: str = ""
    time: str = ""


class TempleTimings(BaseModel):
    """Morning and evening timings."""
    morning_open: str = "6:00 AM"
    morning_close: str = "12:30 PM"
    evening_open: str = "5:00 PM"
    evening_close: str = "8:30 PM"
    special_poojas: List[PoojaTime] = []


class TempleContact(BaseModel):
    """Temple contact information."""
    phone: str = ""
    email: str = ""
    address_en: str = ""
    address_kn: str = ""


class Temple(Document):
    """Represents the temple information — singleton document."""

    name_en: str = "Shree Shanishwara Swamy Temple (R.)"
    name_kn: str = "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ)"
    place_en: str = "Shree Kshetra Siddagiri"
    place_kn: str = "ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ"

    history_en: str = ""
    history_kn: str = ""

    importance_en: str = ""
    importance_kn: str = ""

    story_en: str = ""
    story_kn: str = ""

    traditions_en: str = ""
    traditions_kn: str = ""

    vision_en: str = ""
    vision_kn: str = ""

    mission_en: str = ""
    mission_kn: str = ""

    timings: TempleTimings = Field(default_factory=TempleTimings)
    contact: TempleContact = Field(default_factory=TempleContact)

    # Google Maps embed URL
    map_embed_url: str = ""

    class Settings:
        name = "temple"


class CommitteeMember(BaseModel):
    """Entry for a committee member or prominent donor."""
    sl_no: int
    name_kn: str
    name_en: str
    designation_kn: str = ""
    designation_en: str = ""
    location_kn: str = ""
    location_en: str = ""


class DeityInfo(BaseModel):
    """Information on family deities."""
    sl_no: int
    name_kn: str
    name_en: str
    status_kn: str = "ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ"
    status_en: str = "Construction Complete"


class SpecialNotice(BaseModel):
    """Donation notice from official document."""
    min_amount: str = "10,000/-"
    amount_text_kn: str = "10,000/- (ಹತ್ತು ಸಾವಿರ) ಮೇಲೆ"
    amount_text_en: str = "₹10,000/- (Ten Thousand) and above"
    purpose_kn: str = "ದೇವಸ್ಥಾನ ಕಟ್ಟಡಕ್ಕೆ ಧನಸಹಾಯ"
    purpose_en: str = "Contribution for Temple Building Construction"
    condition_kn: str = "ದಾನಿಗಳ ಹೆಸರನ್ನು ಅಮೃತ ಶಿಲಾಫಲಕದಲ್ಲಿ ಬರೆಯಲಾಗುವುದು."
    condition_en: str = "The names of the donors will be inscribed on marble stone plaques."
    benefit_kn: str = "ಶ್ರೀ ಸ್ವಾಮಿಯು ತಮ್ಮ ಹಾಗೂ ಕುಟುಂಬ ವರ್ಗದವರ ಕಷ್ಟ ನಿವಾರಣೆ ಮಾಡಿ ಮೋಕ್ಷಾನುಗ್ರಹಕ್ಕೆ ಪಾತ್ರರಾಗುವಂತೆ ಶ್ರೀ ಸ್ವಾಮಿಯಲ್ಲಿ ಪ್ರಾರ್ಥಿಸಲಾಗುವುದು."
    benefit_en: str = "Prayers will be offered to Lord Shanishwara Swamy to dispel all hardships of the donors and their families and bestow divine grace and salvation upon them."


class AuditLogEntry(BaseModel):
    """Audit log entry for tracking updates to official information."""
    admin_email: str
    action: str
    details: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OfficialTempleInfo(Document):
    """Official temple information, committee members, donation notices, and document verification."""

    heading_kn: str = "ಶ್ರೀ ಶನೀಶ್ವರ ಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ.) ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ"
    heading_en: str = "Shree Shanishwara Swamy Temple (R.), Shri Kshetra Siddagiri"
    registration_no: str = "DRSH/SOR/637/2023-24"
    address_kn: str = "ಕುಸುಗುಂಡಿ ಗ್ರಾಮ, ಕೊಡೂರು ಅಂಚೆ, ಹೊಸನಗರ ತಾ||, ಶಿವಮೊಗ್ಗ ಜಿಲ್ಲೆ"
    address_en: str = "Kusugundi Village, Koduru Post, Hosanagara Tq, Shimoga Dist."
    dharmadarshi_kn: str = "ಶಂಕರ ಸ್ವಾಮಿ"
    dharmadarshi_en: str = "Shankara Swamy"
    dharmadarshi_phone: str = "9841943965 / 9741943965"
    manager_kn: str = "ಶ್ರೀಮತಿ ಎಸ್. ಸಾವಿತ್ರಮ್ಮ"
    manager_en: str = "Smt. S. Savithramma"
    bank_account_info_kn: str = "ಕೆನರಾ ಬ್ಯಾಂಕ್ ಕೋಡೂರು ಶಾಖೆ, ಖಾತೆ ನಂ: CNRB 0001516 ಖಾತೆ ನಂ: 1516101004653"
    bank_account_info_en: str = "Canara Bank Koduru Branch, IFSC: CNRB0001516, A/C: 1516101004653"

    deities: List[DeityInfo] = []
    special_notice: SpecialNotice = Field(default_factory=SpecialNotice)
    committee_members: List[CommitteeMember] = []

    document_image_url: str = "/static/assets/documents/official_document_p2.jpg"
    document_page1_url: str = "/static/assets/documents/official_document_p1.jpg"
    document_pdf_url: str = "/static/assets/documents/official_temple_document.pdf"
    is_document_public: bool = True

    audit_logs: List[AuditLogEntry] = []

    class Settings:
        name = "official_temple_info"

