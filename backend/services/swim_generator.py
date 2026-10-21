import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import date

from backend.services.macrocycle_calculator import get_phase_for_week, get_event_category
from backend.schemas import CompetitionType, Level, PrimaryGoal
from backend.services.css_zones import zone_for_pace, spm_for_zone
from backend.services.salo_mix import (
    salo_main_sets,
    salo_mix_for,
    salo_recovery_sets,
    salo_technique_sets,
)


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


def set_segments(template_set: Dict) -> List[Dict]:
    """Return a book set as one or more structured segments.

    Composite sets ("8x50 @95% + 4x25 starts") carry explicit `segments` in
    data/salo_swim.json. Simple sets fall back to their reps x distance.
    """
    raw = template_set.get("segments")
    if isinstance(raw, list) and raw:
        return [dict(seg) for seg in raw]
    if template_set.get("distance"):
        return [{
            "reps": template_set.get("reps") or 1,
            "distance": template_set["distance"],
        }]
    return [{"meters": template_set.get("meters") or 0}]


def _segment_meters(segment: Dict) -> int:
    if segment.get("distance"):
        return max(1, int(segment.get("reps") or 1)) * int(segment["distance"])
    return int(segment.get("meters") or 0)


def _adjust_segment(segment: Dict, delta: int):
    """Return a copy with one more/less rep or minute, or None if invalid."""
    seg = dict(segment)
    if seg.get("distance"):
        reps = max(1, int(seg.get("reps") or 1)) + delta
        if reps < 1:
            return None
        seg["reps"] = reps
        seg["meters"] = reps * int(seg["distance"])
        return seg
    if seg.get("minutes"):
        minutes = max(1, int(seg["minutes"])) + delta
        if minutes < 1:
            return None
        pace = (seg.get("meters") or 0) / max(1, int(seg["minutes"]))
        seg["minutes"] = minutes
        seg["meters"] = snap_25(minutes * pace) if pace else snap_25(seg.get("meters") or 0)
        return seg
    meters = snap_25((seg.get("meters") or 0) + delta * 25)
    if meters < 25:
        return None
    seg["meters"] = meters
    return seg


def _fit_segments(segments: List[Dict], target: int) -> List[Dict]:
    """Nudge reps/minutes so a set lands as close as possible to its target."""
    target = max(25, snap_25(target))
    for _ in range(24):
        current = sum(_segment_meters(seg) for seg in segments)
        diff = abs(current - target)
        if diff == 0:
            break
        best = None
        for i, seg in enumerate(segments):
            for delta in (1, -1):
                candidate = _adjust_segment(seg, delta)
                if candidate is None:
                    continue
                new_total = current - _segment_meters(seg) + _segment_meters(candidate)
                new_diff = abs(new_total - target)
                if best is None or new_diff < best[0]:
                    best = (new_diff, i, candidate)
        if best is None or best[0] >= diff:
            break
        segments[best[1]] = best[2]
    return segments


def summarize_set(scaled: Dict) -> str:
    """What you'll actually swim, built from SCALED segments.

    Composite sets keep their book structure and rep distances:
    "18×50m @95% + 8×25m starts". The original book string is never used
    for display (10/26 and 20/10 title/content incidents).
    """
    segments = scaled.get("segments")
    if not segments:
        reps = scaled.get("reps") or 1
        dist = scaled.get("distance")
        core = f"{reps}×{dist}m" if dist else f"{scaled.get('meters') or 0}m"
        stroke = (scaled.get("stroke") or "").strip()
        return f"{core} {stroke}".strip()

    parts = []
    has_label = False
    for seg in segments:
        if seg.get("distance"):
            part = f"{seg.get('reps') or 1}×{seg['distance']}m"
        elif seg.get("minutes"):
            part = f"{seg['minutes']}min"
        else:
            part = f"{seg.get('meters') or 0}m"
        label = (seg.get("label") or "").strip()
        if label:
            part = f"{part} {label}"
            has_label = True
        parts.append(part)

    core = " + ".join(parts)
    stroke = (scaled.get("stroke") or "").strip()
    if stroke:
        sep = " · " if len(parts) > 1 or has_label else " "
        core = f"{core}{sep}{stroke}"
    return core


def apply_scaled_description(scaled: Dict) -> Dict:
    """Rewrite a numeric book description from the scaled segments.

    The original book text is kept in `method` for provenance only; the UI
    must never render it as a second prescription.
    """
    if scaled.get("method"):
        scaled["description"] = summarize_set(scaled)
        return scaled
    book = scaled.get("description") or ""
    if not book or not any(ch.isdigit() for ch in book):
        return scaled
    scaled["method"] = book
    scaled["description"] = summarize_set(scaled)
    return scaled


def scale_set_meters(template_set: Dict, target_meters: int, template_total: int) -> Dict:
    """Scale a set by reps/minutes, never by changing the book's rep distance."""
    if template_total == 0:
        return template_set

    scale = target_meters / template_total
    scaled = template_set.copy()
    segments = []
    for raw in set_segments(template_set):
        seg = dict(raw)
        if seg.get("distance"):
            reps = max(1, int(round((seg.get("reps") or 1) * scale)))
            seg["reps"] = reps
            seg["meters"] = reps * int(seg["distance"])
        elif seg.get("minutes"):
            minutes = max(1, int(round(seg["minutes"] * scale)))
            pace = (seg.get("meters") or 0) / max(1, int(seg["minutes"]))
            seg["minutes"] = minutes
            seg["meters"] = snap_25(minutes * pace) if pace else snap_25(
                (seg.get("meters") or 0) * scale
            )
        else:
            seg["meters"] = snap_25((seg.get("meters") or 0) * scale)
        segments.append(seg)

    target = snap_25((template_set.get("meters") or 0) * scale)
    segments = _fit_segments(segments, target)
    scaled["segments"] = segments
    scaled["meters"] = sum(_segment_meters(seg) for seg in segments)

    # Keep reps/distance as the primary block for old clients; `meters` is
    # the set total and includes every segment.
    primary = next((seg for seg in segments if seg.get("distance")), None)
    if primary:
        scaled["reps"] = primary.get("reps")
        scaled["distance"] = primary.get("distance")
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
    total_sessions_in_week: int,
    adaptive: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a single swim session.

    adaptive (opcional): {salo, recovery, feeling, technique_flag, reason}.
    Con salo=True el main set sale del libro (MIX EN1/EN2/SP por evento,
    Ch3/Ch4); recovery/Taper/Race nunca llevan SP (Ch8).
    """
    adaptive = adaptive or {}
    use_salo = bool(adaptive.get("salo"))
    recovery = bool(adaptive.get("recovery"))
    technique_flag = adaptive.get("technique_flag")

    template = load_template(event_category)
    if not template:
        template = load_template("pool_mid")

    phase_name = phase["name"]
    intensity_dist = phase["intensity_distribution"]

    # Split volume: warmup 20%, main 70%, cooldown 10% (25m multiples)
    warmup_meters = snap_25(daily_volume * 0.2)
    main_meters = snap_25(daily_volume * 0.7)
    cooldown_meters = max(25, snap_25(daily_volume - warmup_meters - main_meters))

    if use_salo:
        main_sets = _salo_main_sets(event_category, phase_name, recovery)
    else:
        # Select main set template based on phase
        main_sets = template.get("main_sets", {}).get(phase_name.lower(), template.get("main_sets", {}).get("base", []))
        if not main_sets:
            main_sets = template.get("main_sets", {}).get("base", [])
        if recovery:
            # Recovery adaptativo: sin velocidad, como Taper suave.
            main_sets = [s for s in main_sets if s.get("intensity_zone") not in ("Z4", "Z5")]
            if not main_sets:
                main_sets = template.get("main_sets", {}).get("taper", [])
    
    # Calculate template total meters for scaling
    template_main_total = sum(s.get("meters", 0) for s in main_sets)

    # Refuerzo tecnico Ch1: stroke count alto => drills + DPS (solo si hay
    # velocidad en el plan; en recovery ya va incluido).
    if technique_flag and not recovery and use_salo:
        if not any("Ch1" in (s.get("fuente_pag") or "") for s in main_sets):
            main_sets = list(main_sets) + salo_technique_sets()
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
        scaled = apply_scaled_description(scaled)
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
    rpe_target = rpe_map.get(phase_name, 6)
    focus = focus_map.get(phase_name, "General")
    if recovery and phase_name not in ("Taper", "Race"):
        # Semana recovery adaptativa: carga de Taper aunque la fase diga otra.
        rpe_target = 4
        focus = "Recovery adaptativo (feeling bajo)"

    actual_main = sum(s.get("meters", 0) for s in scaled_main)
    actual_total = warmup_meters + actual_main + cooldown_meters

    return {
        "date": session_date.isoformat(),
        "day_name": session_date.strftime("%A"),
        "week_relative": week_relative,
        "phase_name": phase_name,
        "total_meters": actual_total,
        "estimated_duration_min": min(session_duration_min, max(45, actual_total // 35)),
        "focus": focus,
        "rpe_target": rpe_target,
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
        "generated_by": "macrocycle_v1+salo" if use_salo else "macrocycle_v1",
        "parameters_snapshot": {
            "level": level.value,
            "event_category": event_category,
            "phase": phase_name,
            "daily_volume": daily_volume,
            "planned_meters": daily_volume,
            "actual_meters": actual_total,
            "salo_mix": salo_mix_for(event_category) if use_salo else None,
            "adaptive_reason": adaptive.get("reason"),
        }
    }


def _salo_main_sets(event_category: str, phase_name: str,
                    recovery: bool) -> List[Dict[str, Any]]:
    """Main sets del libro; recovery/Taper/Race nunca llevan SP (Ch8)."""
    sets = salo_main_sets(event_category, phase_name)
    if recovery or phase_name in ("Taper", "Race"):
        sets = [s for s in sets if s.get("intensity_zone") not in ("Z4", "Z5")]
        if recovery and not any("recovery" in (s.get("set_id") or "") for s in sets):
            sets = salo_recovery_sets() + sets
    if not sets:
        sets = salo_recovery_sets()
    return sets


def generate_weekly_swim_plan(
    week_start: date,
    week_relative: int,
    macrocycle_phases: List[Dict],
    profile: Dict[str, Any],
    competition_type: CompetitionType,
    pool_events: List[str],
    ow_distance_km: Optional[float],
    adaptive: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate swim sessions for a week.

    adaptive (opcional): {salo, recovery, volume_factor, feeling,
    technique_flag, reason}. El volumen perdido jamas se reapila: solo se
    modula el volumen futuro con volume_factor.
    """
    adaptive = adaptive or {}

    # week_start puede ser cualquier dia (ej. competencia - N semanas), pero
    # los dias del atleta son weekdays (Lun=0..Dom=6) y la vista es Lun-Dom:
    # normalizar al lunes dentro del bloque de 7 dias.
    week_start = week_start + timedelta(days=(7 - week_start.weekday()) % 7)

    phase = get_phase_for_week(macrocycle_phases, week_relative)
    phase_name = phase["name"]

    # Get available days (Mon=0..Sun=6, same as UI checkboxes)
    available_days = profile.get("available_days", [1, 3, 5])
    swim_days_per_week = min(profile.get("swim_days_per_week", 4), len(available_days))

    # Select swim days from available days
    swim_days = available_days[:swim_days_per_week]

    # Calculate weekly volume (modulado por estado adaptativo, nunca apilado)
    base_weekly_volume = profile.get("swim_days_per_week", 4) * profile.get("target_volume_per_session", 3000)
    weekly_volume = snap_25(base_weekly_volume * phase["swim_volume_mult"]
                            * float(adaptive.get("volume_factor", 1.0)))
    
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
            total_sessions_in_week=swim_days_per_week,
            adaptive=adaptive,
        )
        sessions.append(session)
    
    return sessions


# Need timedelta import
from datetime import timedelta