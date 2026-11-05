/**
 * ============================================================
 * admin.js — Admin Panel Logic
 * ============================================================
 */

/**
 * Render admin sidebar navigation.
 */
function renderAdminSidebar() {
    const currentPage = window.location.pathname;
    const sidebar = document.getElementById('admin-sidebar');
    if (!sidebar) return;

    sidebar.innerHTML = `
        <div class="sidebar-header">
            <h3 style="font-family:var(--font-kannada);font-size:1.02rem;color:var(--gold);margin-bottom:2px;">ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ)</h3>
            <p style="font-size:0.75rem;color:var(--gold-metallic);margin:0;">Shree Shanishwara Swamy Temple (R.)</p>
        </div>
        <a href="/admin" class="nav-item ${currentPage === '/admin' ? 'active' : ''}">
            <span class="icon">📊</span> Dashboard
        </a>
        <a href="/admin/temple" class="nav-item ${currentPage === '/admin/temple' ? 'active' : ''}">
            <span class="icon">🏛️</span> Manage Temple
        </a>
        <a href="/admin/temple-info" class="nav-item ${currentPage === '/admin/temple-info' ? 'active' : ''}">
            <span class="icon">📜</span> ದೇವಸ್ಥಾನದ ಮಾಹಿತಿ (Official Info)
        </a>
        <a href="/admin/festivals" class="nav-item ${currentPage === '/admin/festivals' ? 'active' : ''}">
            <span class="icon">🎉</span> Manage Festivals
        </a>
        <a href="/admin/donations" class="nav-item ${currentPage === '/admin/donations' ? 'active' : ''}">
            <span class="icon">💰</span> Manage Donations
        </a>
        <a href="/admin/users" class="nav-item ${currentPage === '/admin/users' ? 'active' : ''}">
            <span class="icon">👥</span> Manage Users
        </a>
        <a href="/" class="nav-item">
            <span class="icon">🌐</span> View Website
        </a>
    `;
}

/**
 * Check admin auth — redirect if not admin.
 */
function checkAdminAuth() {
    if (!isLoggedIn() || !isAdmin()) {
        showToast('Admin access required', 'error');
        setTimeout(() => window.location.href = '/login', 1000);
        return false;
    }
    return true;
}

/**
 * Helper to escape HTML characters safely.
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Load admin dashboard stats.
 */
async function loadAdminDashboard() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const stats = await apiFetch('/admin/dashboard');

        document.getElementById('stat-total-amount').textContent = formatINR(stats.total_donations.amount);
        document.getElementById('stat-total-count').textContent = `${stats.total_donations.count} donations`;
        document.getElementById('stat-today-amount').textContent = formatINR(stats.today_donations.amount);
        document.getElementById('stat-today-count').textContent = `${stats.today_donations.count} donations`;
        document.getElementById('stat-monthly-amount').textContent = formatINR(stats.monthly_donations.amount);
        document.getElementById('stat-monthly-count').textContent = `${stats.monthly_donations.count} donations`;
        document.getElementById('stat-users').textContent = stats.total_users;

        if (stats.pending_donations) {
            const pCountElem = document.getElementById('stat-pending-count');
            const pAmtElem = document.getElementById('stat-pending-amount');
            if (pCountElem) pCountElem.textContent = `${stats.pending_donations.count} awaiting review →`;
            if (pAmtElem) pAmtElem.textContent = formatINR(stats.pending_donations.amount);
        }

        // Recent donations table
        const tbody = document.getElementById('recent-donations-body');
        if (stats.recent_donations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">No donations yet</td></tr>';
        } else {
            tbody.innerHTML = stats.recent_donations.map(d => `
                <tr>
                    <td>${escapeHtml(d.donor_name)}</td>
                    <td style="font-weight:700;color:var(--saffron);">${formatINR(d.amount)}</td>
                    <td>${escapeHtml(d.donation_type)}</td>
                    <td>
                        <button class="receipt-badge-btn" onclick="downloadReceiptPdf('${d.id}', '${d.receipt_number}')" title="Download Official Receipt PDF">
                            📄 ${d.receipt_number || 'Receipt'}
                        </button>
                    </td>
                    <td>${formatDateTime(d.created_at)}</td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error('Dashboard error:', err);
        showToast('Failed to load dashboard', 'error');
    }
}

// In-memory cache and filter state for admin donations
let allDonationsCache = [];
let currentDonationFilter = 'all';

/**
 * Load all donations for admin with filter tabs and approve/reject actions.
 */
async function loadAdminDonations() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const donations = await apiFetch('/donate/all');
        allDonationsCache = donations || [];

        // Check query param for default filter
        const urlParams = new URLSearchParams(window.location.search);
        const filterParam = urlParams.get('filter');
        if (filterParam && ['all', 'pending_verification', 'completed', 'rejected'].includes(filterParam)) {
            currentDonationFilter = filterParam;
        }

        updateDonationFilterTabs();
        renderDonationsTable();
    } catch (err) {
        console.error('Failed to load donations:', err);
        showToast('Failed to load donations list', 'error');
    }
}

/**
 * Update counters on the filter tabs.
 */
function updateDonationFilterTabs() {
    const totalCount = allDonationsCache.length;
    const pendingCount = allDonationsCache.filter(d => d.status === 'pending_verification' || d.status === 'pending').length;
    const completedCount = allDonationsCache.filter(d => d.status === 'completed').length;
    const rejectedCount = allDonationsCache.filter(d => d.status === 'rejected').length;

    const countAll = document.getElementById('count-all');
    const countPending = document.getElementById('count-pending');
    const countCompleted = document.getElementById('count-completed');
    const countRejected = document.getElementById('count-rejected');

    if (countAll) countAll.textContent = totalCount;
    if (countPending) countPending.textContent = pendingCount;
    if (countCompleted) countCompleted.textContent = completedCount;
    if (countRejected) countRejected.textContent = rejectedCount;

    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-filter') === currentDonationFilter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

/**
 * Switch filter between all, pending_verification, completed, and rejected.
 */
function setDonationFilter(filterType) {
    currentDonationFilter = filterType;
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === filterType);
    });
    renderDonationsTable();
}

/**
 * Search donations across multiple fields.
 */
function searchDonations(query) {
    renderDonationsTable(query);
}

/**
 * Render the donations table based on current filter and search query.
 */
function renderDonationsTable(searchQuery = '') {
    const tbody = document.getElementById('all-donations-body');
    if (!tbody) return;

    const searchInput = document.querySelector('.admin-search');
    const q = (searchQuery || (searchInput ? searchInput.value : '')).trim().toLowerCase();

    let list = allDonationsCache.filter(d => {
        if (currentDonationFilter === 'pending_verification') {
            return d.status === 'pending_verification' || d.status === 'pending';
        }
        if (currentDonationFilter === 'completed') {
            return d.status === 'completed';
        }
        if (currentDonationFilter === 'rejected') {
            return d.status === 'rejected';
        }
        return true;
    });

    if (q) {
        list = list.filter(d => 
            (d.donor_name || '').toLowerCase().includes(q) ||
            (d.donor_mobile || '').toLowerCase().includes(q) ||
            (d.donor_email || '').toLowerCase().includes(q) ||
            (d.utr_number || '').toLowerCase().includes(q) ||
            (d.receipt_number || '').toLowerCase().includes(q) ||
            (d.donation_type || '').toLowerCase().includes(q) ||
            (d.status || '').toLowerCase().includes(q) ||
            String(d.amount).includes(q)
        );
    }

    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:36px;color:var(--text-muted);font-size:0.95rem;">
            No donations found for this selection.
        </td></tr>`;
        return;
    }

    tbody.innerHTML = list.map(d => {
        const isPending = d.status === 'pending_verification' || d.status === 'pending';
        const isCompleted = d.status === 'completed';
        const isRejected = d.status === 'rejected';

        const statusBadge = isPending 
            ? `<span class="status-badge pending_verification">⏳ Pending Review</span>`
            : (isCompleted 
                ? `<span class="status-badge completed">✅ Approved</span>`
                : (isRejected 
                    ? `<span class="status-badge rejected">❌ Rejected</span>`
                    : `<span class="status-badge ${d.status}">${d.status}</span>`));

        const utrDisplay = d.utr_number 
            ? `<div style="display:inline-flex;align-items:center;gap:6px;">
                 <span style="font-family:monospace;font-size:0.85rem;background:#F3F4F6;padding:2px 7px;border-radius:4px;border:1px solid #E5E7EB;font-weight:700;color:#1F2937;">${escapeHtml(d.utr_number)}</span>
                 <button type="button" class="action-btn copy" onclick="copyUtrText('${escapeHtml(d.utr_number)}', this)" title="Copy UTR Reference" style="background:#E5E7EB;color:#374151;padding:2px 6px;">📋</button>
               </div>`
            : `<span style="color:var(--text-muted);font-size:0.85rem;">—</span>`;

        let actionHtml = '';
        if (isPending) {
            actionHtml = `
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:nowrap;">
                    <button class="btn-approve" onclick="showApprovalModal({ id: '${d.id}', donorName: '${escapeHtml(d.donor_name)}', amount: ${d.amount}, utr: '${escapeHtml(d.utr_number || '')}' })" title="Verify bank credit & approve donation">
                        <span>✓</span> Approve
                    </button>
                    <button class="btn-reject" onclick="showRejectModal({ id: '${d.id}', donorName: '${escapeHtml(d.donor_name)}', amount: ${d.amount}, utr: '${escapeHtml(d.utr_number || '')}' })" title="Reject unverified reference">
                        <span>✕</span> Reject
                    </button>
                </div>
            `;
        } else if (isCompleted) {
            actionHtml = `
                <div style="display:flex;gap:8px;align-items:center;">
                    <button class="receipt-badge-btn" onclick="downloadReceiptPdf('${d.id}', '${d.receipt_number}')" title="Download Official Receipt PDF">
                        📄 ${d.receipt_number || 'Receipt'}
                    </button>
                </div>
            `;
        } else {
            actionHtml = `<span style="font-size:0.8rem;color:var(--error);font-weight:600;">Rejected</span>`;
        }

        return `
            <tr id="donation-row-${d.id}">
                <td>
                    <strong>${escapeHtml(d.donor_name)}</strong>
                    <div style="font-size:0.8rem;color:var(--text-muted);">${escapeHtml(d.donor_mobile || d.donor_email || '—')}</div>
                </td>
                <td style="font-weight:800;color:var(--dark-green);font-size:1.05rem;">
                    ${formatINR(d.amount)}
                </td>
                <td>${utrDisplay}</td>
                <td><span style="font-size:0.85rem;text-transform:capitalize;">${escapeHtml(d.donation_type || 'General')}</span></td>
                <td>${statusBadge}</td>
                <td style="font-size:0.82rem;color:var(--text-muted);white-space:nowrap;">
                    ${formatDateTime(d.created_at)}
                </td>
                <td>${actionHtml}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Helper to get or create the admin modal container in the DOM.
 */
function getAdminModalContainer() {
    let backdrop = document.getElementById('temple-admin-modal-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'temple-admin-modal-backdrop';
        backdrop.className = 'temple-modal-backdrop';
        backdrop.innerHTML = `
            <div class="temple-modal-card" id="temple-admin-modal-card" onclick="event.stopPropagation()">
                <!-- Content dynamically injected here -->
            </div>
        `;
        backdrop.onclick = closeAdminModal;
        document.body.appendChild(backdrop);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeAdminModal();
        });
    }
    return backdrop;
}

/**
 * Close the admin modal dialog.
 */
function closeAdminModal() {
    const backdrop = document.getElementById('temple-admin-modal-backdrop');
    if (backdrop) {
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Show a beautiful approval confirmation modal.
 */
function showApprovalModal({ id, donorName, amount, utr }) {
    const backdrop = getAdminModalContainer();
    const card = document.getElementById('temple-admin-modal-card');
    const formattedAmt = typeof formatINR === 'function' ? formatINR(amount) : `₹${amount}`;

    card.innerHTML = `
        <div style="text-align:center;">
            <div class="modal-header-badge">
                <span>ॐ</span>
                <span>ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ • ADMIN VERIFICATION</span>
            </div>
            
            <div class="modal-icon-circle approve">
                <span>✅</span>
            </div>

            <h2 class="modal-title">Approve Devotee Payment</h2>
            <p class="modal-subtitle">
                Please verify bank credit before issuing the official temple receipt.
            </p>

            <div class="modal-details-box">
                <div class="modal-detail-row">
                    <span class="modal-label">Devotee Name</span>
                    <span class="modal-val">${escapeHtml(donorName)}</span>
                </div>
                <div class="modal-detail-row">
                    <span class="modal-label">Offering Amount</span>
                    <span class="modal-val amount-highlight">${formattedAmt}</span>
                </div>
                <div class="modal-detail-row">
                    <span class="modal-label">12-Digit UTR Ref</span>
                    <span class="modal-val mono-badge">${escapeHtml(utr || 'Direct Transfer')}</span>
                </div>
            </div>

            <div class="modal-notice-box">
                <span style="font-size:1.1rem;line-height:1;">ℹ️</span>
                <span>
                    This confirms that the bank transfer has been verified in Canara Bank. The donation status will change to <strong>'Completed'</strong> and an official receipt will be generated.
                </span>
            </div>

            <div class="modal-actions-row">
                <button type="button" class="modal-btn cancel" onclick="closeAdminModal()">
                    <span>Cancel</span>
                </button>
                <button type="button" class="modal-btn approve-confirm" id="btn-modal-confirm-approve">
                    <span>✓ Confirm & Approve Payment</span>
                </button>
            </div>
        </div>
    `;

    document.getElementById('btn-modal-confirm-approve').onclick = async () => {
        const btn = document.getElementById('btn-modal-confirm-approve');
        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> <span>Approving...</span>';

        try {
            const result = await apiFetch(`/donate/approve/${id}`, {
                method: 'POST',
            });

            // Show celebratory success modal!
            showSuccessApprovalModal({
                id,
                donorName,
                amount,
                receiptNumber: result.receipt_number
            });

            // Refresh donations table in the background
            if (typeof loadAdminDonations === 'function') {
                loadAdminDonations();
            }
        } catch (err) {
            console.error('Approve donation error:', err);
            closeAdminModal();
            showToast(err.message || 'Failed to approve donation', 'error');
        }
    };

    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Show a celebratory success modal once donation is approved.
 */
function showSuccessApprovalModal({ id, donorName, amount, receiptNumber }) {
    const card = document.getElementById('temple-admin-modal-card');
    const formattedAmt = typeof formatINR === 'function' ? formatINR(amount) : `₹${amount}`;

    card.innerHTML = `
        <div style="text-align:center;">
            <div class="modal-header-badge" style="background:#E8F5E9;color:#2E7D32;border-color:#A5D6A7;">
                <span>✨</span>
                <span>VERIFIED & APPROVED</span>
            </div>
            
            <div class="modal-icon-circle success">
                <span>🎉</span>
            </div>

            <h2 class="modal-title" style="color:#145A32;">Payment Approved!</h2>
            <p class="modal-subtitle">
                Devotional offering of <strong>${formattedAmt}</strong> from <strong>${escapeHtml(donorName)}</strong> has been verified and recorded.
            </p>

            <div style="background:#F8F5EE;border-radius:16px;padding:20px;margin-bottom:24px;border:1px solid rgba(212,175,55,0.4);">
                <div style="font-size:0.8rem;text-transform:uppercase;color:#6B7280;font-weight:700;margin-bottom:6px;letter-spacing:0.5px;">
                    Official Receipt Number
                </div>
                <div style="font-family:monospace;font-size:1.35rem;font-weight:800;color:#052E20;letter-spacing:1px;">
                    ${escapeHtml(receiptNumber || 'Generated')}
                </div>
            </div>

            <div class="modal-actions-row">
                <button type="button" class="modal-btn cancel" onclick="closeAdminModal()">
                    <span>Done</span>
                </button>
                <button type="button" class="modal-btn approve-confirm" onclick="closeAdminModal(); downloadReceiptPdf('${id}', '${receiptNumber}')">
                    <span>📄 Download Receipt PDF</span>
                </button>
            </div>
        </div>
    `;
}

/**
 * Show a beautiful rejection confirmation modal.
 */
function showRejectModal({ id, donorName, amount, utr }) {
    const backdrop = getAdminModalContainer();
    const card = document.getElementById('temple-admin-modal-card');
    const formattedAmt = typeof formatINR === 'function' ? formatINR(amount) : `₹${amount}`;

    card.innerHTML = `
        <div style="text-align:center;">
            <div class="modal-header-badge" style="background:#FFEBEE;color:#C62828;border-color:#FFCDD2;">
                <span>⚠️</span>
                <span>PAYMENT REJECTION</span>
            </div>
            
            <div class="modal-icon-circle reject">
                <span>⚠️</span>
            </div>

            <h2 class="modal-title" style="color:#B71C1C;">Reject Payment Reference?</h2>
            <p class="modal-subtitle">
                This indicates that no matching credit was found in the temple bank account.
            </p>

            <div class="modal-details-box">
                <div class="modal-detail-row">
                    <span class="modal-label">Devotee Name</span>
                    <span class="modal-val">${escapeHtml(donorName)}</span>
                </div>
                <div class="modal-detail-row">
                    <span class="modal-label">Offering Amount</span>
                    <span class="modal-val">${formattedAmt}</span>
                </div>
                <div class="modal-detail-row">
                    <span class="modal-label">UTR Ref</span>
                    <span class="modal-val mono-badge">${escapeHtml(utr || 'Direct Transfer')}</span>
                </div>
            </div>

            <div class="modal-notice-box danger">
                <span style="font-size:1.1rem;line-height:1;">⚠️</span>
                <span>
                    The reference will be marked as <strong>'Rejected'</strong>. No official donation receipt will be generated.
                </span>
            </div>

            <div class="modal-actions-row">
                <button type="button" class="modal-btn cancel" onclick="closeAdminModal()">
                    <span>Cancel</span>
                </button>
                <button type="button" class="modal-btn reject-confirm" id="btn-modal-confirm-reject">
                    <span>✕ Confirm Rejection</span>
                </button>
            </div>
        </div>
    `;

    document.getElementById('btn-modal-confirm-reject').onclick = async () => {
        const btn = document.getElementById('btn-modal-confirm-reject');
        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> <span>Rejecting...</span>';

        try {
            await apiFetch(`/donate/reject/${id}`, {
                method: 'POST',
            });

            closeAdminModal();
            showToast(`Payment reference for ${donorName} marked as rejected.`, 'info');

            if (typeof loadAdminDonations === 'function') {
                loadAdminDonations();
            }
        } catch (err) {
            console.error('Reject donation error:', err);
            closeAdminModal();
            showToast(err.message || 'Failed to reject donation', 'error');
        }
    };

    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
}

/**
 * Approve a pending donation by admin (wrapper calling showApprovalModal).
 */
function approveDonation(id, donorName, amount, utr) {
    showApprovalModal({ id, donorName, amount, utr });
}

/**
 * Reject an unverified donation reference (wrapper calling showRejectModal).
 */
function rejectDonation(id, donorName, amount = 0, utr = '') {
    showRejectModal({ id, donorName, amount, utr });
}

/**
 * Copy UTR text to clipboard with visual feedback.
 */
function copyUtrText(text, btnElement) {
    navigator.clipboard.writeText(text).then(() => {
        const orig = btnElement.innerHTML;
        btnElement.innerHTML = '✓';
        btnElement.style.background = '#2E7D32';
        btnElement.style.color = '#fff';
        showToast('Copied UTR: ' + text, 'success');
        setTimeout(() => {
            btnElement.innerHTML = orig;
            btnElement.style.background = '';
            btnElement.style.color = '';
        }, 1800);
    }).catch(err => {
        console.error('Failed to copy text:', err);
    });
}

/**
 * Export donations to CSV based on loaded records.
 */
function exportDonationsCSV() {
    if (!allDonationsCache || allDonationsCache.length === 0) {
        showToast('No donations available to export', 'warning');
        return;
    }

    const headers = ['Receipt No', 'Donor Name', 'Mobile', 'Email', 'Amount (INR)', 'Type', 'Status', 'UTR Reference', 'Date'];
    const rows = allDonationsCache.map(d => [
        `"${(d.receipt_number || '').replace(/"/g, '""')}"`,
        `"${(d.donor_name || '').replace(/"/g, '""')}"`,
        `"${(d.donor_mobile || '').replace(/"/g, '""')}"`,
        `"${(d.donor_email || '').replace(/"/g, '""')}"`,
        d.amount,
        `"${(d.donation_type || '').replace(/"/g, '""')}"`,
        `"${(d.status || '').replace(/"/g, '""')}"`,
        `"${(d.utr_number || '').replace(/"/g, '""')}"`,
        `"${(d.created_at || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const now = new Date().toISOString().slice(0, 10);
    a.download = `shree_temple_donations_${now}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Donations CSV exported! 📥', 'success');
}


/**
 * Download a single donation receipt as a PDF.
 */
async function downloadReceiptPdf(donationId, receiptNumber) {
    if (!donationId) {
        showToast('Receipt not found', 'error');
        return;
    }
    showToast('Preparing receipt PDF... 📄', 'info');
    try {
        const token = localStorage.getItem('temple_token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`/api/donate/receipt/${donationId}`, { headers });
        if (!response.ok) {
            throw new Error('Failed to download receipt');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt_${receiptNumber || donationId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Receipt PDF downloaded! 🙏', 'success');
    } catch (err) {
        console.error('Download receipt error:', err);
        showToast('Failed to download receipt PDF', 'error');
    }
}

/**
 * Export donations report as a branded multi-page PDF.
 */
async function exportDonationsPDF() {
    showToast('Generating donations report PDF... 📄', 'info');
    try {
        const token = localStorage.getItem('temple_token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const searchInput = document.querySelector('.admin-search');
        const query = searchInput ? searchInput.value.trim() : '';
        const url = `/api/donate/export-pdf${query ? `?query=${encodeURIComponent(query)}` : ''}`;

        const response = await fetch(url, { headers });
        if (!response.ok) {
            throw new Error('Failed to generate donations report PDF');
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        const now = new Date().toISOString().slice(0, 10);
        a.download = `shree_temple_donations_report_${now}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
        showToast('Donations report PDF downloaded! 🙏', 'success');
    } catch (err) {
        console.error('Export PDF error:', err);
        showToast('Failed to download donations report PDF', 'error');
    }
}

/**
 * Load all users for admin.
 */
async function loadAdminUsers() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const users = await apiFetch('/users/all');
        const tbody = document.getElementById('all-users-body');
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.name}</td>
                <td>${u.email}</td>
                <td>${u.mobile}</td>
                <td><span class="status-badge ${u.is_active ? 'completed' : 'failed'}">${u.is_active ? 'Active' : 'Blocked'}</span></td>
                <td>${u.role}</td>
                <td>${formatDate(u.created_at)}</td>
                <td>
                    ${u.role !== 'admin' ? `
                        <button class="action-btn block" onclick="toggleBlockUser('${u.id}')">${u.is_active ? 'Block' : 'Unblock'}</button>
                        <button class="action-btn delete" onclick="deleteUser('${u.id}')">Delete</button>
                    ` : '<span style="color:var(--text-muted);font-size:0.8rem;">Admin</span>'}
                </td>
            </tr>
        `).join('');
    } catch (err) { console.error(err); }
}

async function toggleBlockUser(userId) {
    if (!confirm('Are you sure?')) return;
    try {
        await apiFetch(`/users/${userId}/block`, { method: 'PUT' });
        showToast('User status updated', 'success');
        loadAdminUsers();
    } catch (err) { showToast('Failed', 'error'); }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This cannot be undone.')) return;
    try {
        await apiFetch(`/users/${userId}`, { method: 'DELETE' });
        showToast('User deleted', 'success');
        loadAdminUsers();
    } catch (err) { showToast('Failed', 'error'); }
}

/**
 * Load temple data for editing.
 */
async function loadAdminTemple() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const temple = await apiFetch('/temple');
        document.getElementById('temple-history-en').value = temple.history_en || '';
        document.getElementById('temple-history-kn').value = temple.history_kn || '';
        document.getElementById('temple-morning-open').value = temple.timings?.morning_open || '';
        document.getElementById('temple-morning-close').value = temple.timings?.morning_close || '';
        document.getElementById('temple-evening-open').value = temple.timings?.evening_open || '';
        document.getElementById('temple-evening-close').value = temple.timings?.evening_close || '';
        document.getElementById('temple-phone').value = temple.contact?.phone || '';
        document.getElementById('temple-email').value = temple.contact?.email || '';
    } catch (err) { console.error(err); }
}

async function saveTempleData(event) {
    event.preventDefault();
    try {
        const data = {
            history_en: document.getElementById('temple-history-en').value,
            history_kn: document.getElementById('temple-history-kn').value,
            timings: {
                morning_open: document.getElementById('temple-morning-open').value,
                morning_close: document.getElementById('temple-morning-close').value,
                evening_open: document.getElementById('temple-evening-open').value,
                evening_close: document.getElementById('temple-evening-close').value,
            },
            contact: {
                phone: document.getElementById('temple-phone').value,
                email: document.getElementById('temple-email').value,
            }
        };
        await apiFetch('/temple', { method: 'PUT', body: JSON.stringify(data) });
        showToast('Temple information updated! 🙏', 'success');
    } catch (err) { showToast('Failed to update', 'error'); }
}

/**
 * Load and manage festivals.
 */
async function loadAdminFestivals() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const festivals = await apiFetch('/festivals');
        const tbody = document.getElementById('festivals-body');
        tbody.innerHTML = festivals.map(f => `
            <tr>
                <td style="font-family:var(--font-kannada);font-weight:600;">${f.name_kn}</td>
                <td>${f.name_en}</td>
                <td>${f.date || '—'}</td>
                <td>
                    <button class="action-btn delete" onclick="deleteFestival('${f._id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (err) { console.error(err); }
}

async function addFestival(event) {
    event.preventDefault();
    try {
        const data = {
            name_en: document.getElementById('fest-name-en').value,
            name_kn: document.getElementById('fest-name-kn').value,
            description_en: document.getElementById('fest-desc-en').value,
            description_kn: document.getElementById('fest-desc-kn').value,
            date: document.getElementById('fest-date').value,
        };
        await apiFetch('/festivals', { method: 'POST', body: JSON.stringify(data) });
        showToast('Festival added! 🎉', 'success');
        event.target.reset();
        loadAdminFestivals();
    } catch (err) { showToast('Failed to add festival', 'error'); }
}

async function deleteFestival(id) {
    if (!confirm('Delete this festival?')) return;
    try {
        await apiFetch(`/festivals/${id}`, { method: 'DELETE' });
        showToast('Festival deleted', 'success');
        loadAdminFestivals();
    } catch (err) { showToast('Failed', 'error'); }
}

/**
 * ============================================================
 * Official Temple Info Admin Management
 * ============================================================
 */
let adminOfficialData = null;

async function loadAdminOfficialInfo() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const data = await apiFetch('/temple/official-info');
        adminOfficialData = data;

        // Populate basic info
        document.getElementById('info-heading-kn').value = data.heading_kn || '';
        document.getElementById('info-heading-en').value = data.heading_en || '';
        document.getElementById('info-reg-no').value = data.registration_no || '';
        document.getElementById('info-address-kn').value = data.address_kn || '';
        document.getElementById('info-address-en').value = data.address_en || '';
        document.getElementById('info-dharmadarshi-kn').value = data.dharmadarshi_kn || '';
        document.getElementById('info-dharmadarshi-en').value = data.dharmadarshi_en || '';
        document.getElementById('info-dharmadarshi-phone').value = data.dharmadarshi_phone || '';
        document.getElementById('info-manager-kn').value = data.manager_kn || '';
        document.getElementById('info-manager-en').value = data.manager_en || '';
        document.getElementById('info-doc-public').checked = data.is_document_public !== false;

        // Populate special notice
        if (data.special_notice) {
            document.getElementById('notice-min-amount').value = data.special_notice.min_amount || '';
            document.getElementById('notice-amount-kn').value = data.special_notice.amount_text_kn || '';
            document.getElementById('notice-amount-en').value = data.special_notice.amount_text_en || '';
            document.getElementById('notice-purpose-kn').value = data.special_notice.purpose_kn || '';
            document.getElementById('notice-purpose-en').value = data.special_notice.purpose_en || '';
            document.getElementById('notice-condition-kn').value = data.special_notice.condition_kn || '';
            document.getElementById('notice-condition-en').value = data.special_notice.condition_en || '';
            document.getElementById('notice-benefit-kn').value = data.special_notice.benefit_kn || '';
            document.getElementById('notice-benefit-en').value = data.special_notice.benefit_en || '';
        }

        // Render Deities
        renderAdminDeities(data.deities || []);

        // Render Committee Members
        renderAdminCommitteeMembers(data.committee_members || []);

        // Render Audit Logs
        loadAdminAuditLogs();
    } catch (err) {
        console.error('Failed to load official info:', err);
        showToast('Failed to load official temple info', 'error');
    }
}

function renderAdminDeities(deities) {
    const tbody = document.getElementById('deities-table-body');
    if (!tbody) return;
    if (!deities || deities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No deities found</td></tr>';
        return;
    }
    tbody.innerHTML = deities.map((d, index) => `
        <tr>
            <td>${d.sl_no || (index + 1)}</td>
            <td style="font-family:var(--font-kannada);font-weight:600;">${d.name_kn}</td>
            <td>${d.name_en}</td>
            <td><span class="status-badge completed">${d.status_kn || 'ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ'}</span></td>
            <td>
                <button type="button" class="action-btn delete" onclick="deleteDeity(${index})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function addDeity(event) {
    event.preventDefault();
    if (!adminOfficialData) return;
    const nameKn = document.getElementById('new-deity-kn').value.trim();
    const nameEn = document.getElementById('new-deity-en').value.trim();
    if (!nameKn || !nameEn) {
        showToast('Please enter both Kannada and English deity names', 'warning');
        return;
    }
    if (!adminOfficialData.deities) adminOfficialData.deities = [];
    adminOfficialData.deities.push({
        sl_no: adminOfficialData.deities.length + 1,
        name_kn: nameKn,
        name_en: nameEn,
        status_kn: "ನಿರ್ಮಾಣ ಸಂಪೂರ್ಣ",
        status_en: "Construction Complete"
    });
    renderAdminDeities(adminOfficialData.deities);
    document.getElementById('new-deity-kn').value = '';
    document.getElementById('new-deity-en').value = '';
    showToast('Deity added to list. Click "Save All Changes" to persist.', 'info');
}

function deleteDeity(index) {
    if (!confirm('Remove this deity?')) return;
    adminOfficialData.deities.splice(index, 1);
    adminOfficialData.deities.forEach((d, i) => d.sl_no = i + 1);
    renderAdminDeities(adminOfficialData.deities);
    showToast('Deity removed. Click "Save All Changes" to persist.', 'info');
}

function renderAdminCommitteeMembers(members) {
    const tbody = document.getElementById('committee-table-body');
    if (!tbody) return;
    if (!members || members.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No members found</td></tr>';
        return;
    }
    tbody.innerHTML = members.map((m, index) => `
        <tr>
            <td style="font-weight:700;">${m.sl_no}</td>
            <td style="font-family:var(--font-kannada);font-weight:600;">${m.name_kn}</td>
            <td>${m.name_en}</td>
            <td>${m.designation_kn || '—'}</td>
            <td>${m.location_kn || '—'}</td>
            <td style="white-space:nowrap;">
                <button type="button" class="action-btn" onclick="editCommitteeMember(${m.sl_no})" style="background:var(--secondary);color:#fff;margin-right:4px;">Edit</button>
                <button type="button" class="action-btn delete" onclick="deleteCommitteeMember(${m.sl_no})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function openAddMemberModal() {
    document.getElementById('modal-member-title').textContent = 'Add Committee Member';
    document.getElementById('member-edit-sl').value = '';
    document.getElementById('member-sl-no').value = (adminOfficialData?.committee_members?.length || 0) + 1;
    document.getElementById('member-name-kn').value = '';
    document.getElementById('member-name-en').value = '';
    document.getElementById('member-desig-kn').value = '';
    document.getElementById('member-desig-en').value = '';
    document.getElementById('member-loc-kn').value = '';
    document.getElementById('member-loc-en').value = '';
    document.getElementById('member-modal').style.display = 'flex';
}

function editCommitteeMember(slNo) {
    const member = adminOfficialData?.committee_members?.find(m => m.sl_no === slNo);
    if (!member) return;
    document.getElementById('modal-member-title').textContent = `Edit Member #${slNo}`;
    document.getElementById('member-edit-sl').value = slNo;
    document.getElementById('member-sl-no').value = member.sl_no;
    document.getElementById('member-name-kn').value = member.name_kn;
    document.getElementById('member-name-en').value = member.name_en;
    document.getElementById('member-desig-kn').value = member.designation_kn || '';
    document.getElementById('member-desig-en').value = member.designation_en || '';
    document.getElementById('member-loc-kn').value = member.location_kn || '';
    document.getElementById('member-loc-en').value = member.location_en || '';
    document.getElementById('member-modal').style.display = 'flex';
}

function closeMemberModal() {
    document.getElementById('member-modal').style.display = 'none';
}

function saveMemberFromModal(event) {
    event.preventDefault();
    const editSl = document.getElementById('member-edit-sl').value;
    const slNo = parseInt(document.getElementById('member-sl-no').value, 10);
    const nameKn = document.getElementById('member-name-kn').value.trim();
    const nameEn = document.getElementById('member-name-en').value.trim();
    const desigKn = document.getElementById('member-desig-kn').value.trim();
    const desigEn = document.getElementById('member-desig-en').value.trim();
    const locKn = document.getElementById('member-loc-kn').value.trim();
    const locEn = document.getElementById('member-loc-en').value.trim();

    if (!nameKn) {
        showToast('Kannada name is required', 'warning');
        return;
    }

    if (!adminOfficialData.committee_members) adminOfficialData.committee_members = [];

    const memberObj = {
        sl_no: slNo,
        name_kn: nameKn,
        name_en: nameEn || nameKn,
        designation_kn: desigKn,
        designation_en: desigEn,
        location_kn: locKn,
        location_en: locEn
    };

    if (editSl) {
        const idx = adminOfficialData.committee_members.findIndex(m => m.sl_no === parseInt(editSl, 10));
        if (idx !== -1) {
            adminOfficialData.committee_members[idx] = memberObj;
        }
    } else {
        adminOfficialData.committee_members.push(memberObj);
    }

    adminOfficialData.committee_members.sort((a, b) => a.sl_no - b.sl_no);
    renderAdminCommitteeMembers(adminOfficialData.committee_members);
    closeMemberModal();
    showToast('Member saved in list. Click "Save All Changes" to persist.', 'info');
}

function deleteCommitteeMember(slNo) {
    if (!confirm(`Delete committee member #${slNo}?`)) return;
    adminOfficialData.committee_members = adminOfficialData.committee_members.filter(m => m.sl_no !== slNo);
    renderAdminCommitteeMembers(adminOfficialData.committee_members);
    showToast('Member removed. Click "Save All Changes" to persist.', 'info');
}

async function saveOfficialTempleData(event) {
    if (event) event.preventDefault();
    try {
        const updatePayload = {
            heading_kn: document.getElementById('info-heading-kn').value,
            heading_en: document.getElementById('info-heading-en').value,
            registration_no: document.getElementById('info-reg-no').value,
            address_kn: document.getElementById('info-address-kn').value,
            address_en: document.getElementById('info-address-en').value,
            dharmadarshi_kn: document.getElementById('info-dharmadarshi-kn').value,
            dharmadarshi_en: document.getElementById('info-dharmadarshi-en').value,
            dharmadarshi_phone: document.getElementById('info-dharmadarshi-phone').value,
            manager_kn: document.getElementById('info-manager-kn').value,
            manager_en: document.getElementById('info-manager-en').value,
            is_document_public: document.getElementById('info-doc-public').checked,
            special_notice: {
                min_amount: document.getElementById('notice-min-amount').value,
                amount_text_kn: document.getElementById('notice-amount-kn').value,
                amount_text_en: document.getElementById('notice-amount-en').value,
                purpose_kn: document.getElementById('notice-purpose-kn').value,
                purpose_en: document.getElementById('notice-purpose-en').value,
                condition_kn: document.getElementById('notice-condition-kn').value,
                condition_en: document.getElementById('notice-condition-en').value,
                benefit_kn: document.getElementById('notice-benefit-kn').value,
                benefit_en: document.getElementById('notice-benefit-en').value
            },
            deities: adminOfficialData.deities || [],
            committee_members: adminOfficialData.committee_members || []
        };

        const res = await apiFetch('/temple/official-info', {
            method: 'PUT',
            body: JSON.stringify(updatePayload)
        });

        showToast('Official temple info updated successfully! 🙏', 'success');
        loadAdminOfficialInfo();
    } catch (err) {
        console.error('Update error:', err);
        showToast('Failed to save changes: ' + (err.message || 'Unknown error'), 'error');
    }
}

async function uploadOfficialDocumentFile(event) {
    event.preventDefault();
    const fileInput = document.getElementById('doc-upload-file');
    const docType = document.getElementById('doc-upload-type').value;

    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to upload', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const token = localStorage.getItem('temple_token');
        const res = await fetch(`/api/temple/official-info/upload?doc_type=${docType}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Upload failed');

        showToast('Document uploaded successfully! 📄', 'success');
        fileInput.value = '';
        loadAdminOfficialInfo();
    } catch (err) {
        console.error('Upload error:', err);
        showToast('Failed to upload document: ' + err.message, 'error');
    }
}

async function loadAdminAuditLogs() {
    try {
        const logs = await apiFetch('/temple/official-info/audit-logs');
        const tbody = document.getElementById('audit-logs-body');
        if (!tbody) return;
        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No audit logs yet</td></tr>';
            return;
        }
        tbody.innerHTML = logs.map(l => `
            <tr>
                <td>${formatDateTime(l.timestamp)}</td>
                <td><strong>${l.admin_email}</strong></td>
                <td><span class="status-badge completed">${l.action}</span></td>
                <td>${l.details}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error loading audit logs:', err);
    }
}
