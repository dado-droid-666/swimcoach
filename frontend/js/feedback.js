// Feedback View
async function renderFeedback(app) {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const todayLocal = new Date().toLocaleDateString('en-CA');
    const preselectedDate = urlParams.get('date') || todayLocal;
    const preselectedType = urlParams.get('type') || 'swim';

    // Single shared pagination state (fixes split local/global `page` bug)
    window._fb = { items: [], page: 1, pageSize: 20, total: 0, loading: false };

    async function loadHistory(reset) {
        if (window._fb.loading) return;
        if (reset) {
            window._fb.page = 1;
            window._fb.items = [];
        }
        window._fb.loading = true;
        try {
            const data = await api.getFeedbackHistory(window._fb.page, window._fb.pageSize);
            window._fb.total = data.total || 0;
            window._fb.items = reset ? data.items : window._fb.items.concat(data.items);
            renderHistory();
        } catch (error) {
            app.showError('Failed to load feedback history');
        } finally {
            window._fb.loading = false;
        }
    }

    function renderHistory() {
        const history = window._fb.items;
        const list = history.map(f => `
            <article class="card" style="margin-bottom: 0.75rem; padding: 1rem;">
                <header style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>${window.app.formatDate(f.date)}</strong>
                    <span style="color: var(--muted-color); font-size: 0.875rem;">
                        ${f.swim_completed ? '🏊' : ''} ${f.strength_completed ? '💪' : ''}
                    </span>
                </header>
                <div style="display: flex; gap: 1rem; color: var(--muted-color); font-size: 0.875rem; margin-bottom: 0.5rem;">
                    ${f.swim_feeling !== null && f.swim_feeling !== undefined ? `<span>🏊 Swim: ${'★'.repeat(f.swim_feeling)}${'☆'.repeat(5 - f.swim_feeling)} (${f.swim_feeling}/5)</span>` : ''}
                    ${f.strength_feeling !== null && f.strength_feeling !== undefined ? `<span>💪 Strength: ${'★'.repeat(f.strength_feeling)}${'☆'.repeat(5 - f.strength_feeling)} (${f.strength_feeling}/5)</span>` : ''}
                </div>
                ${f.comments ? `<p style="margin: 0; font-size: 0.875rem;"></p>` : ''}
            </article>
        `).join('') || '<p style="text-align: center; color: var(--muted-color); padding: 2rem;">No feedback logged yet</p>';

        // NOTE: comments rendered escaped below to avoid HTML injection
        const listEl = document.getElementById('history-list');
        listEl.innerHTML = list;
        listEl.querySelectorAll('article.card').forEach((el, i) => {
            const p = el.querySelector('p');
            const item = history[i];
            if (p && item && item.comments) p.textContent = item.comments;
        });

        const totalEl = document.getElementById('history-total');
        if (totalEl) totalEl.textContent = window._fb.total ? `(${window._fb.total})` : '';
        const moreBtn = document.getElementById('load-more-btn');
        if (moreBtn) moreBtn.style.display = (window._fb.items.length < window._fb.total) ? '' : 'none';
    }

    window._fbReload = () => loadHistory(true);
    window.loadMoreFeedback = async () => {
        if (window._fb.items.length >= window._fb.total) return;
        window._fb.page += 1;
        await loadHistory(false);
    };
    
    const html = `
        <div class="feedback-view" style="max-width: 600px; margin: 0 auto;">
            <header style="margin-bottom: 1.5rem;">
                <h1>Feedback Log</h1>
                <p style="color: var(--muted-color); margin: 0;">Track how you feel after each session</p>
            </header>
            
            <!-- Feedback Form -->
            <section id="feedback-form" class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
                <h2 style="margin: 0 0 1rem;">Log Today's Session</h2>
                
                <div class="grid" style="margin-bottom: 1rem;">
                    <label for="feedback-date">Date</label>
                    <input type="date" id="feedback-date" value="${preselectedDate}" max="${todayLocal}">
                </div>
                
                <fieldset style="margin-bottom: 1rem; padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem;">
                    <legend style="margin-bottom: 0.5rem;">🏊 Swim Session</legend>
                    <div class="grid" style="margin-bottom: 0.5rem;">
                        <label>
                            <input type="checkbox" id="swim-completed" onchange="toggleSwimFields(this)">
                            Completed swim session
                        </label>
                    </div>
                    <div id="swim-fields" style="display: none; margin-top: 0.5rem;">
                        <div class="grid" style="margin-bottom: 0.5rem;">
                            <label for="swim-feeling">Feeling (1-5)</label>
                            <select id="swim-feeling">
                                <option value="">Select...</option>
                                <option value="1">★☆☆☆☆ Terrible</option>
                                <option value="2">★★☆☆☆ Poor</option>
                                <option value="3">★★★☆☆ Okay</option>
                                <option value="4" selected>★★★★☆ Good</option>
                                <option value="5">★★★★★ Excellent</option>
                            </select>
                        </div>
                        <div class="grid" style="margin-bottom: 0.5rem;">
                            <label for="swim-meters">Meters Completed</label>
                            <input type="number" id="swim-meters" min="0" step="100" placeholder="Meters">
                        </div>
                    </div>
                </fieldset>
                
                <fieldset style="margin-bottom: 1rem; padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem;">
                    <legend style="margin-bottom: 0.5rem;">💪 Strength Session</legend>
                    <div class="grid" style="margin-bottom: 0.5rem;">
                        <label>
                            <input type="checkbox" id="strength-completed" onchange="toggleStrengthFields(this)">
                            Completed strength session
                        </label>
                    </div>
                    <div id="strength-fields" style="display: none; margin-top: 0.5rem;">
                        <div class="grid" style="margin-bottom: 0.5rem;">
                            <label for="strength-feeling">Feeling (1-5)</label>
                            <select id="strength-feeling">
                                <option value="">Select...</option>
                                <option value="1">★☆☆☆☆ Terrible</option>
                                <option value="2">★★☆☆☆ Poor</option>
                                <option value="3">★★★☆☆ Okay</option>
                                <option value="4" selected>★★★★☆ Good</option>
                                <option value="5">★★★★★ Excellent</option>
                            </select>
                        </div>
                    </div>
                </fieldset>
                
                <div class="grid" style="margin-bottom: 1rem;">
                    <label for="feedback-comments">Notes (optional)</label>
                    <textarea id="feedback-comments" rows="3" placeholder="How did it go? Any issues, adjustments, notes..."></textarea>
                </div>
                
                <button class="primary" onclick="submitFeedback()">Save Feedback</button>
            </section>
            
            <!-- History -->
            <section>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2 style="margin: 0;">History <span id="history-total" style="font-size: 0.875rem; color: var(--muted-color); font-weight: normal;"></span></h2>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="secondary" onclick="loadMoreFeedback()" id="load-more-btn">Load More</button>
                    </div>
                </div>
                
                <div id="history-list"></div>
            </section>
            
            ${app.state.tier === 'free' ? `
                <div id="ad-banner" style="margin-top: 2rem; text-align: center; min-height: 90px;">
                    <ins class="adsbygoogle"
                         style="display:block"
                          data-ad-client="ca-pub-4540036176937342"
                          data-ad-slot="2885278049"
                         data-ad-format="auto"
                         data-full-width-responsive="true"></ins>
                </div>
            ` : ''}
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
    
    // Pre-fill type
    if (preselectedType === 'swim') {
        document.getElementById('swim-completed').checked = true;
        toggleSwimFields(document.getElementById('swim-completed'));
    } else if (preselectedType === 'strength') {
        document.getElementById('strength-completed').checked = true;
        toggleStrengthFields(document.getElementById('strength-completed'));
    }
    
    loadHistory(true);
}

function toggleSwimFields(checkbox) {
    const el = document.getElementById('swim-fields');
    if (el) el.style.display = checkbox.checked ? 'block' : 'none';
}

function toggleStrengthFields(checkbox) {
    const el = document.getElementById('strength-fields');
    if (el) el.style.display = checkbox.checked ? 'block' : 'none';
}

async function submitFeedback() {
    const date = document.getElementById('feedback-date').value;
    
    const data = {
        date,
        swim_completed: document.getElementById('swim-completed').checked,
        strength_completed: document.getElementById('strength-completed').checked,
        comments: document.getElementById('feedback-comments').value
    };
    
    if (document.getElementById('swim-completed').checked) {
        data.swim_feeling = parseInt(document.getElementById('swim-feeling').value) || null;
        data.swim_completed_meters = parseInt(document.getElementById('swim-meters').value) || null;
    }
    
    if (document.getElementById('strength-completed').checked) {
        data.strength_feeling = parseInt(document.getElementById('strength-feeling').value) || null;
    }
    
    if (!data.swim_completed && !data.strength_completed) {
        alert('Please mark at least one session as completed');
        return;
    }
    
    if (data.swim_completed && !data.swim_feeling) {
        alert('Please select a feeling for swim');
        return;
    }
    
    if (data.strength_completed && !data.strength_feeling) {
        alert('Please select a feeling for strength');
        return;
    }
    
    try {
        await api.submitFeedback(data);
        window.app.showSuccess('Feedback saved!');
        
        // Reset form
        document.getElementById('swim-completed').checked = false;
        document.getElementById('strength-completed').checked = false;
        document.getElementById('swim-fields').style.display = 'none';
        document.getElementById('strength-fields').style.display = 'none';
        document.getElementById('swim-feeling').value = '';
        document.getElementById('strength-feeling').value = '';
        document.getElementById('swim-meters').value = '';
        document.getElementById('feedback-comments').value = '';
        
        // Reload history from page 1
        if (window._fbReload) await window._fbReload();
    } catch (error) {
        window.app.showError(error.message);
    }
}

// Export
window.renderFeedback = renderFeedback;
window.submitFeedback = submitFeedback;
window.toggleSwimFields = toggleSwimFields;
window.toggleStrengthFields = toggleStrengthFields;