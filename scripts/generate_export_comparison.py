from __future__ import annotations

import argparse
import difflib
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtWidgets import QApplication

from exports.pattern_exporters import (
    _build_atdi_vrp_series,
    _display_from_internal_azimuth,
    _get_azimuth_row_reordered,
    _get_displayed_hrp,
    _get_displayed_vrp,
    _get_integer_vrp_cut,
    _get_maximum_angles,
    _get_peak_horizontal_pattern,
    _internal_from_display_azimuth,
    _voltage_to_db,
    export_to_format,
)
from main import ADTMainWindow
from solver.pattern_synthesis import extract_hrp_cut, extract_vrp_cut, get_3d_directivity


TEXT_EXPORTS = {
    "HRP PAT": "hrp.pat",
    "VRP PAT": "vrp.pat",
    "HRP Text": "hrp.txt",
    "VRP Text": "vrp.txt",
    "HRP CSV": "hrp.csv",
    "VRP CSV": "vrp.csv",
    "HRP V-Soft": "hrp.vep",
    "VRP V-Soft": "vrp.vep",
    "HRP ATDI": "hrp.H_DIA.DIA",
    "VRP ATDI": "vrp.V_DIA.DIA",
    "3D ATDI": "pattern3d.csv",
    "3D Text": "pattern.3dp",
    "NGW3D": "pattern.ng3dant",
    "PRN": "pattern.prn",
    "EDX": "pattern.ProgiraEDX.pat",
    "Complex EDX": "pattern_complex.ProgiraEDX.pat",
    "Directivity": "pattern.dir",
}

VISUAL_EXPORTS = {
    "HRP JPEG": "hrp.jpg",
    "VRP JPEG": "vrp.jpg",
    "Layout JPEG": "layout.jpg",
    "Summary PDF": "summary.pdf",
    "Panel PDF": "panels.pdf",
    "All PDF": "all.pdf",
    "Video": "vrp_animation.avi",
}

VISUAL_METHOD_NOTES = {
    "HRP JPEG": "Legacy source method: FormFuncs.CreateHRPplot",
    "VRP JPEG": "Legacy source method: FormFuncs.CreateVRPplot",
    "Layout JPEG": "Legacy source method: layout image export from MainForm / Layout3D renderer",
    "Summary PDF": "Legacy source method: FormFuncs.CreateResultSumpdf",
    "Panel PDF": "Legacy source method: FormFuncs.CreatePanelPospdf",
    "All PDF": "Legacy source methods: CreateHRPTabupdf + CreateVRPTabupdf + CreateResultSumpdf + CreatePanelPospdf + CreatePatLayoutPage",
    "Video": "Legacy source path: VRP animation export from MainForm with temporary frame generation",
}


@dataclass
class ComparisonRow:
    format_name: str
    filename: str
    exact_match: bool
    python_lines: int
    legacy_lines: int
    diff_path: str


def _fmt(value: float, decimals: int) -> str:
    return f"{float(value):.{decimals}f}"


def _fmt_int(value: float) -> str:
    return f"{float(value):.0f}"


def _date_long() -> str:
    from datetime import datetime

    return datetime.now().strftime("%B %d, %Y").replace(" 0", " ")


def _date_short() -> str:
    from datetime import datetime

    return datetime.now().strftime("%d/%m/%Y")


def _build_window_with_pattern():
    app = QApplication.instance() or QApplication([])
    window = ADTMainWindow()
    window.show()
    app.processEvents()
    window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
    window.on_calculate_clicked()
    app.processEvents()
    return app, window


def _write(path: Path, content: str, encoding: str = "utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding, newline="\n")


def _reordered_hrp(angles_deg: np.ndarray, magnitudes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    wrapped = []
    for angle, magnitude in zip(np.asarray(angles_deg, dtype=float), np.asarray(magnitudes, dtype=float)):
        value = float(angle)
        while value >= 360.0:
            value -= 360.0
        while value < 0.0:
            value += 360.0
        wrapped.append((value, float(magnitude)))
    wrapped.sort(key=lambda item: item[0])
    return (
        np.asarray([item[0] for item in wrapped], dtype=float),
        np.asarray([item[1] for item in wrapped], dtype=float),
    )


def _legacy_hrp_pat(context) -> str:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    lines = ["Edited by Deglitch", _fmt(context.project.metadata.channel_frequency_mhz, 2), "1", "0 0 0 1 0", "voltage"]
    for angle, magnitude in zip(angles_deg, magnitudes):
        lines.append(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}\t0")
    return "\n".join(lines) + "\n"


def _legacy_vrp_pat(context) -> str:
    angles_deg, magnitudes, _azimuth_deg, _directivity, _tilt_deg = _get_displayed_vrp(context)
    lines = ["Edited by Deglitch", _fmt(context.project.metadata.channel_frequency_mhz, 2), "1", "0 0 0 1 0", "voltage"]
    for angle, magnitude in zip(np.asarray(angles_deg, dtype=float), np.asarray(magnitudes, dtype=float)):
        lines.append(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}\t0")
    return "\n".join(lines) + "\n"


def _legacy_hrp_txt(context) -> str:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    lines = [
        "RFS Horizontal Radiation Pattern Data",
        "E / Emax (voltage)",
        "Angle\tMagnitude",
    ]
    for angle, magnitude in zip(angles_deg, magnitudes):
        lines.append(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}")
    return "\n".join(lines) + "\n"


def _legacy_vrp_txt(context) -> str:
    angles_deg, magnitudes, _azimuth_deg, _directivity, _tilt_deg = _get_displayed_vrp(context)
    lines = [
        "RFS Vertical Radiation Pattern Data",
        "E / Emax (voltage)",
        "Angle\tMagnitude",
    ]
    for angle, magnitude in zip(angles_deg[:-1], magnitudes[:-1]):
        lines.append(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}")
    return "\n".join(lines) + "\n"


def _legacy_hrp_csv(context) -> str:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    meta = context.project.metadata
    lines = [
        "manufacturer:\tRFS",
        f"date:\t{_date_long()}",
        "pattern_plane:\tAzimuth",
        f"polarisation:\t{meta.polarization}",
        f"frequency_MHz:\t{_fmt(meta.channel_frequency_mhz, 2)}",
        " E / Emax (voltage)",
        " Angle   Magnitude",
    ]
    for angle, magnitude in zip(angles_deg, magnitudes):
        lines.append(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}")
    lines.append(f"180\t{_fmt(magnitudes[0], 4)}")
    return "\n".join(lines) + "\n"


def _legacy_vrp_csv(context) -> str:
    angles_deg, magnitudes, _azimuth_deg, _directivity, _tilt_deg = _get_displayed_vrp(context)
    meta = context.project.metadata
    lines = [
        "manufacturer:\tRFS",
        f"date:\t{_date_long()}",
        "pattern_plane:\tElevation",
        f"polarisation:\t{meta.polarization}",
        f"frequency_MHz:\t{_fmt(meta.channel_frequency_mhz, 2)}",
        " E / Emax (voltage)",
        " Angle   Magnitude",
    ]
    for angle, magnitude in zip(angles_deg, magnitudes):
        lines.append(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}")
    return "\n".join(lines) + "\n"


def _legacy_hrp_vep(context) -> str:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    wrapped_angles, wrapped_magnitudes = _reordered_hrp(angles_deg, magnitudes)
    lines = ["360,0,1"]
    for magnitude in wrapped_magnitudes:
        lines.append(_fmt(magnitude, 4))
    return "\n".join(lines) + "\n"


def _legacy_vrp_vep(context) -> str:
    angles_deg, magnitudes, _azimuth_deg, _directivity, tilt_deg = _get_displayed_vrp(context)
    lines = [
        "Generated by RFS ADT Elevation Pattern for use in V-Soft software",
        "Beam Tilt = " + str(float(tilt_deg)),
    ]
    angle_list = np.asarray(angles_deg, dtype=float)
    mag_list = np.asarray(magnitudes, dtype=float)
    if float(angle_list[0]) != -90.0:
        lines.append("-90.0 " + _fmt(mag_list[-1], 4))
    for angle, magnitude in zip(angle_list, mag_list):
        if angle <= -10.0:
            prefix = ""
        elif angle < 0.0:
            prefix = " "
        elif angle < 10.0:
            prefix = "  "
        else:
            prefix = " "
        lines.append(prefix + _fmt(angle, 1) + " " + _fmt(magnitude, 4))
    if float(angle_list[-1]) != 90.0:
        lines.append(" 90.0 " + _fmt(mag_list[0], 4))
    return "\n".join(lines) + "\n"


def _legacy_hrp_dia(context) -> str:
    meta = context.project.metadata
    gain_max = get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)) + 2.15
    phi_max, theta_max = _get_maximum_angles(context)
    angles_deg, magnitudes, _elevation_deg = extract_hrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        elevation_deg=theta_max,
    )
    lines = [
        f"product_number:\t{meta.antenna_model}",
        "manufacturer:\tRFS",
        f"comment:\t{meta.site_name}",
        f"date:\t{_date_short()}",
        f"frequency_MHz:\t{_fmt(meta.channel_frequency_mhz, 2)}",
        "gain_max_dBi\t" + _fmt(gain_max, 3),
        "pattern_plane:\tAzimuth",
        f"polarisation:\t{meta.polarization}",
        "azimuth_angle:\tvariable",
        "elevation_angle:\t" + _fmt(theta_max, 1) + " degree",
        "pattern_origin::\t",
        "dia\tResponse in dB",
    ]
    for angle, magnitude in zip(angles_deg, magnitudes):
        lines.append(f"{_fmt_int(angle)}\t{_fmt(_voltage_to_db(magnitude), 2)}")
    lines.append(f"180\t{_fmt(_voltage_to_db(magnitudes[0]), 2)}")
    return "\n".join(lines) + "\n"


def _legacy_vrp_dia(context) -> str:
    meta = context.project.metadata
    gain_max = get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)) + 2.15
    phi_max, _theta_max = _get_maximum_angles(context)
    _front_phi, series = _build_atdi_vrp_series(context)
    lines = [
        f"product_number:\t{meta.antenna_model}",
        "manufacturer:\tRFS",
        f"comment:\t{meta.site_name}",
        f"date:\t{_date_short()}",
        f"frequency_MHz:\t{_fmt(meta.channel_frequency_mhz, 2)}",
        "gain_max_dBi\t" + _fmt(gain_max, 3),
        "pattern_plane:\tElevation",
        f"polarisation:\t{meta.polarization}",
        "azimuth_angle:\t" + _fmt(_display_from_internal_azimuth(phi_max), 1) + " degree",
        "elevation_angle:\tvariable",
        "pattern_origin::\t",
        "dia\tResponse in dB",
    ]
    for angle, magnitude in series:
        lines.append(f"{angle}\t{_fmt(_voltage_to_db(magnitude), 2)}")
    return "\n".join(lines) + "\n"


def _legacy_3d_dia(context) -> str:
    magnitude = np.asarray(context.mag_3d, dtype=float)
    elevation_angles = np.asarray(context.el_angles, dtype=float)
    integer_el_indices = [
        (int(round(angle)), index)
        for index, angle in enumerate(elevation_angles)
        if round(float(angle), 1).is_integer()
    ]
    az_lookup = {round(float(angle), 1): index for index, angle in enumerate(np.asarray(context.az_angles, dtype=float))}
    lines = ["Azim\\Tilt" + "".join(f",{angle}°" for angle, _index in integer_el_indices)]
    for display_azimuth in range(0, 360):
        internal = round(_internal_from_display_azimuth(display_azimuth), 1)
        az_index = az_lookup[internal]
        row = [f"{display_azimuth}°"]
        for _angle, el_index in integer_el_indices:
            row.append(_fmt(-1.0 * _voltage_to_db(magnitude[az_index, el_index]), 2))
        lines.append(",".join(row))
    row = ["360°"]
    az_index = az_lookup[0.0]
    for _angle, el_index in integer_el_indices:
        row.append(_fmt(-1.0 * _voltage_to_db(magnitude[az_index, el_index]), 2))
    lines.append(",".join(row))
    return "\n".join(lines) + "\n"


def _legacy_3dp(context) -> str:
    lines = ["3D Data File by HVPAT (E/Emax)", "Azimuth ->", "Elevation"]
    lines.append("      " + "".join(f"      {angle}" for angle in range(0, 361)))
    for el_index, elevation_angle in enumerate(np.asarray(context.el_angles, dtype=float)):
        row_values = _get_azimuth_row_reordered(context, el_index)
        lines.append(f"{_fmt(elevation_angle, 1)}" + "".join(f" {_fmt(value, 4)}" for value in row_values))
    return "\n".join(lines) + "\n"


def _legacy_ngw3d(context) -> str:
    meta = context.project.metadata
    lines = [
        "[Comments]",
        f"{meta.site_name} {meta.antenna_model} By ADT".strip(),
        "[Gain dBdipole]",
        _fmt(get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)), 2),
        "[3D-Data]",
        "361",
        "251",
    ]
    for el_index, elevation_angle in enumerate(np.asarray(context.el_angles, dtype=float)):
        display_angle = -1.0 * float(elevation_angle)
        if display_angle < -20.0 or display_angle > 5.0:
            continue
        row_values = _get_azimuth_row_reordered(context, el_index)
        lines.append(f"{_fmt(display_angle, 1)}" + "".join(f" {_fmt(_voltage_to_db(value), 3)}" for value in row_values))
    return "\n".join(lines) + "\n"


def _legacy_prn(context) -> str:
    meta = context.project.metadata
    gain_dbi = get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)) + 2.15
    hrp_peak = _get_peak_horizontal_pattern(context)
    display_hrp = np.asarray([_display_from_internal_azimuth(angle) for angle in context.az_angles], dtype=float)
    order = np.argsort(display_hrp)
    hrp_sorted = hrp_peak[order]
    phi_max, _theta_max = _get_maximum_angles(context)
    front_angles, front_values = _get_integer_vrp_cut(context, phi_max)
    back_angles, back_values = _get_integer_vrp_cut(
        context,
        _internal_from_display_azimuth(_display_from_internal_azimuth(phi_max) + 180.0),
    )
    vertical_points: list[tuple[int, float]] = []
    for angle, magnitude in zip(front_angles, front_values):
        mapped = angle + 360.0 if angle < 0.0 else angle
        vertical_points.append((int(round(mapped)), float(magnitude)))
    for angle, magnitude in zip(back_angles, back_values):
        if angle <= -90.0 or angle >= 90.0:
            continue
        vertical_points.append((int(round(180.0 - angle)), float(magnitude)))
    vertical_points.sort(key=lambda item: item[0])
    lines = [
        "NAME " + "PATTERN",
        "MAKE RFS",
        "FREQUENCY " + _fmt(meta.channel_frequency_mhz, 2) + " MHz",
        "H_WIDTH",
        "V_WIDTH",
        "FRONT_TO_BACK",
        "GAIN " + _fmt(gain_dbi, 2) + " dBi",
        "TILT MECHANICAL",
        "HORIZONTAL 360",
    ]
    for index, magnitude in enumerate(hrp_sorted):
        lines.append(f"{index}\t{_fmt(-1.0 * _voltage_to_db(magnitude), 4)}")
    lines.append("VERTICAL 360")
    for index, magnitude in vertical_points:
        lines.append(f"{index}\t{_fmt(-1.0 * _voltage_to_db(magnitude), 4)}")
    return "\n".join(lines) + "\n"


def _legacy_edx(context) -> str:
    gain_dbi = get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)) + 2.15
    hrp_peak = _get_peak_horizontal_pattern(context)
    display_hrp = np.asarray([_display_from_internal_azimuth(angle) for angle in context.az_angles], dtype=float)
    order = np.argsort(display_hrp)
    hrp_sorted = hrp_peak[order]
    phi_max, _theta_max = _get_maximum_angles(context)
    vrp_angles, vrp_magnitudes, _azimuth = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=phi_max,
    )
    start_v = -1.0
    stop_v = 17.0
    increment = 0.1
    count = int((stop_v - start_v) / increment + 1.0)
    lines = [f"'By ADT', {_fmt(gain_dbi, 3)}, 1"]
    for index, magnitude in enumerate(hrp_sorted):
        lines.append(f"{index}, {_fmt(magnitude, 4)}")
    lines.append("999")
    lines.append(f"1, {count}")
    lines.append(f"{int(round(_display_from_internal_azimuth(phi_max)))},")
    lookup = {round(float(angle), 1): float(mag) for angle, mag in zip(vrp_angles, vrp_magnitudes)}
    for step in range(count):
        angle = round(start_v + step * increment, 1)
        lines.append(f"{_fmt(-1.0 * angle, 1)}, {_fmt(lookup[angle], 4)}")
    return "\n".join(lines) + "\n"


def _build_complex_sections() -> list[tuple[float, float, float, bool]]:
    return [(-10.0, -5.0, 0.5, False), (-5.0, 10.0, 0.1, False)]


def _legacy_complex_edx(context) -> str:
    gain_dbi = get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)) + 2.15
    hrp_peak = _get_peak_horizontal_pattern(context)
    display_hrp = np.asarray([_display_from_internal_azimuth(angle) for angle in context.az_angles], dtype=float)
    order = np.argsort(display_hrp)
    hrp_sorted = hrp_peak[order]
    phi_max, _theta_max = _get_maximum_angles(context)
    vrp_angles, vrp_magnitudes, _azimuth = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=phi_max,
    )
    lookup = {round(float(angle), 1): float(mag) for angle, mag in zip(vrp_angles, vrp_magnitudes)}
    sections = _build_complex_sections()
    total_points = sum(int((stop - start) / inc) + 1 for start, stop, inc, _zero in sections)
    for index in range(len(sections) - 1):
        if round(sections[index + 1][0] - sections[index][1], 2) == 0.0:
            total_points -= 1
        else:
            total_points += int((sections[index + 1][0] - sections[index][1]) / 0.1) - 1
    lines = [f"'By ADT', {_fmt(gain_dbi, 3)}, 1"]
    for index, magnitude in enumerate(hrp_sorted):
        lines.append(f"{index}, {_fmt(magnitude, 4)}")
    lines.append("999")
    lines.append(f"1, {total_points}")
    lines.append(f"{int(round(_display_from_internal_azimuth(phi_max)))},")

    for section_index, (start, stop, inc, zero) in enumerate(sections):
        section_count = int((stop - start) / inc)
        if section_index < len(sections) - 1:
            iterable = range(section_count)
        else:
            iterable = range(section_count + 1)
        for step in iterable:
            angle = round(start + step * inc, 1)
            value = 0.0001 if zero else lookup[angle]
            lines.append(f"{_fmt(-1.0 * angle, 1)}, {_fmt(value, 4)}")
        if section_index < len(sections) - 1:
            next_start = sections[section_index + 1][0]
            if round(next_start - stop, 2) != 0.0:
                gap_count = int((next_start - stop) / 0.1)
                for gap_step in range(gap_count):
                    angle = round(stop + gap_step * 0.1, 1)
                    lines.append(f"{_fmt(-1.0 * angle, 1)}, {_fmt(lookup[angle], 4)}")
    return "\n".join(lines) + "\n"


def _legacy_dir(context) -> str:
    meta = context.project.metadata
    phi_max, theta_max = _get_maximum_angles(context)
    hrp_angles, hrp_magnitudes, _ = extract_hrp_cut(
        context.mag_3d, context.az_angles, context.el_angles, elevation_deg=theta_max
    )
    vrp_angles, vrp_magnitudes, _ = extract_vrp_cut(
        context.mag_3d, context.az_angles, context.el_angles, azimuth_deg=phi_max
    )
    # These formulas are the same ones aligned earlier with the legacy ADT.
    from solver.pattern_synthesis import compute_hrp_cut_directivity_db, compute_vrp_cut_directivity_db

    lines = [
        _fmt(meta.channel_frequency_mhz, 2),
        _fmt_int(_display_from_internal_azimuth(phi_max)),
        _fmt(theta_max, 1),
        _fmt(compute_hrp_cut_directivity_db(hrp_magnitudes, hrp_magnitudes), 2),
        _fmt(compute_vrp_cut_directivity_db(vrp_angles, vrp_magnitudes, vrp_magnitudes), 2),
        _fmt(get_3d_directivity(np.asarray(context.mag_3d, dtype=float), np.asarray(context.el_angles, dtype=float)), 2),
    ]
    return "\n".join(lines) + "\n"


LEGACY_REFERENCE_BUILDERS = {
    "HRP PAT": _legacy_hrp_pat,
    "VRP PAT": _legacy_vrp_pat,
    "HRP Text": _legacy_hrp_txt,
    "VRP Text": _legacy_vrp_txt,
    "HRP CSV": _legacy_hrp_csv,
    "VRP CSV": _legacy_vrp_csv,
    "HRP V-Soft": _legacy_hrp_vep,
    "VRP V-Soft": _legacy_vrp_vep,
    "HRP ATDI": _legacy_hrp_dia,
    "VRP ATDI": _legacy_vrp_dia,
    "3D ATDI": _legacy_3d_dia,
    "3D Text": _legacy_3dp,
    "NGW3D": _legacy_ngw3d,
    "PRN": _legacy_prn,
    "EDX": _legacy_edx,
    "Complex EDX": _legacy_complex_edx,
    "Directivity": _legacy_dir,
}


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "ascii", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except Exception:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _write_visual_notes(target_dir: Path):
    lines = [
        "# Visual and Binary Export Notes",
        "",
        "The legacy reference generator in this comparison folder rebuilds the engineering and text-based exports directly from the recovered ADT source logic.",
        "",
        "For the visual exports below, the original ADT depends on chart/report rendering paths that are not yet replayed headlessly here:",
        "",
    ]
    for format_name, note in VISUAL_METHOD_NOTES.items():
        lines.append(f"- `{format_name}`: {note}")
    _write(target_dir / "VISUAL_EXPORT_NOTES.md", "\n".join(lines) + "\n")


def generate_comparison(output_dir: Path):
    if output_dir.exists():
        shutil.rmtree(output_dir)
    python_dir = output_dir / "adt_py"
    legacy_dir = output_dir / "legacy_reference"
    diffs_dir = output_dir / "diffs"
    python_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir.mkdir(parents=True, exist_ok=True)

    app, window = _build_window_with_pattern()
    context = window._build_export_context()

    for format_name, filename in {**TEXT_EXPORTS, **VISUAL_EXPORTS}.items():
        export_to_format(format_name, python_dir / filename, context)

    rows: list[ComparisonRow] = []
    for format_name, filename in TEXT_EXPORTS.items():
        legacy_content = LEGACY_REFERENCE_BUILDERS[format_name](context)
        legacy_path = legacy_dir / filename
        _write(legacy_path, legacy_content, encoding="utf-8")
        python_path = python_dir / filename
        python_content = _read_text(python_path)
        exact_match = python_content == legacy_content
        diff_path = ""
        if not exact_match:
            diff_text = "".join(
                difflib.unified_diff(
                    legacy_content.splitlines(keepends=True),
                    python_content.splitlines(keepends=True),
                    fromfile=f"legacy_reference/{filename}",
                    tofile=f"adt_py/{filename}",
                )
            )
            diff_file = diffs_dir / f"{filename}.diff.txt"
            _write(diff_file, diff_text)
            diff_path = str(diff_file.relative_to(output_dir))
        rows.append(
            ComparisonRow(
                format_name=format_name,
                filename=filename,
                exact_match=exact_match,
                python_lines=len(python_content.splitlines()),
                legacy_lines=len(legacy_content.splitlines()),
                diff_path=diff_path,
            )
        )

    _write_visual_notes(legacy_dir)

    report_lines = [
        "# Legacy vs Python Export Comparison",
        "",
        "Case: `default_case_4face_4level`",
        "",
        "## Text and engineering exports",
        "",
        "| Format | File | Match | Python lines | Legacy lines | Diff |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        report_lines.append(
            f"| `{row.format_name}` | `{row.filename}` | {'YES' if row.exact_match else 'NO'} | {row.python_lines} | {row.legacy_lines} | `{row.diff_path or '-'}` |"
        )

    report_lines.extend(
        [
            "",
            "## Visual and binary exports",
            "",
            "The Python outputs were generated into `adt_py/` for these formats too:",
            "",
        ]
    )
    for format_name, filename in VISUAL_EXPORTS.items():
        report_lines.append(f"- `{format_name}` -> `adt_py/{filename}`")
    report_lines.extend(
        [
            "",
            "The legacy renderer/source mapping for those visual exports is documented in `legacy_reference/VISUAL_EXPORT_NOTES.md`.",
            "",
        ]
    )
    _write(output_dir / "report.md", "\n".join(report_lines) + "\n")

    window.close()
    app.processEvents()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy vs Python export comparison.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "legacy_vs_python_exports" / "default_case_4face_4level"),
        help="Target directory for the comparison package.",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir).resolve()
    generate_comparison(output_dir)
    print(f"Comparison written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
