// Macrocycle View
async function renderMacrocycle(app) {
    if (!app.state.macrocycle) {
        const html = `
            <div style="max-width: 600px; margin: 2rem auto; text-align: center;">
                <h1>Macrocycle Plan</h1>
                <p style="color: var(--muted-color);">No macrocycle generated yet.</p>
                <a href="#/onboarding?step=4" class="primary" style="margin-top: 1rem; display: inline-block;">Set Competition Goal</a>
            </div>
        `;
        document.getElementById('app').innerHTML = html;
        return;
    }
    
    const macro = app.state.macrocycle;
    const competition = app.state.competition;
    
    const html = `
        <div class="macrocycle-view" style="max-width: 1000px; margin: 0 auto;">
            <header style="margin-bottom: 2rem;">
                <h1>Macrocycle Plan</h1>
                <p style="color: var(--muted-color);">
                    ${competition.competition_type === 'pool' ? 'Pool' : 'Open Water'} • ${competition.competition_date} • ${macro.total_weeks} weeks
                </p>
            </header>
            
            <!-- Phase Timeline -->
            <section style="margin-bottom: 2rem;">
                <h2 style="margin-bottom: 1rem;">Phase Timeline</h2>
                
                <div class="timeline" style="position: relative; padding-left: 2rem;">
                    <div style="position: absolute; left: 0; top: 0; bottom: 0; width: 2px; background: var(--border-color);"></div>
                    
                    ${macro.phases.map((phase, i) => `
                        <div class="timeline-item card week-card" style="position: relative; padding-bottom: 1.5rem; margin-bottom: 12px;">
                            <div style="position: absolute; left: -2.5rem; top: 0.25rem; width: 1rem; height: 1rem; border-radius: 50%; background: ${app.getPhaseColor(phase.name)}; border: 2px solid white; box-shadow: 0 0 0 2px ${app.getPhaseColor(phase.name)};"></div>
                            
                            <div style="margin-left: 1rem;">
                                <div class="week-card-top" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                                    <span class="fase-badge" style="background: ${app.getPhaseColor(phase.name)}; color: white; padding: 4px 9px; border-radius: 999px; font-size: 11px; font-weight: bold;">${phase.name}</span>
                                    <span class="week-dates" style="color: var(--muted-color); font-size: 13px;">Weeks ${Math.abs(phase.start_week)}–${Math.abs(phase.end_week)} (${phase.end_week - phase.start_week + 1} weeks)</span>
                                </div>
                                <div style="display: flex; gap: 1.5rem; font-size: 0.875rem; color: var(--muted-color); margin-bottom: 0.5rem;">
                                    <span>🏊 ${phase.swim_focus}</span>
                                    <span>💪 ${phase.strength_focus}</span>
                                    <span>Vol: ${phase.swim_volume_mult}x</span>
                                    <span>Str: ${phase.strength_days}/wk</span>
                                </div>
                                
                                <!-- Week bars -->
                                <div style="display: flex; gap: 4px; margin-top: 0.5rem; overflow-x: auto; padding-bottom: 0.25rem;">
                                    ${Array.from({length: phase.end_week - phase.start_week + 1}, (_, j) => {
                                        const week = phase.start_week + j;
                                        const isCurrent = week === getCurrentWeek(app);
                                        return `
                                            <div class="week-bar" style="flex: 1; min-width: 40px; height: 24px; background: ${app.getPhaseColor(phase.name)}; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; color: white; font-weight: bold; ${isCurrent ? 'box-shadow: 0 0 0 2px ' + app.getPhaseColor(phase.name) : ''}" 
                                                 title="Week ${Math.abs(week)} (${week < 0 ? Math.abs(week) + ' weeks out' : week === 0 ? 'RACE WEEK' : week + ' weeks post'})"
                                                 onclick="viewWeek(${week})">
                                                W${Math.abs(week)}
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                                <div class="week-progress-bar"><div style="width: ${phaseProgress(phase, app)}%; background: ${app.getPhaseColor(phase.name)};"></div></div>
                                <div class="week-progress-txt">${phaseProgressLabel(phase, app)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
            
            <!-- Key Metrics -->
            <section style="margin-bottom: 2rem;">
                <h2>Key Metrics</h2>
                <div class="grid" style="margin-bottom: 1rem;">
                    <article class="card">
                        <h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Total Weeks</h3>
                        <div style="font-size: 2rem; font-weight: bold;">${macro.total_weeks}</div>
                    </article>
                    <article class="card">
                        <h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Peak Volume Week</h3>
                        <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">${calculatePeakVolume(macro)}m</div>
                    </article>
                    <article class="card">
                        <h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Taper Starts</h3>
                        <div style="font-size: 2rem; font-weight: bold;">${Math.abs(getTaperStart(macro))} weeks out</div>
                    </article>
                </div>
            </section>
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
}

function getCurrentWeek(app) {
    if (!app.state.macrocycle) return 0;
    const today = new Date();
    const start = new Date(app.state.macrocycle.phases[0].start_week < 0 ? 
        new Date(new Date().setDate(new Date().getDate() + app.state.macrocycle.phases[0].start_week * 7)) : new Date());
    const diff = Math.floor((new Date() - start) / (1000 * 60 * 60 * 24 * 7));
    return -app.state.macrocycle.total_weeks + diff;
}

function calculatePeakVolume(macro) {
    const profile = window.app?.state?.profile;
    const basePerSession = profile?.target_volume_per_session || 3000;
    const swimDays = profile?.swim_days_per_week || 4;
    const baseWeekly = basePerSession * swimDays;
    const peakPhase = macro.phases.find(p => p.name === 'Peak');
    return Math.round(baseWeekly * (peakPhase?.swim_volume_mult || 1.0)).toLocaleString();
}

function getTaperStart(macro) {
    const taper = macro.phases.find(p => p.name === 'Taper');
    return taper?.start_week || -2;
}

function viewWeek(week) {
    // week is week_relative (negative = weeks out from race).
    // Anchor on today + delta from current week, then take Monday.
    const current = window.app ? getCurrentWeek(window.app) : 0;
    const deltaWeeks = week - current;
    const target = new Date();
    target.setDate(target.getDate() + deltaWeeks * 7);
    const monday = new Date(target);
    monday.setDate(target.getDate() - ((target.getDay() + 6) % 7));
    const iso = monday.toLocaleDateString('en-CA');
    window.location.hash = `#/week?start=${iso}`;
}

function phaseProgress(phase, app) {
    const cur = getCurrentWeek(app);
    const len = phase.end_week - phase.start_week + 1;
    if (cur < phase.start_week) return 0;
    if (cur > phase.end_week) return 100;
    return Math.round(((cur - phase.start_week + 1) / len) * 100);
}

function phaseProgressLabel(phase, app) {
    const cur = getCurrentWeek(app);
    if (cur < phase.start_week) return 'Upcoming';
    if (cur > phase.end_week) return 'Completed';
    return 'In progress';
}

window.viewWeek = viewWeek;

// Export
window.renderMacrocycle = renderMacrocycle;