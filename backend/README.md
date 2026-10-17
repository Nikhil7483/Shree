# Backend Architecture & Developer Guide

**Shree Shanishwara Swamy Temple Website**  
**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

---

## 1. Tech Stack

- **Runtime:** Python 3.10+
- **Web Framework:** FastAPI (Asynchronous ASGI)
- **ASGI Server:** Uvicorn
- **Database:** MongoDB (using Motor async driver and Beanie ODM)
- **Authentication:** JWT (JSON Web Tokens) with Passlib bcrypt password hashing
- **Payment Gateway:** Razorpay Python SDK
- **PDF Generation & Typography:** ReportLab 4.2.2 + HarfBuzz (`uharfbuzz`) + FreeType (`freetype-py`) + PyPDF
- **Testing:** Pytest + HTTPX

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py               # Application factory, lifespan, static mounting, page routing
│   ├── config.py             # Re-exported configuration interface
│   ├── api/                  # Unified API router interface (includes /api/*)
│   ├── routes/               # Modular router export interface
│   ├── services/             # Domain business logic service interface
│   ├── models/               # Beanie ODM document models interface
│   ├── database/             # Database initialization interface
│   ├── payments/             # Razorpay order creation & payment verification
│   ├── receipts/             # Bilingual PDF receipt generation interface
│   ├── core/                 # Core security, dependencies, and pydantic settings
│   │   ├── config.py         # Settings class with pydantic-settings
│   │   ├── dependencies.py   # FastAPI dependency injections (current_user, require_admin)
│   │   └── security.py       # Password hashing & JWT creation/verification
│   ├── db/                   # Database connection lifecycle & default seed data
│   │   └── init_db.py        # Initializes Beanie models & seeds default admin/temple
│   ├── domain/               # Domain-driven feature implementations
│   │   ├── admin/            # Dashboard stats and report aggregation
│   │   ├── auth/             # Login, registration, token issuance
│   │   ├── donations/        # Razorpay checkout, models, receipts, donor history
│   │   ├── festivals/        # Festival calendar models & CRUD routes
│   │   ├── gallery/          # Media gallery models & upload handlers
│   │   ├── temple/           # Singleton temple profile & timings models
│   │   └── users/            # Devotee profile management
│   └── utils/                # Utility modules
│       ├── pdf_receipt.py    # HarfBuzz OpenType shaped Kannada PDF receipt generator
│       └── download_fonts.py # Automated font downloader for NotoSansKannada
├── tests/                    # Automated Test Suite
│   ├── test_api_endpoints.py # Tests all HTML page routes and REST API endpoints
│   ├── test_auth_security.py # Tests bcrypt hashing and JWT token operations
│   ├── test_receipt_generator.py # Tests PDF receipt generation, edge cases, and reports
│   └── test_receipt_inspection.py # Visual inspection rendering tool
├── uploads/                  # Server-side upload directory
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This developer guide
```

---

## 3. Quick Start & Setup

### 1. Setup Virtual Environment
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure MongoDB is running locally (`mongodb://localhost:27017`) or configure your MongoDB Atlas connection string.

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Open **http://127.0.0.1:8000** in your browser.  
Interactive OpenAPI documentation: **http://127.0.0.1:8000/docs**

---

## 4. Running Tests

Run the full automated test suite using pytest:
```bash
pytest -v tests
```
Or run the receipt visual verification script:
```bash
python tests/test_receipt_inspection.py
```
*(Generates sample PDFs and rendered PNGs for visual inspection).*
