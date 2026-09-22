// Session View (date helpers come from utils.js: parseISODate, mondayISO,
// localISO, shiftISO, normDate — single source, local timezone, no UTC shift)

async function findNearestSessions(dateISO) {
    // Scan ±14 days for the closest days with sessions (for rest-day card)
    const prev = [];
    const next = [];
    const seen = new Set();
    for (let off = 1; off <= 14; off++) {
        for (const [arr, delta] of [[prev, -off], [next, off]]) {
            const iso = window.shiftISO ? shiftISO(dateISO, delta) : dateISO;
            const wk = mondayISO(iso);
            if (seen.has(wk)) continue;
            seen.add(wk);
            try {
                const plan = await api.getWeekPlan(wk);
                const has = (plan.swim_sessions || []).concat(plan.strength_sessions || [])
                    .some(s => s.date === iso);
                if (has) arr.push(iso);
            } catch { /* ignore offline weeks */ }
        }
        if (prev.length && next.length) break;
    }
    return { prev: prev[0] || null, next: next[0] || null };
}

async function renderSession(app, dateParam) {
    const todayISO = window.localISO ? localISO(new Date()) : new Date().toLocaleDateString('en-CA');
    const date = dateParam === 'today' ? todayISO : dateParam;

    let sessionData;
    try {
        if (dateParam === 'today') {
            sessionData = await api.getTodayPlan();
        } else {
            const weekPlan = await api.getWeekPlan(mondayISO(date));
            const key = window.normDate ? normDate(date) : date;
            sessionData = {
                swim: weekPlan.swim_sessions.find(s => (window.normDate ? normDate(s.date) : s.date) === key) || null,
                strength: weekPlan.strength_sessions.find(s => (window.normDate ? normDate(s.date) : s.date) === key) || null
            };
        }
    } catch (error) {
        app.showError('Failed to load session');
        return;
    }
    
    const sessionDate = parseISODate(date);
    const dayName = sessionDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

    const swim = sessionData.swim;
    const strength = sessionData.strength;
    const prevISO = window.shiftISO ? shiftISO(date, -1) : date;
    const nextISO = window.shiftISO ? shiftISO(date, 1) : date;
    
    const html = `
        <div class="session-view" style="max-width: 800px; margin: 0 auto;">
            <header style="margin-bottom: 1rem;">
                <div class="topbar"><a href="#/dashboard" class="secondary" style="text-decoration: none; font-size: 0.875rem;">← Dashboard</a><span><a href="#" onclick="event.preventDefault();window.showGuide('session')" style="font-size: 0.875rem;" title="Take the tour">? Guide</a> · <a href="#/week?start=${mondayISO(date)}" style="font-size: 0.875rem;">Week →</a></span></div>
                <h1 style="margin: 0.5rem 0 0;">${dayName}</h1>
                <p style="color: var(--muted-color); margin: 0;">${swim?.phase_name || strength?.phase_name || 'Training'} • Week ${swim?.week_relative || strength?.week_relative || '?'}</p>
            </header>

            <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem;">
                <button class="secondary" style="flex: 1;" onclick="location.hash='#/session?date=${prevISO}'">← Prev day</button>
                <button class="secondary" style="flex: 1;" onclick="location.hash='#/session/today'">Today</button>
                <button class="secondary" style="flex: 1;" onclick="location.hash='#/session?date=${nextISO}'">Next day →</button>
            </div>

            <div id="rest-day-slot"></div>
            
            <div class="tabs" style="display: flex; border-bottom: 1px solid var(--border-color); margin-bottom: 1.5rem;" role="tablist">
                <button role="tab" class="tab-btn ${swim ? 'active' : ''}" data-tab="swim" ${!swim ? 'disabled' : ''} onclick="switchTab('swim')">
                    🏊 Swim ${swim ? `<span class="badge">${swim.total_meters.toLocaleString()}m</span>` : ''}
                </button>
                <button role="tab" class="tab-btn ${!swim && strength ? 'active' : ''}" data-tab="strength" ${!strength ? 'disabled' : ''} onclick="switchTab('strength')">
                    💪 Strength ${strength ? `<span class="badge">${strength.exercises?.length || 0} ex</span>` : ''}
                </button>
            </div>
            
            ${(swim || strength) ? `<button class="big-btn" id="start-player-btn" style="margin-bottom: 1.5rem;">▶ Start guided session</button>` : ''}

            <div id="player-view" style="display: none;">
                <div class="topbar"><span class="brand">Guided <b>session</b></span><span class="player-progress" id="player-progress"></span></div>
                <div class="progressbar-track"><div id="player-progress-bar" style="width: 0%;"></div></div>
                <div class="player-body" id="player-block"></div>
                <div class="rest-timer" id="rest-timer-wrap">
                    <div class="rest-timer-row">
                        <div id="timer-display">--:--</div>
                        <button id="timer-stop">stop</button>
                    </div>
                    <div class="timer-btns" id="timer-btns"></div>
                    <div class="timer-sound-hint">🔇 Enable sound (unmute) to hear the alarm</div>
                </div>
                <div class="player-nav">
                    <button class="big-btn secondary" id="btn-anterior">←</button>
                    <button class="big-btn" id="btn-siguiente">Next →</button>
                </div>
                <button class="big-btn secondary" id="btn-exit-player">Exit player</button>
            </div>

            <div id="tab-content">
                ${swim ? renderSwimTab(swim) : ''}
                ${strength ? renderStrengthTab(strength) : ''}
            </div>
            
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
    
    // Show correct tab by default (null-safe: day may have only swim or only strength)
    const swimTab = document.getElementById('swim-tab');
    const strengthTab = document.getElementById('strength-tab');
    if (swimTab && strengthTab) {
        if (swim) {
            swimTab.style.display = 'block';
            strengthTab.style.display = 'none';
        } else {
            swimTab.style.display = 'none';
            strengthTab.style.display = 'block';
        }
    } else if (swimTab) {
        swimTab.style.display = 'block';
    } else if (strengthTab) {
        strengthTab.style.display = 'block';
    }

    wirePlayer(swim, strength);

    if (!swim && !strength) {
        renderRestDay(date);
    }

    if (window.maybeAutoTour) maybeAutoTour('session');
}

async function renderRestDay(dateISO) {
    const slot = document.getElementById('rest-day-slot');
    if (!slot) return;
    slot.innerHTML = `
        <article class="card" style="margin-bottom: 1.5rem; text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">😴</div>
            <h2 style="margin: 0 0 0.5rem;">Rest day</h2>
            <p style="color: var(--muted-color); margin: 0 0 1rem;">Your plan schedules no training for this day. Recovery is part of the program.</p>
            <div id="nearest-sessions" style="color: var(--muted-color); font-size: 0.875rem;">Looking for nearby sessions…</div>
        </article>`;
    try {
        const { prev, next } = await findNearestSessions(dateISO);
        const box = document.getElementById('nearest-sessions');
        if (!box) return;
        if (!prev && !next) {
            box.textContent = 'No sessions found within ±14 days.';
            return;
        }
        box.innerHTML = `
            <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;">
                ${prev ? `<button class="secondary" onclick="location.hash='#/session?date=${prev}'">← ${prev}</button>` : ''}
                ${next ? `<button class="secondary" onclick="location.hash='#/session?date=${next}'">${next} →</button>` : ''}
            </div>`;
    } catch {
        const box = document.getElementById('nearest-sessions');
        if (box) box.textContent = '';
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    const swimTab = document.getElementById('swim-tab');
    const strengthTab = document.getElementById('strength-tab');
    if (swimTab) swimTab.style.display = tab === 'swim' ? 'block' : 'none';
    if (strengthTab) strengthTab.style.display = tab === 'strength' ? 'block' : 'none';
}

function renderSwimTab(swim) {
    const paceStr = swim.main_set?.[0]?.target_pace_per_100 
        ? `${Math.floor(swim.main_set[0].target_pace_per_100 / 60)}:${String(swim.main_set[0].target_pace_per_100 % 60).padStart(2, '0')}/100m`
        : '—';
    
    return `
        <div id="swim-tab" style="display: block;">
            <article class="card" style="margin-bottom: 1rem;">
                <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <h2 style="margin: 0;">🏊 Swim Session</h2>
                        <p style="margin: 0; color: var(--muted-color);">${swim.focus} • RPE ${swim.rpe_target}/10</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--primary);">${swim.total_meters.toLocaleString()}m</div>
                        <div style="color: var(--muted-color); font-size: 0.875rem;">~${swim.estimated_duration_min} min</div>
                    </div>
                </header>
                
                <section style="margin-bottom: 1.5rem;">
                    <h3 style="margin: 0 0 0.5rem; color: var(--primary);">🏁 Warmup (${swim.warmup?.meters || 0}m)</h3>
                    <p style="margin: 0; color: var(--muted-color);">${swim.warmup?.description || '—'}</p>
                    ${swim.warmup?.drills?.length ? `
                        <ul style="margin: 0.5rem 0 0; padding-left: 1.5rem; color: var(--muted-color);">
                            ${swim.warmup.drills.map(d => `<li>${d}</li>`).join('')}
                        </ul>
                    ` : ''}
                </section>
                
                <section style="margin-bottom: 1.5rem;">
                    <h3 style="margin: 0 0 0.5rem; color: var(--primary);">🎯 Main Set (${swim.main_set?.reduce((sum, s) => sum + (s.meters || 0), 0) || 0}m)</h3>
                    <p style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Target pace: ~${swim.main_set?.[0]?.target_pace_per_100 ? formatPace(swim.main_set[0].target_pace_per_100) : '—'}</p>
                    
                    ${swim.main_set?.map((set, i) => `
                        <article class="card" style="margin-bottom: 0.75rem; padding: 1rem;">
                            <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <h4 style="margin: 0;">Set ${i + 1}: ${set.description}</h4>
                                <span style="background: var(--primary-background); color: var(--primary); padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.75rem;">${set.intensity_zone || 'Z2'}</span>
                            </header>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem; font-size: 0.875rem; color: var(--muted-color);">
                                <div><strong>${set.reps}×${set.distance}m</strong> ${set.stroke}</div>
                                <div>Rest: ${set.rest_seconds}s</div>
                                <div>Pace: ${set.target_pace_per_100 ? formatPace(set.target_pace_per_100) : '—'}</div>
                                <div>Equip: ${set.equipment?.join(', ') || 'None'}</div>
                                ${set.css_zone ? `<div><span class="tipo-badge tipo-alberca">${set.css_zone}</span></div>` : ''}
                                ${set.stroke_rate_spm ? `<div>⏱️ Rate: <strong>${set.stroke_rate_spm} SPM</strong> (metronome)</div>` : (set.target_spm ? `<div>Tempo guide: ${set.target_spm} SPM</div>` : '')}
                            </div>
                            ${set.notes ? `<p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">${set.notes}</p>` : ''}
                        </article>
                    `).join('') || '<p style="color: var(--muted-color);">No main sets defined</p>'}
                </section>
                
                <section>
                    <h3 style="margin: 0 0 0.5rem; color: var(--primary);">🧘 Cooldown (${swim.cooldown?.meters || 0}m)</h3>
                    <p style="margin: 0; color: var(--muted-color);">${swim.cooldown?.description || '—'}</p>
                </section>
                
                <div style="margin-top: 2rem; display: flex; gap: 1rem;">
                    <button class="primary" onclick="completeSession('swim')">✅ Mark Complete</button>
                    <button class="secondary" onclick="logFeedback('swim')">📝 Log Feedback</button>
                </div>
            </div>
        </div>
    `;
}

function renderStrengthTab(strength) {
    return `
        <div id="strength-tab" style="display: none;">
            <article class="card" style="margin-bottom: 1rem;">
                <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <h2 style="margin: 0;">💪 Strength Session</h2>
                        <p style="margin: 0; color: var(--muted-color);">${strength.focus} • ${strength.exercises?.length || 0} exercises</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--warning-color);">${strength.estimated_duration_min} min</div>
                        <div style="color: var(--muted-color); font-size: 0.875rem;">Estimated</div>
                    </div>
                </header>
                
                ${strength.exercises?.map((ex, i) => `
                    <article class="card" style="margin-bottom: 0.75rem; padding: 1rem;">
                        <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <h4 style="margin: 0;">${ex.name}</h4>
                            <span style="background: var(--warning-background); color: var(--warning-color); padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.75rem;">RPE ${ex.rpe}</span>
                        </header>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.5rem; font-size: 0.875rem; color: var(--muted-color);">
                            <div><strong>${ex.sets} sets</strong> × ${ex.reps || ex.duration + 's'}</div>
                            <div>Rest: ${ex.rest}s</div>
                            <div>Tempo: ${ex.tempo || '—'}</div>
                        </div>
                        ${ex.progression ? `<p style="margin: 0.5rem 0 0; font-size: 0.875rem; color: var(--muted-color);">Progression: ${ex.progression}</p>` : ''}
                    </article>
                `).join('') || '<p style="color: var(--muted-color);">No exercises defined</p>'}
                
                <div style="margin-top: 2rem; display: flex; gap: 1rem;">
                    <button class="primary" onclick="completeSession('strength')">✅ Mark Complete</button>
                    <button class="secondary" onclick="logFeedback('strength')">📝 Log Feedback</button>
                </div>
            </div>
        </div>
    `;
}

function formatPace(seconds) {
    if (!seconds) return '—';
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    return `${min}:${String(sec).padStart(2, '0')}/100m`;
}

// ---------- Guided player (fused from entrenamiento-app) ----------
let _player = null;
let _timerId = null;
let _timerLeft = 0;

function buildPlayerBlocks(swim, strength) {
    const blocks = [];
    if (swim) {
        if (swim.warmup) blocks.push({ kind: 'swim', tag: 'Warmup', title: `Warmup · ${swim.warmup.meters || 0}m`, desc: swim.warmup.description || 'Easy swimming', sub: (swim.warmup.drills || []).join(' · ') });
        (swim.main_set || []).forEach((s, i) => {
            blocks.push({
                kind: 'swim', tag: `Main set ${i + 1}/${swim.main_set.length}${s.css_zone ? ` · ${s.css_zone}` : ''}`,
                title: s.description || `Set ${i + 1}`,
                desc: `${s.reps}×${s.distance}m ${s.stroke || ''}`.trim(),
                sub: [`Rest ${s.rest_seconds || 0}s`, s.target_pace_per_100 ? `Pace ${formatPace(s.target_pace_per_100)}` : null, (s.equipment || []).length ? `Gear: ${s.equipment.join(', ')}` : null, s.stroke_rate_spm ? `⏱️ ${s.stroke_rate_spm} SPM` : (s.target_spm ? `${s.target_spm} SPM` : null), s.notes || null].filter(Boolean).join(' · ')
            });
        });
        if (swim.cooldown) blocks.push({ kind: 'swim', tag: 'Cooldown', title: `Cooldown · ${swim.cooldown.meters || 0}m`, desc: swim.cooldown.description || 'Very easy' });
    }
    if (strength) {
        (strength.exercises || []).forEach((ex, i) => {
            blocks.push({
                kind: 'strength', tag: `Exercise ${i + 1}/${strength.exercises.length}`,
                title: ex.name, desc: `${ex.sets} sets × ${ex.reps || (ex.duration + 's')}`,
                sub: [`Rest ${ex.rest || 60}s`, ex.tempo ? `Tempo ${ex.tempo}` : null, `RPE ${ex.rpe}`, ex.progression || null].filter(Boolean).join(' · '),
                rest: ex.rest || 60
            });
        });
    }
    return blocks;
}

function renderPlayerBlock() {
    const total = _player.blocks.length;
    const b = _player.blocks[_player.idx];
    document.getElementById('player-progress').textContent = `Block ${_player.idx + 1} of ${total}${_player.mlLabel ? ` · ${_player.mlLabel}` : ''}`;
    document.getElementById('player-progress-bar').style.width = `${((_player.idx + 1) / total) * 100}%`;
    document.getElementById('player-block').innerHTML = `
        <div class="block-title">${b.kind === 'swim' ? '🏊' : '💪'} ${b.tag}</div>
        <div class="block-desc">${b.title}</div>
        <div style="color: var(--muted-color); font-size: 15px;">${b.desc || ''}</div>
        ${b.sub ? `<div style="color: var(--muted-color); font-size: 13px; margin-top: 8px;">${b.sub}</div>` : ''}
    `;
    document.getElementById('btn-anterior').disabled = _player.idx === 0;
    document.getElementById('btn-siguiente').textContent = _player.idx === total - 1 ? 'Finish ✓' : 'Next →';
    setupRestTimer(b.kind === 'strength' ? (b.rest || 60) : 0);
}

function setupRestTimer(suggested) {
    stopTimer();
    const wrap = document.getElementById('rest-timer-wrap');
    const btns = document.getElementById('timer-btns');
    if (!wrap || !btns) return;
    if (!suggested) { wrap.classList.remove('open'); btns.innerHTML = ''; return; }
    wrap.classList.add('open');
    const presets = [15, 30, 45, 60, 90, 120];
    btns.innerHTML = '';
    presets.forEach(sec => {
        const b = document.createElement('button');
        b.className = 'timer-btn' + (sec === suggested ? ' suggested' : '');
        b.textContent = sec >= 60 ? `${sec / 60}m` : `${sec}s`;
        b.addEventListener('click', () => startTimer(sec));
        btns.appendChild(b);
    });
    document.getElementById('timer-display').textContent = 'Rest';
    document.getElementById('timer-stop').onclick = stopTimer;
}

function startTimer(seconds) {
    stopTimer();
    _timerLeft = seconds;
    const disp = document.getElementById('timer-display');
    const tick = () => {
        const m = Math.floor(_timerLeft / 60);
        const s = _timerLeft % 60;
        disp.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        if (_timerLeft <= 0) { stopTimer(); beep(); flashScreen(3); disp.textContent = 'Go!'; return; }
        _timerLeft -= 1;
        _timerId = setTimeout(tick, 1000);
    };
    tick();
}

function stopTimer() {
    if (_timerId) { clearTimeout(_timerId); _timerId = null; }
}

function beep() {
    try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        if (!Ctx) return;
        const ctx = new Ctx();
        [0, 0.25, 0.5].forEach((t, i) => {
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.frequency.value = i === 2 ? 880 : 660;
            o.start(ctx.currentTime + t);
            o.stop(ctx.currentTime + t + 0.2);
        });
    } catch (e) { /* silent devices fall back to flash */ }
}

async function finishPlayer() {
    const hasSwim = _player.blocks.some(b => b.kind === 'swim');
    const hasStrength = _player.blocks.some(b => b.kind === 'strength');
    const isPro = window.app && window.app.state.tier === 'pro';
    const items = await openExerciseLog(_player.swimRef, _player.strengthRef, isPro);
    if (items === null && !isPro) return; // free must log effort
    const today = window.localISO ? localISO(new Date()) : new Date().toLocaleDateString('en-CA');
    try {
        if (items && items.length) {
            await api.submitExerciseLogs(items.map(it => ({
                date: today,
                session_type: it.session_type,
                exercise_name: it.name,
                weight_kg: it.weight === '' || it.weight == null ? null : parseFloat(it.weight),
                reps: it.reps || null,
                time_seg: it.time_seg != null ? it.time_seg : null,
                effort: it.effort || null,
            })));
        }
        const avg = (arr) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null;
        const swimEff = items ? avg(items.filter(i => i.session_type === 'swim' && i.effort).map(i => i.effort)) : null;
        const strEff = items ? avg(items.filter(i => i.session_type === 'strength' && i.effort).map(i => i.effort)) : null;
        const meters = items ? items.filter(i => i.session_type === 'swim').reduce((a, i) => a + (parseInt(i.meters) || 0), 0) || null : null;
        await api.submitFeedback({
            date: today,
            swim_completed: hasSwim,
            strength_completed: hasStrength,
            swim_feeling: swimEff,
            strength_feeling: strEff,
            swim_completed_meters: meters,
            comments: ''
        });
        window.app.showSuccess(items ? 'Session complete! Feedback saved.' : 'Session marked complete.');
        exitPlayer();
    } catch (err) {
        window.app.showError(err.message || 'Could not save feedback');
    }
}

// Per-exercise log modal (bottom-sheet). Free: effort 1-5 mandatory per
// item to finish. Pro: Skip button visible, weight/reps always optional.
// Resolves with items array, null on skip, or null on dismiss (free blocks).
function openExerciseLog(swim, strength, isPro) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('exlog-overlay');
        if (!overlay) { resolve([]); return; }
        const items = [];
        if (strength && strength.exercises) {
            strength.exercises.forEach(ex => items.push({
                session_type: 'strength', name: ex.name,
                weight: '', reps: ex.reps || '', time_seg: ex.duration || null, effort: 0,
            }));
        }
        if (swim) {
            items.push({
                session_type: 'swim', name: `Swim — ${swim.focus || 'session'}`,
                meters: swim.total_meters || null, effort: 0,
            });
        }
        if (!items.length) { resolve([]); return; }
        let idx = 0;
        const title = document.getElementById('exlog-title');
        const prog = document.getElementById('exlog-progress');
        const body = document.getElementById('exlog-body');
        const err = document.getElementById('exlog-error');
        const nextBtn = document.getElementById('exlog-next');
        const backBtn = document.getElementById('exlog-back');
        const skipBtn = document.getElementById('exlog-skip');
        const labels = ['Terrible', 'Poor', 'Okay', 'Good', 'Excellent'];
        const emojis = ['😩', '😕', '😐', '🙂', '🤩'];
        skipBtn.style.display = isPro ? 'block' : 'none';

        const cleanup = (val) => {
            overlay.classList.remove('open');
            overlay.setAttribute('aria-hidden', 'true');
            nextBtn.onclick = backBtn.onclick = skipBtn.onclick = null;
            resolve(val);
        };
        const render = () => {
            const it = items[idx];
            err.style.display = 'none';
            prog.textContent = `Exercise ${idx + 1} of ${items.length}${isPro ? ' (Pro: skippable)' : ''}`;
            title.textContent = it.name;
            const eBtns = labels.map((lb, i) => `
                <button class="esfuerzo-btn ${it.effort === i + 1 ? 'selected' : ''}" data-v="${i + 1}">
                    <span class="emoji">${emojis[i]}</span><span>${i + 1} · ${lb}</span>
                </button>`).join('');
            body.innerHTML = `
                ${it.session_type === 'strength' ? `
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem;">
                        <label style="flex: 1; font-size: 12px; color: var(--muted-color);">Weight (kg, optional)<input id="exlog-weight" type="number" min="0" step="0.5" value="${it.weight}" style="width: 100%; margin-top: 4px;"></label>
                        <label style="flex: 1; font-size: 12px; color: var(--muted-color);">Reps (optional)<input id="exlog-reps" type="text" value="${it.reps || ''}" style="width: 100%; margin-top: 4px;"></label>
                    </div>` : `
                    <div style="margin-bottom: 0.75rem;">
                        <label style="font-size: 12px; color: var(--muted-color);">Meters completed<input id="exlog-meters" type="number" min="0" step="25" value="${it.meters || ''}" style="width: 100%; margin-top: 4px;"></label>
                    </div>`}
                <p style="font-size: 13px; color: var(--muted-color); margin: 0 0 8px;">How did it feel? (1-5, required${isPro ? ' unless skipped' : ''})</p>
                <div class="esfuerzo-opciones">${eBtns}</div>`;
            body.querySelectorAll('.esfuerzo-btn').forEach(b => b.addEventListener('click', () => {
                it.effort = parseInt(b.dataset.v);
                err.style.display = 'none';
                body.querySelectorAll('.esfuerzo-btn').forEach(x => x.classList.toggle('selected', x === b));
            }));
            backBtn.disabled = idx === 0;
            backBtn.style.opacity = idx === 0 ? 0.35 : 1;
            nextBtn.textContent = idx === items.length - 1 ? 'Finish ✓' : 'Next →';
        };
        const stash = () => {
            const it = items[idx];
            if (it.session_type === 'strength') {
                const w = document.getElementById('exlog-weight');
                const r = document.getElementById('exlog-reps');
                if (w) it.weight = w.value;
                if (r) it.reps = r.value;
            } else {
                const m = document.getElementById('exlog-meters');
                if (m) it.meters = m.value;
            }
        };
        nextBtn.onclick = () => {
            stash();
            if (!items[idx].effort) { err.style.display = 'block'; return; }
            if (idx < items.length - 1) { idx += 1; render(); }
            else cleanup(items);
        };
        backBtn.onclick = () => { stash(); if (idx > 0) { idx -= 1; render(); } };
        skipBtn.onclick = () => cleanup(null);
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        render();
    });
}

function exitPlayer() {
    stopTimer();
    _player = null;
    document.getElementById('player-view').style.display = 'none';
    document.getElementById('tab-content').style.display = 'block';
    const btn = document.getElementById('start-player-btn');
    if (btn) btn.style.display = 'block';
}

// ---------- ML load suggestion (Model 2, applied softly) ----------
function scaleReps(reps, factor) {
    if (reps == null) return reps;
    return String(reps).replace(/\d+/g, n => Math.max(1, Math.round(parseInt(n, 10) * factor)));
}

async function enrichStrengthWithMl(strength) {
    if (!strength || !strength.exercises) return { label: null };
    if (!window.combinedSuggestion) return { label: null };
    try {
        const [hist, stats] = await Promise.all([
            api.getFeedbackHistory(1, 10).catch(() => ({ items: [] })),
            api.getStatsSummary().catch(() => null),
        ]);
        const items = (hist.items || []).slice().reverse(); // oldest -> newest
        const efforts = items.flatMap(f => [f.swim_feeling, f.strength_feeling].filter(v => v != null));
        const last3 = efforts.slice(-3);
        const avg3 = last3.length ? last3.reduce((a, b) => a + b, 0) / last3.length : 3;
        const prev3 = efforts.slice(-6, -3);
        const prevAvg = prev3.length ? prev3.reduce((a, b) => a + b, 0) / prev3.length : avg3;
        const tierA = window.getTierAssessment ? getTierAssessment() : null;
        const features = {
            tier: tierA ? tierA.tier : 2,
            esfuerzo_promedio_3: avg3,
            tendencia_esfuerzo: avg3 - prevAvg,
            adherencia_reciente: stats ? stats.completion_rate : 0.7,
            semana_plan: Math.abs(strength.week_relative || 0),
        };
        const recentHistory = items.map(f => !!(f.swim_completed || f.strength_completed));
        const { factor, source, reason } = combinedSuggestion(features, recentHistory);
        const isMl = source && !String(source).includes('conservative') && !String(source).includes('heuristic');
        strength.exercises.forEach(ex => {
            ex.reps = scaleReps(ex.reps, factor);
            ex.ml_factor = Math.round(factor * 100) / 100;
        });
        return { label: isMl ? `ML ×${factor.toFixed(2)}` : `Coach's call ×${factor.toFixed(2)}${reason ? ` (${reason})` : ''}` };
    } catch {
        return { label: null };
    }
}

function wirePlayer(swim, strength) {
    const startBtn = document.getElementById('start-player-btn');
    if (!startBtn) return;
    startBtn.addEventListener('click', async () => {
        startBtn.disabled = true;
        startBtn.textContent = 'Loading ML suggestion…';
        try {
            const ml = await withTimeout(enrichStrengthWithMl(strength), 8000);
            _player = { blocks: buildPlayerBlocks(swim, strength), idx: 0, mlLabel: ml.label, swimRef: swim, strengthRef: strength };
            if (!_player.blocks.length) { window.app.showError('No blocks in this session'); return; }
            document.getElementById('tab-content').style.display = 'none';
            startBtn.style.display = 'none';
            document.getElementById('player-view').style.display = 'block';
            renderPlayerBlock();
        } catch (err) {
            console.error('[player] start failed:', err);
            window.app.showError('Could not start guided session. Showing details instead.');
            exitPlayer();
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = '▶ Start guided session';
        }
    });
    document.getElementById('btn-anterior').addEventListener('click', () => {
        try {
            if (_player && _player.idx > 0) { _player.idx -= 1; renderPlayerBlock(); }
        } catch (err) {
            console.error('[player] prev failed:', err);
            window.app.showError('Could not go back a block.');
        }
    });
    document.getElementById('btn-siguiente').addEventListener('click', () => {
        try {
            if (!_player) return;
            if (_player.idx < _player.blocks.length - 1) { _player.idx += 1; renderPlayerBlock(); }
            else finishPlayer().catch(err => {
                console.error('[player] finish failed:', err);
                window.app.showError('Could not finish session.');
            });
        } catch (err) {
            console.error('[player] next failed:', err);
            window.app.showError('Could not advance. Try exiting and re-entering the player.');
        }
    });
    document.getElementById('btn-exit-player').addEventListener('click', exitPlayer);
}

function withTimeout(promise, ms) {
    return Promise.race([
        promise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('ML timeout')), ms)),
    ]);
}

async function completeSession(type) {
    const date = window.localISO ? localISO(new Date()) : new Date().toLocaleDateString('en-CA');
    const data = {
        date,
        swim_completed: type === 'swim',
        strength_completed: type === 'strength',
        comments: ''
    };
    try {
        if (type === 'swim') {
            const swimTab = document.querySelector('#swim-tab');
            const metersText = swimTab ? swimTab.textContent.match(/([\d,]+)m/) : null;
            if (metersText) data.swim_completed_meters = parseInt(metersText[1].replace(/,/g, ''), 10) || null;
            data.swim_feeling = 4;
        } else {
            data.strength_feeling = 4;
        }
        await api.submitFeedback(data);
        window.app.showSuccess(`${type === 'swim' ? 'Swim' : 'Strength'} session marked complete!`);
    } catch (err) {
        window.app.showError(err.message || 'Could not mark session complete');
    }
}

function logFeedback(type) {
    const today = window.localISO ? localISO(new Date()) : new Date().toLocaleDateString('en-CA');
    window.location.hash = `#/feedback?date=${today}&type=${type}`;
}

// Export
window.renderSession = renderSession;
window.switchTab = switchTab;
window.completeSession = completeSession;
window.logFeedback = logFeedback;