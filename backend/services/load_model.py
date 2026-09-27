"""Modelo 2 en servidor: sugiere un FACTOR de ajuste de carga/volumen a partir
del estado adaptativo del atleta.

Espejo de frontend/js/load_model.js (conservative rules + bosque si existe):
1. Si hay bosque exportado (data/ml/modelo2_bosque.json, formato
   {version, trees:[...]} con hojas {'valor': f}), se promedia el bosque
   (features: tier, avg_effort_3, effort_trend, adherence, plan_week).
2. Si no, reglas conservadoras de adherencia (igual que el frontend).
3. Clamp de seguridad +-25%: nunca mas de golpe.

El frontend sigue funcionando offline con su copia; el servidor manda en
regenerate/generate cuando hay datos.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

MODEL2_PATHS = [
    Path(__file__).parent.parent.parent / "data" / "ml" / "modelo2_bosque.json",
    Path(__file__).parent.parent.parent / "frontend" / "ml" / "modelo2_bosque.json",
]

MODEL2_VERSION_FALLBACK = "conservative_rules_v1"
_FOREST_CACHE: Dict[str, Any] = {"loaded": False, "forest": None}


def load_forest() -> Optional[Dict[str, Any]]:
    if _FOREST_CACHE["loaded"]:
        return _FOREST_CACHE["forest"]
    forest = None
    for path in MODEL2_PATHS:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    forest = json.load(f)
                break
            except (OSError, ValueError):
                continue
    _FOREST_CACHE.update(loaded=True, forest=forest)
    return forest


def _walk(node: Dict[str, Any], features: Dict[str, float]) -> Optional[float]:
    if node is None:
        return None
    if "valor" in node:
        return node["valor"]
    value = features.get(node.get("feature"))
    if value is None:
        return _walk(node.get("left"), features)
    branch = node.get("left") if value <= node.get("threshold") else node.get("right")
    return _walk(branch, features)


def forest_mean_factor(forest: Dict[str, Any],
                       features: Dict[str, float]) -> Optional[float]:
    trees = forest.get("trees") if forest else None
    if not trees:
        return None
    values = [v for v in (_walk(t, features) for t in trees) if v is not None]
    if not values:
        return None
    try:
        mean = sum(values) / len(values)
    except (TypeError, ValueError):
        return None
    return mean if mean == mean and mean not in (float("inf"), float("-inf")) else None


def conservative_factor(completion_rate: Optional[float],
                        planned: int = 0) -> Dict[str, Any]:
    if not planned or completion_rate is None:
        return {"factor": 1.0, "source": MODEL2_VERSION_FALLBACK, "reason": "no history yet"}
    if completion_rate >= 0.8:
        return {"factor": 1.05, "source": MODEL2_VERSION_FALLBACK, "reason": "good adherence"}
    if completion_rate < 0.5:
        return {"factor": 0.85, "source": MODEL2_VERSION_FALLBACK, "reason": "low adherence"}
    return {"factor": 1.0, "source": MODEL2_VERSION_FALLBACK, "reason": "steady"}


def suggest_load_factor(state: Dict[str, Any], tier: int = 2,
                        plan_week: int = 1) -> Dict[str, Any]:
    """Combina bosque (si existe) con reglas conservadoras.

    state: salida de adaptive_state.compute_athlete_state.
    Devuelve {factor, source, reason?} con factor en [0.75, 1.25].

    Sin historial (planned==0) manda la regla conservadora (1.0): el
    bosque se entreno con adherencia real y un 0.0 significaria "baja
    adherencia", castigando a usuarios nuevos sin datos.
    """
    if not state.get("planned"):
        return conservative_factor(state.get("completion_rate"), 0)
    # Nombres EXACTOS de train_modelo2.py (FEATURES); si falta uno el arbol
    # toma rama izquierda por defecto, asi que van todos siempre.
    features = {
        "tier": float(tier),
        "esfuerzo_promedio_3": float(state.get("avg_effort") or 3.0),
        "tendencia_esfuerzo": float(state.get("effort_trend") or 0.0),
        "adherencia_reciente": float(state.get("completion_rate") or 0.0),
        "semana_plan": float(plan_week),
    }
    forest = load_forest()
    if forest:
        factor = forest_mean_factor(forest, features)
        if factor is not None:
            version = forest.get("version", "model2_v1")
            return {"factor": min(1.25, max(0.75, factor)), "source": version}
    fb = conservative_factor(state.get("completion_rate"), state.get("planned", 0))
    return fb


def reset_cache() -> None:
    _FOREST_CACHE.update(loaded=False, forest=None)
