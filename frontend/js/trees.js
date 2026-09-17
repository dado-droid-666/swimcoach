// Generic interpreter for decision/regression trees exported from sklearn
// (format: {feature, threshold, left, right} | leaf {@leafKey: value}).
// Used by tier_model.js (tier classification, majority vote) and
// load_model.js (load-adjustment regression, forest mean).

function walkTree(node, features, leafKey) {
    if (node == null) return null;
    if (typeof node[leafKey] !== 'undefined') return node[leafKey];
    const value = features[node.feature];
    if (value == null) return walkTree(node.left, features, leafKey); // missing data: default branch
    return value <= node.threshold
        ? walkTree(node.left, features, leafKey)
        : walkTree(node.right, features, leafKey);
}

// aggregation: 'vote' (classification, most-voted class) or
// 'mean' (regression, numeric forest mean).
function predictForest(trees, features, { aggregation, leafKey }) {
    const values = trees
        .map(tree => walkTree(tree, features, leafKey))
        .filter(v => v != null);
    if (!values.length) return null;

    if (aggregation === 'mean') {
        return values.reduce((a, b) => a + b, 0) / values.length;
    }
    const counts = {};
    values.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
    let best = null, bestCount = -1;
    Object.keys(counts).forEach(k => {
        if (counts[k] > bestCount) { bestCount = counts[k]; best = isNaN(k) ? k : parseFloat(k); }
    });
    return best;
}

window.predictForest = predictForest;
