import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date

from backend.services.macrocycle_calculator import get_phase_for_week, get_event_category
from backend.schemas import CompetitionType, Level, PrimaryGoal
from backend.services.css_zones import zone_for_pace, spm_for_zone


def load_template(template_name: str) -> Dict[str, Any]:
    """Load a swim template from JSON file."""
    template_path = Path(__file__).parent.parent.parent / "data" / "swim_templates" / f"{template_name}.json"
    if template_path.exists():
        with open(template_path, "r") as f:
            return json.load(f)
    return {}


def load_drills() -> Dict[str, List[Dict[str, Any]]]:
    """Load the drill library (breath control, kick, technique)."""
    drill_path = Path(__file__).parent.parent.parent / "data" / "drill_library.json"
    if drill_path.exists():
        with open(drill_path, "r") as f:
            return json.load(f)
    return {}


def pick_drills(drills: Dict[str, List[Dict[str, Any]]], phase_name: str,
               session_number: int) -> Dict[str, List[str]]:
    """Deterministically pick one drill per block, rotating by session.

    Returns {breath_control, kick, technique} drill names suitable for the
    phase. Rotation (not random) keeps plans reproducible per session slot.
    """
    picked = {}
    for i, block in enumerate(("breath_control", "kick", "technique")):
        cands = [d for d in drills.get(block, [])
                 if phase_name in d.get("phases", [])] or drills.get(block, [])
        if not cands:
            picked[block] = []
            continue
        rot = (session_number + i) % len(cands)
        picked[block] = [cands[rot]["name"]]
    return picked


def estimate_pace(level: Level, ftp_pace: Optional[int], zone: str) -> int:
    """Estimate target pace per 100m for a given zone."""
    if ftp_pace:
        # Based on FTP/threshold pace
        zone_offsets = {"Z1": 15, "Z2": 5, "Z3": -5, "Z4": -15}
        return ftp_pace + zone_offsets.get(zone, 0)
    
    # Estimate by level
    base_paces = {
        Level.BEGINNER: {"Z1": 140, "Z2": 125, "Z3": 115, "Z4": 105},
        Level.INTERMEDIATE: {"Z1": 120, "Z2": 105, "Z3": 95, "Z4": 85},
        Level.ADVANCED: {"Z1": 100, "Z2": 90, "Z3": 80, "Z4": 72},
    }
    return base_paces.get(level, base_paces[Level.INTERMEDIATE]).get(zone, 105)


def suggest_stroke_rate(level: Level, phase_name: str) -> int:
    """Suggest stroke rate (strokes/min) for tempo-trainer sets."""
    base = {
        Level.BEGINNER: 58,
        Level.INTERMEDIATE: 64,
        Level.ADVANCED: 70,
    }.get(level, 64)
    if phase_name in ("Peak", "Race"):
        base += 2
    elif phase_name in ("Base", "Taper"):
        base -= 2
    return base


def snap_25(meters: float) -> int:
    """Snap meters to a 25m-pool multiple (min 25). Fixed 25m base."""
    return max(25, int(round(meters / 25.0)) * 25)


def scale_set_meters(template_set: Dict, target_meters: int, template_total: int) -> Dict:
    """Scale a template set to match target meters (25m multiples)."""
    if template_total == 0:
        return template_set

    scale = target_meters / template_total
    scaled = template_set.copy()
    scaled["meters"] = snap_25(template_set.get("meters", 0) * scale)
    scaled["reps"] = max(1, round(template_set.get("reps", 1) * scale))
    if "distance" in scaled:
        # Snap rep distance first, then fit reps so reps x distance
        # stays a 25m multiple near the scaled total.
        rep_m = snap_25(template_set["distance"] * scale)
        want_total = snap_25(template_set.get("meters", rep_m) * scale)
        reps = max(1, round(template_set.get("reps", 1) * scale))
        reps = max(1, int(round(want_total / rep_m))) if rep_m > 0 else reps
        scaled["distance"] = rep_m
        scaled["reps"] = reps
        scaled["meters"] = reps * rep_m
    return scaled


def generate_swim_session(
    session_date: date,
    week_relative: int,
    phase: Dict[str, Any],
    daily_volume: int,
    available_equipment: List[str],
    preferred_strokes: List[str],
    level: Level,
    ftp_pace: Optional[int],
    event_category: str,
    session_duration_min: int,
    session_number: int,
    total_sessions_in_week: int
) -> Dict[str, Any]:
    """Generate a single swim session."""
    
    template = load_template(event_category)
    if not template:
        template = load_template("pool_mid")
    
    phase_name = phase["name"]
    intensity_dist = phase["intensity_distribution"]
    
    # Split volume: warmup 20%, main 70%, cooldown 10% (25m multiples)
    warmup_meters = snap_25(daily_volume * 0.2)
    main_meters = snap_25(daily_volume * 0.7)
    cooldown_meters = max(25, snap_25(daily_volume - warmup_meters - main_meters))
    
    # Select main set template based on phase
    main_sets = template.get("main_sets", {}).get(phase_name.lower(), template.get("main_sets", {}).get("base", []))
    if not main_sets:
        main_sets = template.get("main_sets", {}).get("base", [])
    
    # Calculate template total meters for scaling
    template_main_total = sum(s.get("meters", 0) for s in main_sets)
    
    # Scale main sets
    scaled_main = []
    for i, ts in enumerate(main_sets):
        scaled = scale_set_meters(ts, main_meters, template_main_total) if template_main_total > 0 else ts
        # Override pace based on level/ftp
        if "target_pace_per_100" not in scaled or scaled["target_pace_per_100"] is None:
            zone = scaled.get("intensity_zone", "Z2")
            scaled["target_pace_per_100"] = estimate_pace(level, ftp_pace, zone)
        # Filter equipment
        scaled["equipment"] = [e for e in scaled.get("equipment", []) if e in available_equipment]
        scaled["set_id"] = f"ms{i+1}"
        # CSS zone + stroke-rate guidance (FTP pace ≈ CSS anchor)
        css_anchor = ftp_pace or estimate_pace(level, None, "Z3")
        scaled["css_zone"] = zone_for_pace(css_anchor, scaled.get("target_pace_per_100"))
        scaled["target_spm"] = spm_for_zone(scaled["css_zone"])
        scaled_main.append(scaled)

    # Metronome: unlock stroke-rate guidance on intense sets (template
    # zone or CSS-derived zone) plus explicitly marked candidates
    if "metronome" in (available_equipment or []):
        for scaled in scaled_main:
            zone = scaled.get("intensity_zone", "Z2")
            if zone in ("Z4", "Z5") or scaled.get("css_zone") in ("Z4", "Z5") \
                    or scaled.get("stroke_rate_optional"):
                scaled["stroke_rate_spm"] = suggest_stroke_rate(level, phase_name)
                scaled["notes"] = ((scaled.get("notes") or "") + " | Tempo trainer @ "
                                   f"{scaled['stroke_rate_spm']} SPM").strip(" |")
                if "metronome" not in scaled.get("equipment", []):
                    scaled["equipment"] = list(scaled.get("equipment", [])) + ["metronome"]
                break
    
    # Build warmup from the drill library: breath control + kick +
    # technique blocks (rotating by session slot), kept in template order
    # so the session reads like hand-written blocks.
    drill_blocks = pick_drills(load_drills(), phase_name, session_number)
    warmup_drills = (drill_blocks.get("breath_control", [])
                     + drill_blocks.get("kick", [])
                     + drill_blocks.get("technique", []))
    if not warmup_drills:
        warmup_drills = template.get("warmup_drills", ["400 swim", "200 drill", "200 kick"])
    warmup_desc = " + ".join(warmup_drills[:3])
    
    # Build cooldown
    cooldown_desc = template.get("cooldown", "200 easy + 200 choice")
    
    # Determine focus
    focus_map = {
        "Base": "Aerobic endurance",
        "Build": "Threshold development",
        "Peak": "Race pace specificity",
        "Taper": "Sharpening",
        "Race": "Competition"
    }
    
    rpe_map = {"Base": 5, "Build": 6, "Peak": 7, "Taper": 4, "Race": 8}
    
    return {
        "date": session_date.isoformat(),
        "day_name": session_date.strftime("%A"),
        "week_relative": week_relative,
        "phase_name": phase_name,
        "total_meters": daily_volume,
        "estimated_duration_min": min(session_duration_min, max(45, daily_volume // 35)),
        "focus": focus_map.get(phase_name, "General"),
        "rpe_target": rpe_map.get(phase_name, 6),
        "warmup": {
            "meters": warmup_meters,
            "description": warmup_desc,
            "drills": warmup_drills[:3]
        },
        "main_set": scaled_main,
        "cooldown": {
            "meters": cooldown_meters,
            "description": cooldown_desc
        },
        "blocks": [
            {"title": "Warmup", "desc": warmup_desc},
            {"title": "Breath control", "desc": ", ".join(drill_blocks.get("breath_control", [])) or "—"},
            {"title": "Kick", "desc": ", ".join(drill_blocks.get("kick", [])) or "—"},
            {"title": "Technique", "desc": ", ".join(drill_blocks.get("technique", [])) or "—"},
            {"title": "Main set", "desc": f"{len(scaled_main)} sets"},
            {"title": "Cooldown", "desc": cooldown_desc},
        ],
        "generated_by": "macrocycle_v1",
        "parameters_snapshot": {
            "level": level.value,
            "event_category": event_category,
            "phase": phase_name,
            "daily_volume": daily_volume
        }
    }


def generate_weekly_swim_plan(
    week_start: date,
    week_relative: int,
    macrocycle_phases: List[Dict],
    profile: Dict[str, Any],
    competition_type: CompetitionType,
    pool_events: List[str],
    ow_distance_km: Optional[float]
) -> List[Dict[str, Any]]:
    """Generate swim sessions for a week."""
    
    phase = get_phase_for_week(macrocycle_phases, week_relative)
    phase_name = phase["name"]
    
    # Get available days (Mon=0..Sun=6, same as UI checkboxes)
    available_days = profile.get("available_days", [1, 3, 5])
    swim_days_per_week = min(profile.get("swim_days_per_week", 4), len(available_days))
    
    # Select swim days from available days
    swim_days = available_days[:swim_days_per_week]
    
    # Calculate weekly volume
    base_weekly_volume = profile.get("swim_days_per_week", 4) * profile.get("target_volume_per_session", 3000)
    weekly_volume = snap_25(base_weekly_volume * phase["swim_volume_mult"])
    
    # Daily volume distribution
    daily_volume = snap_25(weekly_volume / swim_days_per_week) if swim_days_per_week > 0 else 0
    
    # Event category
    event_category = get_event_category(competition_type, pool_events, ow_distance_km)
    
    sessions = []
    for i, day_offset in enumerate(swim_days):
        session_date = week_start + timedelta(days=day_offset)
        session = generate_swim_session(
            session_date=session_date,
            week_relative=week_relative,
            phase=phase,
            daily_volume=daily_volume,
            available_equipment=profile.get("available_equipment", []),
            preferred_strokes=profile.get("preferred_strokes", ["freestyle"]),
            level=Level(profile.get("level", "intermediate")),
            ftp_pace=profile.get("ftp_pace_per_100"),
            event_category=event_category,
            session_duration_min=profile.get("session_duration_min", 90),
            session_number=i,
            total_sessions_in_week=swim_days_per_week
        )
        sessions.append(session)
    
    return sessions


# Need timedelta import
from datetime import timedelta