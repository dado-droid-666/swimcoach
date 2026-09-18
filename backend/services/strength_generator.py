import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date, timedelta


def load_strength_template(template_name: str) -> Dict[str, Any]:
    """Load a strength template from JSON file."""
    template_path = Path(__file__).parent.parent.parent / "data" / "strength_templates" / f"{template_name}.json"
    if template_path.exists():
        with open(template_path, "r") as f:
            return json.load(f)
    return {}


def get_strength_template_for_phase(phase_name: str) -> str:
    """Map phase to strength template."""
    mapping = {
        "Base": "bodyweight_general",
        "Build": "bodyweight_max_strength",
        "Peak": "bodyweight_power",
        "Taper": "mobility",
        "Race": "mobility"
    }
    return mapping.get(phase_name, "bodyweight_general")


def generate_strength_session(
    session_date: date,
    week_relative: int,
    phase: Dict[str, Any],
    available_equipment: List[str],
    strength_days_per_week: int,
    session_number: int,
    total_sessions_in_week: int
) -> Dict[str, Any]:
    """Generate a single strength session."""
    
    phase_name = phase["name"]
    template_name = get_strength_template_for_phase(phase_name)
    template = load_strength_template(template_name)

    if not template:
        template = load_strength_template("bodyweight_general")

    # Owned-equipment general templates are mixed in so the user's gear
    # (bands/kettlebell/trx) actually changes the session.
    owned_templates = []
    for eq, tpl in (("bands", "bands_general"), ("kettlebell", "kettlebell_general"), ("trx", "trx_general")):
        if eq in (available_equipment or []):
            extra = load_strength_template(tpl)
            if extra.get("exercises"):
                owned_templates.append(extra)

    def _eligible(exercises):
        out = []
        for ex in exercises:
            required_equip = ex.get("equipment", ["bodyweight"])
            if all(eq in available_equipment or eq == "bodyweight" for eq in required_equip):
                progression_week = max(0, week_relative + 24)  # Normalize to positive
                out.append(apply_progression(ex, phase_name, progression_week))
        return out

    base_pool = _eligible(template.get("exercises", []))
    source_pools = []
    for extra in owned_templates:
        pool = _eligible(extra.get("exercises", []))
        if pool:
            source_pools.append(pool)
    source_pools.append(base_pool)

    # Interleave round-robin across each source (owned gear templates +
    # base) so every owned implement shows up instead of the first file
    # filling the whole session. Dedup by (name, reps, sets).
    exercises = []
    seen = set()
    idx = [0] * len(source_pools)
    progress = True
    while progress:
        progress = False
        for s, pool in enumerate(source_pools):
            while idx[s] < len(pool):
                nxt = pool[idx[s]]
                idx[s] += 1
                key = (nxt.get("name"), nxt.get("reps"), nxt.get("sets"))
                if key in seen:
                    continue
                seen.add(key)
                exercises.append(nxt)
                progress = True
                break
    
    # Limit exercises based on phase
    max_exercises = {
        "Base": 6,
        "Build": 5,
        "Peak": 4,
        "Taper": 3,
        "Race": 0
    }.get(phase_name, 6)

    # Weekly rotation (conjugate-lite): shift the start each week so the
    # surviving cut varies across weeks instead of repeating one order.
    if len(exercises) > 1:
        rot = abs(week_relative) % len(exercises)
        exercises = exercises[rot:] + exercises[:rot]

    exercises = exercises[:max_exercises]
    
    # Duration estimate
    duration_map = {
        "Base": 35,
        "Build": 40,
        "Peak": 30,
        "Taper": 20,
        "Race": 0
    }
    
    focus_map = {
        "Base": "General adaptation",
        "Build": "Max strength",
        "Peak": "Power conversion",
        "Taper": "Mobility & recovery",
        "Race": "None"
    }
    
    return {
        "date": session_date.isoformat(),
        "day_name": session_date.strftime("%A"),
        "week_relative": week_relative,
        "phase_name": phase_name,
        "focus": focus_map.get(phase_name, "General"),
        "exercises": exercises,
        "estimated_duration_min": duration_map.get(phase_name, 30),
        "equipment_needed": list(set(eq for ex in exercises for eq in ex.get("equipment", ["bodyweight"]))),
        "is_completed": False
    }


def apply_progression(exercise: Dict, phase_name: str, week: int) -> Dict:
    """Apply progression to exercise based on phase and week."""
    ex = exercise.copy()
    
    # Base progression: add 1 rep or 5 sec per 2 weeks
    if phase_name == "Base":
        if "reps" in ex and isinstance(ex["reps"], str) and "-" in ex["reps"]:
            # Handle formats like "8-10" or "8/leg-10/leg"
            parts = ex["reps"].split("-")
            low = parse_rep_value(parts[0])
            high = parse_rep_value(parts[1])
            if low is not None and high is not None:
                ex["reps"] = f"{low + week // 2}-{high + week // 2}"
        elif "duration" in ex:
            ex["duration"] = ex.get("duration", 30) + (week // 2) * 5
    
    # Build progression: add intensity (reduce reps, increase difficulty)
    elif phase_name == "Build":
        if "reps" in ex and isinstance(ex["reps"], str) and "-" in ex["reps"]:
            parts = ex["reps"].split("-")
            low = parse_rep_value(parts[0])
            high = parse_rep_value(parts[1])
            if low is not None and high is not None:
                ex["reps"] = f"{max(3, low - 1)}-{max(5, high - 1)}"
                ex["rpe"] = min(9, ex.get("rpe", 7) + 1)
    
    # Peak: maintain, focus on quality
    elif phase_name == "Peak":
        ex["rpe"] = min(8, ex.get("rpe", 7))
    
    # Taper: reduce volume
    elif phase_name == "Taper":
        if "reps" in ex and isinstance(ex["reps"], str) and "-" in ex["reps"]:
            parts = ex["reps"].split("-")
            low = parse_rep_value(parts[0])
            high = parse_rep_value(parts[1])
            if low is not None and high is not None:
                ex["reps"] = f"{max(2, low - 1)}-{max(4, high - 1)}"
        if "sets" in ex:
            ex["sets"] = max(1, ex["sets"] - 1)
    
    return ex


def parse_rep_value(val: str) -> Optional[int]:
    """Parse rep value from strings like '8', '8/leg', '10-12'."""
    try:
        # Remove any suffix like '/leg'
        if "/" in val:
            val = val.split("/")[0]
        return int(val)
    except (ValueError, TypeError):
        return None


def generate_weekly_strength_plan(
    week_start: date,
    week_relative: int,
    macrocycle_phases: List[Dict],
    profile: Dict[str, Any],
    swim_days: List[int]  # Days of week used for swim (0-6)
) -> List[Dict[str, Any]]:
    """Generate strength sessions for a week."""
    
    from backend.services.macrocycle_calculator import get_phase_for_week
    
    phase = get_phase_for_week(macrocycle_phases, week_relative)
    phase_name = phase["name"]
    
    strength_days_per_week = phase["strength_days"]
    if strength_days_per_week == 0:
        return []
    
    # Available days for strength (non-swim days first)
    all_days = list(range(7))
    available_for_strength = [d for d in all_days if d not in swim_days]
    
    # If not enough non-swim days, allow same-day (AM/PM split)
    if len(available_for_strength) < strength_days_per_week:
        available_for_strength.extend([d for d in swim_days if d not in available_for_strength])
    
    strength_days = available_for_strength[:strength_days_per_week]
    
    sessions = []
    for i, day_offset in enumerate(strength_days):
        session_date = week_start + timedelta(days=day_offset)
        session = generate_strength_session(
            session_date=session_date,
            week_relative=week_relative,
            phase=phase,
            available_equipment=profile.get("available_equipment", []) + ["bodyweight"],
            strength_days_per_week=strength_days_per_week,
            session_number=i,
            total_sessions_in_week=strength_days_per_week
        )
        sessions.append(session)
    
    return sessions