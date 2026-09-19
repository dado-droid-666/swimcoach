from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from backend.schemas import CompetitionType, Level, PrimaryGoal, OWConditions


class PhaseName(str, Enum):
    BASE = "Base"
    BUILD = "Build"
    PEAK = "Peak"
    TAPER = "Taper"
    RACE = "Race"


@dataclass
class PhaseConfig:
    name: PhaseName
    pct_of_total: float
    min_weeks: int
    swim_focus: str
    strength_focus: str
    swim_volume_mult: float
    strength_days_per_week: int
    intensity_distribution: Dict[str, float]  # Z1, Z2, Z3, Z4 percentages


# Phase configurations (will be scaled to fit total weeks)
PHASE_CONFIGS = [
    PhaseConfig(
        name=PhaseName.BASE,
        pct_of_total=0.35,
        min_weeks=2,
        swim_focus="Aerobic capacity + Technique",
        strength_focus="General adaptation",
        swim_volume_mult=1.0,
        strength_days_per_week=4,
        intensity_distribution={"Z1": 0.70, "Z2": 0.20, "Z3": 0.10, "Z4": 0.0}
    ),
    PhaseConfig(
        name=PhaseName.BUILD,
        pct_of_total=0.25,
        min_weeks=2,
        swim_focus="Threshold + Race pace",
        strength_focus="Max strength",
        swim_volume_mult=1.1,
        strength_days_per_week=4,
        intensity_distribution={"Z1": 0.55, "Z2": 0.30, "Z3": 0.15, "Z4": 0.0}
    ),
    PhaseConfig(
        name=PhaseName.PEAK,
        pct_of_total=0.20,
        min_weeks=1,
        swim_focus="Race simulation + Sharpening",
        strength_focus="Power conversion",
        swim_volume_mult=1.0,
        strength_days_per_week=3,
        intensity_distribution={"Z1": 0.50, "Z2": 0.25, "Z3": 0.20, "Z4": 0.05}
    ),
    PhaseConfig(
        name=PhaseName.TAPER,
        pct_of_total=0.0,  # Fixed 2 weeks
        min_weeks=2,
        swim_focus="Sharpening + Recovery",
        strength_focus="Mobility only",
        swim_volume_mult=0.6,
        strength_days_per_week=1,
        intensity_distribution={"Z1": 0.70, "Z2": 0.20, "Z3": 0.10, "Z4": 0.0}
    ),
    PhaseConfig(
        name=PhaseName.RACE,
        pct_of_total=0.0,  # Fixed 1 week
        min_weeks=1,
        swim_focus="Competition",
        strength_focus="None",
        swim_volume_mult=0.3,
        strength_days_per_week=0,
        intensity_distribution={"Z1": 0.80, "Z2": 0.20, "Z3": 0.0, "Z4": 0.0}
    ),
]


@dataclass
class MacrocyclePlan:
    total_weeks: int
    phases: List[Dict[str, Any]]
    competition_date: date
    start_date: date


def calculate_macrocycle(
    competition_date: date,
    competition_type: CompetitionType,
    pool_events: List[str],
    ow_distance_km: Optional[float],
    today: Optional[date] = None
) -> MacrocyclePlan:
    """
    Calculate macrocycle phases working backwards from competition date.
    
    Returns phases with start_week, end_week (relative to race week = 0)
    """
    if today is None:
        today = date.today()
    
    days_until_race = (competition_date - today).days
    if days_until_race < 0:
        days_until_race = 0
    
    total_weeks = max(6, min(30, (days_until_race + 6) // 7))  # 6-30 weeks
    
    # Fixed duration phases (in weeks)
    taper_weeks = 2
    race_weeks = 1
    peak_weeks = max(1, int(total_weeks * 0.20))
    build_weeks = max(2, int(total_weeks * 0.25))
    base_weeks = total_weeks - taper_weeks - race_weeks - peak_weeks - build_weeks
    base_weeks = max(2, base_weeks)
    
    # Recalculate if needed
    if base_weeks + build_weeks + peak_weeks + taper_weeks + race_weeks != total_weeks:
        build_weeks = total_weeks - base_weeks - peak_weeks - taper_weeks - race_weeks
        build_weeks = max(2, build_weeks)
    
    # Build phases (week 0 = race week, negative = before race)
    phases = []
    current_week = -total_weeks
    
    # Base phase
    base_end = current_week + base_weeks - 1
    phases.append({
        "name": PhaseName.BASE.value,
        "start_week": current_week,
        "end_week": base_end,
        "swim_focus": "Aerobic capacity + Technique",
        "strength_focus": "General adaptation",
        "swim_volume_mult": 1.0,
        "strength_days": 4,
        "intensity_distribution": {"Z1": 0.70, "Z2": 0.20, "Z3": 0.10, "Z4": 0.0}
    })
    current_week = base_end + 1
    
    # Build phase
    build_end = current_week + build_weeks - 1
    phases.append({
        "name": PhaseName.BUILD.value,
        "start_week": current_week,
        "end_week": build_end,
        "swim_focus": "Threshold + Race pace",
        "strength_focus": "Max strength",
        "swim_volume_mult": 1.1,
        "strength_days": 4,
        "intensity_distribution": {"Z1": 0.55, "Z2": 0.30, "Z3": 0.15, "Z4": 0.0}
    })
    current_week = build_end + 1
    
    # Peak phase
    peak_end = current_week + peak_weeks - 1
    phases.append({
        "name": PhaseName.PEAK.value,
        "start_week": current_week,
        "end_week": peak_end,
        "swim_focus": "Race simulation + Sharpening",
        "strength_focus": "Power conversion",
        "swim_volume_mult": 1.0,
        "strength_days": 3,
        "intensity_distribution": {"Z1": 0.50, "Z2": 0.25, "Z3": 0.20, "Z4": 0.05}
    })
    current_week = peak_end + 1
    
    # Taper phase (fixed 2 weeks)
    taper_end = current_week + taper_weeks - 1
    phases.append({
        "name": PhaseName.TAPER.value,
        "start_week": current_week,
        "end_week": taper_end,
        "swim_focus": "Sharpening + Recovery",
        "strength_focus": "Mobility only",
        "swim_volume_mult": 0.6,
        "strength_days": 1,
        "intensity_distribution": {"Z1": 0.70, "Z2": 0.20, "Z3": 0.10, "Z4": 0.0}
    })
    current_week = taper_end + 1
    
    # Race phase (fixed 1 week)
    phases.append({
        "name": PhaseName.RACE.value,
        "start_week": current_week,
        "end_week": current_week,
        "swim_focus": "Competition",
        "strength_focus": "None",
        "swim_volume_mult": 0.3,
        "strength_days": 0,
        "intensity_distribution": {"Z1": 0.80, "Z2": 0.20, "Z3": 0.0, "Z4": 0.0}
    })
    
    start_date = competition_date - timedelta(weeks=total_weeks)
    
    return MacrocyclePlan(
        total_weeks=total_weeks,
        phases=phases,
        competition_date=competition_date,
        start_date=start_date
    )


def get_phase_for_week(phases: List[Dict], week_relative: int) -> Dict[str, Any]:
    """Get phase config for a given relative week."""
    for phase in phases:
        if phase["start_week"] <= week_relative <= phase["end_week"]:
            return phase
    # Default to last phase
    return phases[-1]


def get_event_category(competition_type: CompetitionType, pool_events: List[str], ow_distance_km: Optional[float]) -> str:
    """Determine event category for template selection."""
    if competition_type == CompetitionType.OPEN_WATER:
        if ow_distance_km is None:
            return "ow_long"
        if ow_distance_km <= 3:
            return "ow_short"
        elif ow_distance_km <= 10:
            return "ow_long"
        else:
            return "ow_ultra"
    else:
        # Pool events - categorize by shortest/primary event
        sprint_events = ["50_free", "50_back", "50_breast", "50_fly", "100_free", "100_back", "100_breast", "100_fly"]
        mid_events = ["200_free", "200_back", "200_breast", "200_fly", "200_im"]
        distance_events = ["400_free", "400_im", "800_free", "1500_free"]
        
        for event in pool_events:
            if event in sprint_events:
                return "pool_sprint"
        for event in pool_events:
            if event in mid_events:
                return "pool_mid"
        for event in pool_events:
            if event in distance_events:
                return "pool_distance"
        
        # Default to IM if mixed
        if "200_im" in pool_events or "400_im" in pool_events:
            return "pool_im"
        
        return "pool_mid"