// Model 2: continuous load/reps adjustment trained pooled over all users
// (see train_modelo2.py). Only the exported forest is loaded here to suggest
// an ADJUSTMENT FACTOR over the planned load/reps.
//
// Falls back to conservative adherence rules when the model is unavailable
// or there is not enough history (new user, offline). Never blocks the flow.

var MODEL2_FOREST = null; // window-scoped so loader + predictor share it
const MODEL2_VERSION_FALLBACK = 'conservative_rules_v1';

async function loadModel2() {
    try {
        const res = await fetch('ml/modelo2_bosque.json', { cache: 'no-store' });
        if (!res.ok) return null;
        MODEL2_FOREST = await res.json();
        return MODEL2_FOREST;
    } catch {
        return null;
    }
}

// features: { tier, avg_effort_3, effort_trend, recent_adherence, plan_week }
// Returns { factor, modelVersion }; factor is null when the model cannot run.
function suggestLoadFactor(features) {
    if (MODEL2_FOREST && MODEL2_FOREST.trees && MODEL2_FOREST.trees.length) {
        const factor = predictForest(MODEL2_FOREST.trees, features, { aggregation: 'mean', leafKey: 'valor' });
        if (factor != null && isFinite(factor)) {
            // Safety clamp: never adjust more than +/-25% at once
            return { factor: Math.min(1.25, Math.max(0.75, factor)), modelVersion: MODEL2_FOREST.version || 'model2_v1' };
        }
    }
    return { factor: null, modelVersion: MODEL2_VERSION_FALLBACK };
}

// Conservative adherence fallback (mirrors progresion.js logic):
// history Danmark: array of booleans (completed or not) for recent sessions.
function conservativeFactor(recentHistory) {
    if (!recentHistory || !recentHistory.length) return { factor: 1.0, source: MODEL2_VERSION_FALLBACK, reason: 'no history yet' };
    const rate = recentHistory.filter(Boolean).length / recentHistory.length;
    if (rate >= 0.8) return { factor: 1.05, source: MODEL2_VERSION_FALLBACK, reason: 'good adherence' };
    if (rate <= 0.5) return { factor: 0.85, source: MODEL2_VERSION_FALLBACK, reason: 'low adherence' };
    return { factor: 1.0, source: MODEL2_VERSION_FALLBACK, reason: 'steady' };
}

// Combined suggestion: model first, rules when the model cannot run.
function combinedSuggestion(features, recentHistory) {
    const { factor, modelVersion } = suggestLoadFactor(features);
    if (factor != null) return { factor, source: modelVersion };
    const fb = conservativeFactor(recentHistory);
    return { factor: fb.factor, source: fb.source, reason: fb.reason };
}

window.loadModel2 = loadModel2;
window.suggestLoadFactor = suggestLoadFactor;
window.combinedSuggestion = combinedSuggestion;
