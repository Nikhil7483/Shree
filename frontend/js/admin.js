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
            <h3>🙏 Admin Panel</h3>
            <p>Temple Management</p>
        </div>
        <a href="/admin" class="nav-item ${currentPage === '/admin' ? 'active' : ''}">
            <span class="icon">📊</span> Dashboard
        </a>
        <a href="/admin/temple" class="nav-item ${currentPage === '/admin/temple' ? 'active' : ''}">
            <span class="icon">🏛️</span> Manage Temple
        </a>
        <a href="/admin/temple-info" class="nav-item ${currentPage === '/admin/temple-info' ? 'active' : ''}">
            <span class="icon">📜</span> Official Info
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

        // Recent donations table
        const tbody = document.getElementById('recent-donations-body');
        if (stats.recent_donations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">No donations yet</td></tr>';
        } else {
            tbody.innerHTML = stats.recent_donations.map(d => `
                <tr>
                    <td>${d.donor_name}</td>
                    <td style="font-weight:700;color:var(--saffron);">${formatINR(d.amount)}</td>
                    <td>${d.donation_type}</td>
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

/**
 * Load all donations for admin.
 */
async function loadAdminDonations() {
    if (!checkAdminAuth()) return;
    renderAdminSidebar();

    try {
        const donations = await apiFetch('/donate/all');
        const tbody = document.getElementById('all-donations-body');
        if (donations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No donations</td></tr>';
        } else {
            tbody.innerHTML = donations.map(d => `
                <tr>
                    <td>${d.donor_name}</td>
                    <td>${d.donor_email || '—'}</td>
                    <td style="font-weight:700;">${formatINR(d.amount)}</td>
                    <td>${d.donation_type}</td>
                    <td><span class="status-badge ${d.status}">${d.status}</span></td>
                    <td>
                        <button class="receipt-badge-btn" onclick="downloadReceiptPdf('${d.id}', '${d.receipt_number}')" title="Download Official Receipt PDF">
                            📄 ${d.receipt_number || 'Receipt'}
                        </button>
                    </td>
                    <td>${formatDate(d.created_at)}</td>
                </tr>
            `).join('');
        }
    } catch (err) { console.error(err); }
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
                <td>${f.name_en}</td>
                <td>${f.name_kn}</td>
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
