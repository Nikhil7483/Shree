# Full-Stack System Architecture

**Shree Shanishwara Swamy Temple Website**  
**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

---

## 1. Architectural Overview

The Shree Shanishwara Swamy Temple system is built as a high-performance, asynchronous full-stack web application designed for reliability, fast load times, and bilingual accessibility (English & Kannada).

```
                      +------------------------------------------+
                      |               Client Browser             |
                      |   (Desktop, Tablet, Mobile Devotees)     |
                      +--------------------+---------------------+
                                           |
                                   HTTP / HTTPS
                                           |
                                           v
                      +------------------------------------------+
                      |            FastAPI Application           |
                      |       (Uvicorn ASGI Server @ :8000)      |
                      +--------------------+---------------------+
                                           |
             +-----------------------------+-----------------------------+
             |                             |                             |
             v                             v                             v
+------------------------+    +------------------------+    +------------------------+
|    Static File Engine  |    |     REST API Routers   |    |  PDF Receipt Pipeline  |
|  (/static -> frontend) |    |      (/api/* routes)   |    |  (ReportLab + HarfBuzz)|
|  - HTML Pages (pages/) |    |  - Auth & JWT Security |    |  - FreeType Ligatures  |
|  - CSS Design Tokens   |    |  - Temple & Festivals  |    |  - Offline Vector QR   |
|  - JS Runtime & i18n   |    |  - Gallery Management  |    |  - Single-Page A4      |
|  - Photography Assets  |    |  - Donations & Razorpay|    +------------------------+
+------------------------+    |  - Admin Dashboard     |
                              +------------+-----------+
                                           |
                                           v
                              +------------------------+
                              |    Beanie ODM Layer    |
                              |   (Motor Async Driver) |
                              +------------+-----------+
                                           |
                                           v
                              +------------------------+
                              |    MongoDB Database    |
                              |      (shree_temple)    |
                              +------------------------+
```

---

## 2. Directory Structure & Layer Responsibilities

```
temple-website/
├── frontend/                     # Client Presentation Layer
│   ├── index.html                # Main landing page
│   ├── pages/                    # Domain views & secondary pages
│   │   ├── about.html            # History, lineage, and sanctum details
│   │   ├── contact.html          # Temple location, phone, and inquiry form
│   │   ├── dashboard.html        # Devotee portal with personal donation history
│   │   ├── donate.html           # Razorpay donation interface with seva selection
│   │   ├── festivals.html        # Annual temple celebration calendar
│   │   ├── gallery.html          # Categorized image gallery with lightbox
│   │   ├── login.html            # Devotee authentication
│   │   ├── register.html         # Devotee registration
│   │   ├── temple-info.html      # Comprehensive temple architectural & document guide
│   │   └── timings.html          # Daily darshan, abhisheka, and pooja timings
│   ├── admin/                    # Administrative Control Panel views
│   │   ├── index.html            # Admin metrics & analytics dashboard
│   │   ├── donations.html        # Comprehensive transaction manager & report export
│   │   ├── festivals.html        # Festival creation & management
│   │   ├── temple.html           # Quick temple timings and contact editor
│   │   ├── temple-info.html      # Full temple rich content editor
│   │   └── users.html            # Devotee accounts & access manager
│   ├── components/               # Modular frontend component specifications
│   ├── css/                      # Stylesheets & Visual Design System
│   │   ├── style.css             # Base reset, typography, responsive grid, color tokens
│   │   ├── components.css        # Cards, modals, buttons, forms, badges, headers
│   │   └── admin.css             # Data tables, KPI widgets, sidebar navigation
│   ├── js/                       # Client Logic & State Management
│   │   ├── app.js                # Core UI router, navbar/footer injection, modals
│   │   ├── i18n.js               # Comprehensive English <-> Kannada bilingual translation
│   │   ├── auth.js               # JWT storage, session handling, login/register logic
│   │   └── admin.js              # Admin API client, dynamic tables, stats charts
│   └── assets/                   # Static Visual Media
│       ├── gallery/              # Original high-resolution temple photographs
│       ├── documents/            # Official registration certificates & appeals
│       ├── logos/                # Vector temple insignia and favicons
│       ├── qr/                   # UPI payment QR presets and verification specs
│       ├── fonts/                # Unicode Kannada TrueType font bundles
│       └── uploads/              # Dynamic uploaded media
│
├── backend/                      # Server Application Layer
│   ├── app/                      # Application Package
│   │   ├── main.py               # FastAPI entry point, static mount, page routes
│   │   ├── config.py             # Re-exported settings facade
│   │   ├── api/                  # Unified API router registry
│   │   ├── routes/               # Route handlers interface
│   │   ├── services/             # Service business logic interface
│   │   ├── models/               # ODM data models interface
│   │   ├── database/             # Database initialization facade
│   │   ├── payments/             # Razorpay payment verification interface
│   │   ├── receipts/             # PDF receipt generation interface
│   │   ├── core/                 # Core security, JWT, and config settings
│   │   ├── db/                   # MongoDB connection lifecycle & default seed data
│   │   ├── domain/               # Domain-driven feature implementations
│   │   │   ├── admin/            # Dashboard analytics & aggregation queries
│   │   │   ├── auth/             # Login, registration, token generation
│   │   │   ├── donations/        # Razorpay integration, receipts, donation schemas
│   │   │   ├── festivals/        # Festival calendar models & CRUD
│   │   │   ├── gallery/          # Media gallery models & upload handlers
│   │   │   ├── temple/           # Singleton temple profile & timings models
│   │   │   └── users/            # Devotee profile management
│   │   └── utils/                # PDF receipt generator & HarfBuzz font shaping
│   ├── uploads/                  # Server-side persistent file storage
│   ├── tests/                    # Automated regression & integration test suite
│   ├── requirements.txt          # Python dependencies
│   └── README.md                 # Backend developer guide
│
├── docs/                         # Technical Architecture & Operations Documentation
├── scripts/                      # PowerShell & automation deployment scripts
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git tracking rules
└── README.md                     # Root project documentation
```

---

## 3. Request Lifecycle & Routing

1. **Incoming Request:** Devotee or administrator accesses `https://example.com/donate`.
2. **FastAPI Route Resolver:** The request matches `app.get("/donate")` in `backend/app/main.py`.
3. **Resilient Page Resolver:** `get_page_path("donate.html")` locates `frontend/pages/donate.html` (falling back to `frontend/donate.html` if required) and returns it with HTTP 200.
4. **Static Assets:** The browser downloads `/static/css/style.css`, `/static/js/app.js`, and `/static/js/i18n.js`.
5. **Client-Side Hydration:**
   - `app.js` renders the universal Header and Footer into the DOM placeholders.
   - `i18n.js` checks `localStorage.getItem("temple_lang")` and populates bilingual strings instantly.
6. **API Transactions:** When the user initiates a donation, `POST /api/donate/create-order` creates a Razorpay payment order and stores a pending donation document in MongoDB.
7. **Receipt Generation:** Upon successful payment verification (`POST /api/donate/verify`), the server completes the donation and generates an official bilingual PDF donation receipt on-demand via `GET /api/donate/receipt/{id}`.
