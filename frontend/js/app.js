/**
 * ============================================================
 * app.js — Core Application Logic
 * ============================================================
 * Navigation, API helpers, scroll animations, toasts, mobile menu.
 * ============================================================
 */

const API_BASE = '/api';

// ============================
// API Helper
// ============================

/**
 * Make an authenticated API request.
 * @param {string} endpoint - API endpoint (e.g., '/temple')
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('temple_token');
    const headers = {
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Only set Content-Type for JSON requests (not FormData)
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401 && endpoint !== '/auth/login') {
        // Token expired or invalid
        localStorage.removeItem('temple_token');
        localStorage.removeItem('temple_user');
        window.location.href = '/login';
        return;
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }

    return data;
}

// ============================
// User State
// ============================

function getUser() {
    const user = localStorage.getItem('temple_user');
    return user ? JSON.parse(user) : null;
}

function isLoggedIn() {
    return !!localStorage.getItem('temple_token');
}

function isAdmin() {
    const user = getUser();
    return user && user.role === 'admin';
}

function logout() {
    localStorage.removeItem('temple_token');
    localStorage.removeItem('temple_user');
    showToast('Logged out successfully', 'success');
    setTimeout(() => window.location.href = '/', 500);
}

// ============================
// Navigation Renderer
// ============================

function renderNavbar() {
    const currentPage = window.location.pathname;
    const user = getUser();

    const logoSVG = `
    <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="temple-logo-svg">
      <circle cx="50" cy="50" r="46" fill="#0B3D2E" stroke="#D4AF37" stroke-width="4"/>
      <path d="M45 18 L50 8 L55 18 Z" fill="#D4AF37"/>
      <path d="M42 20 L58 20 L56 28 L44 28 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
      <path d="M38 30 L62 30 L59 42 L41 42 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
      <path d="M32 44 L68 44 L64 60 L36 60 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
      <path d="M26 62 L74 62 L74 80 L68 80 L68 66 L32 66 L32 80 L26 80 Z" fill="#D4AF37"/>
      <path d="M50 64 C46 70 46 76 50 78 C54 76 54 70 50 64 Z" fill="#FF8C00"/>
      <path d="M50 68 C48 72 48 75 50 76 C52 75 52 72 50 68 Z" fill="#FFD700"/>
      <path d="M42 78 L58 78 L55 82 L45 82 Z" fill="#D4AF37"/>
      <path d="M18 82 L82 82 L80 86 L20 86 Z" fill="#D4AF37"/>
    </svg>
    `;

    const navHTML = `
    <nav class="navbar ${currentPage === '/' ? 'transparent' : ''}" id="main-navbar">
        <div class="container">
            <a href="/" class="nav-brand">
                ${logoSVG}
                <span class="brand-text">
                    <span class="brand-title-kn">ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ (ರಿ)</span>
                    <small class="brand-sub-en">Shree Shanishwara Swamy Temple (R.)</small>
                </span>
            </a>

            <div class="nav-links">
                <a href="/" class="${currentPage === '/' ? 'active' : ''}" data-i18n="nav_home">Home</a>
                <a href="/about" class="${currentPage === '/about' ? 'active' : ''}" data-i18n="nav_about">About</a>
                <a href="/temple-info" class="${currentPage === '/temple-info' ? 'active' : ''}" data-i18n="nav_temple_info">ದೇವಸ್ಥಾನದ ಮಾಹಿತಿ</a>
                <a href="/timings" class="${currentPage === '/timings' ? 'active' : ''}" data-i18n="nav_timings">Timings</a>
                <a href="/contact" class="${currentPage === '/contact' ? 'active' : ''}" data-i18n="nav_contact">Contact</a>
                ${user ? `<a href="/dashboard" class="${currentPage === '/dashboard' ? 'active' : ''}" data-i18n="nav_dashboard">Dashboard</a>` : ''}
                ${user && user.role === 'admin' ? `<a href="/admin" class="${currentPage.startsWith('/admin') ? 'active' : ''}" data-i18n="nav_admin">Admin</a>` : ''}
            </div>

            <div class="nav-actions">
                <button class="lang-toggle" id="lang-toggle" onclick="toggleLanguage()" data-i18n="lang_switch">ಕನ್ನಡ</button>
                ${user
                    ? `
                       <div class="user-profile-menu">
                           <button class="avatar-btn" onclick="toggleProfileDropdown(event)">
                               ${user.photo_url 
                                   ? `<img src="${user.photo_url}" alt="${user.name}" class="avatar-img">`
                                   : `<div class="avatar-initials">${getUserInitials(user.name)}</div>`
                               }
                           </button>
                           <div class="profile-dropdown" id="profile-dropdown">
                               <div class="dropdown-header">
                                   <span class="user-name">${user.name}</span>
                                   <span class="user-email">${user.email}</span>
                               </div>
                               <div class="dropdown-divider"></div>
                               <a href="/dashboard?tab=profile" class="dropdown-item">👤 <span data-i18n="menu_profile">My Profile</span></a>
                               <a href="/dashboard?tab=donations" class="dropdown-item">📜 <span data-i18n="menu_history">Donations</span></a>
                               <a href="/dashboard?tab=profile" class="dropdown-item">⚙️ <span data-i18n="menu_settings">Settings</span></a>
                               <div class="dropdown-divider"></div>
                               <button onclick="logout()" class="dropdown-item logout-btn">🚪 <span data-i18n="nav_logout">Logout</span></button>
                           </div>
                       </div>
                       `
                    : `<a href="/login" class="nav-auth-btn" data-i18n="nav_login">Login</a>
                       <a href="/donate" class="btn btn-primary btn-sm nav-donate-btn" data-i18n="nav_donate">Donate</a>`
                }
                <button class="mobile-menu-btn" onclick="toggleMobileMenu()" aria-label="Menu">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </div>
    </nav>

    <div class="mobile-nav" id="mobile-nav">
        <div class="mobile-nav-header">
            <span class="menu-title" data-i18n="nav_menu">MENU</span>
            <button class="mobile-nav-close" onclick="toggleMobileMenu()">✕</button>
        </div>
        <a href="/" ${currentPage === '/' ? 'class="active"' : ''} data-i18n="nav_home">Home</a>
        <a href="/about" ${currentPage === '/about' ? 'class="active"' : ''} data-i18n="nav_about">About</a>
        <a href="/timings" ${currentPage === '/timings' ? 'class="active"' : ''} data-i18n="nav_timings">Timings</a>
        <a href="/contact" ${currentPage === '/contact' ? 'class="active"' : ''} data-i18n="nav_contact">Contact</a>
        <a href="/donate" ${currentPage === '/donate' ? 'class="active"' : ''} data-i18n="nav_donate">Donate</a>
        ${user ? `<a href="/dashboard" ${currentPage === '/dashboard' ? 'class="active"' : ''} data-i18n="nav_dashboard">Dashboard</a>` : ''}
        ${user && user.role === 'admin' ? `<a href="/admin" ${currentPage.startsWith('/admin') ? 'class="active"' : ''} data-i18n="nav_admin">Admin</a>` : ''}
        ${user
            ? `<a href="#" onclick="logout()" data-i18n="nav_logout">Logout</a>`
            : `<a href="/login" ${currentPage === '/login' ? 'class="active"' : ''} data-i18n="nav_login">Login</a>`
        }
    </div>
    `;

    // Insert navbar at top of body
    const navContainer = document.getElementById('navbar-container');
    if (navContainer) {
        navContainer.innerHTML = navHTML;
    }
}

// ============================
// Footer Renderer
// ============================

function renderFooter() {
    const footerHTML = `
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-brand">
                    <div class="temple-icon">
                        <svg width="50" height="50" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="temple-logo-svg">
                          <circle cx="50" cy="50" r="46" fill="#0B3D2E" stroke="#D4AF37" stroke-width="4"/>
                          <path d="M45 18 L50 8 L55 18 Z" fill="#D4AF37"/>
                          <path d="M42 20 L58 20 L56 28 L44 28 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
                          <path d="M38 30 L62 30 L59 42 L41 42 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
                          <path d="M32 44 L68 44 L64 60 L36 60 Z" fill="#D4AF37" stroke="#0B3D2E" stroke-width="0.5"/>
                          <path d="M26 62 L74 62 L74 80 L68 80 L68 66 L32 66 L32 80 L26 80 Z" fill="#D4AF37"/>
                          <path d="M50 64 C46 70 46 76 50 78 C54 76 54 70 50 64 Z" fill="#FF8C00"/>
                          <path d="M50 68 C48 72 48 75 50 76 C52 75 52 72 50 68 Z" fill="#FFD700"/>
                          <path d="M42 78 L58 78 L55 82 L45 82 Z" fill="#D4AF37"/>
                          <path d="M18 82 L82 82 L80 86 L20 86 Z" fill="#D4AF37"/>
                        </svg>
                    </div>
                    <div class="brand-name-kn">ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ)</div>
                    <div class="brand-name">Shree Shanishwara Swamy Temple (R.)</div>
                    <p data-i18n="footer_about">A sacred temple dedicated to Lord Shanishwara, located at the divine Siddagiri hill.</p>
                    <div class="social-links" style="display:flex;gap:var(--space-sm);margin-top:var(--space-md);">
                        <a href="#" style="font-size:1.4rem;" title="Facebook">🌐</a>
                        <a href="#" style="font-size:1.4rem;" title="YouTube">📺</a>
                        <a href="#" style="font-size:1.4rem;" title="Instagram">📸</a>
                    </div>
                </div>

                <div class="footer-links">
                    <h4 data-i18n="footer_quick_links">Quick Links</h4>
                    <a href="/" data-i18n="nav_home">Home</a>
                    <a href="/about" data-i18n="nav_about">About</a>
                    <a href="/temple-info" data-i18n="nav_temple_info">ದೇವಸ್ಥಾನದ ಮಾಹಿತಿ</a>
                    <a href="/gallery" data-i18n="nav_gallery">Gallery</a>
                    <a href="/donate" data-i18n="nav_donate">Donate</a>
                </div>

                <div class="footer-links">
                    <h4 data-i18n="footer_timings">Temple Timings</h4>
                    <a href="/timings" data-i18n="nav_timings">Timings</a>
                    <a href="/festivals" data-i18n="nav_festivals">Festivals</a>
                    <a href="/contact" data-i18n="nav_contact">Contact</a>
                </div>

                <div class="footer-contact">
                    <h4 data-i18n="footer_contact">Contact Info</h4>
                    <p><span class="icon">📍</span> Kusugundi Village, Koduru Post, Hosanagara Taluk, Shimoga, Karnataka</p>
                    <p><span class="icon">📞</span> <a href="tel:+919741943965" style="color:inherit;text-decoration:none;">+91 9741943965</a></p>
                    <p><span class="icon">✉️</span> info@shreeshani.com</p>
                    <p><a href="https://maps.google.com" target="_blank" class="btn btn-sm btn-outline" style="margin-top:var(--space-xs);"><span class="icon">🗺️</span> <span data-i18n="contact_map">Find Us on Map</span></a></p>
                </div>
            </div>

            <div class="footer-bottom">
                <p data-i18n="footer_copyright">© 2025 ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ) • Shree Shanishwara Swamy Temple (R.), Shree Kshetra Siddagiri. All rights reserved.</p>
            </div>
        </div>
    </footer>
    `;

    const footerContainer = document.getElementById('footer-container');
    if (footerContainer) {
        footerContainer.innerHTML = footerHTML;
    }
}

// ============================
// Mobile Menu
// ============================

function toggleMobileMenu() {
    const mobileNav = document.getElementById('mobile-nav');
    const menuBtn = document.querySelector('.mobile-menu-btn');
    if (mobileNav) {
        const isOpen = mobileNav.classList.toggle('open');
        if (menuBtn) {
            menuBtn.classList.toggle('active');
        }
    }
}

// ============================
// Scroll Effects
// ============================

function initScrollEffects() {
    // Navbar transparency on scroll (home page only)
    const navbar = document.getElementById('main-navbar');
    if (navbar && window.location.pathname === '/') {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 80) {
                navbar.classList.remove('transparent');
            } else {
                navbar.classList.add('transparent');
            }
        });
    }

    // Scroll animations with Intersection Observer
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .scale-in').forEach(el => {
        observer.observe(el);
    });
}

// ============================
// Toast Notifications
// ============================

function showToast(message, type = 'info', duration = 4000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${icons[type] || ''}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================
// Utility Functions
// ============================

/**
 * Format amount in INR.
 */
function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Format date string to locale format.
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
    });
}

/**
 * Format date and time.
 */
function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// ============================
// Page Initialization
// ============================

document.addEventListener('DOMContentLoaded', () => {
    renderNavbar();
    renderFooter();
    initScrollEffects();
    animateCounters();
    loadDonationTicker();
    // Re-apply translations after dynamic rendering
    setLanguage(getCurrentLang());
});

// ============================
// Animated Counters Observer
// ============================
function animateCounters() {
    const statsSection = document.getElementById('stats-section');
    if (!statsSection) return;

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counters = entry.target.querySelectorAll('.stat-number');
                counters.forEach(counter => {
                    const target = parseInt(counter.getAttribute('data-target'), 10);
                    let count = 0;
                    const duration = 2000; // 2 seconds
                    const increment = target / (duration / 16);
                    const suffix = counter.getAttribute('data-suffix') || '';
                    
                    const updateCount = () => {
                        count += increment;
                        if (count < target) {
                            counter.textContent = Math.ceil(count) + suffix;
                            requestAnimationFrame(updateCount);
                        } else {
                            counter.textContent = target + suffix;
                        }
                    };
                    updateCount();
                });
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    observer.observe(statsSection);
}

// ============================
// Password Toggle Helper
// ============================
function togglePasswordVisibility(id) {
    const input = document.getElementById(id);
    if (input) {
        const toggleBtn = input.nextElementSibling;
        if (input.type === 'password') {
            input.type = 'text';
            if (toggleBtn) toggleBtn.textContent = '🙈';
        } else {
            input.type = 'password';
            if (toggleBtn) toggleBtn.textContent = '👁️';
        }
    }
}

// ============================
// User Profile Helpers
// ============================
function getUserInitials(name) {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0][0].toUpperCase();
}

function toggleProfileDropdown(event) {
    if (event) event.stopPropagation();
    const dropdown = document.getElementById('profile-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('open');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    const dropdown = document.getElementById('profile-dropdown');
    if (dropdown && dropdown.classList.contains('open')) {
        dropdown.classList.remove('open');
    }
});

// ============================
// Live Donation Ticker
// ============================
async function loadDonationTicker() {
    const tickerSection = document.getElementById('donation-ticker-section');
    const track = document.getElementById('ticker-track');
    if (!tickerSection || !track) return;

    try {
        const donations = await apiFetch('/donate/recent');
        if (donations.length === 0) {
            track.innerHTML = `
                <div class="ticker-empty">
                    <span data-i18n="ticker_empty_en">Be the first devotee to donate.</span> | 
                    <span data-i18n="ticker_empty_kn" style="font-family: var(--font-kannada);">ಮೊದಲ ದೇಣಿಗೆ ನೀಡುವ ಭಕ್ತರಾಗಿರಿ.</span>
                </div>`;
            tickerSection.style.display = 'block';
            return;
        }

        const typeLabels = {
            general: 'General',
            annadanam: 'Annadanam',
            temple_development: 'Development',
            festival: 'Festival',
            goshala: 'Goshala'
        };

        const currentLang = getCurrentLang();
        const donatedText = currentLang === 'kn' ? 'ದೇಣಿಗೆ ನೀಡಿದ್ದಾರೆ' : 'donated';
        const forText = currentLang === 'kn' ? 'ಗೆ' : 'for';

        const cardsHTML = donations.map(d => {
            const formattedAmt = formatINR(d.amount);
            const typeStr = typeLabels[d.donation_type] || d.donation_type;
            const timeStr = timeAgo(d.created_at);
            
            if (currentLang === 'kn') {
                return `
                <div class="ticker-card">
                    <span>🙏 ${d.donor_name}</span>
                    <span class="amt">${formattedAmt}</span>
                    <span>${typeStr} ${forText} ${donatedText}</span>
                    <span class="time">• ${timeStr}</span>
                </div>`;
            } else {
                return `
                <div class="ticker-card">
                    <span>🙏 ${d.donor_name}</span>
                    <span>${donatedText}</span>
                    <span class="amt">${formattedAmt}</span>
                    <span>${forText}</span>
                    <span class="type">${typeStr}</span>
                    <span class="time">• ${timeStr}</span>
                </div>`;
            }
        }).join('');

        // Duplicate the content to create a seamless infinite scroll wrap
        track.innerHTML = cardsHTML + cardsHTML;
        tickerSection.style.display = 'block';
        
        // Re-apply translations for static texts in ticker
        document.querySelectorAll('#donation-ticker-section [data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[currentLang] && translations[currentLang][key]) {
                el.textContent = translations[currentLang][key];
            }
        });
    } catch (err) {
        console.error('Failed to load donation ticker:', err);
    }
}

function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}
