// Guided tour engine (coach-marks): highlights the real element with a
// spotlight + bubble (Next/Skip, step counter, Esc/arrows). English, dark
// ocean style. One generic motor + per-screen step definitions.
(function () {
    const SEEN_KEY = 'swimcoach_tour_seen_v1';
    let active = null;

    function seenScreens() {
        try { return JSON.parse(localStorage.getItem(SEEN_KEY)) || {}; }
        catch { return {}; }
    }
    function markSeen(screen) {
        const s = seenScreens();
        s[screen] = true;
        try { localStorage.setItem(SEEN_KEY, JSON.stringify(s)); } catch { /* noop */ }
    }
    function neverShow() {
        try { localStorage.setItem(SEEN_KEY, JSON.stringify({ session: true, dashboard: true })); } catch { /* noop */ }
    }

    function elRect(sel) {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        if (!r.width && !r.height) return null;
        return { el, r };
    }

    function closeTour(mark) {
        if (mark && active) markSeen(active.screen);
        const ov = document.getElementById('tour-overlay');
        if (ov) ov.remove();
        active = null;
    }

    function renderStep() {
        const ov = document.getElementById('tour-overlay');
        if (!ov || !active) return;
        const step = active.steps[active.idx];
        const found = elRect(step.sel);
        const spot = ov.querySelector('.tour-spot');
        const bubble = ov.querySelector('.tour-bubble');
        const count = ov.querySelector('.tour-count');
        count.textContent = `${active.idx + 1} of ${active.steps.length}`;
        ov.querySelector('.tour-title').textContent = step.title;
        ov.querySelector('.tour-text').textContent = step.text;
        ov.querySelector('.tour-next').textContent =
            active.idx === active.steps.length - 1 ? 'Finish ✓' : 'Next →';
        if (!found) {
            // Element not on screen (e.g. empty state): show centered notice
            spot.style.display = 'none';
            bubble.style.cssText = 'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);max-width:min(420px,90vw);';
            return;
        }
        spot.style.display = 'block';
        const pad = 8;
        spot.style.cssText = `position:fixed;left:${found.r.left - pad + window.scrollX * 0}px;top:${found.r.top - pad}px;` +
            `width:${found.r.width + pad * 2}px;height:${found.r.height + pad * 2}px;` +
            'border:2px solid var(--primary);border-radius:14px;box-shadow:0 0 0 9999px rgba(4,14,26,.72);pointer-events:none;';
        found.el.scrollIntoView({ block: 'center', behavior: 'smooth' });
        // Bubble below the element, or above if no room
        const below = found.r.bottom + 16 + 180 < window.innerHeight;
        bubble.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);max-width:min(420px,92vw);' +
            (below ? `top:${found.r.bottom + 16}px;` : 'bottom:16px;');
    }

    function startTour(screen, steps) {
        closeTour(false);
        if (!steps || !steps.length) return;
        active = { screen, steps, idx: 0 };
        const ov = document.createElement('div');
        ov.id = 'tour-overlay';
        ov.style.cssText = 'position:fixed;inset:0;z-index:2000;';
        ov.innerHTML = `
            <div class="tour-spot"></div>
            <div class="tour-bubble card" style="padding: 1.25rem;">
                <div class="tour-count" style="font-size: 11px; color: var(--muted-color); text-transform: uppercase; letter-spacing: .06em;"></div>
                <h3 class="tour-title" style="margin: 0.25rem 0 0.5rem;"></h3>
                <p class="tour-text" style="margin: 0 0 1rem; color: var(--muted-color); font-size: 0.9rem; line-height: 1.5;"></p>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="big-btn secondary tour-skip" style="margin-top: 0; padding: 12px;">Skip</button>
                    <button class="big-btn tour-next" style="margin-top: 0; padding: 12px; flex: 2;">Next →</button>
                </div>
                <button class="tour-never" style="background: none; border: none; color: var(--muted-color); font-size: 12px; margin-top: 0.75rem; cursor: pointer; text-decoration: underline;">Don't show again</button>
            </div>`;
        document.body.appendChild(ov);
        ov.querySelector('.tour-skip').addEventListener('click', () => closeTour(true));
        ov.querySelector('.tour-never').addEventListener('click', () => { neverShow(); closeTour(false); });
        ov.querySelector('.tour-next').addEventListener('click', () => {
            if (active.idx < active.steps.length - 1) {
                active.idx += 1;
                renderStep();
            } else {
                closeTour(true);
            }
        });
        document.addEventListener('keydown', tourKeys);
        renderStep();
    }

    function tourKeys(e) {
        if (!active) {
            document.removeEventListener('keydown', tourKeys);
            return;
        }
        if (e.key === 'Escape') closeTour(true);
        if (e.key === 'ArrowRight') {
            if (active.idx < active.steps.length - 1) { active.idx += 1; renderStep(); }
            else closeTour(true);
        }
        if (e.key === 'ArrowLeft' && active.idx > 0) { active.idx -= 1; renderStep(); }
    }

    function maybeAutoTour(screen) {
        const seen = seenScreens();
        if (seen[screen]) return;
        const steps = screen === 'session' ? SESSION_STEPS : DASHBOARD_STEPS;
        // Small delay so the view finishes rendering first
        setTimeout(() => {
            if (seenScreens()[screen]) return;
            startTour(screen, steps);
        }, 900);
    }

    const SESSION_STEPS = [
        { sel: '.tabs', title: 'Swim & strength tabs', text: 'Each day can have a swim session, a strength session, or both. Switch tabs to see each one.' },
        { sel: '#start-player-btn', title: 'Guided player', text: 'Start guided session walks you block by block with a rest timer — ideal on deck.' },
        { sel: '.tipo-badge', title: 'CSS zone badges', text: 'Badges like Z3 show the intensity zone derived from your Critical Swim Speed. SPM is your target stroke rate.' },
        { sel: '#tab-content', title: 'Sets in detail', text: 'Every set shows reps × distance, rest, pace and gear. Metronome sets show the exact SPM to dial in.' },
        { sel: '.player-nav, #btn-siguiente', title: 'Player controls', text: 'In the player: previous/next block, rest timer presets, and a mandatory effort log (1-5) at the end.' },
        { sel: '#btn-exit-player, .bottomnav', title: 'Bottom navigation', text: 'Today, Week, Session, Log and Profile are always one tap away at the bottom.' },
    ];

    const DASHBOARD_STEPS = [
        { sel: '.countdown', title: 'Race countdown', text: 'Days left until your competition, computed from your macrocycle.' },
        { sel: '.session-card', title: 'Tier & target pace', text: 'Your ML-calibrated tier and CSS target pace appear here when you take the swim test.' },
        { sel: '#start-player-btn, .big-btn', title: "Today's session", text: 'Jump straight into today\'s guided session or log feedback for completed work.' },
        { sel: '.card', title: 'Retest reminder', text: 'Every 6 weeks we ask for a fresh CSS test so zones and tiers stay honest.' },
    ];

    window.startTour = startTour;
    window.maybeAutoTour = maybeAutoTour;
    window.closeTour = closeTour;
    window.showGuide = function (screen) {
        startTour(screen, screen === 'session' ? SESSION_STEPS : DASHBOARD_STEPS);
    };
})();
