// Settings View
async function renderSettings(app) {
    const html = `
        <div class="settings-view" style="max-width: 600px; margin: 0 auto;">
            <header style="margin-bottom: 1.5rem;">
                <h1>Settings</h1>
                <p style="color: var(--muted-color); margin: 0;">App preferences and data management</p>
            </header>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Notifications</h2>
                <p style="color: var(--muted-color); margin-bottom: 1rem;">Push notifications coming in future update</p>
                
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; background: var(--muted-background); border-radius: 0.5rem;">
                    <div>
                        <strong>Daily Training Reminder</strong>
                        <div style="color: var(--muted-color); font-size: 0.875rem;">Get notified at your preferred training time</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" disabled>
                        <span class="slider"></span>
                    </label>
                </div>
            </section>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Account</h2>
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                    <div>
                        <strong>Log out</strong>
                        <div style="font-size: 0.875rem; color: var(--muted-color);">Sign in with a different account</div>
                    </div>
                    <button class="secondary" onclick="logOut()">Log out</button>
                </div>
            </section>

            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Change password</h2>
                <form id="password-form" onsubmit="return false;">
                    <div style="margin-bottom: 1rem;">
                        <label for="pw-current">Current password</label>
                        <input type="password" id="pw-current" autocomplete="current-password" required minlength="1">
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <label for="pw-new">New password (min 8 characters)</label>
                        <input type="password" id="pw-new" autocomplete="new-password" required minlength="8">
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <label for="pw-confirm">Confirm new password</label>
                        <input type="password" id="pw-confirm" autocomplete="new-password" required minlength="8" oninput="hideFieldError('pw-error')">
                        <p class="field-error" id="pw-error"></p>
                    </div>
                    <button type="submit" class="primary" id="pw-submit" onclick="changePassword()">Update password</button>
                </form>
            </section>

            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Data & Privacy</h2>
                
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <button class="secondary" onclick="exportData()" style="text-align: left;">
                        <strong>📥 Export My Data</strong>
                        <div style="font-size: 0.875rem; color: var(--muted-color);">Download all your data as JSON</div>
                    </button>
                    
                    <button class="secondary" onclick="clearCache()" style="text-align: left;">
                        <strong>🧹 Clear Offline Cache</strong>
                        <div style="font-size: 0.875rem; color: var(--muted-color);">Clear stored data for fresh start</div>
                    </button>
                    
                    <button class="secondary" style="background: var(--error-color); color: white; border: none;" onclick="confirmDeleteAll()" style="text-align: left;">
                        <strong>🗑️ Delete All Data</strong>
                        <div style="font-size: 0.875rem; color: var(--muted-color);">Permanently delete all local data</div>
                    </button>
                </div>
            </section>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">About</h2>
                <div style="color: var(--muted-color); font-size: 0.875rem;">
                    <p><strong>SwimCoach</strong> v1.0.0</p>
                    <p>Competition-focused periodization for swimmers</p>
                    <p style="margin-top: 1rem;">
                        Built with FastAPI, Vanilla JS, and Pico.css<br>
                        PWA enabled • Works offline
                    </p>
                </div>
            </section>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem; border: 1px solid var(--error-color); background: var(--error-background);">
                <h2 style="margin: 0 0 0.5rem; color: var(--error-color);">Danger Zone</h2>
                <button class="secondary" style="background: var(--error-color); color: white; border: none; width: 100%;" onclick="confirmDeleteAccount()">
                    🗑️ Delete Account Permanently
                </button>
            </section>
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
}

function exportData() {
    if (window.exportSwimData && window.app) return window.exportSwimData(window.app);
    alert('Export not available - please log in first');
}

async function changePassword() {
    const current = document.getElementById('pw-current').value;
    const next = document.getElementById('pw-new').value;
    const confirm = document.getElementById('pw-confirm').value;
    if (!current || !next) {
        showFieldError('pw-error', 'Please complete all password fields.');
        return;
    }
    if (next.length < 8) {
        showFieldError('pw-error', 'New password must be at least 8 characters.');
        return;
    }
    if (next !== confirm) {
        showFieldError('pw-error', 'New passwords do not match.');
        return;
    }
    hideFieldError('pw-error');
    const btn = document.getElementById('pw-submit');
    btn.disabled = true;
    btn.textContent = 'Updating…';
    try {
        await api.changePassword(current, next);
        document.getElementById('pw-current').value = '';
        document.getElementById('pw-new').value = '';
        document.getElementById('pw-confirm').value = '';
        window.app.showSuccess('Password updated.');
    } catch (err) {
        const msg = err.message || 'Password update failed';
        if (/incorrect|current password|401/i.test(msg)) {
            showFieldError('pw-error', 'Current password is incorrect.');
        } else {
            window.app.showError(msg);
        }
    } finally {
        btn.disabled = false;
        btn.textContent = 'Update password';
    }
}

function clearCache() {
    if (confirm('Clear all offline cached data? This will require re-downloading on next visit.')) {
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => caches.delete(name));
            });
        }
        localStorage.clear();
        sessionStorage.clear();
        alert('Cache cleared! Reload the page.');
        location.reload();
    }
}

function confirmDeleteAll() {
    if (confirm('Delete ALL local data including feedback, sessions, and settings? This cannot be undone.')) {
        if (confirm('Type "DELETE ALL" to confirm:')) {
            localStorage.clear();
            sessionStorage.clear();
            if ('caches' in window) {
                caches.keys().then(names => names.forEach(name => caches.delete(name)));
            }
            alert('All local data deleted. Reload the page.');
            location.reload();
        }
    }
}

async function confirmDeleteAccount() {
    if (!confirm('This will PERMANENTLY delete your account and ALL data from the server. This cannot be undone!')) return;
    const typed = prompt('Type DELETE to confirm account deletion:');
    if (typed !== 'DELETE') {
        window.app.showError('Deletion cancelled.');
        return;
    }
    try {
        await api.deleteAccount();
        await api.logout().catch(() => {});
        window.app.state.user = null;
        window.app.state.profile = null;
        window.app.state.competition = null;
        window.app.state.macrocycle = null;
        try { localStorage.clear(); } catch { /* noop */ }
        window.app.showSuccess('Account deleted.');
        setTimeout(() => { window.location.hash = '#/login'; }, 800);
    } catch (error) {
        window.app.showError(error.message || 'Delete failed');
    }
}

// Export
window.renderSettings = renderSettings;
window.exportData = exportData;
window.changePassword = changePassword;
window.clearCache = clearCache;
window.confirmDeleteAll = confirmDeleteAll;
window.confirmDeleteAccount = confirmDeleteAccount;