"""
ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) — Shree Shanishwara Swamy Temple (R.)
ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ
FastAPI Application Entry Point

This module initializes the FastAPI application, sets up the database,
registers all API routers, and serves the static frontend.
"""

import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse

from app.core.config import get_settings
from app.db.init_db import init_db
from app.domain.auth.router import router as auth_router
from app.domain.temple.router import router as temple_router
from app.domain.gallery.router import router as gallery_router
from app.domain.festivals.router import router as festivals_router
from app.domain.donations.router import router as donations_router
from app.domain.users.router import router as users_router
from app.domain.admin.router import router as admin_router

# Path to frontend and pages directories
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")


def get_page_path(*path_parts: str) -> str:
    """
    Locate a frontend HTML file with backward compatibility:
    Checks frontend/pages/ first, falling back to frontend/.
    """
    candidate_in_pages = os.path.join(PAGES_DIR, *path_parts)
    if os.path.exists(candidate_in_pages):
        return candidate_in_pages
    return os.path.join(FRONTEND_DIR, *path_parts)


async def init_db_safe():
    """Background task to initialize DB and seed data without blocking web server startup."""
    for attempt in range(1, 30):
        try:
            print(f"[DB] Initializing database (attempt {attempt})...")
            await init_db()
            print("[DB] Database initialized successfully!")
            return
        except Exception as exc:
            print(f"[DB] Attempt {attempt} waiting for MongoDB: {exc}. Retrying in 4s...")
            await asyncio.sleep(4)
    print("[DB ERROR] Could not connect to MongoDB after retries. Operating in static/offline mode.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: starts web server immediately and initializes DB in background."""
    print("Starting Shree Shanishwara Swamy Temple Server...")
    # Launch database initialization in background so healthcheck passes instantly
    db_task = asyncio.create_task(init_db_safe())
    print("Web server ready to accept incoming traffic.")
    yield
    print("Server shutting down...")
    db_task.cancel()


settings = get_settings()
is_prod = settings.APP_ENV.lower() == "production"

app = FastAPI(
    title="ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) — Shree Shanishwara Swamy Temple (R.)",
    description="ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) • Shree Shanishwara Swamy Temple - Temple Information & Donation API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if (not is_prod or settings.ENABLE_DOCS) else None,
    redoc_url="/redoc" if (not is_prod or settings.ENABLE_DOCS) else None,
    openapi_url="/openapi.json" if (not is_prod or settings.ENABLE_DOCS) else None,
)

# CORS middleware — production domain restriction or local wildcard
cors_origins = (
    ["*"]
    if settings.ALLOWED_ORIGINS.strip() == "*"
    else [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
)
allow_credentials = False if "*" in cors_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback
    trace = traceback.format_exc()
    print(f"[UNHANDLED EXCEPTION] {request.method} {request.url.path}: {exc}\n{trace}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Register API routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(temple_router, prefix="/api")
app.include_router(gallery_router, prefix="/api")
app.include_router(festivals_router, prefix="/api")
app.include_router(donations_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Ensure uploads directory exists
uploads_dir = os.path.join(FRONTEND_DIR, "assets", "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Mount static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# --- Healthcheck Endpoint ---

@app.get("/health")
async def health_check():
    """Lightweight healthcheck endpoint for Railway / Cloud load balancers."""
    db_status = "offline"
    admin_info = None
    try:
        from app.domain.users.models import User
        admin = await User.find_one({"role": "admin"})
        db_status = "connected"
        admin_info = admin.email if admin else "none"
    except Exception as e:
        admin_info = f"err: {str(e)}"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "database": db_status,
        "active_admin": admin_info,
    }


# --- Serve Frontend HTML Pages ---

@app.get("/")
async def serve_home():
    """Serve the home page."""
    return FileResponse(get_page_path("index.html"))


@app.get("/about")
async def serve_about():
    return FileResponse(get_page_path("about.html"))


@app.get("/gallery")
async def serve_gallery():
    return FileResponse(get_page_path("gallery.html"))


@app.get("/timings")
async def serve_timings():
    return FileResponse(get_page_path("timings.html"))


@app.get("/festivals")
async def serve_festivals():
    return FileResponse(get_page_path("festivals.html"))


@app.get("/donate")
async def serve_donate():
    return FileResponse(get_page_path("donate.html"))


@app.get("/donations")
async def serve_donations_redirect():
    return RedirectResponse(url="/donate")


@app.get("/login")
async def serve_login():
    return FileResponse(get_page_path("login.html"))


@app.get("/register")
async def serve_register():
    return FileResponse(get_page_path("register.html"))


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(get_page_path("dashboard.html"))


@app.get("/contact")
async def serve_contact():
    return FileResponse(get_page_path("contact.html"))


@app.get("/temple-info")
async def serve_temple_info():
    return FileResponse(get_page_path("temple-info.html"))


# Admin pages
@app.get("/admin")
async def serve_admin_dashboard():
    return FileResponse(get_page_path("admin", "index.html"))


@app.get("/admin/temple")
async def serve_admin_temple():
    return FileResponse(get_page_path("admin", "temple.html"))


@app.get("/admin/temple-info")
async def serve_admin_temple_info():
    return FileResponse(get_page_path("admin", "temple-info.html"))


@app.get("/admin/donations")
async def serve_admin_donations():
    return FileResponse(get_page_path("admin", "donations.html"))


@app.get("/admin/users")
async def serve_admin_users():
    return FileResponse(get_page_path("admin", "users.html"))


@app.get("/admin/festivals")
async def serve_admin_festivals():
    return FileResponse(get_page_path("admin", "festivals.html"))


