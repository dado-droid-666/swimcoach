// Week View: Mon-Sun strip with per-day swim/strength badges.
function mondayOf(d) {
    const m = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    m.setDate(m.getDate() - ((m.getDay() + 6) % 7));
    return m;
}

function addDays(d, n) {
    const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    x.setDate(x.getDate() + n);
    return x;
}

function toISODate(d) {
    return d.toLocaleDateString('en-CA');
}

async function renderWeek(app, startParam) {
    const base = startParam && /^\d{4}-\d{2}-\d{2}$/.test(startParam)
        ? new Date(parseInt(startParam.slice(0, 4)), parseInt(startParam.slice(5, 7)) - 1, parseInt(startParam.slice(8, 10)))
        : new Date();
    if (isNaN(base.getTime())) {
        app.showError('Invalid week date');
        window.location.hash = '#/dashboard';
        return;
    }
    const monday = mondayOf(base);
    const startISO = toISODate(monday);

    let week;
    try {
        week = await api.getWeekPlan(startISO);
    } catch (err) {
        app.showError(err.message || 'Failed to load week');
        return;
    }

    const swimByDate = {};
    (week.swim_sessions || []).forEach(s => { swimByDate[s.date] = s; });
    const strByDate = {};
    (week.strength_sessions || []).forEach(s => { strByDate[s.date] = s; });
    const hasAny = Object.keys(swimByDate).length + Object.keys(strByDate).length > 0;

    // If this week is empty but the user has a plan, offer a jump to the
    // current training week instead of a silent wall of rest days.
    let emptyNotice = '';
    if (!hasAny) {
        const jump = trainingWeekMonday();
        if (jump && jump !== startISO) {
            emptyNotice = `
                <article class="card" style="margin-bottom: 1rem; border-left: 4px solid var(--warning-color);">
                    <strong>No sessions this week.</strong>
                    <div style="color: var(--muted-color); font-size: 0.875rem; margin: 0.25rem 0 0.75rem;">Your plan trains other weeks — jump straight there.</div>
                    <button class="big-btn secondary" onclick="location.hash='#/week?start=${jump}'">Go to my training week →</button>
                </article>`;
        }
    }

    const days = [];
    for (let i = 0; i < 7; i++) {
        const d = addDays(monday, i);
        const iso = toISODate(d);
        const isToday = iso === toISODate(new Date());
        days.push({
            iso,
            name: d.toLocaleDateString('en-US', { weekday: 'short' }),
            num: d.getDate(),
            swim: swimByDate[iso] || null,
            strength: strByDate[iso] || null,
            isToday,
        });
    }

    const prevISO = toISODate(addDays(monday, -7));
    const nextISO = toISODate(addDays(monday, 7));
    const isPro = window.app && window.app.state.tier === 'pro';
    const regenLink = isPro
        ? `<a href="#" id="regen-week" style="font-size: 13px;">↻ Regenerate</a>`
        : `<a href="#" id="regen-week" style="font-size: 13px; opacity: 0.55;" title="Pro feature">🔒 Regenerate</a>`;
    const title = `${monday.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${addDays(monday, 6).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;

    const dayType = (day) => {
        if (day.swim && day.strength) return 'tipo-competencia';
        if (day.swim) return 'tipo-alberca';
        if (day.strength) return 'tipo-fuerza';
        return 'tipo-descanso';
    };

    document.getElementById('app').innerHTML = `
        <div style="max-width: 520px; margin: 0 auto;">
            <div class="topbar"><span class="brand">Your <b>week</b></span><span><a href="#/macrocycle" style="font-size: 13px;">Full plan →</a> · ${regenLink}</span></div>
            <div class="semana-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <button class="semana-nav-btn" onclick="location.hash='#/week?start=${prevISO}'">←</button>
                <div style="text-align:center"><div id="semana-titulo" style="font-weight: 700;">${title}</div><div style="font-size: 11px; color: var(--muted-color);">Drag sessions between days (Pro) · tap to open</div></div>
                <button class="semana-nav-btn" onclick="location.hash='#/week?start=${nextISO}'">→</button>
            </div>
            <div id="week-list">
                ${emptyNotice}
                ${days.map(day => `
                    <div class="card day-row ${dayType(day)}" data-date="${day.iso}"
                         ondragover="event.preventDefault()" ondrop="dropSession(event, '${day.iso}')"
                         style="cursor: pointer;" onclick="weekDayTap('${day.iso}')">
                        <div class="day-row-left" style="display: flex; flex-direction: column; width: 78px; flex-shrink: 0;">
                            <span class="day-name">${day.name}${day.isToday ? ' · Today' : ''}</span>
                            <span class="day-date">${day.num}</span>
                        </div>
                        <div class="day-row-mid" style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
                            ${day.swim ? `<span draggable="true" ondragstart="dragSession(event, 'swim', ${day.swim.id})" onclick="pickSession(event, 'swim', ${day.swim.id})" title="Drag or tap to move"><span class="tipo-badge tipo-alberca">Swim ✥</span> <span class="day-total">${day.swim.total_meters.toLocaleString()}m · ${day.swim.focus || ''}</span></span>` : ''}
                            ${day.strength ? `<span draggable="true" ondragstart="dragSession(event, 'strength', ${day.strength.id})" onclick="pickSession(event, 'strength', ${day.strength.id})" title="Drag or tap to move"><span class="tipo-badge tipo-fuerza">Strength ✥</span> <span class="day-total">${day.strength.exercises?.length || 0} ex · ${day.strength.focus || ''}</span></span>` : ''}
                            ${!day.swim && !day.strength ? `<span class="day-total">Rest day</span>` : ''}
                        </div>
                        <div class="day-row-right">→</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    document.getElementById('regen-week').addEventListener('click', async (e) => {
        e.preventDefault();
        if (!requireProUI()) return;
        if (!confirm(`Regenerate week of ${startISO}? Current sessions will be replaced.`)) return;
        try {
            const res = await api.regenerateWeek(startISO);
            window.app.showSuccess(`Week regenerated (${res.swim_sessions} swim + ${res.strength_sessions} strength)`);
            renderWeek(window.app, startISO);
        } catch (err) {
            window.app.showError(err.message || 'Regenerate failed');
        }
    });
    if (window.app) window.app.updateNav();
}

function requireProUI() {
    if (window.app && window.app.state.tier === 'pro') return true;
    if (window.app) window.app.showError('Pro feature — upgrade to move or regenerate sessions.');
    setTimeout(() => { window.location.hash = '#/upgrade'; }, 800);
    return false;
}

function dragSession(e, type, id) {
    if (!requireProUI()) { e.preventDefault(); return; }
    e.dataTransfer.setData('application/json', JSON.stringify({ type, id }));
    e.dataTransfer.effectAllowed = 'move';
}

async function dropSession(e, targetISO) {
    e.preventDefault();
    e.stopPropagation();
    await moveSessionTo(targetISO, e.dataTransfer ? e.dataTransfer.getData('application/json') : null);
}

// Tap-to-move fallback for touch (drag rarely works on mobile):
// tap a session to pick it up, tap another day to drop it.
let _movePick = null;

function pickSession(e, type, id) {
    e.stopPropagation();
    if (!requireProUI()) return;
    if (_movePick && _movePick.type === type && _movePick.id === id) {
        _movePick = null;
        window.app.showSuccess('Move cancelled.');
        return;
    }
    _movePick = { type, id };
    window.app.showSuccess('Session picked — tap a day to move it.');
}

function weekDayTap(iso) {
    if (_movePick) {
        const pick = _movePick;
        _movePick = null;
        moveSessionTo(iso, JSON.stringify(pick));
    } else {
        window.location.hash = `#/session?date=${iso}`;
    }
}

async function moveSessionTo(targetISO, raw) {
    if (!raw) return;
    let sel;
    try { sel = JSON.parse(raw); } catch { return; }
    if (!sel || !sel.type || !sel.id) return;
    try {
        await api.moveSession(sel.type, sel.id, targetISO);
        window.app.showSuccess(`Moved to ${targetISO}`);
        renderWeek(window.app, targetISO);
    } catch (err) {
        window.app.showError(err.message || 'Move failed (day may be occupied)');
    }
}

window.dragSession = dragSession;
window.dropSession = dropSession;
window.pickSession = pickSession;
window.weekDayTap = weekDayTap;

// Monday of the user's current training week, derived from the
// competition date + macrocycle length. Null when unknown.
function trainingWeekMonday() {
    try {
        const app = window.app;
        const comp = app && app.state.competition;
        const macro = app && app.state.macrocycle;
        if (!comp || !comp.competition_date || !macro || !macro.total_weeks) return null;
        const race = new Date(parseInt(comp.competition_date.slice(0, 4)),
            parseInt(comp.competition_date.slice(5, 7)) - 1,
            parseInt(comp.competition_date.slice(8, 10)));
        const start = new Date(race.getFullYear(), race.getMonth(), race.getDate());
        start.setDate(start.getDate() - macro.total_weeks * 7);
        const today = new Date();
        const t = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const anchor = t < start ? start : (t > race ? race : t);
        const mon = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate());
        mon.setDate(mon.getDate() - ((mon.getDay() + 6) % 7));
        return mon.toLocaleDateString('en-CA');
    } catch {
        return null;
    }
}

window.renderWeek = renderWeek;
window.mondayOf = mondayOf;
window.addDays = addDays;
window.toISODate = toISODate;
