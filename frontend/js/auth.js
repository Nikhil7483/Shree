/**
 * ============================================================
 * auth.js — Authentication Logic (Login & Registration)
 * ============================================================
 */

/**
 * Clear all inline field validation errors.
 */
function clearErrors() {
    document.querySelectorAll('.form-error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.form-input').forEach(el => {
        el.classList.remove('input-invalid');
    });
}

/**
 * Show error for a specific field.
 */
function showFieldError(fieldId, message) {
    const errorEl = document.getElementById(`error-${fieldId}`);
    const inputEl = document.getElementById(fieldId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
    if (inputEl) {
        inputEl.classList.add('input-invalid');
    }
}

/**
 * Handle login form submission.
 */
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const submitBtn = event.target.querySelector('button[type="submit"]');

    clearErrors();
    let hasError = false;

    if (!email) {
        showFieldError('login-email', 'Please enter your email or mobile number');
        hasError = true;
    } else {
        const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        const isPhone = /^[0-9+\-\s]{10,15}$/.test(email);
        const isAdminUser = email.toLowerCase() === 'admin';
        if (!isEmail && !isPhone && !isAdminUser) {
            showFieldError('login-email', 'Please enter a valid email address or 10-digit mobile number');
            hasError = true;
        }
    }

    if (!password) {
        showFieldError('login-password', 'Password is required');
        hasError = true;
    }

    if (hasError) {
        showToast('Please correct the validation errors', 'warning');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.classList.add('btn-loading');

    try {
        const data = await apiFetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });

        // Store token and user info
        localStorage.setItem('temple_token', data.access_token);
        localStorage.setItem('temple_user', JSON.stringify({
            name: data.user_name,
            email: data.user_email,
            role: data.user_role,
            preferred_language: data.preferred_language,
            photo_url: data.photo_url,
        }));

        // Set preferred language
        setLanguage(data.preferred_language);

        showToast('Login successful! Welcome back.', 'success');

        // Redirect based on redirect parameter or role
        const urlParams = new URLSearchParams(window.location.search);
        const redirectUrl = urlParams.get('redirect');

        setTimeout(() => {
            if (redirectUrl) {
                window.location.href = redirectUrl;
            } else if (data.user_role === 'admin') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/dashboard';
            }
        }, 800);
    } catch (err) {
        const msg = err.message || 'Login failed';
        showToast(msg, 'error');
        showFieldError('login-password', msg);
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-loading');
    }
}

/**
 * Handle registration form submission.
 */
async function handleRegister(event) {
    event.preventDefault();

    const name = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const mobile = document.getElementById('register-mobile').value.trim();
    const password = document.getElementById('register-password').value.trim();
    const confirmPassword = document.getElementById('register-confirm').value.trim();
    const preferredLanguage = document.getElementById('register-language').value;
    const submitBtn = event.target.querySelector('button[type="submit"]');

    clearErrors();
    let hasError = false;

    if (!name) {
        showFieldError('register-name', 'Full name is required');
        hasError = true;
    }

    if (!email) {
        showFieldError('register-email', 'Email address is required');
        hasError = true;
    } else {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showFieldError('register-email', 'Please enter a valid email address');
            hasError = true;
        }
    }

    if (!mobile) {
        showFieldError('register-mobile', 'Mobile number is required');
        hasError = true;
    } else {
        const cleanDigits = mobile.replace(/[^0-9]/g, '');
        if (cleanDigits.length < 10) {
            showFieldError('register-mobile', 'Please enter a valid 10-digit mobile number');
            hasError = true;
        }
    }

    if (!password) {
        showFieldError('register-password', 'Password is required');
        hasError = true;
    } else if (password.length < 6) {
        showFieldError('register-password', 'Password must be at least 6 characters');
        hasError = true;
    }

    if (!confirmPassword) {
        showFieldError('register-confirm', 'Please confirm your password');
        hasError = true;
    } else if (password !== confirmPassword) {
        showFieldError('register-confirm', 'Passwords do not match');
        hasError = true;
    }

    if (hasError) {
        showToast('Please correct the validation errors', 'warning');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.classList.add('btn-loading');

    try {
        const data = await apiFetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                name,
                email,
                mobile,
                password,
                confirm_password: confirmPassword,
                preferred_language: preferredLanguage,
            }),
        });

        // Store token and user info
        localStorage.setItem('temple_token', data.access_token);
        localStorage.setItem('temple_user', JSON.stringify({
            name: data.user_name,
            email: data.user_email,
            role: data.user_role,
            preferred_language: data.preferred_language,
            photo_url: data.photo_url,
        }));

        // Set preferred language
        setLanguage(data.preferred_language);

        showToast('Account created successfully! Welcome.', 'success');

        const urlParams = new URLSearchParams(window.location.search);
        const redirectUrl = urlParams.get('redirect');

        setTimeout(() => {
            if (redirectUrl) {
                window.location.href = redirectUrl;
            } else {
                window.location.href = '/dashboard';
            }
        }, 800);
    } catch (err) {
        const msg = err.message || 'Registration failed';
        showToast(msg, 'error');
        if (msg.toLowerCase().includes('email')) {
            showFieldError('register-email', msg);
        } else if (msg.toLowerCase().includes('mobile')) {
            showFieldError('register-mobile', msg);
        } else {
            showFieldError('register-name', msg);
        }
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-loading');
    }
}

// ============================
// Password Strength & Match Checking
// ============================
function checkPasswordStrength() {
    const password = document.getElementById('register-password').value;
    const meter = document.getElementById('strength-meter');
    const bar = document.getElementById('strength-bar');
    const text = document.getElementById('strength-text');
    
    if (!password) {
        if (meter) meter.style.display = 'none';
        if (text) text.textContent = '';
        return;
    }
    
    if (meter) meter.style.display = 'block';
    let strength = 0;
    
    if (password.length >= 6) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    if (strength <= 1) {
        if (bar) {
            bar.style.width = '33%';
            bar.style.backgroundColor = 'var(--error)';
        }
        if (text) {
            text.textContent = 'Weak Password';
            text.style.color = 'var(--error)';
        }
    } else if (strength === 2 || strength === 3) {
        if (bar) {
            bar.style.width = '66%';
            bar.style.backgroundColor = '#f57f17';
        }
        if (text) {
            text.textContent = 'Medium Password';
            text.style.color = '#f57f17';
        }
    } else {
        if (bar) {
            bar.style.width = '100%';
            bar.style.backgroundColor = 'var(--success)';
        }
        if (text) {
            text.textContent = 'Strong Password';
            text.style.color = 'var(--success)';
        }
    }
}

function checkPasswordMatch() {
    const password = document.getElementById('register-password').value;
    const confirm = document.getElementById('register-confirm').value;
    const text = document.getElementById('match-text');
    
    if (!confirm) {
        if (text) text.textContent = '';
        return;
    }
    
    if (password === confirm) {
        if (text) {
            text.textContent = '✓ Passwords match';
            text.style.color = 'var(--success)';
        }
    } else {
        if (text) {
            text.textContent = '✗ Passwords do not match';
            text.style.color = 'var(--error)';
        }
    }
}
