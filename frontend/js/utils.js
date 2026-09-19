// Shared helpers
async function exportSwimData(app) {
    try {
        const response = await api.getFeedbackHistory(1, 1000);
        const data = {
            profile: app.state.profile,
            competition: app.state.competition,
            feedback: response.items,
            exported_at: new Date().toISOString()
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `swimcoach-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        app.showSuccess('Data exported!');
    } catch (error) {
        app.showError('Export failed');
    }
}

window.exportSwimData = exportSwimData;
// Back-compat alias used by inline onclick="exportData()"
window.exportData = function () {
    if (window.app) return exportSwimData(window.app);
};

// Flash overlay (timer fallback when sound is muted, from entrenamiento-app)
function flashScreen(times) {
    const el = document.getElementById('flash-overlay');
    if (!el) return;
    el.classList.remove('flash-pulse');
    void el.offsetWidth;
    el.classList.add('flash-pulse');
    if (times && times > 1) {
        let n = 1;
        const iv = setInterval(() => {
            n += 1;
            if (n >= times) { clearInterval(iv); return; }
            el.classList.remove('flash-pulse');
            void el.offsetWidth;
            el.classList.add('flash-pulse');
        }, 600);
    }
}

// RPE effort modal (English 1-5, mandatory). Resolves with 1-5 or null if dismissed.
function askEffort(title) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('rpe-overlay');
        const options = document.getElementById('rpe-options');
        const err = document.getElementById('rpe-error');
        const confirmBtn = document.getElementById('rpe-confirm');
        if (!overlay || !options) { resolve(null); return; }
        document.getElementById('rpe-title').textContent = title || 'How did it feel?';
        const labels = ['Terrible', 'Poor', 'Okay', 'Good', 'Excellent'];
        const emojis = ['😩', '😕', '😐', '🙂', '🤩'];
        let selected = 0;
        err.style.display = 'none';
        options.innerHTML = '';
        for (let i = 1; i <= 5; i++) {
            const b = document.createElement('button');
            b.className = 'esfuerzo-btn';
            b.dataset.value = String(i);
            b.innerHTML = `<span class="emoji">${emojis[i - 1]}</span><span>${i} · ${labels[i - 1]}</span>`;
            b.addEventListener('click', () => {
                selected = i;
                err.style.display = 'none';
                options.querySelectorAll('.esfuerzo-btn').forEach(x => x.classList.toggle('selected', x.dataset.value === String(i)));
            });
            options.appendChild(b);
        }
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        const cleanup = (val) => {
            overlay.classList.remove('open');
            overlay.setAttribute('aria-hidden', 'true');
            confirmBtn.onclick = null;
            overlay.onclick = null;
            resolve(val);
        };
        confirmBtn.onclick = () => {
            if (!selected) { err.style.display = 'block'; return; }
            cleanup(selected);
        };
        overlay.onclick = (e) => { if (e.target === overlay) cleanup(null); };
    });
}

window.flashScreen = flashScreen;
window.askEffort = askEffort;

// One-tap pill checkboxes. The label handles the tap explicitly
// (preventDefault + manual flip) so selection always happens on the
// FIRST tap on desktop and touch — no double-tap quirk, no double-fire.
function pillClick(e, label) {
    if (e) e.preventDefault();
    const box = label ? label.querySelector('input[type="checkbox"]') : null;
    if (!box || box.disabled) return;
    box.checked = !box.checked;
    paintPill(box);
    box.dispatchEvent(new Event('change', { bubbles: true }));
}

function paintPill(box) {
    if (box && box.parentElement) {
        box.parentElement.style.background = box.checked ? 'var(--primary-background)' : '';
        box.parentElement.style.borderColor = box.checked ? 'var(--primary)' : '';
    }
}

window.pillClick = pillClick;
window.paintPill = paintPill;
