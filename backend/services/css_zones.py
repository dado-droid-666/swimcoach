"""CSS-anchored 5-zone system (Wakayoshi 1992; SwimSmooth offsets).

Free references (linked, not copied): TrainingZones.io, TriathlonRegimen,
SportPlan, MyProCoach, TritonWear, SwimmingRegimen.

Zones are pace offsets around the user's Critical Swim Speed (sec/100m),
each with RPE, stroke-rate guidance (SPM) and purpose. Weekly volume
guardrails: Z1-Z2 70-80%, Z3 15-20%, Z4-Z5 5-10%.
"""
from typing import Dict, List, Optional


# (lower_mult, upper_mult) of CSS pace; <1.0 means faster than CSS.
ZONES = {
    "Z1": {"name": "Recovery", "pace_lo": 1.15, "pace_hi": 1.30,
           "rpe": "2-3", "spm": (50, 55),
           "purpose": "Warm-up, cool-down, technique, active recovery",
           "examples": ["8x50 easy", "4x100 drill/swim"]},
    "Z2": {"name": "Endurance", "pace_lo": 1.05, "pace_hi": 1.15,
           "rpe": "4-5", "spm": (55, 60),
           "purpose": "Aerobic base, steady distance, sustainable technique",
           "examples": ["10x100 @CSS+10s", "5x200 @CSS+15s"]},
    "Z3": {"name": "Threshold", "pace_lo": 0.95, "pace_hi": 1.05,
           "rpe": "6-7", "spm": (60, 65),
           "purpose": "Lactate threshold, race-pace endurance",
           "examples": ["10x100 @CSS", "5x200 @CSS"]},
    "Z4": {"name": "VO2max", "pace_lo": 0.85, "pace_hi": 0.95,
           "rpe": "8-9", "spm": (65, 70),
           "purpose": "Maximal aerobic power, speed reserve",
           "examples": ["8x100 fast", "4x150 hard"]},
    "Z5": {"name": "Sprint", "pace_lo": 0.75, "pace_hi": 0.85,
           "rpe": "9-10", "spm": (70, 75),
           "purpose": "Anaerobic power, starts, top-end speed",
           "examples": ["12x25 sprint", "8x50 all-out"]},
}

WEEKLY_DISTRIBUTION = {"Z1-Z2": (0.70, 0.80), "Z3": (0.15, 0.20), "Z4-Z5": (0.05, 0.10)}

RETEST_WEEKS = 6


def zone_for_pace(css_pace: Optional[float], target_pace: Optional[float]) -> str:
    """Map a target pace to its CSS zone. Falls back to Z2 without CSS."""
    if not css_pace or not target_pace or css_pace <= 0:
        return "Z2"
    ratio = target_pace / css_pace
    for zone, spec in (("Z5", ZONES["Z5"]), ("Z4", ZONES["Z4"]), ("Z3", ZONES["Z3"]),
                       ("Z2", ZONES["Z2"]), ("Z1", ZONES["Z1"])):
        if spec["pace_lo"] <= ratio <= spec["pace_hi"]:
            return zone
    return "Z2" if ratio > 1.0 else "Z5"


def zone_bounds(css_pace: float, zone: str) -> Dict[str, float]:
    """Pace bounds (sec/100m) of a zone for a given CSS."""
    spec = ZONES.get(zone, ZONES["Z2"])
    return {"lo": round(css_pace * spec["pace_lo"], 1),
            "hi": round(css_pace * spec["pace_hi"], 1)}


def spm_for_zone(zone: str) -> int:
    """Midpoint stroke rate for a zone."""
    lo, hi = ZONES.get(zone, ZONES["Z2"])["spm"]
    return (lo + hi) // 2


def zone_table(css_pace: float) -> List[Dict]:
    """Full 5-zone table with concrete paces for a CSS value."""
    table = []
    for zone, spec in ZONES.items():
        b = zone_bounds(css_pace, zone)
        table.append({"zone": zone, "name": spec["name"],
                      "pace_lo": b["lo"], "pace_hi": b["hi"],
                      "rpe": spec["rpe"], "spm": f"{spec['spm'][0]}-{spec['spm'][1]}",
                      "purpose": spec["purpose"]})
    return table


def distribution_check(zone_meters: Dict[str, float]) -> Dict[str, bool]:
    """Check weekly meters per zone against guardrails."""
    total = sum(zone_meters.values()) or 1.0
    groups = {
        "Z1-Z2": zone_meters.get("Z1", 0) + zone_meters.get("Z2", 0),
        "Z3": zone_meters.get("Z3", 0),
        "Z4-Z5": zone_meters.get("Z4", 0) + zone_meters.get("Z5", 0),
    }
    return {g: lo <= (v / total) <= hi for g, (lo, hi) in
            ((g, WEEKLY_DISTRIBUTION[g]) for g, v in groups.items())}
