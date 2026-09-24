// Dashboard View
async function renderDashboard(app) {
    if (!app.state.profile || !app.state.competition) {
        window.location.hash = '#/onboarding';
        return;
    }
    
    // Load today's plan and stats
    const [todayPlan, stats] = await Promise.all([
        api.getTodayPlan().catch(() => ({ swim: null, strength: null })),
        api.getStatsSummary().catch(() => ({ 
            weekly_volume: 0, 
            weekly_swim_sessions: 0, 
            weekly_strength_sessions: 0,
            avg_swim_feeling: null,
            avg_strength_feeling: null,
            completion_rate: 0
        }))
    ]);
    
    app.state.todaySession = todayPlan;

    // ML tier assessment (client-side, optional)
    const tierA = window.getTierAssessment ? getTierAssessment() : null;
    const tierBadge = tierA ? `<span class="tipo-badge tipo-competencia" style="margin-left: 0.5rem;">Tier ${tierA.tier} · ${window.TIER_LABEL ? TIER_LABEL[tierA.tier] : ''}</span>` : '';
    const cssLine = tierA && tierA.cssPace ? `<div style="color: var(--primary); font-size: 0.875rem; margin-top: 0.25rem;">🎯 Target pace (CSS): ${Math.floor(tierA.cssPace / 60)}:${String(Math.round(tierA.cssPace % 60)).padStart(2, '0')} /100m</div>` : '';
    // CSS retest prompt (sole benchmark, every 6 weeks)
    let retestDays = null;
    if (tierA && tierA.saved_at) {
        retestDays = Math.floor((Date.now() - new Date(tierA.saved_at).getTime()) / 86400000);
    }
    const showRetest = !tierA || (retestDays != null && retestDays >= 42);
    const retestCard = showRetest ? `
        <article class="card" style="margin-bottom: 1.5rem; border-left: 4px solid var(--primary);">
            <strong>⏱️ ${tierA ? `CSS test is ${retestDays} days old — retest to keep zones honest` : 'No CSS test yet — calibrate your zones'}</strong>
            <div style="color: var(--muted-color); font-size: 0.875rem; margin: 0.25rem 0 0.75rem;">Swim 400m + 200m all-out, update your test in onboarding step 1.</div>
            <a href="#/onboarding?step=1" class="big-btn secondary" style="text-decoration: none; margin-top: 0;">${tierA ? 'Retest CSS' : 'Take the CSS test'}</a>
        </article>` : '';
    
    // Calculate days until competition
    const compDate = new Date(app.state.competition.competition_date);
    const today = new Date();
    const daysUntil = Math.ceil((compDate - today) / (1000 * 60 * 60 * 24));
    const weeksUntil = Math.ceil(daysUntil / 7);
    
    const html = `
        <div class="dashboard">
            <div class="topbar"><span class="brand">Swim<strong>Coach</strong>${tierBadge}</span><span><span class="brand">${app.state.competition.competition_type === 'pool' ? 'Pool' : 'Open Water'} · ${app.state.competition.competition_date}</span> <a href="#" onclick="event.preventDefault();window.showGuide('dashboard')" style="font-size: 13px;" title="Take the tour">? Guide</a></span></div>
            <div class="countdown">
                <div class="countdown-num">${daysUntil}</div>
                <div class="countdown-label">days until competition · ${weeksUntil} weeks</div>
            </div>
            ${retestCard}
            
            <!-- Stats Grid -->
            <div class="grid" style="margin-bottom: 1.5rem;">
                <article class="card">
                    <header><h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">This Week</h3></header>
                    <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">${stats.weekly_volume.toLocaleString()}m</div>
                    <div style="color: var(--muted-color); font-size: 0.875rem;">${stats.weekly_swim_sessions} swim + ${stats.weekly_strength_sessions} strength</div>
                </article>
                
                <article class="card">
                    <header><h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Avg Feeling (7d)</h3></header>
                    <div style="font-size: 2rem; font-weight: bold; color: ${stats.avg_swim_feeling ? (stats.avg_swim_feeling >= 3.5 ? '#10b981' : stats.avg_swim_feeling >= 2.5 ? '#f59e0b' : '#ef4444') : 'var(--muted-color)'};">
                        ${stats.avg_swim_feeling ? stats.avg_swim_feeling.toFixed(1) : '—'}
                    </div>
                    <div style="color: var(--muted-color); font-size: 0.875rem;">Swim: ${stats.avg_swim_feeling ? stats.avg_swim_feeling.toFixed(1) : '—'} | Strength: ${stats.avg_strength_feeling ? stats.avg_strength_feeling.toFixed(1) : '—'}</div>
                </article>
                
                <article class="card">
                    <header><h3 style="margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--muted-color);">Completion Rate</h3></header>
                    <div style="font-size: 2rem; font-weight: bold; color: ${stats.completion_rate >= 0.8 ? '#10b981' : stats.completion_rate >= 0.6 ? '#f59e0b' : '#ef4444'};">
                        ${Math.round(stats.completion_rate * 100)}%
                    </div>
                    <div style="color: var(--muted-color); font-size: 0.875rem;">This week</div>
                </article>
            </div>
            
            <!-- Today's Session -->
            <section style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2 style="margin: 0;">Today's Session</h2>
                    <a href="#/session/today" class="secondary" style="font-size: 0.875rem;">View Details →</a>
                </div>
                
                ${todayPlan.swim || todayPlan.strength ? `
                    <div class="grid" style="margin-bottom: 1rem;">
                        ${todayPlan.swim ? `
                            <article class="card session-card" style="cursor: pointer;" onclick="location.hash='#/session/today'">
                                <div class="session-card-top">
                                    <span class="tipo-badge tipo-alberca">🏊 Swim</span>
                                    <span class="total">${todayPlan.swim.total_meters.toLocaleString()}m</span>
                                </div>
                                <h2>${todayPlan.swim.focus}</h2>
                                ${cssLine}
                                <div style="font-size: 0.875rem; color: var(--muted-color);">
                                    ${todayPlan.swim.main_set?.length || 0} sets • ${app.formatDuration(todayPlan.swim.estimated_duration_min)}
                                </div>
                            </article>
                        ` : ''}
                        ${todayPlan.strength ? `
                            <article class="card session-card" style="cursor: pointer; border-left-color: #3d6ac9;" onclick="location.hash='#/session/today'">
                                <div class="session-card-top">
                                    <span class="tipo-badge tipo-fuerza">💪 Strength</span>
                                    <span class="total">${todayPlan.strength.exercises?.length || 0} exercises</span>
                                </div>
                                <h2>${todayPlan.strength.focus}</h2>
                                <div style="font-size: 0.875rem; color: var(--muted-color);">
                                    ${app.formatDuration(todayPlan.strength.estimated_duration_min)} estimated
                                </div>
                            </article>
                        ` : ''}
                    </div>
                ` : `
                    <article class="card" style="text-align: center; padding: 2rem;">
                        <p style="color: var(--muted-color);">No session scheduled for today</p>
                        <p style="color: var(--muted-color); font-size: 0.875rem;">Rest day or check your training days</p>
                    </article>
                `}
            </section>
            
            <!-- Quick Actions -->
            <section>
                <h3 class="section-title">Quick Actions</h3>
                <a href="#/session/today" class="big-btn" style="text-decoration: none;">🏊 Start session</a>
                <a href="#/feedback" class="big-btn secondary" style="text-decoration: none;">📝 Log feedback</a>
            </section>
            
            <!-- AdSense Banner (Free tier) -->
            ${app.state.tier === 'free' ? `
                <div id="ad-banner" style="margin-top: 2rem; text-align: center; min-height: 90px;">
                    <div style="font-size: 10px; color: var(--muted-color); text-transform: uppercase; letter-spacing: .08em;">Advertisement</div>
                    <ins class="adsbygoogle"
                         style="display:block"
                          data-ad-client="ca-pub-4540036176937342"
                          data-ad-slot="7276396302"
                         data-ad-format="auto"
                         data-full-width-responsive="true"></ins>
                </div>
            ` : ''}
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
    if (window.maybeAutoTour) maybeAutoTour('dashboard');
    
    // Initialize AdSense if needed
    if (app.state.tier === 'free' && window.adsbygoogle) {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
    }
}

// Export
window.renderDashboard = renderDashboard;