# Shree Shanishwara Swamy Temple — Website

**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**  
*A bilingual (English / Kannada) temple information, devotee portal, and online donation system.*

---

## 🙏 Features

- **Temple Information**: History, traditions, trust details, and sacred sanctum information.
- **Gallery**: High-resolution image gallery with category filters and lightbox view.
- **Darshan Timings**: Dynamic daily schedules, abhisheka, and pooja timings managed by administration.
- **Festival Calendar**: Comprehensive temple celebrations calendar with dates and Kannada descriptions.
- **Online Donations**: Seamless Razorpay payment gateway integration supporting 5 sacred seva types.
- **Bilingual PDF Receipts**: Downloadable single-page A4 donation receipts rendered with HarfBuzz Kannada typography, native offline vector QR code verification, and temple trust insignia.
- **User Accounts**: Devotee registration, authentication, personal dashboard, and donation history.
- **Admin Control Panel**: Real-time KPI analytics, donor history management, festival manager, and PDF export reports.
- **Bilingual i18n Engine**: Seamless instant English ↔ ಕನ್ನಡ translation switching across the entire UI.
- **Responsive Aesthetics**: Saffron and gold traditional temple elegance optimized for desktop, tablet, and mobile.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | Vanilla client-side architecture with instant i18n |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous REST API server |
| **Database** | MongoDB 6.0+, Beanie ODM, Motor | Asynchronous document database for donations & temple info |
| **Auth** | JWT (python-jose) + Passlib (bcrypt) | Stateless secure session tokens & password hashing |
| **Payments** | Razorpay Python SDK | Secure online donation processing |
| **PDF Generation** | ReportLab 4.2.2 + HarfBuzz + FreeType | Publication-grade bilingual Kannada & English typography |
| **Testing** | Pytest, HTTPX | Automated integration & regression test suite |

---

## 📁 Project Structure

```
temple-website/
├── frontend/                     # Client Presentation Layer
│   ├── index.html                # Main landing page
│   ├── pages/                    # Domain views & secondary pages
│   │   ├── about.html            # Temple history, committee & sanctum details
│   │   ├── contact.html          # Contacts, map location & inquiry form
│   │   ├── dashboard.html        # Devotee portal with personal donation history
│   │   ├── donate.html           # Razorpay online donation interface
│   │   ├── festivals.html        # Annual celebration calendar
│   │   ├── gallery.html          # Categorized image gallery with lightbox
│   │   ├── login.html            # Devotee & admin authentication
│   │   ├── register.html         # Devotee registration
│   │   ├── temple-info.html      # Temple architectural guide & document reader
│   │   └── timings.html          # Darshan, abhisheka & pooja schedules
│   ├── admin/                    # Administrative Control Panel
│   │   ├── index.html            # Metrics & analytics dashboard
│   │   ├── donations.html        # Donation ledger & PDF report generator
│   │   ├── festivals.html        # Festival creation & management
│   │   ├── temple.html           # Quick timings & contact editor
│   │   ├── temple-info.html      # Rich content management
│   │   └── users.html            # User account directory
│   ├── components/               # Modular UI component specifications
│   ├── css/                      # Stylesheets & Visual Design System
│   │   ├── style.css             # Base reset, typography, responsive layout
│   │   ├── components.css        # Cards, modals, buttons, forms, badges
│   │   └── admin.css             # Admin dashboard tables & metric widgets
│   ├── js/                       # Client-Side Application Logic
│   │   ├── app.js                # Core UI router, navbar/footer, modals
│   │   ├── i18n.js               # English <-> Kannada bilingual translation
│   │   ├── auth.js               # JWT storage, session handling
│   │   └── admin.js              # Admin API client & dynamic data tables
│   ├── assets/                   # Media & Design Assets
│   │   ├── gallery/              # High-resolution authentic temple photographs
│   │   ├── documents/            # Official temple appeal & registration documents
│   │   ├── logos/                # Vector temple insignia and favicons
│   │   ├── qr/                   # UPI payment QR presets and verification specs
│   │   ├── fonts/                # Unicode Kannada TrueType font bundles
│   │   └── uploads/              # Dynamic uploaded media
│   └── README.md                 # Frontend developer guide
│
├── backend/                      # Server Application Layer
│   ├── app/                      # Application Package
│   │   ├── main.py               # FastAPI entry point, static mount, page routing
│   │   ├── config.py             # Re-exported configuration interface
│   │   ├── api/                  # Unified API router interface (includes /api/*)
│   │   ├── routes/               # Modular router export interface
│   │   ├── services/             # Domain business logic service interface
│   │   ├── models/               # Beanie ODM document models interface
│   │   ├── database/             # Database initialization interface
│   │   ├── payments/             # Razorpay order creation & payment verification
│   │   ├── receipts/             # Bilingual PDF receipt generation interface
│   │   ├── core/                 # Core security, dependencies, and settings
│   │   ├── db/                   # Database connection lifecycle & default seed data
│   │   ├── domain/               # Domain-driven feature implementations
│   │   │   ├── admin/            # Dashboard stats and report aggregation
│   │   │   ├── auth/             # Login, registration, token issuance
│   │   │   ├── donations/        # Razorpay checkout, models, receipts
│   │   │   ├── festivals/        # Festival calendar models & CRUD routes
│   │   │   ├── gallery/          # Media gallery models & upload handlers
│   │   │   ├── temple/           # Singleton temple profile & timings models
│   │   │   └── users/            # Devotee profile management
│   │   └── utils/                # Utility modules (pdf_receipt, download_fonts)
│   ├── tests/                    # Automated regression & integration test suite
│   ├── uploads/                  # Server-side upload directory
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── README.md                 # Backend developer guide
│
├── docs/                         # Technical Architecture & Operations Documentation
│   ├── architecture.md           # Full-stack system architecture & data flow
│   ├── api.md                    # REST API endpoints specification
│   ├── receipt-system.md         # HarfBuzz Kannada PDF receipt engine guide
│   ├── database.md               # MongoDB collections & Beanie ODM models
│   └── deployment.md             # Production deployment guide
│
├── scripts/                      # PowerShell & Automation Deployment Scripts
│   ├── run_backend.ps1           # Production backend server launcher
│   ├── run_dev.ps1               # Local development launcher with hot reload
│   ├── test_receipts.ps1         # PDF receipt test runner
│   └── download_fonts.ps1        # Font download utility
│
├── .env.example                  # Root environment configuration template
├── .gitignore                    # Version control ignore rules
└── README.md                     # Root project documentation
```

---

## 📋 Prerequisites

- **Python 3.10+** (Python 3.11 / 3.12 recommended)
- **MongoDB 6.0+** running locally on `localhost:27017` or a MongoDB Atlas connection string

---

## 🚀 Setup & Run

### 1. Configure Environment
Copy `.env.example` to `backend/.env` and update the placeholder values:
```bash
cp .env.example backend/.env
```

### 2. Setup Virtual Environment & Dependencies
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Install all dependencies:
pip install -r requirements.txt
```

### 3. Run the Backend & Frontend

#### Option A: Unified Full-Stack Run via FastAPI (Recommended)
FastAPI serves the entire frontend with clean URLs (`/`, `/about`, `/donate`):
```bash
# From the backend directory:
uvicorn app.main:app --reload --port 8000
```
Or using the provided PowerShell script from project root:
```powershell
.\scripts\run_backend.ps1
```
Open **http://localhost:8000** in your browser.

#### Option B: Run Frontend Separately
If developing frontend assets independently:
```bash
# Terminal 1 — Backend:
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend:
cd frontend
python -m http.server 3000
```
Open **http://localhost:3000** in your browser.

---

## 🧪 Testing & Verification

Run the automated test suite:
```bash
cd backend
pytest -v tests
```
Or run the receipt visual verification suite:
```powershell
.\scripts\test_receipts.ps1
```

---

## 👤 Default Administrator Credentials

When the backend initializes for the first time, it automatically creates the default administrator account:
- **Email**: `admin@shreeshani.com`
- **Password**: `Admin@123`
- **Admin Panel**: `http://localhost:8000/admin`

---

## 📖 Technical Documentation

- [Full-Stack Architecture](docs/architecture.md)
- [REST API Reference](docs/api.md)
- [Bilingual PDF Receipt Engine](docs/receipt-system.md)
- [Database Schema & Models](docs/database.md)
- [Production Deployment Guide](docs/deployment.md)

---

**ॐ ಶ್ರೀ ಶನೀಶ್ವರಾಯ ನಮಃ 🙏**
