// Profile View
async function renderProfile(app) {
    const profile = app.state.profile;
    const tier = app.state.tier;
    const user = app.state.user;
    
    const html = `
        <div class="profile-view" style="max-width: 600px; margin: 0 auto;">
            <header style="margin-bottom: 1.5rem;">
                <h1>Profile</h1>
                <p style="color: var(--muted-color); margin: 0;">${user?.email} • ${tier === 'pro' ? '🌟 Pro' : 'Free'}</p>
            </header>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Subscription</h2>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: ${tier === 'pro' ? 'var(--success-background)' : 'var(--warning-background)'}; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <div>
                        <strong style="font-size: 1.25rem;">${tier === 'pro' ? '🌟 Pro' : 'Free'}</strong>
                        <div style="color: var(--muted-color); font-size: 0.875rem;">
                            ${tier === 'pro' 
                                ? `Active until ${user.current_period_end ? new Date(user.current_period_end).toLocaleDateString() : '—'}`
                                : 'Upgrade for unlimited history, readiness score, charts, and no ads'
                            }
                        </div>
                    </div>
                    <a href="#/upgrade" class="primary">${tier === 'pro' ? 'Manage Subscription' : 'Upgrade to Pro'}</a>
                </div>
            </section>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Profile Settings</h2>
                <form id="profile-form">
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="level">Level</label>
                        <select id="level" name="level" required>
                            <option value="beginner" ${app.state.profile?.level === 'beginner' ? 'selected' : ''}>Beginner</option>
                            <option value="intermediate" ${app.state.profile?.level === 'intermediate' ? 'selected' : ''}>Intermediate</option>
                            <option value="advanced" ${app.state.profile?.level === 'advanced' ? 'selected' : ''}>Advanced</option>
                        </select>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="swim_days_per_week">Swim Days/Week</label>
                        <input type="number" id="swim_days_per_week" name="swim_days_per_week" min="3" max="6" value="${app.state.profile?.swim_days_per_week || 4}" required>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="target_volume_per_session">Target Volume/Session (m)</label>
                        <input type="number" id="target_volume_per_session" name="target_volume_per_session" min="1500" max="8000" step="100" value="${app.state.profile?.target_volume_per_session || 3000}" required>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="session_duration_min">Session Duration (min)</label>
                        <input type="number" id="session_duration_min" name="session_duration_min" min="45" max="150" value="${app.state.profile?.session_duration_min || 90}" required>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="ftp_pace_per_100">FTP Pace/100m (sec, optional)</label>
                        <input type="number" id="ftp_pace_per_100" name="ftp_pace_per_100" min="60" max="300" value="${app.state.profile?.ftp_pace_per_100 || ''}" placeholder="e.g., 95 = 1:35/100m">
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="primary_goal">Primary Goal</label>
                        <select id="primary_goal" name="primary_goal">
                            <option value="endurance" ${app.state.profile?.primary_goal === 'endurance' ? 'selected' : ''}>Endurance</option>
                            <option value="speed" ${app.state.profile?.primary_goal === 'speed' ? 'selected' : ''}>Speed</option>
                            <option value="technique" ${app.state.profile?.primary_goal === 'technique' ? 'selected' : ''}>Technique</option>
                            <option value="mixed" ${app.state.profile?.primary_goal === 'mixed' ? 'selected' : ''}>Mixed</option>
                        </select>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="available_days">Training Days</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => `
                                <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;">
                                    <input type="checkbox" name="available_days" value="${i === 6 ? 0 : i}" ${(app.state.profile?.available_days || [1,3,5]).includes(i === 6 ? 0 : i) ? 'checked' : ''} onchange="updateDays()">
                                    ${d}
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="preferred_strokes">Preferred Strokes</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            ${['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'im'].map(s => `
                                <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;">
                                    <input type="checkbox" name="preferred_strokes" value="${s}" ${(app.state.profile?.preferred_strokes || ['freestyle']).includes(s) ? 'checked' : ''} onchange="updateStrokes()">
                                    ${s.charAt(0).toUpperCase() + s.slice(1)}
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="available_equipment">Swim Equipment</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            ${['pull_buoy', 'paddles', 'fins', 'snorkel', 'kickboard', 'metronome'].map(e => `
                                <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;">
                                    <input type="checkbox" name="available_equipment" value="${e}" ${(app.state.profile?.available_equipment || []).includes(e) ? 'checked' : ''} onchange="updateEquipment(this)">
                                    ${e.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </label>
                            `).join('')}
                        </div>
                    </div>

                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="available_equipment">Strength Equipment</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            ${['bodyweight', 'bands', 'kettlebell', 'trx'].map(e => `
                                <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;">
                                    <input type="checkbox" name="available_equipment" value="${e}" ${(app.state.profile?.available_equipment || []).includes(e) || e === 'bodyweight' ? 'checked' : ''} onchange="updateEquipment(this)">
                                    ${e.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}${e === 'bodyweight' ? ' (always)' : ''}
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="grid" style="margin-bottom: 1rem;">
                        <label for="injury_notes">Injury Notes</label>
                        <textarea id="injury_notes" name="injury_notes" rows="3" placeholder="Shoulder issues, knee problems, etc.">${app.state.profile?.injury_notes || ''}</textarea>
                    </div>
                    
                    <button type="submit" class="primary" id="profile-save-btn">Save Profile</button>
                </form>
            </section>
            
            <section class="card" style="margin-bottom: 1.5rem; padding: 1.5rem; border: 1px solid var(--error-color); background: var(--error-background);">
                <h3 style="margin: 0 0 0.5rem; color: var(--error-color);">⚠️ Danger Zone</h3>
                <p style="margin: 0 0 1rem; color: var(--muted-color);">These actions are irreversible.</p>
                <button class="secondary" style="background: var(--error-color); color: white; border: none;" onclick="exportData()">📥 Export My Data</button>
                <button class="secondary" style="background: var(--error-color); color: white; border: none; margin-left: 0.5rem;" onclick="confirmDelete()">🗑️ Delete Account</button>
            </section>
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
    
    // Add form handler
    document.getElementById('profile-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveProfile();
    });
}

async function saveProfile() {
    const form = document.getElementById('profile-form');
    const formData = new FormData(form);
    
    const data = {
        level: formData.get('level'),
        swim_days_per_week: parseInt(formData.get('swim_days_per_week')),
        target_volume_per_session: parseInt(formData.get('target_volume_per_session')),
        session_duration_min: parseInt(formData.get('session_duration_min')),
        primary_goal: formData.get('primary_goal'),
        ftp_pace_per_100: formData.get('ftp_pace_per_100') ? parseInt(formData.get('ftp_pace_per_100')) : null,
        injury_notes: formData.get('injury_notes') || '',
        available_days: Array.from(form.querySelectorAll('input[name="available_days"]:checked')).map(cb => parseInt(cb.value)),
        preferred_strokes: Array.from(form.querySelectorAll('input[name="preferred_strokes"]:checked')).map(cb => cb.value),
        available_equipment: Array.from(new Set(
            Array.from(form.querySelectorAll('input[name="available_equipment"]:checked')).map(cb => cb.value)
                .concat(['bodyweight'])
        ))
    };
    
    try {
        const btn = document.getElementById('profile-save-btn');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }
        await api.updateProfile(data);
        window.app.showSuccess('Profile updated!');
        await window.app.loadProfile();
        if (btn) { btn.disabled = false; btn.textContent = 'Save Profile'; }
    } catch (error) {
        window.app.showError(error.message);
        const btn = document.getElementById('profile-save-btn');
        if (btn) { btn.disabled = false; btn.textContent = 'Save Profile'; }
    }
}

function highlightToggle(input) {
    if (input && input.parentElement) {
        input.parentElement.style.background = input.checked ? 'var(--primary-background)' : '';
    }
}
function updateDays(input) { highlightToggle(input || window.event?.target); }
function updateStrokes(input) { highlightToggle(input || window.event?.target); }
function updateEquipment(input) { highlightToggle(input || window.event?.target); }

async function exportData() {
    if (window.exportSwimData && window.app) return window.exportSwimData(window.app);
}

function confirmDelete() {
    if (prompt('This will permanently delete your account and all data. Type "DELETE MY ACCOUNT" to confirm:') === 'DELETE MY ACCOUNT') {
        window.app.showError('Delete account API not yet implemented');
    }
}

window.renderProfile = renderProfile;
window.saveProfile = saveProfile;
window.updateDays = updateDays;
window.updateStrokes = updateStrokes;
window.updateEquipment = updateEquipment;
window.exportData = exportData;
window.confirmDelete = confirmDelete;