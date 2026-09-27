"""Estado adaptativo del atleta: convierte feedback + adherencia + esfuerzo en
ajustes de plan. Principios:

- El volumen perdido NO se apila (Salo): las sesiones pasadas sin completar
  se marcan, no se reprograman; solo se modula el volumen/intensidad futuro.
- feeling<=2 (nado o fuerza) => semana en recovery: sin SP, RPE 4, +prehab.
- Adherencia alta => +5% volumen; media => igual; baja (<50%) => -15% y
  foco en tecnica (nunca castigo con mas carga).
"""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models import DailyFeedback, ExerciseLog, TrainingSession, StrengthSession
from backend.services.load_model import suggest_load_factor

RECOVERY_FEELING = 2


def _min_feeling(fb: DailyFeedback) -> Optional[int]:
    vals = [v for v in (fb.swim_feeling, fb.strength_feeling) if v is not None]
    return min(vals) if vals else None


def compute_athlete_state(db: Session, user_id: int,
                          today: Optional[date] = None,
                          window_days: int = 21) -> Dict[str, Any]:
    """Calcula el estado adaptativo de las ultimas `window_days` dias.

    Devuelve dict con feelings, completion_rate, sesiones perdidas,
    esfuerzo promedio, volume_factor, recovery y motivo.
    """
    if today is None:
        today = date.today()
    since = today - timedelta(days=window_days)

    feedbacks: List[DailyFeedback] = (
        db.query(DailyFeedback)
        .filter(DailyFeedback.user_id == user_id, DailyFeedback.date >= since,
                DailyFeedback.date <= today)
        .order_by(DailyFeedback.date.desc()).all()
    )

    feelings = [f for f in (_min_feeling(fb) for fb in feedbacks) if f is not None]
    avg_swim = _avg([fb.swim_feeling for fb in feedbacks if fb.swim_feeling is not None])
    avg_str = _avg([fb.strength_feeling for fb in feedbacks if fb.strength_feeling is not None])
    min_feeling = min(feelings) if feelings else None
    last_feeling = feelings[0] if feelings else None

    # Adherencia: sesiones pasadas programadas vs feedbacks completados.
    past_swim = (
        db.query(TrainingSession)
        .filter(TrainingSession.user_id == user_id,
                TrainingSession.date >= since, TrainingSession.date < today).all()
    )
    past_str = (
        db.query(StrengthSession)
        .filter(StrengthSession.user_id == user_id,
                StrengthSession.date >= since, StrengthSession.date < today).all()
    )
    n_planned = len(past_swim) + len(past_str)
    n_done = sum(1 for fb in feedbacks if fb.swim_completed) + sum(
        1 for fb in feedbacks if fb.strength_completed)
    completion_rate = (n_done / n_planned) if n_planned else 1.0
    missed = max(0, n_planned - n_done)

    efforts = [
        l.effort for l in db.query(ExerciseLog)
        .filter(ExerciseLog.user_id == user_id, ExerciseLog.date >= since,
                ExerciseLog.date <= today).all() if l.effort is not None
    ]
    avg_effort = _avg(efforts)
    # Tendencia de esfuerzo: ultimos 3 vs 3 previos (0 si no hay historial).
    effort_trend = 0.0
    if len(efforts) >= 4:
        effort_trend = (_avg(efforts[-3:]) or 0.0) - (_avg(efforts[-6:-3]) or 0.0)

    recovery = bool(min_feeling is not None and min_feeling <= RECOVERY_FEELING)
    if n_planned == 0:
        volume_factor, reason = 1.0, "sin historial: volumen planificado"
    elif recovery:
        volume_factor, reason = 0.7, f"feeling {min_feeling}<=2: recovery sin SP + prehab"
    elif completion_rate >= 0.8:
        volume_factor, reason = 1.05, f"adherencia {completion_rate:.0%}: +5% volumen"
    elif completion_rate < 0.5 and n_planned > 0:
        volume_factor, reason = 0.85, f"adherencia {completion_rate:.0%}: -15% + tecnica"
    else:
        volume_factor, reason = 1.0, "estable: volumen planificado"

    return {
        "avg_swim_feeling": avg_swim,
        "avg_strength_feeling": avg_str,
        "min_feeling": min_feeling,
        "last_feeling": last_feeling,
        "completion_rate": round(completion_rate, 3),
        "planned": n_planned,
        "completed": n_done,
        "missed": missed,
        "avg_effort": round(avg_effort, 2) if avg_effort is not None else None,
        "effort_trend": round(effort_trend, 2),
        "volume_factor": volume_factor,
        "recovery": recovery,
        "reason": reason,
    }


def _avg(vals: List[float]) -> Optional[float]:
    vals = [v for v in vals if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def build_week_adaptive(db: Session, user_id: int, profile, goal,
                        week_start: date,
                        today: Optional[date] = None) -> Dict[str, Any]:
    """Contexto adaptativo para generar UNA semana.

    - salo=True siempre (metodologia del libro).
    - El estado (feeling/adherencia/perdidas/ML) solo se aplica a la semana
      actual (today dentro de [week_start, week_start+6]) o futuras: las
      semanas pasadas se generan planificadas (el historial vive en
      feedback, y el volumen perdido jamas se reapila).
    - feeling<=2 (nado o fuerza) => recovery: sin SP, RPE 4, +prehab.
    - volume_factor: ML (bosque) si existe, si no reglas de adherencia.
    """
    if today is None:
        today = date.today()
    week_end = week_start + timedelta(days=6)
    is_actionable = week_end >= today

    base: Dict[str, Any] = {
        "salo": True,
        "recovery": False,
        "volume_factor": 1.0,
        "feeling": None,
        "edad": getattr(profile, "edad", None),
        "injury_notes": getattr(profile, "injury_notes", "") or "",
        "technique_flag": None,
        "reason": "planificado",
        "ml_source": "none",
    }
    if not is_actionable:
        return base

    state = compute_athlete_state(db, user_id, today)
    tier = 2
    try:
        from backend.models import SwimTest
        latest = (
            db.query(SwimTest).filter(SwimTest.user_id == user_id)
            .order_by(SwimTest.date.desc(), SwimTest.id.desc()).first()
        )
        if latest is not None and latest.tier in (1, 2, 3):
            tier = latest.tier
    except Exception:
        pass
    ml = suggest_load_factor(state, tier=tier)
    factor = ml["factor"] if ml.get("source") != "conservative_rules_v1" else state["volume_factor"]
    if state["recovery"]:
        factor = 0.7

    base.update({
        "recovery": state["recovery"],
        "volume_factor": round(factor, 3),
        "feeling": state["min_feeling"],
        "reason": state["reason"] + f" | ml:{ml.get('source')}",
        "ml_source": ml.get("source"),
        "completion_rate": state["completion_rate"],
        "missed": state["missed"],
    })
    return base
