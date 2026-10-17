"""
Shree Shanishwara Swamy Temple — FastAPI Application Entry Point

ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ), ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ

This module initializes the FastAPI application, sets up the database,
registers all API routers, and serves the static frontend.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.db.init_db import init_db
from app.domain.auth.router import router as auth_router
from app.domain.temple.router import router as temple_router
from app.domain.gallery.router import router as gallery_router
from app.domain.festivals.router import router as festivals_router
from app.domain.donations.router import router as donations_router
from app.domain.users.router import router as users_router
from app.domain.admin.router import router as admin_router

# Path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database on startup."""
    print("Starting Shree Shanishwara Swamy Temple Server...")
    await init_db()
    print("Database initialized successfully")
    print("Server is ready at http://localhost:8000")
    yield
    print("Server shutting down...")


app = FastAPI(
    title="Shree Shanishwara Swamy Temple",
    description="ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ - Temple Information & Donation API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware — allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

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


# --- Serve Frontend HTML Pages ---

@app.get("/")
async def serve_home():
    """Serve the home page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/about")
async def serve_about():
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))


@app.get("/gallery")
async def serve_gallery():
    return FileResponse(os.path.join(FRONTEND_DIR, "gallery.html"))


@app.get("/timings")
async def serve_timings():
    return FileResponse(os.path.join(FRONTEND_DIR, "timings.html"))


@app.get("/festivals")
async def serve_festivals():
    return FileResponse(os.path.join(FRONTEND_DIR, "festivals.html"))


@app.get("/donate")
async def serve_donate():
    return FileResponse(os.path.join(FRONTEND_DIR, "donate.html"))


@app.get("/donations")
async def serve_donations_redirect():
    return RedirectResponse(url="/donate")


@app.get("/login")
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/register")
async def serve_register():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/contact")
async def serve_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))


@app.get("/temple-info")
async def serve_temple_info():
    return FileResponse(os.path.join(FRONTEND_DIR, "temple-info.html"))


# Admin pages
@app.get("/admin")
async def serve_admin_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "index.html"))


@app.get("/admin/temple")
async def serve_admin_temple():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "temple.html"))


@app.get("/admin/temple-info")
async def serve_admin_temple_info():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "temple-info.html"))


@app.get("/admin/donations")
async def serve_admin_donations():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "donations.html"))


@app.get("/admin/users")
async def serve_admin_users():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "users.html"))


@app.get("/admin/festivals")
async def serve_admin_festivals():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "festivals.html"))

