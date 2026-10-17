# Frontend Architecture & Developer Guide

**Shree Shanishwara Swamy Temple Website**  
**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

---

## 1. Directory Structure

```
frontend/
├── index.html            # Landing / Homepage (Hero banner, about summary, gallery preview, quick darshan)
├── pages/                # Secondary Content & Feature Views
│   ├── about.html        # Sacred history, origins, committee details, and lineage
│   ├── contact.html      # Temple contacts, interactive Google Maps location, and inquiry form
│   ├── dashboard.html    # Devotee portal with personal profile and donation history
│   ├── donate.html       # Online donation interface with seva selection & Razorpay checkout
│   ├── festivals.html    # Annual festival calendar with auspicious tithis and celebrations
│   ├── gallery.html      # Filterable image gallery with lightbox
│   ├── login.html        # Devotee and administrator login page
│   ├── register.html     # New devotee registration form
│   ├── temple-info.html  # Comprehensive architectural guide & official document reader
│   └── timings.html      # Darshan, abhisheka, and pooja schedules
│
├── admin/                # Admin Panel Interface
│   ├── index.html        # Analytics KPI metrics & recent transactions
│   ├── donations.html    # Donation ledger, CSV export, and PDF report generator
│   ├── festivals.html    # Festival creation, editing, and publishing
│   ├── temple.html       # Quick timings and contact editor
│   ├── temple-info.html  # Full rich text temple content management
│   └── users.html        # Devotee accounts directory
│
├── components/           # Reusable UI component definitions & documentation
├── css/                  # Stylesheets & Visual Design System
│   ├── style.css         # Reset, CSS variables, typography, layout grid
│   ├── components.css    # Reusable UI components (cards, modals, badges, hero)
│   └── admin.css         # Admin dashboard tables, sidebar, and metric widgets
│
├── js/                   # Client-Side Application Logic
│   ├── app.js            # Global UI controller, dynamic navbar/footer injection, modals
│   ├── i18n.js           # Bilingual dictionary (English <-> Kannada) and DOM translator
│   ├── auth.js           # Devotee authentication, token storage, and session guards
│   └── admin.js          # Admin dashboard client, CRUD operations, dynamic tables
│
└── assets/               # Media & Design Assets
    ├── gallery/          # High-resolution authentic temple photographs
    ├── documents/        # Official temple appeal and registration documents
    ├── logos/            # Vector temple insignia and icons
    ├── qr/               # UPI payment QR presets and verification specs
    ├── fonts/            # Unicode Kannada TrueType font files
    └── uploads/          # Dynamic media uploaded by admins/devotees
```

---

## 2. Visual Design System & Aesthetics

- **Color Palette:**
  - Primary Saffron: `#FF9933` / `#E67E22`
  - Temple Gold: `#D4AF37` / `#FFD700`
  - Sacred Maroon / Deep Red: `#800000` / `#990000`
  - Dark Brown / Sanctum Green: `#1A1108` / `#052E20`
  - Background Warm White: `#FDFBF7` / `#F8F5EE`
- **Typography:**
  - English: Modern clean sans-serif (`Poppins`, `Inter`, `system-ui`)
  - Kannada: `Noto Sans Kannada`, `Nirmala UI`, `sans-serif`
- **Bilingual i18n Engine:**
  - Instant client-side language switching between English and ಕನ್ನಡ without full page reload.
  - Persists preference in `localStorage.getItem("temple_lang")`.
  - DOM elements using `data-i18n="key"` automatically translate upon toggle.

---

## 3. How to Run Locally

### Option A: Via FastAPI (Recommended)
FastAPI serves the frontend with clean URLs (`/`, `/about`, `/donate`):
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
Open **http://localhost:8000** in your browser.

### Option B: Standalone Web Server
You can also preview frontend files using Python's built-in HTTP server or VS Code Live Server:
```bash
cd frontend
python -m http.server 3000
```
*(Note: API interactions and PDF receipts require the backend to be running on port 8000).*
