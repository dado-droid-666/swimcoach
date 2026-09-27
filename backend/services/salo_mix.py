"""Metodologia Salo & Riewald (Complete Conditioning for Swimming) como capa
de programacion sobre los generadores existentes.

- Natacion: mezcla EN1/EN2/SP por categoria de evento (Ch3/Ch4) servida desde
  data/salo_swim.json. Taper/Race y recovery NUNCA llevan SP (Ch8).
- Fuerza: grupos core/power/prehab/flex (Ch5/Ch6/Ch7/Ch8) desde
  data/salo_dryland.json para mezclar con las plantillas TRX/calistenia/KB
  existentes. Power solo en comp + edad>=14 + supervision.

Todo es opcional por llamada (flag salo=True) para no romper planes ya
generados. Sin texto del libro: solo estructura de sets y nombres.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"

YOUTH_MIN_AGE_POWER = 14

SHOULDER_WORDS = ("hombro", "shoulder", "manguito", "rotator", "cuff")
KNEE_WORDS = ("rodilla", "knee", "pecho", "breast")


@lru_cache(maxsize=1)
def load_salo_swim() -> Dict[str, Any]:
    path = DATA_DIR / "salo_swim.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_salo_dryland() -> Dict[str, Any]:
    path = DATA_DIR / "salo_dryland.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salo_mix_for(event_category: str) -> Dict[str, float]:
    """Mezcla EN1/EN2/SP del libro por categoria de evento."""
    mix = (load_salo_swim().get("mix") or {})
    return mix.get(event_category) or {"EN1": 0.4, "EN2": 0.35, "SP": 0.25}


def salo_main_sets(event_category: str, phase_name: str) -> List[Dict[str, Any]]:
    """Bloques principales Salo por categoria y fase (copias para escalar)."""
    main = (load_salo_swim().get("main_sets") or {})
    cat = main.get(event_category) or main.get("pool_mid") or {}
    key = (phase_name or "base").lower()
    sets = cat.get(key) or cat.get("base") or []
    return [dict(s) for s in sets]


def salo_recovery_sets() -> List[Dict[str, Any]]:
    return [dict(s) for s in (load_salo_swim().get("recovery") or [])]


def salo_technique_sets() -> List[Dict[str, Any]]:
    return [dict(s) for s in (load_salo_swim().get("tecnica_ch1") or [])]


def salo_dryland_group(grupo: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    grupos = (load_salo_dryland().get("grupos") or {})
    items = [dict(e) for e in grupos.get(grupo, [])]
    return items[:limit] if limit else items


def salo_dryland_picks(fase: str, feeling: Optional[int],
                       edad: Optional[int]) -> List[Dict[str, Any]]:
    """Core siempre; power solo comp + edad>=14; prehab si feeling<=2.

    fase: 'Base'|'Build'|'Peak'|'Taper'|'Race' (power solo en Peak/Build).
    Devuelve ejercicios en formato StrengthExerciseSchema-compatible.
    """
    picks: List[Dict[str, Any]] = []
    picks += salo_dryland_group("core", 2)
    if (fase in ("Build", "Peak")) and (edad is None or edad >= YOUTH_MIN_AGE_POWER):
        picks += salo_dryland_group("power", 1)
    if feeling is not None and feeling <= 2:
        picks += salo_dryland_group("prehab", 2)
    if fase in ("Taper", "Race"):
        picks += salo_dryland_group("flex", 1)
    return picks


def needs_prehab(feeling: Optional[int], injury_notes: str = "") -> bool:
    """Prehab Ch8 si feeling bajo o notas mencionan hombro/rodilla."""
    if feeling is not None and feeling <= 2:
        return True
    text = (injury_notes or "").lower()
    return any(w in text for w in SHOULDER_WORDS + KNEE_WORDS)


def to_strength_exercise(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte un item salo_dryland a formato de plantilla de fuerza."""
    return {
        "name": item.get("name", ""),
        "muscle": item.get("muscle", ""),
        "sets": item.get("sets", 2),
        "reps": item.get("reps", "10-12"),
        "rpe": item.get("rpe", 5),
        "tempo": item.get("tempo"),
        "rest": item.get("rest", 30),
        "equipment": item.get("equipment", ["bodyweight"]),
        "progression": item.get("progression", ""),
        "notes": item.get("notes", ""),
    }
