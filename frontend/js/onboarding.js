// Onboarding Flow
const ONBOARDING_STEPS = [
    { id: 'profile', title: 'Your Profile', component: 'ProfileStep' },
    { id: 'equipment', title: 'Equipment', component: 'EquipmentStep' },
    { id: 'goals', title: 'Goals', component: 'GoalsStep' },
    { id: 'competition', title: 'Competition', component: 'CompetitionStep' },
    { id: 'confirm', title: 'Confirm', component: 'ConfirmStep' }
];

function renderOnboarding(app) {
    const rawStep = new URLSearchParams(window.location.hash.split('?')[1] || '').get('step') || '1';
    const stepMap = { profile: 1, equipment: 2, goals: 3, competition: 4, confirm: 5 };
    let step = parseInt(rawStep, 10);
    if (Number.isNaN(step)) step = stepMap[rawStep] || 1;
    step = Math.min(Math.max(step, 1), ONBOARDING_STEPS.length);
    const currentStep = ONBOARDING_STEPS[step - 1];
    
    const html = `
        <div class="onboarding-container" style="max-width: 600px; margin: 2rem auto;">
            <div class="progress-bar" style="margin-bottom: 2rem;">
                <div class="progress" style="height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden;">
                    <div class="progress-fill" style="height: 100%; background: var(--primary); width: ${(step / ONBOARDING_STEPS.length) * 100}%; transition: width 0.3s;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.75rem; color: var(--muted-color);">
                    ${ONBOARDING_STEPS.map((s, i) => `<span class="${i < step ? 'text-primary' : ''}">${s.title}</span>`).join('')}
                </div>
            </div>
            
            <h2 style="margin-bottom: 0.5rem;">${currentStep.title}</h2>
            <p style="color: var(--muted-color); margin-bottom: 2rem;">Step ${step} of ${ONBOARDING_STEPS.length}</p>
            
            <div id="step-content">
                ${getStepComponent(step, app)}
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 2rem;">
                <button class="secondary" onclick="goToStep(${step - 1})" ${step === 1 ? 'disabled' : ''}>
                    ← Back
                </button>
                <button class="primary" onclick="nextStep(${step}, event)" ${step === ONBOARDING_STEPS.length ? 'disabled' : ''}>
                    ${step === ONBOARDING_STEPS.length ? 'Complete Setup' : 'Next →'}
                </button>
            </div>
        </div>
    `;
    
    document.getElementById('app').innerHTML = html;
}

function getStepComponent(step, app) {
    switch (step) {
        case 1: return profileStep(app);
        case 2: return equipmentStep(app);
        case 3: return goalsStep(app);
        case 4: return competitionStep(app);
        case 5: return confirmStep(app);
        default: return '';
    }
}

function profileStep(app) {
    return `
        <form id="profile-form">
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="level">Level</label>
                <select id="level" name="level" required>
                    <option value="beginner">Beginner (0-1 year)</option>
                    <option value="intermediate" selected>Intermediate (1-3 years)</option>
                    <option value="advanced">Advanced (3+ years)</option>
                </select>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="swim_days_per_week">Swim Days per Week</label>
                <input type="number" id="swim_days_per_week" name="swim_days_per_week" min="3" max="6" value="4" required>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="target_volume_per_session">Target Volume per Session (meters)</label>
                <input type="number" id="target_volume_per_session" name="target_volume_per_session" min="1500" max="8000" value="3000" step="100" required>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="session_duration_min">Session Duration (minutes)</label>
                <input type="number" id="session_duration_min" name="session_duration_min" min="45" max="150" value="90" required>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="ftp_pace_per_100">FTP/Threshold Pace per 100m (seconds, optional)</label>
                <input type="number" id="ftp_pace_per_100" name="ftp_pace_per_100" min="60" max="300" placeholder="e.g., 95 for 1:35/100m">
            </div>

            <fieldset style="margin-bottom: 1rem;">
                <legend>Swim test — CSS (optional, powers ML level calibration)</legend>
                <p style="font-size: 0.8rem; color: var(--muted-color); margin: 0 0 0.75rem;">Swim 400m and 200m all-out (rest between). We compute your Critical Swim Speed and calibrate your level.</p>
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <label style="flex: 1;">400m min<input type="number" id="css_400_min" name="css_400_min" min="0" placeholder="min" oninput="updateCssPreview()"></label>
                    <label style="flex: 1;">400m sec<input type="number" id="css_400_sec" name="css_400_sec" min="0" max="59" placeholder="sec" oninput="updateCssPreview()"></label>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <label style="flex: 1;">200m min<input type="number" id="css_200_min" name="css_200_min" min="0" placeholder="min" oninput="updateCssPreview()"></label>
                    <label style="flex: 1;">200m sec<input type="number" id="css_200_sec" name="css_200_sec" min="0" max="59" placeholder="sec" oninput="updateCssPreview()"></label>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <label style="flex: 1;">50m sec (optional)<input type="number" id="css_50_sec" name="css_50_sec" min="0" step="0.1" placeholder="sec" oninput="updateCssPreview()"></label>
                </div>
                <p id="css-preview" style="font-size: 0.875rem; color: var(--primary); margin: 0.5rem 0 0;"></p>
            </fieldset>

            <fieldset style="margin-bottom: 1rem;">
                <legend>Athlete data (optional, improves ML calibration)</legend>
                <div style="display: flex; gap: 0.5rem;">
                    <label style="flex: 1;">Age<input type="number" id="ath_age" name="ath_age" min="10" max="90" placeholder="years"></label>
                    <label style="flex: 1;">Weight (kg)<input type="number" id="ath_weight" name="ath_weight" min="30" max="200" step="0.5" placeholder="kg"></label>
                    <label style="flex: 1;">Height (cm)<input type="number" id="ath_height" name="ath_height" min="120" max="220" placeholder="cm"></label>
                </div>
            </fieldset>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="injury_notes">Injury Notes / Limitations</label>
                <textarea id="injury_notes" name="injury_notes" rows="3" placeholder="e.g., shoulder issues, knee problems..."></textarea>
            </div>
        </form>
    `;
}

function equipmentStep(app) {
    const swimEquip = ['pull_buoy', 'paddles', 'fins', 'snorkel', 'kickboard', 'metronome'];
    const strengthEquip = ['bodyweight', 'bands', 'kettlebell', 'trx'];
    
    return `
        <form id="equipment-form" onsubmit="return false;">
        <fieldset style="margin-bottom: 1.5rem;">
            <legend style="margin-bottom: 1rem;">Swim Equipment (available)</legend>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                ${swimEquip.map(e => `
                    <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                        <input type="checkbox" name="swim_equip" value="${e}" onchange="toggleEquipment(this)">
                        ${e.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </label>
                `).join('')}
            </div>
        </fieldset>
        
        <fieldset>
            <legend style="margin-bottom: 1rem;">Strength Equipment (available)</legend>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                ${strengthEquip.map(e => `
                    <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                        <input type="checkbox" name="strength_equip" value="${e}" checked onchange="toggleEquipment(this)">
                        ${e.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} ${e === 'bodyweight' ? '(always included)' : ''}
                    </label>
                `).join('')}
            </div>
        </fieldset>
        </form>
    `;
}

function goalsStep(app) {
    return `
        <form id="goals-form">
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="primary_goal">Primary Goal</label>
                <select id="primary_goal" name="primary_goal" required>
                    <option value="endurance">Endurance / Aerobic Base</option>
                    <option value="speed">Speed / Sprint</option>
                    <option value="technique">Technique Improvement</option>
                    <option value="mixed">Balanced / Mixed</option>
                </select>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="preferred_strokes">Preferred Strokes</label>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'im'].map(s => `
                        <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                            <input type="checkbox" name="preferred_strokes" value="${s}" ${s === 'freestyle' ? 'checked' : ''} onchange="toggleStroke(this)">
                            ${s.charAt(0).toUpperCase() + s.slice(1)}
                        </label>
                    `).join('')}
                </div>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="available_days">Training Days (Mon=1...Sun=0)</label>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => `
                        <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                            <input type="checkbox" name="available_days" value="${i === 6 ? 0 : i}" ${[1,3,5].includes(i) ? 'checked' : ''} onchange="toggleDay(this)">
                            ${d}
                        </label>
                    `).join('')}
                </div>
            </div>
        </form>
    `;
}

function competitionStep(app) {
    const todayLocal = new Date().toLocaleDateString('en-CA');
    const maxDate = new Date();
    maxDate.setFullYear(maxDate.getFullYear() + 2);
    const maxLocal = maxDate.toLocaleDateString('en-CA');
    
    return `
        <form id="competition-form">
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="competition_type">Competition Type</label>
                <select id="competition_type" name="competition_type" required onchange="toggleCompetitionFields(this)">
                    <option value="pool">Pool Competition</option>
                    <option value="open_water">Open Water</option>
                </select>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="competition_date">Competition Date</label>
                <input type="date" id="competition_date" name="competition_date" required 
                    min="${todayLocal}" 
                    max="${maxLocal}">
            </div>
            
            <div id="pool-fields" style="margin-bottom: 1rem;">
                <legend style="margin-bottom: 1rem;">Pool Events</legend>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${['50_free', '100_free', '200_free', '400_free', '800_free', '1500_free', '50_back', '100_back', '200_back', '50_breast', '100_breast', '200_breast', '50_fly', '100_fly', '200_fly', '100_im', '200_im', '400_im'].map(e => `
                        <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                            <input type="checkbox" name="pool_events" value="${e}" onchange="toggleEvent(this)">
                            ${e.replace('_', ' ').toUpperCase()}
                        </label>
                    `).join('')}
                </div>
            </div>
            
            <div id="ow-fields" style="display: none; margin-bottom: 1rem;">
                <div class="grid" style="margin-bottom: 1rem;">
                    <label for="ow_distance_km">Distance (km)</label>
                    <select id="ow_distance_km" name="ow_distance_km">
                        <option value="1.5">1.5 km</option>
                        <option value="3">3 km</option>
                        <option value="5" selected>5 km</option>
                        <option value="10">10 km</option>
                        <option value="25">25 km</option>
                    </select>
                </div>
                
                <div class="grid" style="margin-bottom: 1rem;">
                    <label for="ow_conditions">Expected Conditions</label>
                    <select id="ow_conditions" name="ow_conditions">
                        <option value="pool_like">Pool-like (calm)</option>
                        <option value="choppy" selected>Choppy</option>
                        <option value="cold">Cold water</option>
                        <option value="warm">Warm water</option>
                    </select>
                </div>
            </div>
            
            <div class="grid" style="margin-bottom: 1rem;">
                <label for="strength_days_per_week">Strength Sessions per Week (max 4, may share a day with swim)</label>
                <input type="number" id="strength_days_per_week" name="strength_days_per_week" min="1" max="4" value="2" required>
            </div>

            <div class="grid" style="margin-bottom: 1rem;">
                <label>Strength days (optional — leave empty for automatic, non-swim days first)</label>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    ${['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => `
                        <label style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; cursor: pointer;" onclick="pillClick(event, this)">
                            <input type="checkbox" name="strength_days" value="${i}" onchange="toggleDay(this)">
                            ${d}
                        </label>
                    `).join('')}
                </div>
            </div>
        </form>
    `;
}

function confirmStep(app) {
    return `
        <div style="text-align: center; padding: 2rem;">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--success-color); margin-bottom: 1rem;">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <h3>All Set!</h3>
            <p style="color: var(--muted-color); margin-bottom: 2rem;">
                Your profile is ready. We'll generate your personalized macrocycle based on your competition goal.
            </p>
            <button class="primary" onclick="completeOnboarding()">Generate My Plan</button>
        </div>
    `;
}

function goToStep(step) {
    if (step < 1) return;
    window.location.hash = `#/onboarding?step=${step}`;
}

function nextStep(currentStep, event) {
    event.preventDefault();
    if (!validateStep(currentStep)) return;
    saveStepData(currentStep);
    
    if (currentStep < 5) {
        goToStep(currentStep + 1);
    } else {
        completeOnboarding();
    }
}

function validateStep(step) {
    const form = document.querySelector(`#step-content form, #step-content fieldset`);
    if (!form) return true;
    
    const required = form.querySelectorAll('[required]');
    for (const field of required) {
        if (!field.value) {
            field.focus();
            field.style.borderColor = 'var(--error-color)';
            return false;
        }
    }
    // Enforce numeric ranges (min/max), e.g. swim days 3-6: browsers
    // don't block out-of-range typing, and bad values used to brick profiles
    const numerics = form.querySelectorAll('input[type="number"][name]');
    for (const field of numerics) {
        if (field.value === '' || field.value == null) continue;
        const v = parseFloat(field.value);
        const lo = field.min !== '' ? parseFloat(field.min) : null;
        const hi = field.max !== '' ? parseFloat(field.max) : null;
        if ((lo != null && v < lo) || (hi != null && v > hi)) {
            field.focus();
            field.style.borderColor = 'var(--error-color)';
            window.app.showError(
                `${field.name.replaceAll('_', ' ')} must be between ${field.min || '…'} and ${field.max || '…'}.`);
            return false;
        }
        field.style.borderColor = '';
    }
    // Coherence: swim days can't exceed selected training days
    const swimDays = form.querySelector('[name="swim_days_per_week"]');
    const dayBoxes = form.querySelectorAll('input[name="available_days"]:checked');
    if (swimDays && dayBoxes && dayBoxes.length && parseInt(swimDays.value) > dayBoxes.length) {
        swimDays.focus();
        swimDays.style.borderColor = 'var(--error-color)';
        window.app.showError(
            `Swim days (${swimDays.value}) exceed your ${dayBoxes.length} selected training days.`);
        return false;
    }
    return true;
}

function saveStepData(step) {
    // Save to localStorage temporarily.
    // Collects named inputs directly (works with or without a <form>;
    // FormData would throw on a bare <fieldset>, which froze step 2).
    const root = document.getElementById('step-content');
    if (!root) return;

    const saved = JSON.parse(localStorage.getItem('onboarding_data') || '{}');
    const pushVal = (key, value) => {
        if (!key || value == null || value === '') return;
        if (saved[key] !== undefined) {
            if (!Array.isArray(saved[key])) saved[key] = [saved[key]];
            // Avoid duplicates when going Back and Next again
            if (!saved[key].includes(value)) saved[key].push(value);
        } else {
            saved[key] = value;
        }
    };

    root.querySelectorAll('input[name], select[name], textarea[name]').forEach(el => {
        if (el.type === 'checkbox' || el.type === 'radio') {
            if (el.checked) pushVal(el.name, el.value);
        } else {
            pushVal(el.name, el.value);
        }
    });

    localStorage.setItem('onboarding_data', JSON.stringify(saved));
}

function secs(min, sec) {
    const m = parseFloat(min), s = parseFloat(sec);
    if (!m && !s) return null;
    return (m || 0) * 60 + (s || 0);
}

function updateCssPreview() {
    const el = document.getElementById('css-preview');
    if (!el || !window.calcCssPace) return;
    const t400 = secs(document.getElementById('css_400_min')?.value, document.getElementById('css_400_sec')?.value);
    const t200 = secs(document.getElementById('css_200_min')?.value, document.getElementById('css_200_sec')?.value);
    const css = calcCssPace(t400, t200);
    el.textContent = css ? `Your CSS: ${Math.floor(css / 60)}:${String(Math.round(css % 60)).padStart(2, '0')} /100m` : '';
}

function completeOnboarding() {
    const saved = JSON.parse(localStorage.getItem('onboarding_data') || '{}');
    // First value wins (user may go Back/Next and re-save a step)
    const first = (v, dflt) => {
        if (v === undefined || v === null || v === '') return dflt;
        return Array.isArray(v) ? (v.length ? v[0] : dflt) : v;
    };
    ['level', 'swim_days_per_week', 'target_volume_per_session', 'session_duration_min',
     'ftp_pace_per_100', 'injury_notes', 'primary_goal', 'competition_date', 'competition_type',
     'ow_distance_km', 'ow_conditions', 'strength_days_per_week',
     'css_400_min', 'css_400_sec', 'css_200_min', 'css_200_sec', 'css_50_sec',
     'ath_age', 'ath_weight', 'ath_height'].forEach(k => { saved[k] = first(saved[k]); });

    // Validate required profile fields (avoid 422 from backend)
    if (!saved.level || !saved.swim_days_per_week || !saved.target_volume_per_session || !saved.session_duration_min) {
        window.app.showError('Please complete Step 1 (profile) before generating your plan.');
        window.location.hash = '#/onboarding?step=1';
        return;
    }
    if (!saved.competition_date || !saved.competition_type) {
        window.app.showError('Please set a competition date and type (Step 4).');
        window.location.hash = '#/onboarding?step=4';
        return;
    }
    const poolEvents = saved.pool_events ? (Array.isArray(saved.pool_events) ? saved.pool_events : [saved.pool_events]) : [];
    if (saved.competition_type === 'pool' && poolEvents.length === 0) {
        window.app.showError('Select at least one pool event.');
        window.location.hash = '#/onboarding?step=4';
        return;
    }
    if (saved.competition_type === 'open_water' && !saved.ow_distance_km) {
        window.app.showError('Select an open-water distance.');
        window.location.hash = '#/onboarding?step=4';
        return;
    }
    
    // ML tier calibration (Model 1): optional CSS test + athlete data.
    // Tier APPLIES to level (user decision) and scales base volume.
    let tierInfo = null;
    let tierNotice = null;
    try {
        const t400 = secs(saved.css_400_min, saved.css_400_sec);
        const t200 = secs(saved.css_200_min, saved.css_200_sec);
        const cssPace = window.calcCssPace ? calcCssPace(t400, t200) : null;
        const hasAthleteData = saved.ath_age || saved.ath_weight || saved.ath_height;
        if ((cssPace != null || hasAthleteData) && window.predictTier) {
            const levelNum = { beginner: 1, intermediate: 2, advanced: 3 }[saved.level] || 2;
            const levelName = { 1: 'beginner', 2: 'intermediate', 3: 'advanced' }[levelNum];
            tierInfo = predictTier({
                age: saved.ath_age ? parseInt(saved.ath_age) : null,
                weightKg: saved.ath_weight ? parseFloat(saved.ath_weight) : null,
                heightCm: saved.ath_height ? parseFloat(saved.ath_height) : null,
                level: levelName,
                cssPace,
                time50Sec: saved.css_50_sec ? parseFloat(saved.css_50_sec) : null,
            });
            const tierLevel = { 1: 'beginner', 2: 'intermediate', 3: 'advanced' }[tierInfo.tier];
            if (tierLevel && tierLevel !== saved.level) {
                saved.level = tierLevel; // tier applies (approved)
                tierNotice = `Level calibrated by ML to ${tierLevel} (tier ${tierInfo.tier}).`;
            }
            if (window.saveTierAssessment) {
                saveTierAssessment({ tier: tierInfo.tier, cssPace, modelVersion: tierInfo.modelVersion });
            }
        }
    } catch (e) { /* ML never blocks onboarding */ }

    // Process arrays
    const profileData = {
        level: saved.level,
        swim_days_per_week: parseInt(saved.swim_days_per_week),
        target_volume_per_session: Math.round(parseInt(saved.target_volume_per_session) *
            ((window.TIER_SCALE && tierInfo) ? TIER_SCALE[tierInfo.tier].swim_volume_factor : 1) / 100) * 100,
        session_duration_min: parseInt(saved.session_duration_min),
        ftp_pace_per_100: saved.ftp_pace_per_100 ? parseInt(saved.ftp_pace_per_100) : null,
        injury_notes: saved.injury_notes || '',
        available_equipment: Array.from(new Set([
            ...((saved.swim_equip) ? (Array.isArray(saved.swim_equip) ? saved.swim_equip : [saved.swim_equip]) : []),
            ...((saved.strength_equip) ? (Array.isArray(saved.strength_equip) ? saved.strength_equip : [saved.strength_equip]) : []),
            'bodyweight', // always included
        ])),
        preferred_strokes: saved.preferred_strokes ? (Array.isArray(saved.preferred_strokes) ? saved.preferred_strokes : [saved.preferred_strokes]) : ['freestyle'],
        primary_goal: saved.primary_goal || 'endurance',
        available_days: saved.available_days ? (Array.isArray(saved.available_days) ? saved.available_days.map(Number) : [Number(saved.available_days)]) : [1, 3, 5],
        strength_days: saved.strength_days ? (Array.isArray(saved.strength_days) ? saved.strength_days.map(Number).filter(d => d >= 0 && d <= 6) : [Number(saved.strength_days)].filter(d => d >= 0 && d <= 6)) : []
    };
    
    const competitionData = {
        competition_date: saved.competition_date,
        competition_type: saved.competition_type,
        pool_events: poolEvents,
        ow_distance_km: saved.ow_distance_km ? parseFloat(saved.ow_distance_km) : null,
        ow_conditions: saved.ow_conditions || null,
        target_times: {},
        strength_days_per_week: parseInt(saved.strength_days_per_week || '2')
    };
    
    // Submit to API (competition: create, or update if it already exists
    // from a previous partial attempt — retrying Generate must always work)
    const saveCompetition = () => api.createCompetition(competitionData).catch(err => {
        if (err && err.message && err.message.includes('already exists')) {
            return api.updateCompetition(competitionData);
        }
        throw err;
    });
    Promise.resolve()
        .then(() => api.updateProfile(profileData))
        .then(saveCompetition)
        .then(() => api.generateMacrocycle())
        .then(() => {
            localStorage.removeItem('onboarding_data');
            window.app.showSuccess(tierNotice || 'Setup complete! Generating your macrocycle...');
            setTimeout(() => window.location.hash = '#/dashboard', 1500);
        })
        .catch(err => window.app.showError(err.message));
}

function toggleEquipment(checkbox) {
    // Visual feedback
    checkbox.parentElement.style.background = checkbox.checked ? 'var(--primary-background)' : '';
}

function toggleStroke(checkbox) {
    checkbox.parentElement.style.background = checkbox.checked ? 'var(--primary-background)' : '';
}

function toggleDay(checkbox) {
    checkbox.parentElement.style.background = checkbox.checked ? 'var(--primary-background)' : '';
}

function toggleCompetitionFields(select) {
    const poolFields = document.getElementById('pool-fields');
    const owFields = document.getElementById('ow-fields');
    
    if (select.value === 'pool') {
        poolFields.style.display = 'block';
        owFields.style.display = 'none';
    } else {
        poolFields.style.display = 'none';
        owFields.style.display = 'block';
    }
}

function toggleEvent(checkbox) {
    checkbox.parentElement.style.background = checkbox.checked ? 'var(--primary-background)' : '';
}

// Export
window.renderOnboarding = renderOnboarding;
window.secs = secs;
window.updateCssPreview = updateCssPreview;
window.goToStep = goToStep;
window.nextStep = nextStep;
window.completeOnboarding = completeOnboarding;
window.toggleEquipment = toggleEquipment;
window.toggleStroke = toggleStroke;
window.toggleDay = toggleDay;
window.toggleCompetitionFields = toggleCompetitionFields;
window.toggleEvent = toggleEvent;