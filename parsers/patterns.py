import math

import numpy as np


def _select_line_element(line, index, default=0.0):
    parts = str(line).strip().split()
    if index >= len(parts):
        return default
    return float(parts[index])


def read_hrp_pattern(filepath):
    """
    Parses a .pat or .hup HRP antenna pattern file.
    Returns:
        angles_deg: 1D numpy array of angles (-180 to 179)
        mag: 1D numpy array of linear voltage magnitudes
        phase_deg: 1D numpy array of phases in degrees
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

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
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    voltage_index = next(
        index for index, line in enumerate(lines) if line.strip().lower() == "voltage"
    )
    first_data_index = voltage_index + 1
    first_angle_deg = _select_line_element(lines[first_data_index], 0)
    second_angle_deg = _select_line_element(lines[first_data_index + 1], 0)
    step_index = int(abs(second_angle_deg - first_angle_deg) / 0.1)
    if step_index <= 0:
        step_index = 1

    start_index = next(
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("-90")
    )

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
        phase_slope = (stop_phase_deg - start_phase_deg) / (
            stop_angle_deg - start_angle_deg
        )
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
