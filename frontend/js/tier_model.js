// Model 1: predicts TIER (1=beginner, 2=intermediate, 3=advanced) from the
// user profile (age, weight, height, self-reported level, CSS pace,
// optional 50m time).
//
// The real decision forest (Random Forest trained offline, see
// train_modelo1.py in entrenamiento-app-cuentas/ml) is served as JSON and
// loaded into MODEL1_FOREST. If unavailable (offline, not trained yet), a
// heuristic fallback based on CSS pace + self-reported level is used so the
// app never blocks plan generation.

var MODEL1_FOREST = null; // window-scoped so loader + predictor share it
const MODEL1_VERSION_FALLBACK = 'heuristic_v1';

async function loadModel1() {
    try {
        const res = await fetch('ml/modelo1_arbol.json', { cache: 'no-store' });
        if (!res.ok) return null;
        MODEL1_FOREST = await res.json();
        return MODEL1_FOREST;
    } catch {
        return null;
    }
}

// CSS pace (sec/100m) from 400m and 200m all-out times.
function calcCssPace(time400Sec, time200Sec) {
    if (!time400Sec || !time200Sec || time400Sec <= time200Sec) return null;
    return ((time400Sec - time200Sec) / (400 - 200)) * 100;
}

function predictWithForest(trees, features) {
    return predictForest(trees, features, { aggregation: 'vote', leafKey: 'tier' });
}

// Heuristic fallback: blends CSS pace (faster = higher tier) with the
// self-reported level using standard adult recreational pace bands.
function predictTierHeuristic(profile) {
    const { cssPace, level } = profile;
    let tierByPace = 2;
    if (cssPace != null) {
        if (cssPace <= 85) tierByPace = 3;       // fast (<=1:25/100m)
        else if (cssPace <= 110) tierByPace = 2; // intermediate
        else tierByPace = 1;                     // developing
    }
    const tierByLevel = { beginner: 1, intermediate: 2, advanced: 3 }[level] || 2;
    return Math.min(3, Math.max(1, Math.round((tierByPace + tierByLevel) / 2)));
}

// profile: { age, weightKg, heightCm, level, cssPace, time50Sec }
// Returns { tier, modelVersion }
function predictTier(profile) {
    if (MODEL1_FOREST && MODEL1_FOREST.trees && MODEL1_FOREST.trees.length) {
        const features = {
            edad: profile.age,
            peso_kg: profile.weightKg,
            altura_cm: profile.heightCm,
            css_pace: profile.cssPace,
            tiempo_50_seg: profile.time50Sec,
            nivel_experiencia_num: { beginner: 1, intermediate: 2, advanced: 3 }[profile.level] || 2,
        };
        const tier = predictWithForest(MODEL1_FOREST.trees, features);
        if (tier) return { tier, modelVersion: MODEL1_FOREST.version || 'rf_v1' };
    }
    return { tier: predictTierHeuristic(profile), modelVersion: MODEL1_VERSION_FALLBACK };
}

// Per-tier scale to calibrate the generated plan:
// - swim: volume multiplier over the base template
// - strength: suggested reps/sets multiplier
const TIER_SCALE = {
    1: { strength_factor: 0.85, swim_volume_factor: 0.9 },
    2: { strength_factor: 1.0, swim_volume_factor: 1.0 },
    3: { strength_factor: 1.15, swim_volume_factor: 1.1 },
};

const TIER_LABEL = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced' };

// Persisted client-side alongside the profile (backend profile has no tier
// field yet). Used by dashboard + player.
function saveTierAssessment(assessment) {
    try {
        localStorage.setItem('swimcoach_tier_v1', JSON.stringify(Object.assign(
            { saved_at: new Date().toISOString() }, assessment)));
    } catch { /* storage full/blocked: non-fatal */ }
}

function getTierAssessment() {
    try { return JSON.parse(localStorage.getItem('swimcoach_tier_v1')) || null; }
    catch { return null; }
}

window.loadModel1 = loadModel1;
window.calcCssPace = calcCssPace;
window.predictTier = predictTier;
window.TIER_SCALE = TIER_SCALE;
window.TIER_LABEL = TIER_LABEL;
window.saveTierAssessment = saveTierAssessment;
window.getTierAssessment = getTierAssessment;
