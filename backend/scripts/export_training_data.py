"""Exporta datos anonimizados de entrenamiento para reentrenar los bosques
(Modelo 1 tier + Modelo 2 factor de carga) con datos REALES de atletas.

Uso:
    python -m backend.scripts.export_training_data --out data/ml/training_export.csv

Columnas (superconjunto de las que documenta ml/train_modelo2.py + nuevas
features Salo/adaptativas):
    tier, edad, event_category, esfuerzo_promedio_3, tendencia_esfuerzo,
    adherencia_reciente, completion_rate, min_feeling, semana_plan,
    factor_ajuste_real

- factor_ajuste_real: variacion de volumen de nado sostenida en las 2
  semanas siguientes vs la actual (ratio, ej. 1.05). Para fuerza se usa la
  misma fila como contexto (el bosque predice un unico factor semanal).
- Anonimo: user_id se reemplaza por u1, u2...; sin emails ni nombres.
- Requiere DATABASE_URL configurada (.env). Solo lectura.

El reentrenamiento (train_modelo1.py / train_modelo2.py) vive en el repo
entrenamiento-app-cuentas/ml; este CSV es su insumo real cuando haya
historial suficiente. Mientras tanto los bosques actuales + fallbacks
conservadores siguen mandando.
"""
import argparse
import csv
import hashlib
from collections import defaultdict
from datetime import date, timedelta

from backend.database import SessionLocal
from backend.models import DailyFeedback, ExerciseLog, StrengthSession, SwimTest, TrainingSession


def anon(uid: int) -> str:
    return "u" + hashlib.sha256(f"swimcoach-{uid}".encode()).hexdigest()[:8]


def avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/ml/training_export.csv")
    ap.add_argument("--window", type=int, default=21)
    args = ap.parse_args()

    db = SessionLocal()
    try:
        today = date.today()
        since = today - timedelta(days=args.window)
        rows = []
        user_ids = [r[0] for r in db.query(DailyFeedback.user_id).distinct().all()]
        for uid in user_ids:
            fbs = (
                db.query(DailyFeedback)
                .filter(DailyFeedback.user_id == uid, DailyFeedback.date >= since)
                .order_by(DailyFeedback.date).all()
            )
            if len(fbs) < 3:
                continue
            feelings = [min([v for v in (f.swim_feeling, f.strength_feeling) if v is not None] or [None])
                        for f in fbs[-3:]]
            feelings = [v for v in feelings if v is not None]
            avg3 = avg(feelings)
            trend = (feelings[-1] - feelings[0]) if len(feelings) >= 2 else 0.0
            planned = (
                db.query(TrainingSession).filter(TrainingSession.user_id == uid,
                                                 TrainingSession.date >= since).count()
                + db.query(StrengthSession).filter(StrengthSession.user_id == uid,
                                                   StrengthSession.date >= since).count()
            )
            done = sum(1 for f in fbs if f.swim_completed) + sum(1 for f in fbs if f.strength_completed)
            adherence = (done / planned) if planned else None
            efforts = [l.effort for l in db.query(ExerciseLog)
                       .filter(ExerciseLog.user_id == uid, ExerciseLog.date >= since).all()
                       if l.effort is not None]
            test = (
                db.query(SwimTest).filter(SwimTest.user_id == uid)
                .order_by(SwimTest.date.desc(), SwimTest.id.desc()).first()
            )
            # Volumen actual vs 2 semanas siguientes (solo sesiones con fecha).
            cur_vol = sum(s.total_meters or 0 for s in db.query(TrainingSession).filter(
                TrainingSession.user_id == uid, TrainingSession.date >= since,
                TrainingSession.date <= today).all())
            fut_vol = sum(s.total_meters or 0 for s in db.query(TrainingSession).filter(
                TrainingSession.user_id == uid, TrainingSession.date > today,
                TrainingSession.date <= today + timedelta(days=14)).all())
            factor_real = round(fut_vol / cur_vol, 3) if cur_vol > 0 and fut_vol > 0 else None
            rows.append({
                "athlete": anon(uid),
                "tier": (test.tier if test and test.tier else 2),
                "edad": (test.edad if test and test.edad else ""),
                "esfuerzo_promedio_3": round(avg3, 2) if avg3 is not None else "",
                "tendencia_esfuerzo": round(trend, 2),
                "adherencia_reciente": round(adherence, 3) if adherence is not None else "",
                "completion_rate": round(adherence, 3) if adherence is not None else "",
                "min_feeling": min(feelings) if feelings else "",
                "avg_effort_logs": round(avg(efforts), 2) if efforts else "",
                "semana_plan": len({(f.date - since).days // 7 for f in fbs}) or 1,
                "factor_ajuste_real": factor_real if factor_real is not None else "",
            })
    finally:
        db.close()

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["athlete"])
        w.writeheader()
        w.writerows(rows)
    print(f"OK: {len(rows)} atletas -> {args.out}")


if __name__ == "__main__":
    main()
