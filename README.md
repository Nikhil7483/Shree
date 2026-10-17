# Shree Shanishwara Swamy Temple — Website

**ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ**

A bilingual (English / Kannada) temple information and online donation website.

## 🙏 Features

- **Temple Information**: History, traditions, vision & mission
- **Gallery**: Image gallery with category filters and lightbox
- **Darshan Timings**: Dynamic timings updated by admin
- **Festival Calendar**: All temple festivals with descriptions
- **Online Donations**: Razorpay payment integration with 5 donation types
- **PDF Receipts**: Downloadable branded donation receipts
- **User Accounts**: Registration, login, donation history
- **Admin Panel**: Dashboard, manage temple/festivals/donations/users
- **Bilingual**: Complete English ↔ ಕನ್ನಡ support with instant switching
- **Responsive**: Works on desktop, tablet, and mobile

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, FastAPI |
| Database | MongoDB (Beanie ODM) |
| Auth | JWT + bcrypt |
| Payments | Razorpay API |
| PDF | ReportLab |

## 📋 Prerequisites

- **Python 3.10+**
- **MongoDB** (local or Atlas)

## 🚀 Setup & Run

### 1. Clone & Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Key variables to update:
- `MONGODB_URL` — your MongoDB connection string
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — Razorpay API keys
- `JWT_SECRET_KEY` — change for production

### 3. Start the Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Open in Browser

Visit **http://localhost:8000**

## 👤 Default Admin

- **Email**: `admin@shreeshani.com`
- **Password**: `Admin@123`

## 📁 Project Structure

```
Shree/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── core/            # Config, security, dependencies
│   │   ├── db/              # Database initialization
│   │   ├── domain/          # Feature modules
│   │   │   ├── auth/        # Login & registration
│   │   │   ├── temple/      # Temple info management
│   │   │   ├── gallery/     # Image gallery
│   │   │   ├── festivals/   # Festival management
│   │   │   ├── donations/   # Donation system
│   │   │   ├── users/       # User management
│   │   │   └── admin/       # Admin dashboard
│   │   └── utils/           # PDF receipt generator
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html           # Home page
│   ├── about.html           # About temple
│   ├── gallery.html         # Gallery
│   ├── timings.html         # Temple timings
│   ├── festivals.html       # Festivals
│   ├── donate.html          # Donation page
│   ├── login.html           # Login
│   ├── register.html        # Registration
│   ├── dashboard.html       # User dashboard
│   ├── contact.html         # Contact
│   ├── admin/               # Admin panel pages
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript
│   └── assets/              # Images & fonts
└── README.md
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| GET | `/api/temple` | Get temple info |
| PUT | `/api/temple` | Update temple (admin) |
| GET | `/api/gallery` | Get gallery items |
| GET | `/api/festivals` | Get festivals |
| POST | `/api/donate/create-order` | Create donation order |
| POST | `/api/donate/verify` | Verify payment |
| GET | `/api/donate/history` | User donation history |
| GET | `/api/donate/receipt/{id}` | Download PDF receipt |
| GET | `/api/admin/dashboard` | Admin stats |
| GET | `/api/users/all` | List users (admin) |

## 🎨 Design

- **Colors**: Saffron, Gold, Maroon, Dark Brown, Warm White
- **Fonts**: Poppins (English), Noto Sans Kannada (Kannada)
- **Style**: Traditional temple elegance with modern premium feel

---

**ॐ ಶ್ರೀ ಶನೀಶ್ವರಾಯ ನಮಃ 🙏**
