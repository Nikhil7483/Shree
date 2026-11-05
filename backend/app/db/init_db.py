"""
Database initialization: Motor client, Beanie ODM setup, and seed data.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import get_settings
from app.core.security import hash_password
from app.domain.users.models import User
from app.domain.temple.models import (
    Temple, TempleTimings, TempleContact, PoojaTime,
    OfficialTempleInfo, CommitteeMember, DeityInfo, SpecialNotice, AuditLogEntry
)
from app.domain.gallery.models import GalleryItem
from app.domain.festivals.models import Festival
from app.domain.donations.models import Donation

settings = get_settings()


async def init_db():
    """Initialize Motor client and Beanie ODM with all document models."""
    mongo_url = settings.MONGODB_URL
    if "@" in mongo_url and "authSource" not in mongo_url and not mongo_url.startswith("mongodb+srv"):
        separator = "&" if "?" in mongo_url else "?"
        mongo_url = f"{mongo_url}{separator}authSource=admin"

    safe_url = mongo_url
    if "@" in safe_url:
        try:
            prefix, rest = safe_url.split("://", 1)
            _, host = rest.split("@", 1)
            safe_url = f"{prefix}://***:***@{host}"
        except Exception:
            safe_url = "mongodb://[protected_credentials]"
    print(f"Connecting to MongoDB at: {safe_url}")

    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=3000,
    )

    await client.admin.command("ping")
    print("[OK] Database connection verified.")

    database = client[settings.DB_NAME]

    await init_beanie(
        database=database,
        document_models=[
            User,
            Temple,
            OfficialTempleInfo,
            GalleryItem,
            Festival,
            Donation,
        ],
    )

    # Seed default data
    await seed_admin()
    await seed_temple()
    await seed_official_temple_info()
    await seed_festivals()
    await seed_gallery()



async def seed_admin():
    """Create default admin user if not exists."""
    existing = await User.find_one(User.email == settings.ADMIN_EMAIL)
    if not existing:
        admin = User(
            name="Temple Admin",
            email=settings.ADMIN_EMAIL,
            mobile="0000000000",
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            preferred_language="kn",
            role="admin",
        )
        await admin.insert()
        print(f"Admin user created: {settings.ADMIN_EMAIL}")


async def seed_temple():
    """Create default temple document if not exists."""
    existing = await Temple.find_one()
    if not existing:
        temple = Temple(
            name_en="Shree Shanishwara Swamy Temple (R.)",
            name_kn="ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ)",
            place_en="Shree Kshetra Siddagiri",
            place_kn="ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ",
            history_en=(
                "Shree Shanishwara Swamy Temple, located at the sacred Siddagiri hill "
                "in Kusugundi village, Koduru post, Hosanagara taluk, Shimoga district, "
                "Karnataka, is a revered shrine dedicated to Lord Shanishwara (Saturn deity). "
                "The temple holds great spiritual significance and attracts devotثes from "
                "across Karnataka and beyond. Nestled amidst the lush greenery of the "
                "Western Ghats, the temple offers a serene and divine atmosphere for worship. "
                "The temple has been a beacon of faith for generations, with its ancient "
                "traditions and powerful blessings drawing thousands of devotees, especially "
                "on Shani Amavasya days."
            ),
            history_kn=(
                "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನವು ಕರ್ನಾಟಕ ರಾಜ್ಯದ ಶಿವಮೊಗ್ಗ ಜಿಲ್ಲೆಯ "
                "ಹೊಸನಗರ ತಾಲ್ಲೂಕಿನ ಕೊಡೂರು ಅಂಚೆಯ ಕುಸುಗುಂಡಿ ಗ್ರಾಮದಲ್ಲಿರುವ ಪವಿತ್ರ ಸಿದ್ದಗಿರಿ "
                "ಬೆಟ್ಟದಲ್ಲಿ ನೆಲೆಸಿದೆ. ಶನೀಶ್ವರ ದೇವರಿಗೆ ಸಮರ್ಪಿತವಾದ ಈ ದೇವಸ್ಥಾನವು ಅಪಾರ "
                "ಆಧ್ಯಾತ್ಮಿಕ ಮಹತ್ವವನ್ನು ಹೊಂದಿದೆ. ಪಶ್ಚಿಮ ಘಟ್ಟಗಳ ಹಸಿರು ಸಿರಿಯ ನಡುವೆ "
                "ನೆಲೆಸಿರುವ ಈ ದೇವಸ್ಥಾನವು ಪ್ರಶಾಂತ ಮತ್ತು ದೈವಿಕ ವಾತಾವರಣವನ್ನು ನೀಡುತ್ತದೆ. "
                "ತಲೆಮಾರುಗಳಿಂದ ಭಕ್ತರ ನಂಬಿಕೆಯ ಕೇಂದ್ರವಾಗಿರುವ ಈ ದೇವಸ್ಥಾನವು ವಿಶೇಷವಾಗಿ "
                "ಶನಿ ಅಮಾವಾಸ್ಯೆಯ ದಿನಗಳಲ್ಲಿ ಸಾವಿರಾರು ಭಕ್ತರನ್ನು ಆಕರ್ಷಿಸುತ್ತದೆ."
            ),
            importance_en=(
                "Lord Shanishwara is considered one of the Navagrahas (nine planetary deities) "
                "in Hindu astrology. Worshipping Lord Shani is believed to mitigate the "
                "malefic effects of Saturn and bring justice, discipline, and spiritual growth. "
                "Devotees visit this temple to seek blessings for overcoming obstacles, "
                "gaining wisdom, and achieving prosperity."
            ),
            importance_kn=(
                "ಶನೀಶ್ವರ ದೇವರು ಹಿಂದೂ ಜ್ಯೋತಿಷ್ಯಶಾಸ್ತ್ರದಲ್ಲಿ ನವಗ್ರಹಗಳಲ್ಲಿ ಒಬ್ಬರೆಂದು "
                "ಪರಿಗಣಿಸಲಾಗಿದೆ. ಶನೀಶ್ವರನ ಪೂಜೆಯು ಶನಿಯ ದುಷ್ಪರಿಣಾಮಗಳನ್ನು ತಗ್ಗಿಸುತ್ತದೆ "
                "ಮತ್ತು ನ್ಯಾಯ, ಶಿಸ್ತು ಹಾಗೂ ಆಧ್ಯಾತ್ಮಿಕ ಬೆಳವಣಿಗೆಯನ್ನು ತರುತ್ತದೆ ಎಂದು "
                "ನಂಬಲಾಗಿದೆ. ಭಕ್ತರು ಅಡೆತಡೆಗಳನ್ನು ನಿವಾರಿಸಲು, ಜ್ಞಾನ ಪಡೆಯಲು ಮತ್ತು "
                "ಸಮೃದ್ಧಿಯನ್ನು ಸಾಧಿಸಲು ಈ ದೇವಸ್ಥಾನಕ್ಕೆ ಭೇಟಿ ನೀಡುತ್ತಾರೆ."
            ),
            vision_en="To be a spiritual center that uplifts devotees and serves the community through divine grace.",
            vision_kn="ದೈವಿಕ ಕೃಪೆಯ ಮೂಲಕ ಭಕ್ತರನ್ನು ಉನ್ನತೀಕರಿಸುವ ಮತ್ತು ಸಮುದಾಯಕ್ಕೆ ಸೇವೆ ಸಲ್ಲಿಸುವ ಆಧ್ಯಾತ್ಮಿಕ ಕೇಂದ್ರವಾಗುವುದು.",
            mission_en="To preserve temple traditions, promote spiritual education, and provide seva to all devotees.",
            mission_kn="ದೇವಸ್ಥಾನದ ಸಂಪ್ರದಾಯಗಳನ್ನು ಸಂರಕ್ಷಿಸುವುದು, ಆಧ್ಯಾತ್ಮಿಕ ಶಿಕ್ಷಣವನ್ನು ಉತ್ತೇಜಿಸುವುದು ಮತ್ತು ಎಲ್ಲಾ ಭಕ್ತರಿಗೆ ಸೇವೆ ಒದಗಿಸುವುದು.",
            timings=TempleTimings(
                morning_open="6:00 AM",
                morning_close="12:30 PM",
                evening_open="5:00 PM",
                evening_close="8:30 PM",
                special_poojas=[
                    PoojaTime(name_en="Abhisheka", name_kn="ಅಭಿಷೇಕ", time="6:30 AM"),
                    PoojaTime(name_en="Maha Pooja", name_kn="ಮಹಾ ಪೂಜೆ", time="12:00 PM"),
                    PoojaTime(name_en="Evening Aarti", name_kn="ಸಂಜೆ ಆರತಿ", time="7:00 PM"),
                ],
            ),
            contact=TempleContact(
                phone="+91 9741943965",
                email="info@shreeshani.com",
                address_en="Kusugundi Village, Koduru Post, Hosanagara Taluk, Shimoga District, Karnataka – India",
                address_kn="ಕುಸುಗುಂಡಿ ಗ್ರಾಮ, ಕೊಡೂರು ಅಂಚೆ, ಹೊಸನಗರ ತಾಲ್ಲೂಕು, ಶಿವಮೊಗ್ಗ ಜಿಲ್ಲೆ, ಕರ್ನಾಟಕ – ಭಾರತ",
            ),
            map_embed_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3878.5!2d75.0!3d14.0!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTTCsDA0JzAwLjAiTiA3NcKwMDAnMDAuMCJF!5e0!3m2!1sen!2sin!4v1234567890",
        )
        await temple.insert()
        print("Temple data seeded")


async def seed_festivals():
    """Create sample festivals if none exist."""
    count = await Festival.count()
    if count == 0:
        festivals = [
            Festival(
                name_en="Shani Amavasya",
                name_kn="ಶನಿ ಅಮಾವಾಸ್ಯೆ",
                description_en="The most auspicious day dedicated to Lord Shanishwara. Thousands of devotees visit the temple for special pooja and darshan.",
                description_kn="ಶನೀಶ್ವರ ದೇವರಿಗೆ ಸಮರ್ಪಿತ ಅತ್ಯಂತ ಶುಭ ದಿನ. ಸಾವಿರಾರು ಭಕ್ತರು ವಿಶೇಷ ಪೂಜೆ ಮತ್ತು ದರ್ಶನಕ್ಕಾಗಿ ದೇವಸ್ಥಾನಕ್ಕೆ ಭೇಟಿ ನೀಡುತ್ತಾರೆ.",
                date="Every Amavasya",
                is_recurring=True,
            ),
            Festival(
                name_en="Deepavali",
                name_kn="ದೀಪಾವಳಿ",
                description_en="Festival of Lights celebrated with grand illumination, special poojas, and community feast at the temple.",
                description_kn="ಬೆಳಕಿನ ಹಬ್ಬವನ್ನು ಭವ್ಯ ಬೆಳಕಿನ ಅಲಂಕಾರ, ವಿಶೇಷ ಪೂಜೆಗಳು ಮತ್ತು ಸಾಮುದಾಯಿಕ ಭೋಜನದೊಂದಿಗೆ ದೇವಸ್ಥಾನದಲ್ಲಿ ಆಚರಿಸಲಾಗುತ್ತದೆ.",
                date="October/November",
                is_recurring=True,
            ),
            Festival(
                name_en="Ugadi",
                name_kn="ಯುಗಾದಿ",
                description_en="Kannada New Year celebrated with traditional Panchanga Shravana and special temple rituals.",
                description_kn="ಕನ್ನಡ ಹೊಸ ವರ್ಷವನ್ನು ಸಾಂಪ್ರದಾಯಿಕ ಪಂಚಾಂಗ ಶ್ರವಣ ಮತ್ತು ವಿಶೇಷ ದೇವಸ್ಥಾನ ಆಚರಣೆಗಳೊಂದಿಗೆ ಆಚರಿಸಲಾಗುತ್ತದೆ.",
                date="March/April",
                is_recurring=True,
            ),
            Festival(
                name_en="Makara Sankranti",
                name_kn="ಮಕರ ಸಂಕ್ರಾಂತಿ",
                description_en="Harvest festival celebrated with special poojas, ellu-bella distribution, and community gathering.",
                description_kn="ಸುಗ್ಗಿ ಹಬ್ಬವನ್ನು ವಿಶೇಷ ಪೂಜೆಗಳು, ಎಳ್ಳು-ಬೆಲ್ಲ ವಿತರಣೆ ಮತ್ತು ಸಾಮುದಾಯಿಕ ಸಭೆಯೊಂದಿಗೆ ಆಚರಿಸಲಾಗುತ್ತದೆ.",
                date="January 14-15",
                is_recurring=True,
            ),
            Festival(
                name_en="Annual Jatre (Temple Fair)",
                name_kn="ವಾರ್ಷಿಕ ಜಾತ್ರೆ",
                description_en="Grand annual temple fair with special rituals, cultural programs, Annadanam, and religious processions.",
                description_kn="ವಿಶೇಷ ಆಚರಣೆಗಳು, ಸಾಂಸ್ಕೃತಿಕ ಕಾರ್ಯಕ್ರಮಗಳು, ಅನ್ನದಾನ ಮತ್ತು ಧಾರ್ಮಿಕ ಮೆರವಣಿಗೆಗಳೊಂದಿಗೆ ಭವ್ಯ ವಾರ್ಷಿಕ ದೇವಸ್ಥಾನ ಜಾತ್ರೆ.",
                date="February/March",
                is_recurring=True,
            ),
            Festival(
                name_en="Special Poojas",
                name_kn="ವಿಶೇಷ ಪೂಜೆಗಳು",
                description_en="Tailadhaara, Shani Shanti Homa, Navagraha Shanti, and other special rituals performed for devotees.",
                description_kn="ತೈಲಧಾರಾ, ಶನಿ ಶಾಂತಿ ಹೋಮ, ನವಗ್ರಹ ಶಾಂತಿ, ಮತ್ತು ಇತರ ವಿಶೇಷ ಆಚರಣೆಗಳನ್ನು ಭಕ್ತರಿಗಾಗಿ ನಡೆಸಲಾಗುತ್ತದೆ.",
                date="On request",
                is_recurring=True,
            ),
        ]
        for festival in festivals:
            await festival.insert()
        print(f"{len(festivals)} festivals seeded")


async def seed_official_temple_info():
    """Seed official temple info, committee members, deities, and donation notices from the official Kannada document."""
    existing = await OfficialTempleInfo.find_one()
    if not existing:
        deities = [
            DeityInfo(
                sl_no=1,
                name_kn="ಶ್ರೀ ನಾಗಪರಿವಾರ ದೇವರ ದೇವಸ್ಥಾನ ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                name_en="Sri Nagaparivara Devara Temple Construction Complete",
                status_kn="ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                status_en="Construction Complete",
            ),
            DeityInfo(
                sl_no=2,
                name_kn="ಶ್ರೀ ವೀರಕಲ್ಲುಕುಟಿಕ ಪರಿವಾರ ದೈವಗಳ ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                name_en="Sri Veerakallukutika Parivara Deities Construction Complete",
                status_kn="ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                status_en="Construction Complete",
            ),
            DeityInfo(
                sl_no=3,
                name_kn="ಶ್ರೀ ರಕ್ತೇಶ್ವರಿ ದೇವಿ ನೆಲೆಸಿದ ಕ್ಷೇತ್ರ ದೇವಸ್ಥಾನ ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                name_en="Sri Rakteshwari Devi Holy Shrine Construction Complete",
                status_kn="ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
                status_en="Construction Complete",
            ),
        ]

        special_notice = SpecialNotice(
            min_amount="10,000/-",
            amount_text_kn="10,000/- (ಹತ್ತು ಸಾವಿರ) ಮೇಲೆ",
            amount_text_en="₹10,000/- (Ten Thousand) and above",
            purpose_kn="ದೇವಸ್ಥಾನ ಕಟ್ಟಡಕ್ಕೆ ಧನಸಹಾಯ",
            purpose_en="Contribution for Temple Building Construction",
            condition_kn="ದಾನಿಗಳ ಹೆಸರನ್ನು ಅಮೃತ ಶಿಲಾಫಲಕದಲ್ಲಿ ಬರೆಯಲಾಗುವುದು.",
            condition_en="The names of the donors will be inscribed on sacred marble stone plaques.",
            benefit_kn="ಶ್ರೀ ಸ್ವಾಮಿಯು ತಮ್ಮ ಹಾಗೂ ಕುಟುಂಬ ವರ್ಗದವರ ಕಷ್ಟ ನಿವಾರಣೆ ಮಾಡಿ ಮೋಕ್ಷಾನುಗ್ರಹಕ್ಕೆ ಪಾತ್ರರಾಗುವಂತೆ ಶ್ರೀ ಸ್ವಾಮಿಯಲ್ಲಿ ಪ್ರಾರ್ಥಿಸಲಾಗುವುದು.",
            benefit_en="Prayers will be offered to Lord Shanishwara Swamy to dispel all hardships for the donors and their families and bestow divine grace and salvation upon them.",
        )

        committee_members = [
            CommitteeMember(
                sl_no=1,
                name_kn="ಶ್ರೀ ಡಿ.ಹೆಚ್. ಶಂಕರಮೂರ್ತಿ",
                name_en="Sri D.H. Shankaramurthy",
                designation_kn="ಮಾಜಿ ಸ್ಪೀಕರ್, ವಿಧಾನ ಪರಿಷತ್",
                designation_en="Former Chairman / Speaker, Legislative Council",
                location_kn="ಕರ್ನಾಟಕ",
                location_en="Karnataka",
            ),
            CommitteeMember(
                sl_no=2,
                name_kn="ಶ್ರೀ ಉದಯಕುಮಾರ ಶೆಟ್ಟಿ",
                name_en="Sri Udayakumar Shetty",
                designation_kn="",
                designation_en="",
                location_kn="ಪಾಲಾಡಿ, ಬೆಂಗಳೂರು",
                location_en="Paladi, Bengaluru",
            ),
            CommitteeMember(
                sl_no=3,
                name_kn="ಶ್ರೀ ಮತ್ತು ಶ್ರೀಮತಿ ಎಸ್.ಎನ್. ಜ್ಯೋತಿ ಪ್ರಕಾಶ್",
                name_en="Sri & Smt. S.N. Jyothi Prakash",
                designation_kn="ಎಪಿಎಂಸಿ ಮಾಜಿ ಅಧ್ಯಕ್ಷರು",
                designation_en="Former President, APMC",
                location_kn="ಶಿವಮೊಗ್ಗ",
                location_en="Shivamogga",
            ),
            CommitteeMember(
                sl_no=4,
                name_kn="ಶ್ರೀ ಎಂ.ಆರ್. ಮೂರ್ತಿ",
                name_en="Sri M.R. Murthy",
                designation_kn="ಇಂಜಿನಿಯರ್",
                designation_en="Engineer",
                location_kn="",
                location_en="",
            ),
            CommitteeMember(
                sl_no=5,
                name_kn="ಶ್ರೀ ಬಿ.ವೈ. ರಾಘವೇಂದ್ರರವರು",
                name_en="Sri B.Y. Raghavendra",
                designation_kn="ಮಾನ್ಯ ಸಂಸದರು",
                designation_en="Member of Parliament (MP)",
                location_kn="ಶಿವಮೊಗ್ಗ ಲೋಕಸಭಾ ಕ್ಷೇತ್ರ",
                location_en="Shivamogga Lok Sabha Constituency",
            ),
            CommitteeMember(
                sl_no=6,
                name_kn="ಶ್ರೀ ನಟರಾಜ್",
                name_en="Sri Nataraj",
                designation_kn="",
                designation_en="",
                location_kn="ಶಿವಮೊಗ್ಗ",
                location_en="Shivamogga",
            ),
            CommitteeMember(
                sl_no=7,
                name_kn="ಶ್ರೀಮತಿ ಗಣೇಶ್ ಕುಡತ್ಕಲ್",
                name_en="Smt. Ganesh Kudatkal",
                designation_kn="",
                designation_en="",
                location_kn="ಅಂಕೋಲ",
                location_en="Ankola",
            ),
            CommitteeMember(
                sl_no=8,
                name_kn="ಶ್ರೀ ಶಂಕರ ಶೆಟ್ಟಿ",
                name_en="Sri Shankara Shetty",
                designation_kn="",
                designation_en="",
                location_kn="ಕುರುವಳ್ಳಿ ತೀರ್ಥಹಳ್ಳಿ ತಾಲೂಕು",
                location_en="Kuruvalli, Thirthahalli Taluk",
            ),
            CommitteeMember(
                sl_no=9,
                name_kn="ಶ್ರೀ ಮಂಗಲ್ ದಾಸ್ ಮತ್ತು ವಾಮನ ಭಟ್",
                name_en="Sri Mangaldas & Vamana Bhat",
                designation_kn="",
                designation_en="",
                location_kn="ಅಂಕೋಲ",
                location_en="Ankola",
            ),
            CommitteeMember(
                sl_no=10,
                name_kn="ಶ್ರೀ ನಾಗರಾಜ ಶೆಟ್ಟಿ",
                name_en="Sri Nagaraja Shetty",
                designation_kn="",
                designation_en="",
                location_kn="ನಗರ, ಬೆಂಗಳೂರು",
                location_en="Nagara, Bengaluru",
            ),
            CommitteeMember(
                sl_no=11,
                name_kn="ಪೋಲೀಸ್ ಎಸ್.ಎಸ್. ಮಂಜುನಾಥ",
                name_en="Police S.SS. Manjunath",
                designation_kn="ಪೋಲೀಸ್",
                designation_en="Police",
                location_kn="ಬೆಂಗಳೂರು",
                location_en="Bengaluru",
            ),
            CommitteeMember(
                sl_no=12,
                name_kn="ಶ್ರೀ ಆನಂದ ಕುಂದರ್ ಸಿ.",
                name_en="Sri Ananda Kundar C.",
                designation_kn="",
                designation_en="",
                location_kn="ಕೋಟ, ಉಡುಪಿ ಜಿಲ್ಲೆ",
                location_en="Kota, Udupi District",
            ),
            CommitteeMember(
                sl_no=13,
                name_kn="ಶ್ರೀ ಬಸವರಾಜ್ ಮತ್ತು ಮನೆಯವರು",
                name_en="Sri Basavaraj & Family",
                designation_kn="",
                designation_en="",
                location_kn="ಗಾಂಧಿ ಬಜಾರ್, ಶಿವಮೊಗ್ಗ",
                location_en="Gandhi Bazaar, Shivamogga",
            ),
            CommitteeMember(
                sl_no=14,
                name_kn="ಶ್ರೀಮತಿ ಕಾಂಚನ ಕೆ.",
                name_en="Smt. Kanchana K.",
                designation_kn="",
                designation_en="",
                location_kn="",
                location_en="",
            ),
            CommitteeMember(
                sl_no=15,
                name_kn="ಶ್ರೀ ಕೆ.ಆರ್. ರಾಜಶೇಖರ್",
                name_en="Sri K.R. Rajashekhar",
                designation_kn="",
                designation_en="",
                location_kn="",
                location_en="",
            ),
            CommitteeMember(
                sl_no=16,
                name_kn="ದಿ|| ರಾಜಯ್ಯ, ದಿ|| ಸಿದ್ದಲಿಂಗಯ್ಯ ರಬಕವಿ, ದಿ|| ರಾಜಮ್ಮ ಬೆಂಗಳೂರು, ದಿ|| ವೀರಯ್ಯ ಸೋಲಾಪುರ, ದಿ|| ದುಂಡವ್ವ ಗೋಕಾಕ್, ದಿ|| ಚಂದ್ರಶೇಖರ್ ತುಮಕೂರು, ದಿ|| ಸೋಮಶೇಖರ್ ಮೈಸೂರು, ದಿ|| ನೀಲಮ್ಮ, ದಿ|| ಆರಾಧ್ಯ ನೀಲಮ್ಮ",
                name_en="Late Rajayya, Late Siddalingayya (Rabakavi), Late Rajamma (Bengaluru), Late Veerayya (Solapur), Late Dundavva (Gokak), Late Chandrashekhar (Tumakuru), Late Somashekhar (Mysuru), Late Neelamma, Late Aradhya Neelamma",
                designation_kn="ದಿವಂಗತ ಮಹನೀಯರು / ಸ್ಮರಣಾರ್ಥ",
                designation_en="In Sacred Memory of Departed Souls",
                location_kn="ರವಿಕಿ/ರಬಕವಿ, ಬೆಂಗಳೂರು, ಸೋಲಾಪುರ, ಗೋಕಾಕ್, ತುಮಕೂರು, ಮೈಸೂರು",
                location_en="Rabakavi, Bengaluru, Solapur, Gokak, Tumakuru, Mysuru",
            ),
            CommitteeMember(
                sl_no=17,
                name_kn="ಶ್ರೀಮತಿ ಆರ್. ನಾಗವೇಣಿ",
                name_en="Smt. R. Nagaveni",
                designation_kn="ಮಣಿ ಪೈಂಟ್ ಅಂಡ್ ಹಾರ್ಡ್‌ವೇರ್",
                designation_en="Mani Paint and Hardware",
                location_kn="ಶಿವಮೊಗ್ಗ",
                location_en="Shivamogga",
            ),
            CommitteeMember(
                sl_no=18,
                name_kn="ಶ್ರೀ ಆತ್ಮಾರಾಮ್ ರಂಗಡೋಳ್ಕರ್",
                name_en="Sri Atmaram Rangodolkar",
                designation_kn="ಇಂಜಿನಿಯರ್",
                designation_en="Engineer",
                location_kn="",
                location_en="",
            ),
            CommitteeMember(
                sl_no=19,
                name_kn="ಶ್ರೀ ಇಂಬಾಲಿ ಭಾಸ್ಕರ ಕಿಣಿ",
                name_en="Sri Imbali Bhaskara Kini",
                designation_kn="ರಿಟೈರ್ಡ್ ಆರ್ಮಿ",
                designation_en="Retired Army",
                location_kn="ಕುಂಭಾಸಿ",
                location_en="Kumbhashi",
            ),
            CommitteeMember(
                sl_no=20,
                name_kn="ಶ್ರೀಮತಿ ಅಮೃತ, ಶ್ರೀ ನವೀನ್ (ಜಯನಗರ)",
                name_en="Smt. Amrutha & Sri Naveen (Jayanagar)",
                designation_kn="",
                designation_en="",
                location_kn="ಜರ್ಮನಿ",
                location_en="Germany",
            ),
            CommitteeMember(
                sl_no=21,
                name_kn="ಶ್ರೀ ಲಕ್ಷ್ಮಣ್ ಸಾರ್ ಮತ್ತು ಮನೆಯವರು",
                name_en="Sri Lakshman Sir & Family",
                designation_kn="ಗೀತಾಂಜಲಿ ಬಟ್ಟೆ ಅಂಗಡಿ",
                designation_en="Geetanjali Cloth Store",
                location_kn="ಉಡುಪಿ",
                location_en="Udupi",
            ),
            CommitteeMember(
                sl_no=22,
                name_kn="ಶ್ರೀಮತಿ ದಿವ್ಯ ನಾಗರಾಜ",
                name_en="Smt. Divya Nagaraja",
                designation_kn="ಶಂಕರೇಶ್ವರ ಸ್ವೀಟ್ ಹೌಸ್",
                designation_en="Shankareshwara Sweet House",
                location_kn="ಶಿವಮೊಗ್ಗ",
                location_en="Shivamogga",
            ),
            CommitteeMember(
                sl_no=23,
                name_kn="ಶ್ರೀಮತಿ ಕನಕ, ಕೆ.ಎಸ್.ಎನ್. ಮೂರ್ತಿ",
                name_en="Smt. Kanaka, K.S.N. Murthy",
                designation_kn="ಮೂರ್ತಿ ವಾಚ್ ಕಂಪನಿ",
                designation_en="Murthy Watch Company",
                location_kn="ಶಿವಮೊಗ್ಗ",
                location_en="Shivamogga",
            ),
        ]

        info = OfficialTempleInfo(
            heading_kn="ಶ್ರೀ ಶನೀಶ್ವರ ಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ.) ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ",
            heading_en="Shree Shanishwara Swamy Temple (R.), Shri Kshetra Siddagiri",
            registration_no="DRSH/SOR/637/2023-24",
            address_kn="ಕುಸುಗುಂಡಿ ಗ್ರಾಮ, ಕೊಡೂರು ಅಂಚೆ, ಹೊಸನಗರ ತಾ||, ಶಿವಮೊಗ್ಗ ಜಿಲ್ಲೆ",
            address_en="Kusugundi Village, Koduru Post, Hosanagara Tq, Shimoga Dist.",
            dharmadarshi_kn="ಶಂಕರ ಸ್ವಾಮಿ",
            dharmadarshi_en="Shankara Swamy",
            dharmadarshi_phone="9841943965 / 9741943965",
            manager_kn="ಶ್ರೀಮತಿ ಎಸ್. ಸಾವಿತ್ರಮ್ಮ",
            manager_en="Smt. S. Savithramma",
            bank_account_info_kn="ಕೆನರಾ ಬ್ಯಾಂಕ್ ಕೋಡೂರು ಶಾಖೆ, ಖಾತೆ ನಂ: CNRB 0001516 ಖಾತೆ ನಂ: 1516101004653",
            bank_account_info_en="Canara Bank Koduru Branch, IFSC: CNRB0001516, A/C: 1516101004653",
            deities=deities,
            special_notice=special_notice,
            committee_members=committee_members,
            document_image_url="/static/assets/documents/official_document_p2.jpg",
            document_page1_url="/static/assets/documents/official_document_p1.jpg",
            document_pdf_url="/static/assets/documents/official_temple_document.pdf",
            is_document_public=True,
            audit_logs=[
                AuditLogEntry(
                    admin_email="system@shreeshani.com",
                    action="INITIAL_SEED",
                    details="Initial seed of official temple information, committee members, and donation notice from uploaded document.",
                )
            ],
        )
        await info.insert()
        print("Official temple info and committee seeded successfully")


async def seed_gallery():
    """Seed the 7 real temple gallery photographs."""
    count = await GalleryItem.count()
    if count == 0:
        gallery_items = [
            GalleryItem(
                title_en="Temple Entrance",
                title_kn="ದೇವಸ್ಥಾನದ ಪ್ರವೇಶ ದ್ವಾರ",
                image_url="/static/assets/gallery/temple-entrance.png",
                category="temple",
            ),
            GalleryItem(
                title_en="Temple View",
                title_kn="ದೇವಸ್ಥಾನದ ನೋಟ",
                image_url="/static/assets/gallery/temple-view.png",
                category="temple",
            ),
            GalleryItem(
                title_en="Temple Exterior",
                title_kn="ದೇವಸ್ಥಾನದ ಹೊರಾಂಗಣ",
                image_url="/static/assets/gallery/temple-exterior.png",
                category="temple",
            ),
            GalleryItem(
                title_en="Temple Interior",
                title_kn="ದೇವಸ್ಥಾನದ ಒಳಾಂಗಣ",
                image_url="/static/assets/gallery/temple-interior.png",
                category="temple,pooja",
            ),
            GalleryItem(
                title_en="Sacred Shrine",
                title_kn="ಪವಿತ್ರ ಸನ್ನಿಧಿ",
                image_url="/static/assets/gallery/sacred-shrine.png",
                category="pooja",
            ),
            GalleryItem(
                title_en="Deity Shrine",
                title_kn="ದೇವರ ಸನ್ನಿಧಿ",
                image_url="/static/assets/gallery/deity-shrine.png",
                category="temple,pooja",
            ),
            GalleryItem(
                title_en="Temple Pooja",
                title_kn="ದೇವಸ್ಥಾನದ ಪೂಜೆ",
                image_url="/static/assets/gallery/temple-pooja.png",
                category="pooja",
            ),
        ]
        for item in gallery_items:
            await item.insert()
        print("Real temple gallery photographs seeded successfully (7 images)")


