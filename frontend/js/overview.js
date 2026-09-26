// Plan overview: whole plan by week (swim meters + strength load, planned).
async function renderPlanOverview(app) {
    let data;
    try {
        data = await api.getPlanOverview();
    } catch (err) {
        app.showError(err.message || 'Failed to load plan overview');
        return;
    }
    if (!data.weeks || !data.weeks.length) {
        document.getElementById('app').innerHTML = `
            <div style="max-width: 520px; margin: 2rem auto; text-align: center;">
                <h1>Plan overview</h1>
                <p style="color: var(--muted-color);">No sessions planned yet.</p>
                <a href="#/onboarding?step=4" class="big-btn" style="text-decoration: none;">Set competition goal</a>
            </div>`;
        return;
    }

    const maxM = Math.max(...data.weeks.map(w => w.swim_meters), 1);
    const fmtDate = (iso) => {
        const d = new Date(parseInt(iso.slice(0, 4)), parseInt(iso.slice(5, 7)) - 1, parseInt(iso.slice(8, 10)));
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };
    const phaseColor = (name) => (window.app && window.app.getPhaseColor)
        ? window.app.getPhaseColor(name) : 'var(--primary)';

    document.getElementById('app').innerHTML = `
        <div style="max-width: 520px; margin: 0 auto;">
            <div class="topbar"><span class="brand">Plan <b>overview</b></span><a href="#/macrocycle" style="font-size: 13px;">Phases →</a></div>

            <div class="grid" style="margin-bottom: 1.5rem; grid-template-columns: repeat(2, 1fr);">
                <article class="card" style="text-align: center;">
                    <div style="font-size: 1.6rem; font-weight: 800; color: var(--primary);">${data.total_swim_meters.toLocaleString()}m</div>
                    <div style="font-size: 12px; color: var(--muted-color);">${data.total_swim_sessions} swim sessions</div>
                </article>
                <article class="card" style="text-align: center;">
                    <div style="font-size: 1.6rem; font-weight: 800; color: var(--primary);">${data.total_strength_minutes.toLocaleString()} min</div>
                    <div style="font-size: 12px; color: var(--muted-color);">${data.total_strength_sessions} strength sessions</div>
                </article>
            </div>

            <section class="card" style="margin-bottom: 1.5rem;">
                <h3 style="margin: 0 0 1rem; font-size: 0.875rem; color: var(--muted-color);">WEEKLY SWIM VOLUME</h3>
                <div style="display: flex; align-items: flex-end; gap: 4px; height: 120px;">
                    ${data.weeks.map((w, i) => {
                        const peak = w.swim_meters === maxM;
                        return `<div title="Week of ${w.week_start}: ${w.swim_meters.toLocaleString()}m" onclick="location.hash='#/week?start=${w.week_start}'"
                            style="flex: 1; cursor: pointer; background: ${peak ? 'var(--primary)' : 'var(--bg-card2)'}; border: 1px solid ${peak ? 'var(--primary)' : 'var(--border-color)'}; border-radius: 4px 4px 0 0; height: ${Math.max(4, Math.round(w.swim_meters / maxM * 100))}%; min-width: 0;"></div>`;
                    }).join('')}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--muted-color); margin-top: 4px;">
                    <span>${fmtDate(data.weeks[0].week_start)}</span>
                    <span>${fmtDate(data.weeks[data.weeks.length - 1].week_start)}</span>
                </div>
            </section>

            <section>
                ${data.weeks.map(w => `
                    <div class="card week-card" style="margin-bottom: 10px; padding: 1rem; cursor: pointer;" onclick="location.hash='#/week?start=${w.week_start}'">
                        <div class="week-card-top" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                            <strong>W/o ${fmtDate(w.week_start)}</strong>
                            ${w.phase_name ? `<span class="fase-badge" style="background: ${phaseColor(w.phase_name)}; color: white; padding: 4px 9px; border-radius: 999px; font-size: 11px; font-weight: bold;">${w.phase_name}</span>` : ''}
                        </div>
                        <div style="display: flex; gap: 1rem; font-size: 13px; color: var(--muted-color);">
                            <span>🏊 <strong style="color: var(--text-ocean);">${w.swim_meters.toLocaleString()}m</strong> · ${w.swim_sessions} sess</span>
                            <span>💪 <strong style="color: var(--text-ocean);">${w.strength_exercises}</strong> ex · ${w.strength_minutes} min</span>
                        </div>
                    </div>
                `).join('')}
            </section>
        </div>
    `;
    if (window.app) window.app.updateNav();
}

window.renderPlanOverview = renderPlanOverview;
