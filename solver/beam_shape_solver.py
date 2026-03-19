from __future__ import annotations

from dataclasses import dataclass
import json
import math
from functools import lru_cache
from pathlib import Path


MAX_BAYS = 40


@dataclass(frozen=True)
class BeamShapeResult:
    frequency_mhz: float
    bay_count: int
    beam_tilt_deg: float
    spacing_m: float
    null_fill_percent: int
    solution: str
    linear_phase_progression_deg: float
    phases_deg: list[float]


@lru_cache(maxsize=1)
def _load_phase_tables():
    path = Path(__file__).resolve().parents[1] / "assets" / "beam_shape_phase_tables.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def calculate_linear_phase_progression_deg(
    frequency_mhz: float,
    spacing_m: float,
    beam_tilt_deg: float,
) -> float:
    return (
        math.pi
        * 2.0
        / (300.0 / frequency_mhz)
        * spacing_m
        * math.cos(math.pi / 180.0)
        * beam_tilt_deg
    )


def _validate_solution(solution: str) -> str:
    normalized = (solution or "").strip()
    if normalized not in {"Oscillatory", "Non-Oscillatory"}:
        raise ValueError("Beam Shape solution must be 'Oscillatory' or 'Non-Oscillatory'.")
    return normalized


def _validate_bay_count(bay_count: int) -> int:
    if bay_count < 1 or bay_count > MAX_BAYS:
        raise ValueError(f"Beam Shape supports between 1 and {MAX_BAYS} bays.")
    return bay_count


def _get_phase_coefficients(bay_count: int, solution: str) -> tuple[list[float], list[float] | None]:
    tables = _load_phase_tables()
    key = str(bay_count)
    if solution == "Oscillatory":
        return list(tables["oscillatory"][key]), None
    return (
        list(tables["non_oscillatory_linear"][key]),
        list(tables["non_oscillatory_quadratic"][key]),
    )


def calculate_beam_shape_phases(
    frequency_mhz: float,
    bay_count: int,
    beam_tilt_deg: float,
    spacing_m: float,
    null_fill_percent: int,
    solution: str,
) -> BeamShapeResult:
    bay_count = _validate_bay_count(int(bay_count))
    solution = _validate_solution(solution)
    null_fill_percent = int(null_fill_percent)

    linear_phase_progression_deg = calculate_linear_phase_progression_deg(
        float(frequency_mhz),
        float(spacing_m),
        float(beam_tilt_deg),
    )

    base_phases = []
    multiplier = bay_count - 1
    for _index in range(bay_count):
        base_phases.append(linear_phase_progression_deg * multiplier)
        multiplier -= 1

    linear_coefficients, quadratic_coefficients = _get_phase_coefficients(
        bay_count,
        solution,
    )

    phases_deg = []
    if solution == "Oscillatory":
        for index in range(bay_count):
            phases_deg.append(
                linear_coefficients[index] * null_fill_percent + base_phases[index]
            )
    else:
        assert quadratic_coefficients is not None
        for index in range(bay_count):
            phases_deg.append(
                quadratic_coefficients[index] * null_fill_percent * null_fill_percent
                + linear_coefficients[index] * null_fill_percent
                + base_phases[index]
            )

    offset = min(0.0, min(phases_deg, default=0.0))
    if offset < 0.0:
        phases_deg = [phase - offset for phase in phases_deg]

    return BeamShapeResult(
        frequency_mhz=float(frequency_mhz),
        bay_count=bay_count,
        beam_tilt_deg=float(beam_tilt_deg),
        spacing_m=float(spacing_m),
        null_fill_percent=null_fill_percent,
        solution=solution,
        linear_phase_progression_deg=linear_phase_progression_deg,
        phases_deg=phases_deg,
    )


def format_phase_value(phase_deg: float, decimal_places: int) -> str:
    decimal_places = max(0, min(2, int(decimal_places)))
    if decimal_places == 0:
        return f"{round(phase_deg, 0):0.0f}"
    if decimal_places == 1:
        return f"{round(phase_deg, 1):0.1f}"
    return f"{round(phase_deg, 2):0.2f}"
