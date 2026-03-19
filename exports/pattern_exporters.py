from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import io
import math
from pathlib import Path
from typing import Any

import numpy as np
from PyQt6.QtCore import QBuffer, QByteArray, QMarginsF, QRect, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPageLayout, QPageSize, QPdfWriter
from PyQt6.QtWidgets import QApplication
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from app.project_service import build_project_from_ui, compose_panel_excitation
from solver.pattern_synthesis import (
    STANDARD_HRP_ANGLES,
    compute_hrp_cut_directivity_db,
    compute_vrp_cut_directivity_db,
    extract_hrp_cut,
    extract_vrp_cut,
    get_3d_directivity,
    get_maximum_field_angles,
    get_vrp_beam_tilt_deg,
)


EPSILON = 1e-12
PAGE_PORTRAIT = (1240, 1754)
PAGE_LANDSCAPE = (1754, 1240)
LEGACY_PLOT_IMAGE_SIZE = (1000, 1400)
LEGACY_PLOT_HEADER_HEIGHT = 160
LEGACY_PLOT_BODY_HEIGHT = 1000
LEGACY_PLOT_FOOTER_HEIGHT = 240
DEFAULT_EDX_START_DEG = -5.0
DEFAULT_EDX_STOP_DEG = 15.0
DEFAULT_EDX_INCREMENT_DEG = 0.1
DEFAULT_COMPLEX_EDX_SECTIONS = (
    (-10.0, -5.0, 0.5, False),
    (-5.0, 10.0, 0.1, False),
)
DEFAULT_COMPLEX_EDX_ZERO = 0.0001
LEGACY_HEADER_TITLES = {
    "HRP_Header.bmp": "Horizontal Radiation Pattern",
    "VRP_Header.bmp": "Vertical Radiation Pattern",
    "Layout_Header.bmp": "Tower and Panel Layout",
}


@dataclass(frozen=True)
class ExportDefinition:
    label: str
    file_filter: str
    suffix: str
    requires_pattern: bool = True


@dataclass
class ExportContext:
    project: Any | None = None
    metrics: dict[str, Any] | None = None
    mag_3d: np.ndarray | None = None
    az_angles: np.ndarray | None = None
    el_angles: np.ndarray | None = None
    hrp_elevation_deg: float | None = None
    vrp_azimuth_deg: float | None = None
    normalised_vrp: bool = False
    design_info_widget: Any | None = None
    antenna_design_widget: Any | None = None
    pattern_library_widget: Any | None = None
    result_summary_widget: Any | None = None
    hrp_widget: Any | None = None
    vrp_widget: Any | None = None
    tower_preview_widget: Any | None = None
    logo_path: str | Path | None = None
    rotation_angle_deg: float = 0.0
    edx_peak_hrp: bool = True
    edx_start_deg: float = DEFAULT_EDX_START_DEG
    edx_stop_deg: float = DEFAULT_EDX_STOP_DEG
    edx_increment_deg: float = DEFAULT_EDX_INCREMENT_DEG
    export_image_scale: float = 1.0


EXPORT_DEFINITIONS: dict[str, ExportDefinition] = {
    "HRP PAT": ExportDefinition(
        "Save Displayed Pattern as EFTX PAT Format / HRP",
        "Antenna Pattern Files (*.pat);;All Files (*)",
        ".pat",
    ),
    "VRP PAT": ExportDefinition(
        "Save Displayed Pattern as EFTX PAT Format / VRP",
        "Antenna Pattern Files (*.pat);;All Files (*)",
        ".pat",
    ),
    "HRP Text": ExportDefinition(
        "Save Displayed Pattern as Text Format / HRP",
        "Antenna Pattern Files (*.txt);;All Files (*)",
        ".txt",
    ),
    "VRP Text": ExportDefinition(
        "Save Displayed Pattern as Text Format / VRP",
        "Antenna Pattern Files (*.txt);;All Files (*)",
        ".txt",
    ),
    "HRP CSV": ExportDefinition(
        "Save Displayed Pattern as CSV Format / HRP",
        "Antenna Pattern Files (*.csv);;All Files (*)",
        ".csv",
    ),
    "VRP CSV": ExportDefinition(
        "Save Displayed Pattern as CSV Format / VRP",
        "Antenna Pattern Files (*.csv);;All Files (*)",
        ".csv",
    ),
    "HRP V-Soft": ExportDefinition(
        "Save Displayed Pattern as V-Soft Format / HRP",
        "Antenna Pattern Files (*.vep);;All Files (*)",
        ".vep",
    ),
    "VRP V-Soft": ExportDefinition(
        "Save Displayed Pattern as V-Soft Format / VRP",
        "Antenna Pattern Files (*.vep);;All Files (*)",
        ".vep",
    ),
    "HRP ATDI": ExportDefinition(
        "Save Pattern as ATDI Format / HRP",
        "Antenna Pattern Files (*.H_DIA.DIA);;All Files (*)",
        ".H_DIA.DIA",
    ),
    "VRP ATDI": ExportDefinition(
        "Save Pattern as ATDI Format / VRP",
        "Antenna Pattern Files (*.V_DIA.DIA);;All Files (*)",
        ".V_DIA.DIA",
    ),
    "3D ATDI": ExportDefinition(
        "Save Pattern as ATDI Format / 3D",
        "Antenna Pattern Files (*.csv);;All Files (*)",
        ".csv",
    ),
    "3D Text": ExportDefinition(
        "Save 3D Pattern as Text Format (1° Az, 0.1° El)",
        "Antenna Pattern Files (*.3dp);;All Files (*)",
        ".3dp",
    ),
    "NGW3D": ExportDefinition(
        "Save 3D Pattern as NGW3D Format (1° Az, 0.1° El)",
        "Antenna Pattern Files (*.ng3dant);;All Files (*)",
        ".ng3dant",
    ),
    "PRN": ExportDefinition(
        "Save 3D Pattern as PRN Format (1° Az, 1° El)",
        "Antenna Pattern Files (*.prn);;All Files (*)",
        ".prn",
    ),
    "EDX": ExportDefinition(
        "Save Pattern as Progira / EDX Format",
        "Antenna Pattern Files (*.ProgiraEDX.pat);;All Files (*)",
        ".ProgiraEDX.pat",
    ),
    "Complex EDX": ExportDefinition(
        "Save Pattern as Complex Progira / EDX Format",
        "Antenna Pattern Files (*.ProgiraEDX.pat);;All Files (*)",
        ".ProgiraEDX.pat",
    ),
    "Directivity": ExportDefinition(
        "Save Directivity File",
        "Antenna Directivity Files (*.dir);;All Files (*)",
        ".dir",
    ),
    "Video": ExportDefinition(
        "Save VRP Animation as Video (.avi)",
        "Antenna Video Files (*.avi);;All Files (*)",
        ".avi",
    ),
    "HRP JPEG": ExportDefinition(
        "Save Displayed HRP to File (jpg)",
        "Antenna Pattern Files (*.jpg);;All Files (*)",
        ".jpg",
    ),
    "VRP JPEG": ExportDefinition(
        "Save Displayed VRP to File (jpg)",
        "Antenna Pattern Files (*.jpg);;All Files (*)",
        ".jpg",
    ),
    "Layout JPEG": ExportDefinition(
        "Save Layout to File (jpg)",
        "Antenna Pattern Files (*.jpg);;All Files (*)",
        ".jpg",
        requires_pattern=False,
    ),
    "HRP PDF": ExportDefinition(
        "Save Displayed HRP to File (pdf)",
        "Adobe PDF Files (*.pdf);;All Files (*)",
        ".pdf",
    ),
    "VRP PDF": ExportDefinition(
        "Save Displayed VRP to File (pdf)",
        "Adobe PDF Files (*.pdf);;All Files (*)",
        ".pdf",
    ),
    "Summary PDF": ExportDefinition(
        "Save Result Summary to File (pdf)",
        "Adobe PDF Files (*.pdf);;All Files (*)",
        ".pdf",
    ),
    "Panel PDF": ExportDefinition(
        "Save Panel Positions and Electrical Data to File (pdf)",
        "Adobe PDF Files (*.pdf);;All Files (*)",
        ".pdf",
        requires_pattern=False,
    ),
    "All PDF": ExportDefinition(
        "Save All to File (pdf)",
        "Adobe PDF Files (*.pdf);;All Files (*)",
        ".pdf",
    ),
}


def get_export_definition(format_name: str) -> ExportDefinition:
    return EXPORT_DEFINITIONS[format_name]


def ensure_project_context(context: ExportContext) -> ExportContext:
    if context.project is not None:
        return context
    if (
        context.design_info_widget is None
        or context.antenna_design_widget is None
        or context.pattern_library_widget is None
    ):
        return context
    context.project = build_project_from_ui(
        context.design_info_widget,
        context.antenna_design_widget,
        context.pattern_library_widget,
    )
    return context


def _require_pattern(context: ExportContext):
    if context.mag_3d is None or context.az_angles is None or context.el_angles is None:
        raise ValueError("Calculate 3D Pattern first.")


def _fmt(value: float, decimals: int) -> str:
    numeric = 0.0 if abs(float(value)) < 0.5 * 10 ** (-decimals) else float(value)
    return f"{numeric:.{decimals}f}"


def _fmt_int(value: float) -> str:
    return f"{float(value):.0f}"


def _fmt_compact(value: float, decimals: int = 2) -> str:
    text = _fmt(value, decimals).rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


def _fmt_db(value: float, decimals: int) -> str:
    return _fmt(value, decimals)


def _voltage_to_db(magnitude: float) -> float:
    return 20.0 * math.log10(max(float(magnitude), EPSILON))


def _today_long() -> str:
    return datetime.now().strftime("%B %d, %Y").replace(" 0", " ")


def _today_short() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def _open_text_export(path: str | Path, encoding: str = "utf-8"):
    return open(path, "w", encoding=encoding, newline="\r\n")


def _normalize_vrp_if_needed(
    angles_deg: np.ndarray,
    magnitudes: np.ndarray,
    normalised: bool,
) -> tuple[np.ndarray, np.ndarray]:
    ordered_angles = np.asarray(angles_deg, dtype=float)
    ordered_magnitudes = np.asarray(magnitudes, dtype=float)
    order = np.argsort(ordered_angles)
    ordered_angles = ordered_angles[order]
    ordered_magnitudes = ordered_magnitudes[order]
    if not normalised:
        return ordered_angles, ordered_magnitudes
    peak = float(np.max(ordered_magnitudes)) if ordered_magnitudes.size else 0.0
    if peak <= 0.0:
        return ordered_angles, ordered_magnitudes
    return ordered_angles, ordered_magnitudes / peak


def _collect_pattern_metadata(context: ExportContext) -> dict[str, str]:
    context = ensure_project_context(context)
    project = context.project
    if project is None:
        return {
            "customer": "",
            "site_name": "",
            "antenna_model": "",
            "frequency_mhz": "0.00",
            "polarisation": "",
            "design_frequency_mhz": "0.000",
        }
    return {
        "customer": project.metadata.customer,
        "site_name": project.metadata.site_name,
        "antenna_model": project.metadata.antenna_model,
        "frequency_mhz": _fmt(project.metadata.channel_frequency_mhz, 2),
        "polarisation": project.metadata.polarization,
        "design_frequency_mhz": _fmt(project.metadata.design_frequency_mhz, 3),
    }


def _primary_pattern_definition(context: ExportContext):
    context = ensure_project_context(context)
    if context.project is None or not context.project.patterns:
        return None
    return context.project.patterns[0]


def _hrp_unit_pattern_label(context: ExportContext) -> str:
    pattern = _primary_pattern_definition(context)
    if pattern is None:
        return ""
    if pattern.hrp_path:
        return Path(pattern.hrp_path).name
    return pattern.panel_type


def _panel_dimensions_by_slot(context: ExportContext) -> list[tuple[str, str, str]]:
    context = ensure_project_context(context)
    if context.project is None:
        return []

    pattern_by_index = {pattern.index: pattern for pattern in context.project.patterns}
    active_patterns = []
    seen = set()
    for panel in context.project.panels:
        if float(panel.power) == 0.0:
            continue
        pattern = pattern_by_index.get(panel.pattern_index)
        if pattern is None or pattern.index in seen:
            continue
        seen.add(pattern.index)
        width_text = (
            f"{pattern.width_m:.3f}(W)"
            if pattern.depth_m > 0.001
            else f"{pattern.width_m:.3f}(D)"
        )
        depth_text = f"{pattern.depth_m:.3f}" if pattern.depth_m > 0.001 else ""
        active_patterns.append((width_text, f"{pattern.height_m:.3f}", depth_text))
        if len(active_patterns) == 4:
            break
    return active_patterns


def _get_maximum_angles(context: ExportContext) -> tuple[float, float]:
    _require_pattern(context)
    if context.metrics is not None:
        az_text = context.metrics.get("Azimuth Angle (Emax) (deg)")
        el_text = context.metrics.get("Elevation Angle (Emax) (deg)")
        if az_text is not None and el_text is not None:
            return float(az_text), float(el_text)
    azimuth_of_max, elevation_of_max, _az_index, _el_index = get_maximum_field_angles(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.az_angles, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    )
    return float(azimuth_of_max), float(elevation_of_max)


def _get_displayed_hrp(context: ExportContext) -> tuple[np.ndarray, np.ndarray, float, float]:
    _require_pattern(context)
    elevation_deg = context.hrp_elevation_deg
    if elevation_deg is None and context.metrics is not None:
        elevation_deg = context.metrics.get("_hrp_cut_elevation_deg")
    angles_deg, magnitudes, elevation_deg = extract_hrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        elevation_deg=elevation_deg,
    )
    peak = None
    if context.metrics is not None:
        peak = context.metrics.get("_hrp_cut_magnitude")
    if peak is None:
        _az_max, el_max = _get_maximum_angles(context)
        _peak_angles, peak, _peak_elevation = extract_hrp_cut(
            context.mag_3d,
            context.az_angles,
            context.el_angles,
            elevation_deg=el_max,
        )
    directivity = compute_hrp_cut_directivity_db(magnitudes, peak)
    return (
        np.asarray(angles_deg, dtype=float),
        np.asarray(magnitudes, dtype=float),
        float(elevation_deg),
        float(directivity),
    )


def _get_displayed_vrp(
    context: ExportContext,
) -> tuple[np.ndarray, np.ndarray, float, float, float]:
    _require_pattern(context)
    azimuth_deg = context.vrp_azimuth_deg
    if azimuth_deg is None and context.metrics is not None:
        azimuth_deg = context.metrics.get("_vrp_cut_azimuth_deg")
    angles_deg, magnitudes, azimuth_deg = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=azimuth_deg,
    )
    peak = None
    if context.metrics is not None:
        peak = context.metrics.get("_vrp_cut_magnitude")
    if peak is None:
        az_max, _el_max = _get_maximum_angles(context)
        _peak_angles, peak, _peak_azimuth = extract_vrp_cut(
            context.mag_3d,
            context.az_angles,
            context.el_angles,
            azimuth_deg=az_max,
        )
    directivity = compute_vrp_cut_directivity_db(angles_deg, magnitudes, peak)
    tilt_deg = get_vrp_beam_tilt_deg(angles_deg, magnitudes)
    return (
        np.asarray(angles_deg, dtype=float),
        np.asarray(magnitudes, dtype=float),
        float(azimuth_deg),
        float(directivity),
        float(tilt_deg),
    )


def _internal_from_display_azimuth(display_angle_deg: float) -> float:
    return float(((float(display_angle_deg) + 180.0) % 360.0) - 180.0)


def _display_from_internal_azimuth(angle_deg: float) -> float:
    return float(float(angle_deg) % 360.0)


def _angle_index_lookup(angles_deg: np.ndarray) -> dict[float, int]:
    lookup: dict[float, int] = {}
    for index, value in enumerate(np.asarray(angles_deg, dtype=float)):
        lookup[round(float(value), 1)] = index
    return lookup


def _get_azimuth_row_reordered(context: ExportContext, elevation_index: int) -> list[float]:
    azimuth_lookup = _angle_index_lookup(np.asarray(context.az_angles, dtype=float))
    row = np.asarray(context.mag_3d, dtype=float)[:, elevation_index]
    values = []
    for display_azimuth in range(0, 360):
        internal = round(_internal_from_display_azimuth(display_azimuth), 1)
        values.append(float(row[azimuth_lookup[internal]]))
    values.append(values[0])
    return values


def _get_integer_vrp_cut(
    context: ExportContext,
    azimuth_deg: float,
) -> tuple[np.ndarray, np.ndarray]:
    angles_deg, magnitudes, _azimuth_deg = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=azimuth_deg,
    )
    integer_angles = []
    integer_values = []
    for angle, magnitude in zip(angles_deg, magnitudes):
        if round(float(angle), 1).is_integer():
            integer_angles.append(float(round(float(angle), 0)))
            integer_values.append(float(magnitude))
    return np.asarray(integer_angles, dtype=float), np.asarray(integer_values, dtype=float)


def _get_peak_horizontal_pattern(context: ExportContext) -> np.ndarray:
    _require_pattern(context)
    magnitude = np.asarray(context.mag_3d, dtype=float)
    return np.max(magnitude, axis=1)


def _get_peak_horizontal_pattern_sorted(context: ExportContext) -> np.ndarray:
    peak_pattern = _get_peak_horizontal_pattern(context)
    display_angles = np.asarray(
        [_display_from_internal_azimuth(angle) for angle in STANDARD_HRP_ANGLES],
        dtype=float,
    )
    order = np.argsort(display_angles)
    return peak_pattern[order]


def _get_displayed_horizontal_pattern_sorted(context: ExportContext) -> np.ndarray:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    display_angles = np.asarray(
        [_display_from_internal_azimuth(angle) for angle in np.asarray(angles_deg, dtype=float)],
        dtype=float,
    )
    order = np.argsort(display_angles)
    return np.asarray(magnitudes, dtype=float)[order]


def _get_hrp_for_export(context: ExportContext) -> tuple[np.ndarray, np.ndarray]:
    angles_deg, magnitudes, _elevation_deg, _directivity = _get_displayed_hrp(context)
    return angles_deg, magnitudes


def _get_vrp_for_export(context: ExportContext) -> tuple[np.ndarray, np.ndarray]:
    angles_deg, magnitudes, _azimuth_deg, _directivity, _tilt_deg = _get_displayed_vrp(context)
    return _normalize_vrp_if_needed(angles_deg, magnitudes, context.normalised_vrp)


def _build_atdi_vrp_series(context: ExportContext) -> tuple[float, list[tuple[int, float]]]:
    phi_max, _theta_max = _get_maximum_angles(context)
    front_angles, front_magnitudes = _get_integer_vrp_cut(context, phi_max)
    back_angles, back_magnitudes = _get_integer_vrp_cut(
        context,
        _internal_from_display_azimuth(_display_from_internal_azimuth(phi_max) + 180.0),
    )

    series: list[tuple[int, float]] = []
    for angle, magnitude in zip(front_angles, front_magnitudes):
        series.append((int(round(-1.0 * angle)), float(magnitude)))

    for angle, magnitude in zip(back_angles, back_magnitudes):
        if angle in (-90.0, 90.0):
            continue
        adjusted = float(angle)
        if adjusted > -90.0 and adjusted <= 0.0:
            adjusted = -180.0 - adjusted
        elif adjusted > 0.0 and adjusted < 90.0:
            adjusted = 180.0 - adjusted
        series.append((int(round(-1.0 * adjusted)), float(magnitude)))

    for angle, magnitude in list(series):
        if angle == 180:
            series.append((-180, magnitude))
            break

    series.sort(key=lambda item: item[0])
    return phi_max, series


def _result_summary_rows(context: ExportContext) -> list[tuple[str, str]]:
    if context.result_summary_widget is not None:
        table = context.result_summary_widget.table
        rows = []
        for row in range(table.rowCount()):
            key_item = table.item(row, 0)
            value_item = table.item(row, 1)
            rows.append(
                (
                    key_item.text() if key_item is not None else "",
                    value_item.text() if value_item is not None else "",
                )
            )
        return rows
    if context.metrics is None:
        return []
    return [
        (key, str(value))
        for key, value in context.metrics.items()
        if not str(key).startswith("_")
    ]


def _panel_position_rows(context: ExportContext) -> list[list[str]]:
    context = ensure_project_context(context)
    if context.project is None:
        return []

    horizontal_groups = context.project.horizontal_groups
    vertical_groups = context.project.vertical_groups
    rows = []

    for panel in context.project.panels:
        h_group = horizontal_groups.get(panel.face.upper())
        v_group = vertical_groups.get(panel.level)
        effective_power, effective_phase = compose_panel_excitation(
            panel,
            horizontal_groups,
            vertical_groups,
        )
        rows.append(
            [
                str(panel.panel_id),
                _fmt(panel.angle_deg, 1),
                _fmt(panel.offset_m, 3),
                _fmt(panel.elevation_m, 3),
                _fmt(panel.azimuth_deg, 1),
                _fmt(effective_power, 3),
                _fmt(panel.phase_deg, 1),
                f"{v_group.phase_deg:+.1f}" if v_group is not None else f"{0.0:+.1f}",
                f"{h_group.phase_deg:+.1f}" if h_group is not None else f"{0.0:+.1f}",
                f"= {effective_phase:.1f}",
                _fmt(panel.tilt_deg, 1),
                _fmt_int(panel.configuration),
                _fmt_int(panel.pattern_index),
                _fmt_int(panel.level),
                panel.face,
                _fmt_int(panel.input_number),
            ]
        )
    return rows


def _logo_image(context: ExportContext) -> QImage | None:
    if context.logo_path is None:
        return None
    path = Path(context.logo_path)
    if not path.exists():
        return None
    image = QImage(str(path))
    return image if not image.isNull() else None


def _legacy_pic_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[2] / "Pic" / filename


def _font_path(bold: bool = False) -> str | None:
    windows_fonts = Path("C:/Windows/Fonts")
    candidates = ["arialbd.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]
    for candidate in candidates:
        path = windows_fonts / candidate
        if path.exists():
            return str(path)
    return None


def _load_pil_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = _font_path(bold=bold)
    if font_path is None:
        return ImageFont.load_default()
    return ImageFont.truetype(font_path, size=size)


def _qimage_to_pil(image: QImage) -> PILImage.Image:
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    try:
        image.save(buffer, "PNG")
    finally:
        buffer.close()
    return PILImage.open(io.BytesIO(bytes(byte_array))).convert("RGB")


def _qimage_from_pil(image: PILImage.Image) -> QImage:
    rgb = image.convert("RGB")
    data = rgb.tobytes("raw", "RGB")
    qimage = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return qimage.copy()


def _load_eftx_logo_pil(context: ExportContext) -> PILImage.Image | None:
    if context.logo_path is None:
        return None
    logo_path = Path(context.logo_path)
    if not logo_path.exists():
        return None

    logo = PILImage.open(logo_path).convert("RGBA")
    rgba = np.asarray(logo).copy()
    white_mask = (
        (rgba[:, :, 0] > 245)
        & (rgba[:, :, 1] > 245)
        & (rgba[:, :, 2] > 245)
    )
    rgba[white_mask, 3] = 0
    clean_logo = PILImage.fromarray(rgba, mode="RGBA")
    bbox = clean_logo.getbbox()
    return clean_logo.crop(bbox) if bbox else clean_logo


def _template_with_eftx_logo(template_name: str, context: ExportContext) -> PILImage.Image:
    template = PILImage.open(_legacy_pic_path(template_name)).convert("RGBA")
    logo = _load_eftx_logo_pil(context)
    if logo is None:
        return template

    red_pixels = []
    pixels = template.load()
    for y_pos in range(template.height):
        for x_pos in range(template.width):
            red, green, blue, alpha = pixels[x_pos, y_pos]
            if alpha and red > 150 and green < 140 and blue < 140:
                red_pixels.append((x_pos, y_pos))

    if not red_pixels:
        return template

    min_x = min(point[0] for point in red_pixels)
    min_y = min(point[1] for point in red_pixels)
    max_x = max(point[0] for point in red_pixels)
    max_y = max(point[1] for point in red_pixels)
    target_width = max_x - min_x + 1
    target_height = max_y - min_y + 1

    draw = ImageDraw.Draw(template)
    draw.rectangle((min_x, min_y, max_x, max_y), fill="white")

    scaled = logo.copy()
    scaled.thumbnail(
        (max(1, int(target_width * 0.62)), max(1, int(target_height * 0.34))),
        PILImage.Resampling.LANCZOS,
    )
    paste_x = min_x + (target_width - scaled.width) // 2
    paste_y = min_y + 4
    template.alpha_composite(scaled, (paste_x, paste_y))

    title_text = LEGACY_HEADER_TITLES.get(template_name)
    if title_text:
        draw = ImageDraw.Draw(template)
        title_font = _load_pil_font(29, bold=True)
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_x = (template.width - (bbox[2] - bbox[0])) // 2
        draw.rectangle((90, 96, template.width - 90, 156), fill="white")
        draw.text((text_x, 102), title_text, fill="black", font=title_font)

    return template


def _new_canvas(size: tuple[int, int]) -> QImage:
    image = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    return image


def _draw_logo_header(
    painter: QPainter,
    canvas_width: int,
    context: ExportContext,
    title: str,
    subtitle_lines: list[str] | None = None,
):
    logo = _logo_image(context)
    left = 48
    top = 40
    if logo is not None:
        target = QRect(left, top, 180, 80)
        scaled = logo.scaled(
            target.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawImage(
            QRect(target.x(), target.y(), scaled.width(), scaled.height()),
            scaled,
        )
    painter.setPen(QColor("#1a1a1a"))
    painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
    painter.drawText(
        QRect(250, 38, canvas_width - 300, 42),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        title,
    )
    painter.setFont(QFont("Arial", 9))
    if subtitle_lines:
        for index, line in enumerate(subtitle_lines):
            painter.drawText(
                QRect(250, 84 + index * 20, canvas_width - 300, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                line,
            )
    painter.setPen(QColor("#d0d0d0"))
    painter.drawLine(40, 132, canvas_width - 40, 132)


def _metadata_lines(context: ExportContext) -> list[str]:
    meta = _collect_pattern_metadata(context)
    return [
        f"Customer: {meta['customer'] or '-'}",
        f"Site Name: {meta['site_name'] or '-'}",
        f"Antenna Model: {meta['antenna_model'] or '-'}",
        f"Frequency (MHz): {meta['frequency_mhz']}",
        f"Polarisation: {meta['polarisation'] or '-'}",
        f"Prepared: {_today_long()}",
    ]


def _widget_grab(widget: Any, fallback_size: tuple[int, int] = (1200, 700)) -> QImage:
    if widget is None:
        return _new_canvas(fallback_size)
    pixmap = widget.grab()
    if pixmap.isNull():
        return _new_canvas(fallback_size)
    return pixmap.toImage()


def _compose_widget_report_image(
    context: ExportContext,
    title: str,
    widget_image: QImage,
    extra_lines: list[str] | None = None,
    size: tuple[int, int] = PAGE_LANDSCAPE,
) -> QImage:
    canvas = _new_canvas(size)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    lines = _metadata_lines(context)
    if extra_lines:
        lines.extend(extra_lines)
    _draw_logo_header(painter, size[0], context, title, lines[:6])

    content_rect = QRect(40, 156, size[0] - 80, size[1] - 196)
    painter.setPen(QColor("#cfcfcf"))
    painter.setBrush(QColor("white"))
    painter.drawRect(content_rect)

    scaled = widget_image.scaled(
        content_rect.size(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    image_x = content_rect.x() + (content_rect.width() - scaled.width()) // 2
    image_y = content_rect.y() + (content_rect.height() - scaled.height()) // 2
    painter.drawImage(QRect(image_x, image_y, scaled.width(), scaled.height()), scaled)
    painter.end()
    return canvas


def _draw_table(
    painter: QPainter,
    top_left_x: int,
    top_left_y: int,
    column_widths: list[int],
    rows: list[list[str]],
    header_fill: QColor | None = None,
    row_height: int = 26,
    font: QFont | None = None,
):
    if font is not None:
        painter.setFont(font)
    y = top_left_y

    for row_index, row in enumerate(rows):
        x = top_left_x
        if row_index == 0 and header_fill is not None:
            painter.fillRect(QRect(x, y, sum(column_widths), row_height), header_fill)
        for column_index, width in enumerate(column_widths):
            painter.setPen(QColor("#808080"))
            painter.drawRect(QRect(x, y, width, row_height))
            painter.setPen(QColor("#101010"))
            painter.drawText(
                QRect(x + 4, y + 2, width - 8, row_height - 4),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                row[column_index] if column_index < len(row) else "",
            )
            x += width
        y += row_height


def _build_summary_pages(context: ExportContext) -> list[QImage]:
    rows = [["Parameter", "Value"], *_result_summary_rows(context)]
    canvas = _new_canvas(PAGE_PORTRAIT)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    _draw_logo_header(painter, PAGE_PORTRAIT[0], context, "Result Summary")
    _draw_table(
        painter,
        70,
        180,
        [510, 550],
        rows,
        header_fill=QColor("#e8e8e8"),
        row_height=34,
        font=QFont("Arial", 10),
    )
    painter.end()
    return [canvas]


def _build_panel_pages(context: ExportContext) -> list[QImage]:
    meta = _collect_pattern_metadata(context)
    headers = [
        "Panel",
        "Angle",
        "Offset",
        "Elevation",
        "Azimuth",
        "Power",
        "Phase",
        "V Phase",
        "H Phase",
        "Total Φ",
        "Tilt",
        "Config",
        "Pattern",
        "Level",
        "Face",
        "Input",
    ]
    rows = _panel_position_rows(context)
    page_rows = 34
    column_widths = [72, 82, 88, 96, 88, 80, 82, 82, 82, 88, 72, 72, 72, 72, 62, 62]
    pages = []

    for start in range(0, max(1, len(rows)), page_rows):
        canvas = _new_canvas(PAGE_LANDSCAPE)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        subtitle = [f"All phases referenced to {meta['design_frequency_mhz']} MHz"]
        _draw_logo_header(
            painter,
            PAGE_LANDSCAPE[0],
            context,
            "Panel Positions and Electrical Data",
            subtitle,
        )
        page_slice = rows[start:start + page_rows]
        _draw_table(
            painter,
            28,
            182,
            column_widths,
            [headers, *page_slice],
            header_fill=QColor("#e8e8e8"),
            row_height=28,
            font=QFont("Arial", 8),
        )
        painter.end()
        pages.append(canvas)
    return pages


def _write_pdf_pages(path: str | Path, pages: list[QImage], landscape: bool):
    writer = QPdfWriter(str(path))
    writer.setResolution(150)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageOrientation(
        QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait
    )
    writer.setPageMargins(QMarginsF(8, 8, 8, 8))

    painter = QPainter(writer)
    try:
        page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
        for index, image in enumerate(pages):
            if index > 0:
                writer.newPage()
            scaled = image.scaled(
                page_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = page_rect.x() + (page_rect.width() - scaled.width()) // 2
            y = page_rect.y() + (page_rect.height() - scaled.height()) // 2
            painter.drawImage(QRect(x, y, scaled.width(), scaled.height()), scaled)
    finally:
        painter.end()


def _save_image(path: str | Path, image: QImage):
    if not image.save(str(path), "JPG", quality=95):
        raise ValueError(f"Could not export image to {path}")


def _qimage_to_rgb_array(image: QImage) -> np.ndarray:
    rgb_image = image.convertToFormat(QImage.Format.Format_RGB888)
    width = rgb_image.width()
    height = rgb_image.height()
    ptr = rgb_image.bits()
    ptr.setsize(rgb_image.sizeInBytes())
    row_array = np.frombuffer(ptr, np.uint8).reshape((height, rgb_image.bytesPerLine()))
    rgb_array = row_array[:, : width * 3].reshape((height, width, 3))
    return np.ascontiguousarray(rgb_array)


def _grab_widget_resized(widget: Any, width: int, height: int) -> QImage:
    if widget is None:
        return _new_canvas((width, height))

    previous_size = widget.size()
    previous_minimum_size = widget.minimumSize()
    previous_maximum_size = widget.maximumSize()
    try:
        widget.setMinimumSize(width, height)
        widget.setMaximumSize(width, height)
        widget.resize(width, height)
        widget.update()
        QApplication.processEvents()
        pixmap = widget.grab()
    finally:
        widget.setMinimumSize(previous_minimum_size)
        widget.setMaximumSize(previous_maximum_size)
        widget.resize(previous_size)
        widget.update()
        QApplication.processEvents()

    if pixmap.isNull():
        return _new_canvas((width, height))
    return pixmap.toImage()


def _save_pil_image(path: str | Path, image: PILImage.Image, format_name: str):
    if format_name.upper() == "GIF":
        gif_image = image.convert("P", palette=PILImage.Palette.ADAPTIVE, colors=256, dither=PILImage.Dither.NONE)
        gif_image.save(str(path), format=format_name, comment=b"EFTX")
        return
    image.save(str(path), format=format_name)


def _save_pil_pdf(path: str | Path, *pages: PILImage.Image):
    if not pages:
        raise ValueError("No pages provided for PDF export.")
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(
        str(path),
        format="PDF",
        save_all=True,
        append_images=rgb_pages[1:],
        resolution=150.0,
    )
    _normalize_pdf_media_box(path, 595.276, 841.89)


def _normalize_pdf_media_box(path: str | Path, width_pt: float, height_pt: float):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (width_pt, height_pt)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (width_pt, height_pt)
        writer.add_page(page)
    with Path(path).open("wb") as handle:
        writer.write(handle)


def _draw_underlined_text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str = "black",
):
    draw.text(position, text, fill=fill, font=font)
    bbox = draw.textbbox(position, text, font=font)
    underline_y = bbox[3] + 1
    draw.line((bbox[0], underline_y, bbox[2], underline_y), fill=fill, width=1)


def _render_plot_body(
    plot_image: QImage,
    target_box: tuple[int, int, int, int],
) -> PILImage.Image:
    body = PILImage.new("RGBA", (LEGACY_PLOT_IMAGE_SIZE[0], LEGACY_PLOT_BODY_HEIGHT), "white")
    plot = _qimage_to_pil(plot_image).convert("RGBA")
    max_width, max_height = target_box[2], target_box[3]
    plot.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
    x_pos = target_box[0] + (max_width - plot.width) // 2
    y_pos = target_box[1] + (max_height - plot.height) // 2
    body.alpha_composite(plot, (x_pos, y_pos))
    return body


def _compose_hrp_vrp_report_image(
    context: ExportContext,
    template_name: str,
    plot_image: QImage,
    plot_box: tuple[int, int, int, int],
    right_labels: list[tuple[str, str, int]],
    unit_pattern_label: str = "",
) -> PILImage.Image:
    header = _template_with_eftx_logo(template_name, context).convert("RGBA")
    body = _render_plot_body(plot_image, plot_box)
    footer = PILImage.open(_legacy_pic_path("Footer.bmp")).convert("RGBA")

    draw = ImageDraw.Draw(footer)
    regular_font = _load_pil_font(16, bold=False)
    value_font = _load_pil_font(16, bold=False)
    small_font = _load_pil_font(10, bold=False)
    unit_font = _load_pil_font(12, bold=False)

    left_labels = [
        ("Model:", (60, 0)),
        ("Location:", (60, 40)),
        ("Customer:", (60, 80)),
        ("Date:", (60, 120)),
    ]
    meta = _collect_pattern_metadata(context)
    left_values = [
        (meta["antenna_model"], (200, 0)),
        (meta["site_name"], (200, 40)),
        (meta["customer"], (200, 80)),
        (_today_long(), (200, 120)),
    ]
    for text, position in left_labels:
        draw.text(position, text, fill="black", font=regular_font)
    for text, position in left_values:
        draw.text(position, text or "", fill="black", font=value_font)

    for label, value, y_pos in right_labels:
        draw.text((580, y_pos), label, fill="black", font=regular_font)
        if label == "Polarisation:":
            _draw_underlined_text(draw, (790, y_pos), value, value_font)
        else:
            draw.text((790, y_pos), value, fill="black", font=value_font)

    if unit_pattern_label:
        draw.text((580, 160), "Horizontal Unit Pattern:", fill="black", font=regular_font)
        draw.text((580, 200), f"File = {unit_pattern_label}", fill="black", font=unit_font)

    draw.text((60, 200), "Note: Pattern Tolerance +/-5% of Emax", fill="black", font=small_font)

    report = PILImage.new("RGBA", LEGACY_PLOT_IMAGE_SIZE, "white")
    report.alpha_composite(header, (0, 0))
    report.alpha_composite(body, (0, LEGACY_PLOT_HEADER_HEIGHT))
    report.alpha_composite(footer, (0, LEGACY_PLOT_HEADER_HEIGHT + LEGACY_PLOT_BODY_HEIGHT))
    return report.convert("RGB")


def _render_hrp_report_image(context: ExportContext) -> PILImage.Image:
    _angles_deg, _magnitudes, elevation_deg, directivity = _get_displayed_hrp(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    original_show_line = context.hrp_widget.show_selected_azimuth_line
    original_e_emax = context.hrp_widget.rb_e_emax.isChecked()
    try:
        context.hrp_widget.show_selected_azimuth_line = False
        context.hrp_widget.rb_e_emax.setChecked(True)
        context.hrp_widget.redraw_plot()
        QApplication.processEvents()
        plot_image = _grab_widget_resized(context.hrp_widget.plot_widget, 924, 900)
    finally:
        context.hrp_widget.show_selected_azimuth_line = original_show_line
        context.hrp_widget.rb_e_emax.setChecked(original_e_emax)
        context.hrp_widget.redraw_plot()
        QApplication.processEvents()
    footer_lines = [
        ("Polarisation:", _collect_pattern_metadata(context)["polarisation"], 0),
        ("Frequency:", f"{frequency_mhz:.2f} MHz", 40),
        ("Directivity:", f"{10 ** (directivity / 10.0):.1f} ({directivity:.2f} dB)", 80),
        ("Elevation Angle:", f"{elevation_deg:.2f} degrees", 120),
    ]
    image = _compose_hrp_vrp_report_image(
        context,
        "HRP_Header.bmp",
        plot_image,
        (38, 36, 924, 900),
        footer_lines,
        unit_pattern_label=_hrp_unit_pattern_label(context),
    )
    return _apply_export_image_scale(image, context)


def _render_vrp_report_image(context: ExportContext) -> PILImage.Image:
    _angles_deg, _magnitudes, azimuth_deg, directivity, tilt_deg = _get_displayed_vrp(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    original_e_emax = context.vrp_widget.rb_e_emax.isChecked()
    original_start = context.vrp_widget.start_spin.value()
    original_stop = context.vrp_widget.stop_spin.value()
    try:
        context.vrp_widget.rb_e_emax.setChecked(True)
        context.vrp_widget.start_spin.setValue(-90)
        context.vrp_widget.stop_spin.setValue(90)
        context.vrp_widget.redraw_plot()
        QApplication.processEvents()
        plot_image = _grab_widget_resized(context.vrp_widget.plot_widget, 916, 760)
    finally:
        context.vrp_widget.start_spin.setValue(original_start)
        context.vrp_widget.stop_spin.setValue(original_stop)
        context.vrp_widget.rb_e_emax.setChecked(original_e_emax)
        context.vrp_widget.redraw_plot()
        QApplication.processEvents()
    footer_lines = [
        ("Polarisation:", _collect_pattern_metadata(context)["polarisation"], 0),
        ("Frequency:", f"{frequency_mhz:.2f} MHz", 40),
        ("Directivity:", f"{10 ** (directivity / 10.0):.1f} ({directivity:.2f} dBd)", 80),
        ("Beam Tilt:", f"{tilt_deg:.2f} degrees", 120),
        ("Azimuth Angle:", f"{_display_from_internal_azimuth(azimuth_deg):.0f} degrees", 160),
    ]
    image = _compose_hrp_vrp_report_image(
        context,
        "VRP_Header.bmp",
        plot_image,
        (42, 42, 916, 760),
        footer_lines,
    )
    return _apply_export_image_scale(image, context)


def _render_layout_report_image(context: ExportContext) -> PILImage.Image:
    header = _template_with_eftx_logo("Layout_Header.bmp", context).convert("RGBA")
    detail = PILImage.open(_legacy_pic_path("Layout_detail.bmp")).convert("RGBA")
    summary = PILImage.open(_legacy_pic_path("Layout_summary.bmp")).convert("RGBA")
    draw = ImageDraw.Draw(detail)
    font = _load_pil_font(12, bold=False)
    underline_font = _load_pil_font(12, bold=False)

    meta = _collect_pattern_metadata(context)
    project = ensure_project_context(context).project
    preview = context.tower_preview_widget

    if project is not None and project.panels:
        offset_values = [panel.offset_m for panel in project.panels]
        tower_size = max(0.0, max(offset_values) * 2.0 - 0.04)
        panel_patterns = {pattern.index: pattern for pattern in project.patterns}
        lower_edges = []
        upper_edges = []
        for panel in project.panels:
            pattern = panel_patterns.get(panel.pattern_index)
            panel_height = 0.0 if pattern is None else float(pattern.height_m)
            lower_edges.append(float(panel.elevation_m) - panel_height / 2.0)
            upper_edges.append(float(panel.elevation_m) + panel_height / 2.0)
        aperture = max(upper_edges) - min(lower_edges) if lower_edges and upper_edges else 0.0
        face_count = len({round(float(panel.azimuth_deg), 3) for panel in project.panels})
    else:
        tower_size = 0.0
        aperture = 0.0
        face_count = 0

    if face_count == 4:
        tower_section = "Square"
    elif face_count == 3:
        tower_section = "Triangular"
    elif face_count == 6:
        tower_section = "Hexagonal"
    else:
        tower_section = "Schematic"

    detail_text = [
        ("Model:", (20, 40), meta["antenna_model"]),
        ("Location:", (20, 75), meta["site_name"]),
        ("Customer:", (20, 110), meta["customer"]),
        ("Date:", (20, 145), _today_long()),
        ("Tower Section:", (20, 180), tower_section),
        ("Tower Face Width or Diameter:", (20, 215), f"{tower_size:.3f} m"),
        ("Tower Heading:", (20, 250), "0.0 degrees"),
        ("Aperture:", (20, 285), f"{aperture:.3f} m"),
    ]
    for label, pos, value in detail_text:
        draw.text(pos, label, fill="black", font=font)
        draw.text((200 if pos[1] <= 145 else 350, pos[1]), value or "", fill="black", font=font)

    draw.text((20, 355), "Panel Width/Diameter (m):", fill="black", font=font)
    draw.text((20, 390), "Panel Height (m):", fill="black", font=font)
    draw.text((20, 425), "Panel Depth (m):", fill="black", font=font)

    panel_x = [220, 290, 360, 430]
    for idx, (width_label, height_label, depth_label) in enumerate(_panel_dimensions_by_slot(context)):
        draw.text((panel_x[idx], 320), f"Panel {idx + 1}", fill="black", font=font)
        draw.text((panel_x[idx], 355), width_label, fill="black", font=font)
        draw.text((panel_x[idx], 390), height_label, fill="black", font=font)
        if depth_label:
            draw.text((panel_x[idx], 425), depth_label, fill="black", font=font)

    original_preset = preview.view_preset
    original_rotation = preview.view_rotation_deg
    original_elevation = preview.view_elevation_deg
    original_zoom = preview.zoom_percent
    original_wireframe = getattr(preview, "export_wireframe_mode", False)
    try:
        preview.set_view_preset("Top View")
        preview.set_view_controls(0, 0, 100)
        preview.export_wireframe_mode = False
        QApplication.processEvents()
        mid_view_image = _grab_widget_resized(preview, 500, 500)

        preview.set_view_preset("Side View (Back)")
        preview.set_view_controls(original_rotation, 0, 100)
        preview.export_wireframe_mode = True
        QApplication.processEvents()
        bottom_view_image = _grab_widget_resized(preview, 500, 740)
    finally:
        preview.export_wireframe_mode = original_wireframe
        preview.set_view_preset(original_preset)
        preview.set_view_controls(original_rotation, original_elevation, original_zoom)
        QApplication.processEvents()

    report = PILImage.new("RGBA", LEGACY_PLOT_IMAGE_SIZE, "white")
    report.alpha_composite(header, (0, 0))
    report.alpha_composite(detail, (0, 160))
    report.alpha_composite(_qimage_to_pil(mid_view_image).convert("RGBA"), (500, 160))
    report.alpha_composite(summary, (0, 660))
    report.alpha_composite(_qimage_to_pil(bottom_view_image).convert("RGBA"), (500, 660))
    return _apply_export_image_scale(report.convert("RGB"), context)


def _apply_export_image_scale(image: PILImage.Image, context: ExportContext) -> PILImage.Image:
    scale = max(1.0, float(getattr(context, "export_image_scale", 1.0)))
    if abs(scale - 1.0) < 1e-9:
        return image
    new_size = (
        int(round(image.width * scale)),
        int(round(image.height * scale)),
    )
    return image.resize(new_size, PILImage.Resampling.LANCZOS)


def _draw_pdf_table_grid(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    column_width: int,
    row_height: int,
    column_count: int,
    row_count: int,
):
    left, top = origin
    width = column_width * column_count
    height = row_height * row_count
    draw.rectangle((left, top, left + width, top + height), outline="black", width=2)

    for column in range(1, column_count):
        x_pos = left + column * column_width
        draw.line((x_pos, top, x_pos, top + height), fill="black", width=1)

    for row in range(1, row_count):
        y_pos = top + row * row_height
        draw.line((left, y_pos, left + width, y_pos), fill="black", width=1)

    draw.rectangle((left, top, left + width, top + row_height), fill="#e6e6e6", outline="black", width=2)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str = "black",
):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x_pos = bounds[0] + (bounds[2] - bounds[0] - text_width) / 2
    y_pos = bounds[1] + (bounds[3] - bounds[1] - text_height) / 2 - 1
    draw.text((x_pos, y_pos), text, fill=fill, font=font)


def _draw_pattern_pdf_header(
    page: PILImage.Image,
    draw: ImageDraw.ImageDraw,
    context: ExportContext,
    title: str,
    right_rows: list[tuple[str, str]],
):
    meta = _collect_pattern_metadata(context)
    label_font = _load_pil_font(18, bold=False)
    value_font = _load_pil_font(18, bold=True)
    title_font = _load_pil_font(22, bold=True)

    left_rows = [
        ("Model:", meta["antenna_model"]),
        ("Location:", meta["site_name"]),
        ("Customer:", meta["customer"]),
        ("Date:", _today_long()),
    ]

    for index, (label, value) in enumerate(left_rows):
        y_pos = 100 + index * 44
        draw.text((120, y_pos), label, fill="black", font=label_font)
        draw.text((260, y_pos), value or "", fill="black", font=value_font)

    for index, (label, value) in enumerate(right_rows):
        y_pos = 100 + index * 44
        draw.text((690, y_pos), label, fill="black", font=label_font)
        if label == "Polarisation:":
            _draw_underlined_text(draw, (930, y_pos), value, value_font)
        else:
            draw.text((930, y_pos), value, fill="black", font=value_font)

    if context.logo_path is not None and Path(context.logo_path).exists():
        logo = _load_eftx_logo_pil(context)
    else:
        logo = None
    if logo is not None:
        logo.thumbnail((110, 90), PILImage.Resampling.LANCZOS)
        page.alpha_composite(logo, (1040, 78))

    _draw_centered_text(draw, (0, 300, PAGE_PORTRAIT[0], 340), title, title_font)


def _build_hrp_pdf_rows(context: ExportContext) -> list[tuple[str, str]]:
    angles_deg, magnitudes, elevation_deg, directivity = _get_displayed_hrp(context)
    rotated_points: list[tuple[int, float]] = []
    for angle, magnitude in zip(np.asarray(angles_deg, dtype=float), np.asarray(magnitudes, dtype=float)):
        display_angle = float((angle + context.rotation_angle_deg) % 360.0)
        rotated_points.append((int(round(display_angle)), float(magnitude)))
    rotated_points.sort(key=lambda item: item[0])
    lookup = {angle: magnitude for angle, magnitude in rotated_points}
    rows: list[tuple[str, str]] = []
    for angle in range(360):
        rows.append((str(angle), f"{lookup.get(angle, 0.0):.3f}"))
    return rows


def _build_vrp_pdf_rows(context: ExportContext) -> list[tuple[str, str]]:
    angles_deg, magnitudes = _get_vrp_for_export(context)
    lookup = {
        round(float(angle), 1): float(magnitude)
        for angle, magnitude in zip(np.asarray(angles_deg, dtype=float), np.asarray(magnitudes, dtype=float))
    }
    rows: list[tuple[str, str]] = []
    angle = -10.0
    while angle <= 90.0:
        rounded = round(angle, 1)
        rows.append((f"{rounded:.1f}", f"{lookup.get(rounded, 0.0):.3f}"))
        if rounded < -3.0 or rounded >= 11.0:
            angle = round(rounded + 0.5, 1)
        else:
            angle = round(rounded + 0.2, 1)
    return rows


def _build_tabulated_pattern_pdf_page(
    context: ExportContext,
    title: str,
    right_rows: list[tuple[str, str]],
    columns_per_group: int,
    row_count: int,
    data_rows: list[tuple[str, str]],
) -> PILImage.Image:
    page = PILImage.new("RGBA", PAGE_PORTRAIT, "white")
    draw = ImageDraw.Draw(page)
    _draw_pattern_pdf_header(page, draw, context, title, right_rows)

    table_top = 390
    table_left = 60
    total_columns = columns_per_group * 2
    usable_width = PAGE_PORTRAIT[0] - table_left * 2
    column_width = usable_width // total_columns
    row_height = 28
    table_font = _load_pil_font(13, bold=False)
    table_header_font = _load_pil_font(14, bold=True)

    _draw_pdf_table_grid(
        draw,
        (table_left, table_top),
        column_width,
        row_height,
        total_columns,
        row_count + 1,
    )

    for group in range(columns_per_group):
        left = table_left + group * 2 * column_width
        _draw_centered_text(draw, (left, table_top, left + column_width, table_top + row_height), "Angle", table_header_font)
        _draw_centered_text(draw, (left + column_width, table_top, left + 2 * column_width, table_top + row_height), "Field", table_header_font)

    for group in range(columns_per_group):
        for row in range(row_count):
            index = row + row_count * group
            if index >= len(data_rows):
                continue
            angle_text, field_text = data_rows[index]
            left = table_left + group * 2 * column_width
            top = table_top + (row + 1) * row_height
            _draw_centered_text(draw, (left, top, left + column_width, top + row_height), angle_text, table_font)
            _draw_centered_text(draw, (left + column_width, top, left + 2 * column_width, top + row_height), field_text, table_font)

    return page.convert("RGB")


def export_hrp_pat(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_hrp_for_export(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    with _open_text_export(path) as handle:
        handle.write("Edited by Deglitch\n")
        handle.write(f"{_fmt_compact(frequency_mhz, 2)}\n")
        handle.write("1\n")
        handle.write("0 0 0 1 0\n")
        handle.write("voltage\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}\t0\n")


def export_vrp_pat(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_vrp_for_export(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    with _open_text_export(path) as handle:
        handle.write("Edited by Deglitch\n")
        handle.write(f"{_fmt_compact(frequency_mhz, 2)}\n")
        handle.write("1\n")
        handle.write("0 0 0 1 0\n")
        handle.write("voltage\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}\t0\n")


def export_hrp_text(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_hrp_for_export(context)
    with _open_text_export(path) as handle:
        handle.write("EFTX Horizontal Radiation Pattern Data\n")
        handle.write("E / Emax (voltage)\n")
        handle.write("Angle\tMagnitude\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}\n")


def export_vrp_text(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_vrp_for_export(context)
    with _open_text_export(path) as handle:
        handle.write("EFTX Vertical Radiation Pattern Data\n")
        handle.write("E / Emax (voltage)\n")
        handle.write("Angle\tMagnitude\n")
        for angle, magnitude in zip(angles_deg[:-1], magnitudes[:-1]):
            handle.write(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}\n")


def export_hrp_csv(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_hrp_for_export(context)
    meta = _collect_pattern_metadata(context)
    project = ensure_project_context(context).project
    with _open_text_export(path) as handle:
        handle.write("manufacturer:\tEFTX\n")
        handle.write(f"date:\t{_today_long()}\n")
        handle.write("pattern_plane:\tAzimuth\n")
        handle.write(f"polarisation:\t{meta['polarisation']}\n")
        handle.write(f"frequency_MHz:\t{_fmt_compact(project.metadata.channel_frequency_mhz, 2)}\n")
        handle.write(" E / Emax (voltage)\n")
        handle.write(" Angle   Magnitude\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt_int(angle)}\t{_fmt(magnitude, 4)}\n")
        handle.write(f"180\t{_fmt(magnitudes[0], 4)}\n")


def export_vrp_csv(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_vrp_for_export(context)
    meta = _collect_pattern_metadata(context)
    project = ensure_project_context(context).project
    with _open_text_export(path) as handle:
        handle.write("manufacturer:\tEFTX\n")
        handle.write(f"date:\t{_today_long()}\n")
        handle.write("pattern_plane:\tElevation\n")
        handle.write(f"polarisation:\t{meta['polarisation']}\n")
        handle.write(f"frequency_MHz:\t{_fmt_compact(project.metadata.channel_frequency_mhz, 2)}\n")
        handle.write(" E / Emax (voltage)\n")
        handle.write(" Angle   Magnitude\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt(angle, 1)}\t{_fmt(magnitude, 4)}\n")


def export_hrp_vsoft(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_hrp_for_export(context)
    norm_angles = np.asarray(
        [_display_from_internal_azimuth(angle) for angle in angles_deg],
        dtype=float,
    )
    order = np.argsort(norm_angles)
    with _open_text_export(path) as handle:
        handle.write("360,0,1\n")
        for magnitude in np.asarray(magnitudes, dtype=float)[order]:
            handle.write(f"{_fmt(magnitude, 4)}\n")


def export_vrp_vsoft(path: str | Path, context: ExportContext):
    angles_deg, magnitudes = _get_vrp_for_export(context)
    _display_angles, display_magnitudes, _azimuth_deg, _directivity, tilt_deg = _get_displayed_vrp(context)
    if context.normalised_vrp:
        peak = float(np.max(display_magnitudes)) if display_magnitudes.size else 0.0
        if peak > 0.0:
            display_magnitudes = display_magnitudes / peak
    with _open_text_export(path) as handle:
        handle.write("Generated by EFTX ADT Elevation Pattern for use in V-Soft software\n")
        handle.write(f"Beam Tilt = {_fmt_compact(tilt_deg, 2)}\n")
        if angles_deg.size and angles_deg[0] != -90.0:
            handle.write(f"-90.0 {_fmt(magnitudes[-1], 4)}\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            if angle <= -10.0:
                prefix = ""
            elif angle < 0.0:
                prefix = " "
            elif angle < 10.0:
                prefix = "  "
            else:
                prefix = " "
            handle.write(f"{prefix}{_fmt(angle, 1)} {_fmt(magnitude, 4)}\n")
        if angles_deg.size and angles_deg[-1] != 90.0:
            handle.write(f" 90.0 {_fmt(magnitudes[0], 4)}\n")


def export_hrp_atdi(path: str | Path, context: ExportContext):
    _require_pattern(context)
    meta = _collect_pattern_metadata(context)
    _azimuth_of_max, elevation_of_max = _get_maximum_angles(context)
    angles_deg, magnitudes, _elevation_deg = extract_hrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        elevation_deg=elevation_of_max,
    )
    gain_dbi = get_3d_directivity(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    ) + 2.15
    with _open_text_export(path) as handle:
        handle.write(f"product_number:\t{meta['antenna_model']}\n")
        handle.write("manufacturer:\tEFTX\n")
        handle.write(f"comment:\t{meta['site_name']}\n")
        handle.write(f"date:\t{_today_short()}\n")
        handle.write(f"frequency_MHz:\t{float(meta['frequency_mhz']):.2f}\n")
        handle.write(f"gain_max_dBi\t{gain_dbi:.3f}\n")
        handle.write("pattern_plane:\tAzimuth\n")
        handle.write(f"polarisation:\t{meta['polarisation']}\n")
        handle.write("azimuth_angle:\tvariable\n")
        handle.write(f"elevation_angle:\t{elevation_of_max:.1f} degree\n")
        handle.write("pattern_origin::\t\n")
        handle.write("dia\tResponse in dB\n")
        for angle, magnitude in zip(angles_deg, magnitudes):
            handle.write(f"{_fmt_int(angle)}\t{_fmt_db(_voltage_to_db(magnitude), 2)}\n")
        handle.write(f"180\t{_fmt_db(_voltage_to_db(magnitudes[0]), 2)}\n")


def export_vrp_atdi(path: str | Path, context: ExportContext):
    _require_pattern(context)
    meta = _collect_pattern_metadata(context)
    phi_max, series = _build_atdi_vrp_series(context)
    gain_dbi = get_3d_directivity(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    ) + 2.15
    with _open_text_export(path) as handle:
        handle.write(f"product_number:\t{meta['antenna_model']}\n")
        handle.write("manufacturer:\tEFTX\n")
        handle.write(f"comment:\t{meta['site_name']}\n")
        handle.write(f"date:\t{_today_short()}\n")
        handle.write(f"frequency_MHz:\t{float(meta['frequency_mhz']):.2f}\n")
        handle.write(f"gain_max_dBi\t{gain_dbi:.3f}\n")
        handle.write("pattern_plane:\tElevation\n")
        handle.write(f"polarisation:\t{meta['polarisation']}\n")
        handle.write(
            f"azimuth_angle:\t{_display_from_internal_azimuth(phi_max):.1f} degree\n"
        )
        handle.write("elevation_angle:\tvariable\n")
        handle.write("pattern_origin::\t\n")
        handle.write("dia\tResponse in dB\n")
        for angle, magnitude in series:
            handle.write(f"{angle:.0f}\t{_fmt_db(_voltage_to_db(magnitude), 2)}\n")


def export_3d_atdi(path: str | Path, context: ExportContext):
    _require_pattern(context)
    magnitude = np.asarray(context.mag_3d, dtype=float)
    elevation_angles = np.asarray(context.el_angles, dtype=float)
    azimuth_lookup = _angle_index_lookup(np.asarray(context.az_angles, dtype=float))
    integer_el_indices = [
        (int(round(angle)), index)
        for index, angle in enumerate(elevation_angles)
        if round(float(angle), 1).is_integer()
    ]
    with _open_text_export(path) as handle:
        handle.write("Azim\\Tilt")
        for angle, _index in integer_el_indices:
            handle.write(f",{angle}°")
        handle.write("\n")
        for display_azimuth in range(0, 360):
            internal = round(_internal_from_display_azimuth(display_azimuth), 1)
            az_index = azimuth_lookup[internal]
            handle.write(f"{display_azimuth}°")
            for _angle, el_index in integer_el_indices:
                handle.write(f",{_fmt_db(-1.0 * _voltage_to_db(magnitude[az_index, el_index]), 2)}")
            handle.write("\n")
        az_index = azimuth_lookup[0.0]
        handle.write("360°")
        for _angle, el_index in integer_el_indices:
            handle.write(f",{_fmt_db(-1.0 * _voltage_to_db(magnitude[az_index, el_index]), 2)}")
        handle.write("\n")


def export_3d_text(path: str | Path, context: ExportContext):
    _require_pattern(context)
    elevation_angles = np.asarray(context.el_angles, dtype=float)
    with _open_text_export(path) as handle:
        handle.write("3D Data File by HVPAT (E/Emax)\n")
        handle.write("Azimuth ->\n")
        handle.write("Elevation\n")
        header = "      " + "".join(f"      {angle}" for angle in range(0, 361))
        handle.write(header + "\n")
        for el_index, elevation_angle in enumerate(elevation_angles):
            row_values = _get_azimuth_row_reordered(context, el_index)
            handle.write(
                f"{elevation_angle:.1f}"
                + "".join(f" {_fmt(value, 4)}" for value in row_values)
                + "\n"
            )


def export_ngw3d(path: str | Path, context: ExportContext):
    _require_pattern(context)
    meta = _collect_pattern_metadata(context)
    magnitude = np.asarray(context.mag_3d, dtype=float)
    elevation_angles = np.asarray(context.el_angles, dtype=float)
    gain_dbd = get_3d_directivity(magnitude, elevation_angles)
    with _open_text_export(path) as handle:
        handle.write("[Comments]\n")
        comment = f"{meta['site_name']} {meta['antenna_model']} By ADT"
        handle.write(comment + "\n")
        handle.write("[Gain dBdipole]\n")
        handle.write(f"{_fmt_db(gain_dbd, 2)}\n")
        handle.write("[3D-Data]\n")
        handle.write("361\n")
        handle.write("251\n")
        for el_index, elevation_angle in enumerate(elevation_angles):
            display_angle = -1.0 * float(elevation_angle)
            if display_angle < -20.0 or display_angle > 5.0:
                continue
            row_values = _get_azimuth_row_reordered(context, el_index)
            handle.write(
                f"{_fmt_db(display_angle, 1)}"
                + "".join(f" {_fmt_db(_voltage_to_db(value), 3)}" for value in row_values)
                + "\n"
            )


def export_prn(path: str | Path, context: ExportContext):
    _require_pattern(context)
    meta = _collect_pattern_metadata(context)
    magnitude = np.asarray(context.mag_3d, dtype=float)
    azimuth_of_max, _elevation_of_max = _get_maximum_angles(context)
    directivity_dbd = get_3d_directivity(
        magnitude,
        np.asarray(context.el_angles, dtype=float),
    )
    hrp_peak = _get_peak_horizontal_pattern(context)
    display_hrp = np.asarray(
        [_display_from_internal_azimuth(angle) for angle in STANDARD_HRP_ANGLES],
        dtype=float,
    )
    order = np.argsort(display_hrp)
    hrp_sorted = hrp_peak[order]

    front_angles, front_values = _get_integer_vrp_cut(context, azimuth_of_max)
    back_angles, back_values = _get_integer_vrp_cut(
        context,
        _internal_from_display_azimuth(_display_from_internal_azimuth(azimuth_of_max) + 180.0),
    )
    vertical_points = []
    for angle, magnitude_value in zip(front_angles, front_values):
        mapped = angle + 360.0 if angle < 0.0 else angle
        vertical_points.append((int(round(mapped)), float(magnitude_value)))
    for angle, magnitude_value in zip(back_angles, back_values):
        if angle <= -90.0 or angle >= 90.0:
            continue
        vertical_points.append((int(round(180.0 - angle)), float(magnitude_value)))
    vertical_points.sort(key=lambda item: item[0])

    with _open_text_export(path, encoding="ascii") as handle:
        handle.write(f"NAME {Path(path).stem.upper()}\n")
        handle.write("MAKE EFTX\n")
        handle.write(f"FREQUENCY {float(meta['frequency_mhz']):.2f} MHz\n")
        handle.write("H_WIDTH\n")
        handle.write("V_WIDTH\n")
        handle.write("FRONT_TO_BACK\n")
        handle.write(f"GAIN {directivity_dbd + 2.15:.2f} dBi\n")
        handle.write("TILT MECHANICAL\n")
        handle.write("HORIZONTAL 360\n")
        for index, magnitude_value in enumerate(hrp_sorted):
            handle.write(f"{index}\t{_fmt_db(-1.0 * _voltage_to_db(magnitude_value), 4)}\n")
        handle.write("VERTICAL 360\n")
        for index, magnitude_value in vertical_points:
            handle.write(f"{index}\t{_fmt_db(-1.0 * _voltage_to_db(magnitude_value), 4)}\n")


def export_edx(path: str | Path, context: ExportContext):
    _require_pattern(context)
    gain_dbi = get_3d_directivity(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    ) + 2.15
    hrp_sorted = (
        _get_peak_horizontal_pattern_sorted(context)
        if context.edx_peak_hrp
        else _get_displayed_horizontal_pattern_sorted(context)
    )
    phi_max, _theta_max = _get_maximum_angles(context)
    vrp_angles, vrp_magnitudes, _vrp_phi = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=phi_max,
    )
    vrp_lookup = {
        round(float(angle), 1): float(magnitude_value)
        for angle, magnitude_value in zip(vrp_angles, vrp_magnitudes)
    }
    start_deg = float(context.edx_start_deg)
    stop_deg = float(context.edx_stop_deg)
    increment_deg = float(context.edx_increment_deg)
    count = int((stop_deg - start_deg) / increment_deg + 1.0)
    with _open_text_export(path, encoding="ascii") as handle:
        handle.write(f"'By ADT', {gain_dbi:.3f}, 1\n")
        for index, magnitude_value in enumerate(hrp_sorted):
            handle.write(f"{index}, {magnitude_value:.4f}\n")
        handle.write("999\n")
        handle.write(f"1, {count}\n")
        handle.write(f"{int(round(_display_from_internal_azimuth(phi_max)))},\n")
        for step in range(count):
            angle = round(start_deg + step * increment_deg, 1)
            handle.write(f"{_fmt(-1.0 * angle, 1)}, {vrp_lookup[angle]:.4f}\n")


def export_complex_edx(path: str | Path, context: ExportContext):
    _require_pattern(context)
    gain_dbi = get_3d_directivity(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    ) + 2.15
    hrp_sorted = (
        _get_peak_horizontal_pattern_sorted(context)
        if context.edx_peak_hrp
        else _get_displayed_horizontal_pattern_sorted(context)
    )
    phi_max, _theta_max = _get_maximum_angles(context)
    vrp_angles, vrp_magnitudes, _vrp_phi = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=phi_max,
    )
    vrp_lookup = {
        round(float(angle), 1): float(magnitude_value)
        for angle, magnitude_value in zip(vrp_angles, vrp_magnitudes)
    }
    section_count = sum(
        int((stop - start) / increment) + 1
        for start, stop, increment, _zero in DEFAULT_COMPLEX_EDX_SECTIONS
    )
    for index in range(len(DEFAULT_COMPLEX_EDX_SECTIONS) - 1):
        current_stop = DEFAULT_COMPLEX_EDX_SECTIONS[index][1]
        next_start = DEFAULT_COMPLEX_EDX_SECTIONS[index + 1][0]
        if round(next_start - current_stop, 2) == 0.0:
            section_count -= 1
        else:
            section_count += int((next_start - current_stop) / 0.1) - 1
    with _open_text_export(path, encoding="ascii") as handle:
        handle.write(f"'By ADT', {gain_dbi:.3f}, 1\n")
        for index, magnitude_value in enumerate(hrp_sorted):
            handle.write(f"{index}, {magnitude_value:.4f}\n")
        handle.write("999\n")
        handle.write(f"1, {section_count}\n")
        handle.write(f"{int(round(_display_from_internal_azimuth(phi_max)))},\n")
        for section_index, (start, stop, increment, zero_voltage) in enumerate(
            DEFAULT_COMPLEX_EDX_SECTIONS
        ):
            limit = int((stop - start) / increment)
            steps = range(limit) if section_index < len(DEFAULT_COMPLEX_EDX_SECTIONS) - 1 else range(limit + 1)
            for step in steps:
                angle = round(start + step * increment, 1)
                value = DEFAULT_COMPLEX_EDX_ZERO if zero_voltage else vrp_lookup[angle]
                handle.write(f"{_fmt(-1.0 * angle, 1)}, {value:.4f}\n")
            if section_index < len(DEFAULT_COMPLEX_EDX_SECTIONS) - 1:
                next_start = DEFAULT_COMPLEX_EDX_SECTIONS[section_index + 1][0]
                if round(next_start - stop, 2) != 0.0:
                    gap_steps = int((next_start - stop) / 0.1)
                    for gap_step in range(gap_steps):
                        angle = round(stop + gap_step * 0.1, 1)
                        handle.write(f"{_fmt(-1.0 * angle, 1)}, {vrp_lookup[angle]:.4f}\n")


def export_directivity(path: str | Path, context: ExportContext):
    _require_pattern(context)
    frequency_mhz = float(_collect_pattern_metadata(context)["frequency_mhz"])
    azimuth_of_max, elevation_of_max = _get_maximum_angles(context)
    _hrp_angles, hrp_cut, _hrp_elevation = extract_hrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        elevation_deg=elevation_of_max,
    )
    vrp_angles, vrp_cut, _vrp_azimuth = extract_vrp_cut(
        context.mag_3d,
        context.az_angles,
        context.el_angles,
        azimuth_deg=azimuth_of_max,
    )
    hrp_dir = compute_hrp_cut_directivity_db(hrp_cut, hrp_cut)
    vrp_dir = compute_vrp_cut_directivity_db(vrp_angles, vrp_cut, vrp_cut)
    dir3d = get_3d_directivity(
        np.asarray(context.mag_3d, dtype=float),
        np.asarray(context.el_angles, dtype=float),
    )
    with _open_text_export(path) as handle:
        handle.write(f"{frequency_mhz:.2f}\n")
        handle.write(f"{_display_from_internal_azimuth(azimuth_of_max):.0f}\n")
        handle.write(f"{elevation_of_max:.1f}\n")
        handle.write(f"{hrp_dir:.2f}\n")
        handle.write(f"{vrp_dir:.2f}\n")
        handle.write(f"{dir3d:.2f}\n")


def export_hrp_jpeg(path: str | Path, context: ExportContext):
    _require_pattern(context)
    image = _render_hrp_report_image(context)
    _save_pil_image(path, image, "GIF")


def export_vrp_jpeg(path: str | Path, context: ExportContext):
    _require_pattern(context)
    image = _render_vrp_report_image(context)
    _save_pil_image(path, image, "GIF")


def export_layout_jpeg(path: str | Path, context: ExportContext):
    image = _render_layout_report_image(context)
    _save_pil_image(path, image, "BMP")


def export_hrp_pdf(path: str | Path, context: ExportContext):
    _require_pattern(context)
    _angles_deg, _magnitudes, elevation_deg, directivity = _get_displayed_hrp(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    page = _build_tabulated_pattern_pdf_page(
        context,
        "Tabulated Horizontal Radiation Pattern",
        [
            ("Polarisation:", _collect_pattern_metadata(context)["polarisation"]),
            ("Frequency (MHz):", f"{frequency_mhz:.2f}"),
            ("Directivity:", f"{10 ** (directivity / 10.0):.1f} ({directivity:.2f} dB)"),
            ("Elevation Angle:", f"{elevation_deg:.2f} degrees"),
        ],
        columns_per_group=8,
        row_count=45,
        data_rows=_build_hrp_pdf_rows(context),
    )
    _save_pil_pdf(path, _apply_export_image_scale(page, context))


def export_vrp_pdf(path: str | Path, context: ExportContext):
    _require_pattern(context)
    _angles_deg, _magnitudes, _azimuth_deg, directivity, tilt_deg = _get_displayed_vrp(context)
    frequency_mhz = ensure_project_context(context).project.metadata.channel_frequency_mhz
    page = _build_tabulated_pattern_pdf_page(
        context,
        "Tabulated Vertical Radiation Pattern",
        [
            ("Polarisation:", _collect_pattern_metadata(context)["polarisation"]),
            ("Frequency (MHz):", f"{frequency_mhz:.2f}"),
            ("Directivity:", f"{10 ** (directivity / 10.0):.1f} ({directivity:.2f} dB)"),
            ("Beam Tilt:", f"{tilt_deg:.2f} degrees"),
        ],
        columns_per_group=6,
        row_count=41,
        data_rows=_build_vrp_pdf_rows(context),
    )
    _save_pil_pdf(path, _apply_export_image_scale(page, context))


def export_summary_pdf(path: str | Path, context: ExportContext):
    _require_pattern(context)
    _write_pdf_pages(path, _build_summary_pages(context), landscape=False)


def export_panel_pdf(path: str | Path, context: ExportContext):
    _write_pdf_pages(path, _build_panel_pages(context), landscape=True)


def export_all_pdf(path: str | Path, context: ExportContext):
    _require_pattern(context)
    pages = []
    pages.extend(_build_summary_pages(context))
    pages.extend(_build_panel_pages(context))
    pages.append(_qimage_from_pil(_render_hrp_report_image(context)))
    pages.append(_qimage_from_pil(_render_vrp_report_image(context)))
    pages.append(
        _compose_widget_report_image(
            context,
            "Tower and Panel Layout",
            _widget_grab(context.tower_preview_widget),
        )
    )
    _write_pdf_pages(path, pages, landscape=True)


def export_vrp_video(path: str | Path, context: ExportContext):
    _require_pattern(context)
    try:
        import imageio.v2 as imageio
    except ImportError as exc:  # pragma: no cover
        raise ValueError(
            "The imageio and imageio-ffmpeg packages are required for AVI export."
        ) from exc
    if context.hrp_widget is None or context.vrp_widget is None:
        raise ValueError("HRP and VRP widgets are required for AVI export.")

    hrp_angles, hrp_magnitudes, elevation_deg, hrp_directivity = _get_displayed_hrp(context)
    original_azimuth = context.vrp_azimuth_deg
    frames = []
    for display_azimuth in range(0, 360, 10):
        internal_azimuth = _internal_from_display_azimuth(display_azimuth)
        vrp_context = ExportContext(**{**context.__dict__, "vrp_azimuth_deg": internal_azimuth})
        vrp_angles, vrp_magnitudes, _azimuth_deg, vrp_directivity, tilt_deg = _get_displayed_vrp(
            vrp_context
        )
        context.hrp_widget.plot_data(hrp_angles, hrp_magnitudes)
        context.hrp_widget.set_cut_metadata(
            elevation_deg=elevation_deg,
            directivity_dbd=hrp_directivity,
        )
        context.hrp_widget.set_selected_azimuth(internal_azimuth)
        context.vrp_widget.plot_data(vrp_angles, vrp_magnitudes)
        context.vrp_widget.set_cut_metadata(
            azimuth_deg=internal_azimuth,
            directivity_dbd=vrp_directivity,
            tilt_deg=tilt_deg,
        )
        frame_image = _compose_widget_report_image(
            context,
            "VRP Animation",
            _widget_grab(context.vrp_widget),
            [
                f"Az Angle (°): {display_azimuth}",
                f"El Angle (°): {elevation_deg:.1f}",
                f"Dir (dBd): {vrp_directivity:.2f}",
                f"Tilt (°): {tilt_deg:.1f}",
            ],
        )
        frames.append(_qimage_to_rgb_array(frame_image))

    with imageio.get_writer(str(path), fps=5, macro_block_size=1) as writer:
        for frame in frames:
            writer.append_data(frame)

    if original_azimuth is not None:
        context.hrp_widget.set_selected_azimuth(original_azimuth)


def export_to_format(format_name: str, path: str | Path, context: ExportContext):
    definition = get_export_definition(format_name)
    context = ensure_project_context(context)
    if definition.requires_pattern:
        _require_pattern(context)

    exporters = {
        "HRP PAT": export_hrp_pat,
        "VRP PAT": export_vrp_pat,
        "HRP Text": export_hrp_text,
        "VRP Text": export_vrp_text,
        "HRP CSV": export_hrp_csv,
        "VRP CSV": export_vrp_csv,
        "HRP V-Soft": export_hrp_vsoft,
        "VRP V-Soft": export_vrp_vsoft,
        "HRP ATDI": export_hrp_atdi,
        "VRP ATDI": export_vrp_atdi,
        "3D ATDI": export_3d_atdi,
        "3D Text": export_3d_text,
        "NGW3D": export_ngw3d,
        "PRN": export_prn,
        "EDX": export_edx,
        "Complex EDX": export_complex_edx,
        "Directivity": export_directivity,
        "Video": export_vrp_video,
        "HRP JPEG": export_hrp_jpeg,
        "VRP JPEG": export_vrp_jpeg,
        "Layout JPEG": export_layout_jpeg,
        "HRP PDF": export_hrp_pdf,
        "VRP PDF": export_vrp_pdf,
        "Summary PDF": export_summary_pdf,
        "Panel PDF": export_panel_pdf,
        "All PDF": export_all_pdf,
    }
    exporters[format_name](path, context)
