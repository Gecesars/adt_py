from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np


_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
_ALPHA_RE = re.compile(r"[A-DF-Za-df-z]")


def _select_line_element(line, index, default=0.0):
    parts = str(line).strip().split()
    if index >= len(parts):
        return default
    return float(parts[index])


def _read_lines(filepath):
    return Path(filepath).read_text(encoding="utf-8", errors="ignore").splitlines()


def read_pattern_frequency(filepath, default=539.0):
    lines = _read_lines(filepath)
    for line in lines[:20]:
        upper = line.upper()
        if "FREQUENCY" in upper:
            numbers = _NUMBER_RE.findall(line)
            if numbers:
                value = float(numbers[0])
                if "GHZ" in upper:
                    return value * 1000.0
                if "KHZ" in upper:
                    return value / 1000.0
                return value

    rows, headers = _extract_numeric_rows(lines, "HRP")
    freq_col = _infer_frequency_column(rows, headers)
    if freq_col is not None:
        values = np.asarray([row[freq_col] for row in rows], dtype=float)
        if np.ptp(values) < 1e-9:
            value = float(values[0])
            header = headers[freq_col].lower() if freq_col < len(headers) else ""
            if "ghz" in header:
                return value * 1000.0
            if "khz" in header:
                return value / 1000.0
            if value < 20.0:
                return value * 1000.0
            return value

    if len(lines) < 2:
        return default
    try:
        return float(lines[1].strip())
    except ValueError:
        return default


def read_hrp_pattern(filepath):
    """
    Parses a .pat or .hup HRP antenna pattern file.
    Returns:
        angles_deg: 1D numpy array of angles (-180 to 179)
        mag: 1D numpy array of linear voltage magnitudes
        phase_deg: 1D numpy array of phases in degrees
    """
    lines = _read_lines(filepath)

    frequency_mhz = float(lines[1].strip())
    header = lines[3]
    original_xoff_m = _select_line_element(header, 0)
    original_yoff_m = _select_line_element(header, 1)
    tilt_deg = _select_line_element(header, 2)
    power_linear = _select_line_element(header, 3, 1.0)
    phase_deg = _select_line_element(header, 4)

    # The original ADT HPattern constructor resets non-zero file tilt to zero.
    if tilt_deg != 0.0:
        tilt_deg = 0.0
    if power_linear == 0.0:
        power_linear = 1.0

    voltage_index = next(
        index for index, line in enumerate(lines) if line.strip().lower() == "voltage"
    )

    angles = []
    mags = []
    phases = []
    for line in lines[voltage_index + 1 :]:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        angles.append(float(parts[0]))
        mags.append(float(parts[1]))
        phases.append(float(parts[2]))

    if len(angles) > 360:
        angles = angles[:360]
        mags = mags[:360]
        phases = phases[:360]

    angles = np.asarray(angles, dtype=float)
    mags = np.asarray(mags, dtype=float)
    phases = np.asarray(phases, dtype=float)

    if power_linear > 0.0:
        if power_linear != 1.0:
            mags = mags * math.sqrt(power_linear)

        wavelength_m = 300.0 / frequency_mhz
        phases = phases + (
            (-original_yoff_m) * np.cos(np.deg2rad(angles)) / wavelength_m * 360.0
            + (-original_xoff_m) * np.sin(np.deg2rad(angles)) / wavelength_m * 360.0
            + phase_deg
        )

    order = np.argsort(angles)
    return angles[order], mags[order], phases[order]


def read_vrp_pattern(filepath):
    """
    Parses a .pat or .vup VRP antenna pattern file.
    Reconstructs the ADT 0.1 degree grid from the sparse unit pattern file.
    Returns:
        angles_deg: 1D numpy array of angles (-90 to +90)
        mag: 1D numpy array of linear voltage magnitudes
        phase_deg: 1D numpy array of phases in degrees
    """
    lines = _read_lines(filepath)

    voltage_index = next(
        index for index, line in enumerate(lines) if line.strip().lower() == "voltage"
    )
    first_data_index = voltage_index + 1
    first_angle_deg = _select_line_element(lines[first_data_index], 0)
    second_angle_deg = _select_line_element(lines[first_data_index + 1], 0)
    step_index = int(abs(second_angle_deg - first_angle_deg) / 0.1)
    if step_index <= 0:
        step_index = 1

    start_index = next(index for index, line in enumerate(lines) if line.strip().startswith("-90"))

    sparse_points = [None] * 1801
    line_index = start_index
    sparse_index = 0
    while sparse_index < 1801:
        if sparse_index == 1800 and line_index >= len(lines):
            first_point = sparse_points[0]
            sparse_points[sparse_index] = (-first_point[0], first_point[1], first_point[2])
        else:
            angle_deg = _select_line_element(lines[line_index], 0)
            magnitude = _select_line_element(lines[line_index], 1)
            phase_deg = _select_line_element(lines[line_index], 2)
            sparse_points[sparse_index] = (angle_deg, magnitude, phase_deg)
            line_index += 1
        sparse_index += step_index

    for block_start in range(0, 1801 - step_index, step_index):
        start_angle_deg, start_mag, start_phase_deg = sparse_points[block_start]
        stop_angle_deg, stop_mag, stop_phase_deg = sparse_points[block_start + step_index]

        mag_slope = (stop_mag - start_mag) / (stop_angle_deg - start_angle_deg)
        mag_intercept = start_mag - mag_slope * start_angle_deg
        phase_slope = (stop_phase_deg - start_phase_deg) / (stop_angle_deg - start_angle_deg)
        phase_intercept = start_phase_deg - phase_slope * start_angle_deg

        for offset in range(1, step_index):
            angle_deg = start_angle_deg + offset * 0.1
            magnitude = mag_slope * angle_deg + mag_intercept
            phase_deg = phase_slope * angle_deg + phase_intercept
            sparse_points[block_start + offset] = (angle_deg, magnitude, phase_deg)

    angles = np.asarray([point[0] for point in sparse_points], dtype=float)
    magnitude = np.asarray([point[1] for point in sparse_points], dtype=float)
    phase_deg = np.asarray([point[2] for point in sparse_points], dtype=float)
    return angles, magnitude, phase_deg


def _coalesce_duplicate_angles(angles_deg, complex_field):
    unique_angles, inverse = np.unique(angles_deg, return_inverse=True)
    summed = np.zeros(unique_angles.shape, dtype=np.complex128)
    counts = np.zeros(unique_angles.shape, dtype=float)
    np.add.at(summed, inverse, complex_field)
    np.add.at(counts, inverse, 1.0)
    return unique_angles, summed / np.maximum(counts, 1.0)


def _interpolate_complex_angles(angles_deg, magnitude, phase_deg, target_angles_deg, periodic):
    complex_field = np.asarray(magnitude, dtype=float) * np.exp(
        1j * np.deg2rad(np.asarray(phase_deg, dtype=float))
    )
    unique_angles, unique_field = _coalesce_duplicate_angles(
        np.asarray(angles_deg, dtype=float),
        complex_field,
    )
    if periodic:
        sample_angles = np.concatenate(
            [unique_angles - 360.0, unique_angles, unique_angles + 360.0]
        )
        sample_field = np.concatenate([unique_field, unique_field, unique_field])
        real = np.interp(target_angles_deg, sample_angles, sample_field.real)
        imag = np.interp(target_angles_deg, sample_angles, sample_field.imag)
    else:
        real = np.interp(
            target_angles_deg,
            unique_angles,
            unique_field.real,
            left=unique_field.real[0],
            right=unique_field.real[-1],
        )
        imag = np.interp(
            target_angles_deg,
            unique_angles,
            unique_field.imag,
            left=unique_field.imag[0],
            right=unique_field.imag[-1],
        )
    interpolated = real + 1j * imag
    return np.abs(interpolated), np.rad2deg(np.angle(interpolated))


def _split_fields(line):
    stripped = str(line).strip()
    if not stripped:
        return []
    if "\t" in stripped:
        parts = stripped.split("\t")
    elif ";" in stripped and stripped.count(";") >= stripped.count(","):
        parts = stripped.split(";")
    elif "," in stripped:
        parts = stripped.split(",")
    else:
        parts = stripped.split()
    return [part.strip().strip('"').strip("'") for part in parts if part.strip()]


def _parse_numeric_row(line):
    values = []
    fields = _split_fields(line)
    if len(fields) < 2:
        return None
    for field in fields:
        try:
            values.append(float(field))
        except ValueError:
            return None
    return tuple(values) if len(values) >= 2 else None


def _extract_section_lines(lines, pattern_kind):
    pattern_kind = pattern_kind.upper()
    upper_lines = [line.strip().upper() for line in lines]

    marker = None
    stop_markers = []
    if pattern_kind == "HRP" and any(line.startswith("HORIZONTAL") for line in upper_lines):
        marker = "HORIZONTAL"
        stop_markers = ["VERTICAL"]
    elif pattern_kind == "VRP" and any(line.startswith("VERTICAL") for line in upper_lines):
        marker = "VERTICAL"
        stop_markers = ["HORIZONTAL"]

    if marker is not None:
        start_index = next(
            index for index, line in enumerate(upper_lines) if line.startswith(marker)
        ) + 1
        end_index = len(lines)
        for index in range(start_index, len(lines)):
            candidate = upper_lines[index]
            if any(candidate.startswith(stop_marker) for stop_marker in stop_markers):
                end_index = index
                break
        return lines[start_index:end_index]

    for index, line in enumerate(lines):
        if line.strip().lower() == "voltage":
            return lines[index + 1 :]
    return lines


def _extract_numeric_rows(lines, pattern_kind):
    section_lines = _extract_section_lines(lines, pattern_kind)
    blocks = []
    current_block = []
    current_headers = []
    last_non_numeric_fields = []
    min_block_length = 3
    for line in section_lines:
        row = _parse_numeric_row(line)
        if row is not None:
            if not current_block:
                current_headers = list(last_non_numeric_fields)
            current_block.append(row)
        else:
            if len(current_block) >= min_block_length:
                blocks.append((current_block, current_headers))
            current_block = []
            current_headers = []
            fields = _split_fields(line)
            if fields:
                last_non_numeric_fields = fields
    if len(current_block) >= min_block_length:
        blocks.append((current_block, current_headers))
    if not blocks:
        raise ValueError("Could not find a numeric pattern table in the file.")
    rows, headers = max(blocks, key=lambda item: len(item[0]))
    row_lengths = {}
    for row in rows:
        row_lengths[len(row)] = row_lengths.get(len(row), 0) + 1
    target_len = max(row_lengths.items(), key=lambda item: item[1])[0]
    normalized_rows = [row[:target_len] for row in rows if len(row) >= target_len]
    normalized_headers = headers[:target_len] if headers else []
    return normalized_rows, normalized_headers


def _header_value(headers, index):
    if index < len(headers):
        return headers[index].strip().lower()
    return ""


def _header_has(header, *tokens):
    return any(token in header for token in tokens)


def _infer_frequency_column(rows, headers):
    if not rows:
        return None
    column_count = min(len(row) for row in rows)
    for index in range(column_count):
        header = _header_value(headers, index)
        if _header_has(header, "freq", "frequency"):
            return index
    return None


def _infer_angle_column(rows, headers, pattern_kind):
    data = np.asarray(rows, dtype=float)
    column_count = data.shape[1]
    best_index = None
    best_score = None
    for index in range(column_count):
        header = _header_value(headers, index)
        has_angle_hint = _header_has(
            header,
            "theta",
            "phi",
            "angle",
            "az",
            "el",
            "elevation",
            "azimuth",
        )
        values = data[:, index]
        value_min = float(np.min(values))
        value_max = float(np.max(values))
        value_range = value_max - value_min
        unique_count = len(np.unique(np.round(values, 6)))
        min_unique_count = 3 if has_angle_hint else 8
        min_value_range = 1.0 if has_angle_hint else 5.0
        if unique_count < min_unique_count or value_range < min_value_range:
            continue
        if value_min < -400.0 or value_max > 400.0:
            continue

        diffs = np.diff(values)
        nonzero_diffs = diffs[np.abs(diffs) > 1e-9]
        monotonic_ratio = 0.0
        if nonzero_diffs.size:
            monotonic_ratio = max(
                np.mean(nonzero_diffs > 0.0),
                np.mean(nonzero_diffs < 0.0),
            )

        score = unique_count * 5.0 + value_range + monotonic_ratio * 50.0
        if has_angle_hint:
            score += 120.0
        if pattern_kind == "HRP":
            if value_range >= 300.0:
                score += 100.0
            if -185.0 <= value_min <= 0.0 and 0.0 <= value_max <= 360.0:
                score += 50.0
        else:
            if -90.1 <= value_min <= 0.0 and 0.0 <= value_max <= 90.1:
                score += 140.0
            elif 0.0 <= value_min and value_max <= 180.1:
                score += 100.0
        if best_score is None or score > best_score:
            best_index = index
            best_score = score
    if best_index is None:
        raise ValueError("Could not infer the angular column from the imported file.")
    return best_index


def _infer_magnitude_column(rows, headers, angle_index):
    data = np.asarray(rows, dtype=float)
    column_count = data.shape[1]
    best_index = None
    best_score = None
    for index in range(column_count):
        if index == angle_index:
            continue
        values = data[:, index]
        value_range = float(np.max(values) - np.min(values))
        std_dev = float(np.std(values))
        if value_range < 1e-9 or std_dev < 1e-9:
            continue
        header = _header_value(headers, index)
        if _header_has(header, "phase"):
            continue

        score = std_dev * 10.0 + value_range
        if _header_has(header, "gain", "mag", "field", "db", "10^", "power"):
            score += 120.0
        if np.all(values >= 0.0) and np.max(values) <= 1.5:
            score += 90.0
        elif np.max(values) <= 40.0 and np.min(values) >= -200.0:
            score += 80.0
        if np.min(values) < -360.0 or np.max(values) > 360.0:
            score -= 40.0
        if best_score is None or score > best_score:
            best_index = index
            best_score = score
    if best_index is None:
        raise ValueError("Could not infer the magnitude column from the imported file.")
    return best_index


def _infer_phase_column(rows, headers, angle_index, magnitude_index):
    data = np.asarray(rows, dtype=float)
    column_count = data.shape[1]
    best_index = None
    best_score = None
    for index in range(column_count):
        if index in {angle_index, magnitude_index}:
            continue
        values = data[:, index]
        value_range = float(np.max(values) - np.min(values))
        if value_range < 1e-9:
            continue
        header = _header_value(headers, index)
        score = 0.0
        if _header_has(header, "phase"):
            score += 200.0
        if np.min(values) >= -1080.0 and np.max(values) <= 1080.0:
            score += 40.0
        if value_range > 30.0:
            score += 20.0
        if best_score is None or score > best_score:
            best_index = index
            best_score = score
    return best_index


def _normalize_magnitude(raw_values, header_name=""):
    raw_values = np.asarray(raw_values, dtype=float)
    header_name = (header_name or "").lower()
    if "10^" in header_name or "linear" in header_name:
        return np.clip(raw_values, 0.0, None)
    if "db" in header_name and "10^" not in header_name:
        normalized_db = raw_values - np.nanmax(raw_values)
        return np.power(10.0, normalized_db / 20.0)
    if np.all(raw_values >= 0.0) and np.nanmax(raw_values) <= 1.5:
        return np.clip(raw_values, 0.0, None)
    normalized_db = raw_values - np.nanmax(raw_values)
    return np.power(10.0, normalized_db / 20.0)


def _normalize_hrp_angles(raw_angles):
    angles = np.asarray(raw_angles, dtype=float)
    return ((angles + 180.0) % 360.0) - 180.0


def _normalize_vrp_angles(raw_angles):
    angles = np.asarray(raw_angles, dtype=float)
    if np.nanmin(angles) >= 0.0 and np.nanmax(angles) <= 180.0:
        return angles - 90.0
    if np.nanmin(angles) >= 0.0 and np.nanmax(angles) <= 360.0:
        wrapped = ((angles + 180.0) % 360.0) - 180.0
        return wrapped
    return angles


def _generic_pattern_import(filepath, pattern_kind):
    rows, headers = _extract_numeric_rows(_read_lines(filepath), pattern_kind)
    angle_index = _infer_angle_column(rows, headers, pattern_kind)
    magnitude_index = _infer_magnitude_column(rows, headers, angle_index)
    phase_index = _infer_phase_column(rows, headers, angle_index, magnitude_index)

    angles_deg = np.asarray([row[angle_index] for row in rows], dtype=float)
    raw_magnitude = np.asarray([row[magnitude_index] for row in rows], dtype=float)
    if phase_index is not None:
        phase_deg = np.asarray([row[phase_index] for row in rows], dtype=float)
    else:
        phase_deg = np.zeros_like(angles_deg)

    magnitude = _normalize_magnitude(raw_magnitude, _header_value(headers, magnitude_index))

    if pattern_kind == "HRP":
        angles_deg = _normalize_hrp_angles(angles_deg)
        target_angles = np.arange(-180.0, 180.0, 1.0)
        resampled_mag, resampled_phase = _interpolate_complex_angles(
            angles_deg,
            magnitude,
            phase_deg,
            target_angles,
            periodic=True,
        )
        return target_angles, resampled_mag, resampled_phase

    angles_deg = _normalize_vrp_angles(angles_deg)
    valid_mask = np.logical_and(angles_deg >= -90.0, angles_deg <= 90.0)
    if np.count_nonzero(valid_mask) >= 8:
        angles_deg = angles_deg[valid_mask]
        magnitude = magnitude[valid_mask]
        phase_deg = phase_deg[valid_mask]

    target_angles = np.linspace(-90.0, 90.0, 1801)
    resampled_mag, resampled_phase = _interpolate_complex_angles(
        angles_deg,
        magnitude,
        phase_deg,
        target_angles,
        periodic=False,
    )
    return target_angles, resampled_mag, resampled_phase


def load_pattern_for_import(filepath, pattern_kind):
    pattern_kind = pattern_kind.upper()
    try:
        if pattern_kind == "HRP":
            return read_hrp_pattern(filepath)
        return read_vrp_pattern(filepath)
    except Exception:
        return _generic_pattern_import(filepath, pattern_kind)


def write_standard_pattern(
    filepath,
    angles_deg,
    magnitude,
    phase_deg,
    frequency_mhz,
    *,
    title="Generated",
    engineer="EFTX",
    original_xoff_m=0.0,
    original_yoff_m=0.0,
    tilt_deg=0.0,
    power_linear=1.0,
    phase_offset_deg=0.0,
):
    target_path = Path(filepath)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    angles_deg = np.asarray(angles_deg, dtype=float)
    magnitude = np.asarray(magnitude, dtype=float)
    phase_deg = np.asarray(phase_deg, dtype=float)

    step = abs(angles_deg[1] - angles_deg[0]) if angles_deg.size > 1 else 1.0
    angle_format = "{:.0f}" if step >= 0.99 else "{:.1f}"
    header_lines = [
        f"1/02/97 0:00 ; title : {title} ; engineer : {engineer}",
        f"{float(frequency_mhz):10.4f}",
        "1",
        f"{float(original_xoff_m):g}   {float(original_yoff_m):g}    {float(tilt_deg):g}    {float(power_linear):g}   {float(phase_offset_deg):g}",
        "voltage",
    ]
    data_lines = [
        f"{angle_format.format(angle)}    {float(mag):.4f}    {float(phase):.3f}"
        for angle, mag, phase in zip(angles_deg, magnitude, phase_deg)
    ]
    target_path.write_text("\n".join(header_lines + data_lines) + "\n", encoding="utf-8")
    return target_path


def import_pattern_to_standard(filepath, target_path, pattern_kind, frequency_mhz):
    angles_deg, magnitude, phase_deg = load_pattern_for_import(filepath, pattern_kind)
    return write_standard_pattern(
        target_path,
        angles_deg,
        magnitude,
        phase_deg,
        frequency_mhz,
        title="Generated",
        engineer="EFTX",
    )
