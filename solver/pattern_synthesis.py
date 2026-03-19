import math

import numpy as np


STANDARD_HRP_ANGLES = np.arange(-180.0, 180.0, 1.0)
STANDARD_VRP_ANGLES = np.linspace(-90.0, 90.0, 1801)


def wrap_to_minus180_plus180(angles_deg):
    return ((np.asarray(angles_deg) + 180.0) % 360.0) - 180.0


def complex_from_mag_phase(magnitude, phase_deg):
    return np.asarray(magnitude) * np.exp(1j * np.deg2rad(phase_deg))


def compute_pattern_directivity_db(magnitude):
    power = np.asarray(magnitude, dtype=float) ** 2
    if power.size == 0:
        return 0.0

    average_power = np.mean(power)
    max_power = np.max(power)
    if average_power <= 0 or max_power <= 0:
        return 0.0

    return 10.0 * np.log10(max_power / average_power)


def compute_hrp_directivity_db(magnitude):
    power = np.asarray(magnitude, dtype=float) ** 2
    if power.size == 0:
        return 0.0

    max_power = float(np.max(power))
    power_sum = float(np.sum(power))
    if max_power <= 0.0 or power_sum <= 0.0:
        return 0.0

    return 10.0 * np.log10(max_power * power.size / power_sum) + 10.0 * np.log10(
        max_power
    )


def compute_vrp_directivity_db(angles_deg, magnitude):
    angles = np.asarray(angles_deg, dtype=float)
    power = np.asarray(magnitude, dtype=float) ** 2
    if power.size == 0:
        return 0.0

    weighted_power = power * np.sin(np.deg2rad(angles + 90.0))
    max_power = float(np.max(power))
    power_sum = float(np.sum(weighted_power))
    if max_power <= 0.0 or power_sum <= 0.0:
        return 0.0

    return 10.0 * np.log10(
        max_power * power.size * 2.0 / power_sum / np.pi / 1.64
    )


def compute_hrp_cut_directivity_db(selected_magnitude, peak_magnitude):
    selected_power = np.asarray(selected_magnitude, dtype=float) ** 2
    peak_power = np.asarray(peak_magnitude, dtype=float) ** 2
    if selected_power.size == 0 or peak_power.size == 0:
        return 0.0

    max_selected_power = float(np.max(selected_power))
    peak_power_sum = float(np.sum(peak_power))
    if max_selected_power <= 0.0 or peak_power_sum <= 0.0:
        return 0.0

    return 10.0 * np.log10(max_selected_power * selected_power.size / peak_power_sum)


def compute_vrp_cut_directivity_db(angles_deg, selected_magnitude, peak_magnitude):
    angles = np.asarray(angles_deg, dtype=float)
    selected_power = np.asarray(selected_magnitude, dtype=float) ** 2
    peak_power = np.asarray(peak_magnitude, dtype=float) ** 2
    if selected_power.size == 0 or peak_power.size == 0:
        return 0.0

    weighted_peak_power = peak_power * np.sin(np.deg2rad(angles + 90.0))
    max_selected_power = float(np.max(selected_power))
    peak_power_sum = float(np.sum(weighted_peak_power))
    if max_selected_power <= 0.0 or peak_power_sum <= 0.0:
        return 0.0

    return 10.0 * np.log10(
        max_selected_power * selected_power.size * 2.0 / peak_power_sum / np.pi / 1.64
    )


def _round_expected_half_power_angle_deg(half_power_angle_deg):
    quantized = int(float(half_power_angle_deg) * 100.0)
    remainder = quantized % 10
    if remainder < 3:
        remainder = 0
    elif remainder <= 7:
        remainder = 5
    else:
        remainder = 10
    quantized = quantized // 10 * 10 + remainder
    return quantized / 100.0


def _calculate_unit_u(n_value, theta_deg):
    if n_value == 0.0:
        n_value = 1e-8
    if abs(theta_deg) < 1e-12:
        return 1.0

    theta_rad = math.radians(theta_deg)
    numerator = math.sin(n_value * theta_rad)
    denominator = n_value * math.sin(theta_rad)
    return abs(numerator / denominator * math.sin(theta_rad) / theta_rad)


def _normalize_pattern_magnitude(magnitude):
    magnitude = np.asarray(magnitude, dtype=float)
    max_value = float(np.max(magnitude)) if magnitude.size else 0.0
    if max_value <= 0:
        return magnitude.copy()
    return magnitude / max_value


def _generate_unit_pattern_magnitude(n_value):
    angles = np.round(np.linspace(-90.0, 89.9, 1800), 1)
    magnitude = np.zeros_like(angles)
    for index, theta_deg in enumerate(angles):
        if index == 900:
            magnitude[index] = magnitude[index - 1]
        else:
            magnitude[index] = _calculate_unit_u(n_value, theta_deg)

    return angles, _normalize_pattern_magnitude(magnitude)


def _interpolate_half_power_crossing(angle_a, magnitude_a, angle_b, magnitude_b):
    slope = (magnitude_b - magnitude_a) / (angle_b - angle_a)
    intercept = magnitude_a - slope * angle_a
    target = 1.0 / math.sqrt(2.0)
    return (target - intercept) / slope


def _get_half_3db_angle_deg(angles_deg, magnitude):
    angles = np.asarray(angles_deg, dtype=float)
    magnitude = np.asarray(magnitude, dtype=float)
    threshold = 1.0 / math.sqrt(2.0)

    count_above_threshold = int(np.count_nonzero(magnitude > threshold))
    if count_above_threshold == magnitude.size:
        return (angles[-1] - angles[0]) / 2.0

    left_index = 0
    left_distance = 1.0
    midpoint = magnitude.size // 2
    for index in range(midpoint):
        distance = abs(magnitude[index] - threshold)
        if distance < left_distance:
            left_distance = distance
            left_index = index

    if magnitude[left_index] - threshold < 0.0:
        left_angle = _interpolate_half_power_crossing(
            angles[left_index],
            magnitude[left_index],
            angles[left_index + 1],
            magnitude[left_index + 1],
        )
    elif magnitude[left_index] - threshold > 0.0:
        left_angle = _interpolate_half_power_crossing(
            angles[left_index - 1],
            magnitude[left_index - 1],
            angles[left_index],
            magnitude[left_index],
        )
    else:
        left_angle = angles[left_index]

    right_index = magnitude.size - 1
    right_distance = 1.0
    for index in range(magnitude.size - 1, midpoint, -1):
        distance = abs(magnitude[index] - threshold)
        if distance < right_distance:
            right_distance = distance
            right_index = index

    if magnitude[right_index] - threshold < 0.0:
        right_angle = _interpolate_half_power_crossing(
            angles[right_index - 1],
            magnitude[right_index - 1],
            angles[right_index],
            magnitude[right_index],
        )
    elif magnitude[right_index] - threshold > 0.0:
        right_angle = _interpolate_half_power_crossing(
            angles[right_index],
            magnitude[right_index],
            angles[right_index + 1],
            magnitude[right_index + 1],
        )
    else:
        right_angle = angles[right_index]

    return (right_angle - left_angle) / 2.0


def generate_synthetic_vrp_pattern(half_power_angle_deg):
    expected_half_power_angle = _round_expected_half_power_angle_deg(
        half_power_angle_deg
    )
    n_value = 0.0

    angles, magnitude = _generate_unit_pattern_magnitude(n_value)
    current_half_power = _get_half_3db_angle_deg(angles, magnitude)

    for _ in range(10000):
        if current_half_power - expected_half_power_angle < 0.0:
            break
        n_value += 1.0
        angles, magnitude = _generate_unit_pattern_magnitude(n_value)
        current_half_power = _get_half_3db_angle_deg(angles, magnitude)

    _, previous_magnitude = _generate_unit_pattern_magnitude(n_value - 1.0)
    previous_half_power = _get_half_3db_angle_deg(angles, previous_magnitude)
    if previous_half_power == expected_half_power_angle:
        angles, magnitude = _generate_unit_pattern_magnitude(n_value - 1.0)
        magnitude = np.concatenate([magnitude, [magnitude[0]]])
        return STANDARD_VRP_ANGLES.copy(), magnitude, np.zeros_like(STANDARD_VRP_ANGLES)

    best_distance = 0.0
    if abs(current_half_power - expected_half_power_angle) < abs(
        previous_half_power - expected_half_power_angle
    ):
        best_distance = abs(current_half_power - expected_half_power_angle)
        for _ in range(10000):
            if abs(current_half_power - expected_half_power_angle) > best_distance:
                break
            best_distance = abs(current_half_power - expected_half_power_angle)
            n_value -= 0.005
            angles, magnitude = _generate_unit_pattern_magnitude(n_value)
            current_half_power = _get_half_3db_angle_deg(angles, magnitude)
    else:
        n_value -= 1.0
        best_distance = abs(current_half_power - expected_half_power_angle)
        for _ in range(10000):
            if abs(current_half_power - expected_half_power_angle) > best_distance:
                break
            best_distance = abs(current_half_power - expected_half_power_angle)
            n_value += 0.005
            angles, magnitude = _generate_unit_pattern_magnitude(n_value)
            current_half_power = _get_half_3db_angle_deg(angles, magnitude)

    _, magnitude = _generate_unit_pattern_magnitude(n_value)
    magnitude = np.concatenate([magnitude, [magnitude[0]]])
    return STANDARD_VRP_ANGLES.copy(), magnitude, np.zeros_like(STANDARD_VRP_ANGLES)


def find_library_power_ratios(hrp_patterns):
    if not hrp_patterns:
        return {}

    directivities = {}
    for key, (_angles, magnitude, _phase) in hrp_patterns.items():
        directivities[key] = compute_hrp_directivity_db(magnitude)

    reference_directivity = min(directivities.values())
    return {
        key: 10.0 ** ((directivity - reference_directivity) / 10.0)
        for key, directivity in directivities.items()
    }


def calculate_configuration_phase_deg(
    panel_phase_deg,
    configuration,
    channel_frequency_mhz,
    design_frequency_mhz,
):
    reference_frequency = design_frequency_mhz or channel_frequency_mhz or 1.0
    frequency_ratio = channel_frequency_mhz / reference_frequency

    if configuration == 0:
        return panel_phase_deg * frequency_ratio
    if configuration == 1:
        return panel_phase_deg * frequency_ratio - 180.0
    if configuration == 2:
        return (panel_phase_deg - 90.0) * frequency_ratio + 90.0
    if configuration == 3:
        return (panel_phase_deg - 90.0) * frequency_ratio + 90.0 - 180.0
    if configuration == 4:
        return (panel_phase_deg - 180.0) * frequency_ratio + 180.0
    if configuration == 5:
        return (panel_phase_deg - 180.0) * frequency_ratio
    return panel_phase_deg * frequency_ratio


def _sort_samples(angles_deg, magnitude, phase_deg):
    order = np.argsort(angles_deg)
    return (
        np.asarray(angles_deg, dtype=float)[order],
        np.asarray(magnitude, dtype=float)[order],
        np.asarray(phase_deg, dtype=float)[order],
    )


def _mirror_hrp_configuration(angles_deg, magnitude, phase_deg):
    mirrored_angles = np.asarray(angles_deg, dtype=float).copy()
    mask = ~np.isclose(mirrored_angles, -180.0)
    mirrored_angles[mask] = -mirrored_angles[mask]
    return _sort_samples(mirrored_angles, magnitude, phase_deg)


def _apply_vrp_configuration(angles_deg, magnitude, phase_deg, configuration):
    angles = np.asarray(angles_deg, dtype=float).copy()
    mag = np.asarray(magnitude, dtype=float).copy()
    phase = np.asarray(phase_deg, dtype=float).copy()

    if configuration in {0, 2, 4}:
        angles = -angles
        return _sort_samples(angles, mag, phase)

    if configuration in {1, 3, 5}:
        phase = phase[::-1]

    return _sort_samples(angles, mag, phase)


def _interpolate_periodic_complex(source_angles, source_field, target_angles):
    source_angles = np.asarray(source_angles, dtype=float)
    source_field = np.asarray(source_field, dtype=complex)
    target_angles = np.asarray(target_angles, dtype=float)

    extended_angles = np.concatenate(
        [source_angles - 360.0, source_angles, source_angles + 360.0]
    )
    extended_real = np.tile(source_field.real, 3)
    extended_imag = np.tile(source_field.imag, 3)

    real = np.interp(target_angles, extended_angles, extended_real)
    imag = np.interp(target_angles, extended_angles, extended_imag)
    return real + 1j * imag


def _interpolate_bounded_complex(source_angles, source_field, target_angles):
    source_angles = np.asarray(source_angles, dtype=float)
    source_field = np.asarray(source_field, dtype=complex)
    target_angles = np.asarray(target_angles, dtype=float)

    real = np.interp(
        target_angles,
        source_angles,
        source_field.real,
        left=source_field.real[0],
        right=source_field.real[-1],
    )
    imag = np.interp(
        target_angles,
        source_angles,
        source_field.imag,
        left=source_field.imag[0],
        right=source_field.imag[-1],
    )
    return real + 1j * imag


def _map_vrp_field_to_target(source_angles, source_field, target_angles):
    rounded_angles = np.round(np.asarray(source_angles, dtype=float), 1)
    field = np.asarray(source_field, dtype=complex)
    target = np.round(np.asarray(target_angles, dtype=float), 1)

    if rounded_angles.size != target.size or not np.array_equal(
        np.sort(rounded_angles), target
    ):
        return _interpolate_bounded_complex(rounded_angles, field, target)

    mapped = np.zeros_like(target, dtype=complex)
    for angle_deg, field_value in zip(rounded_angles, field):
        index = int(round((angle_deg + 90.0) * 10.0))
        if 0 <= index < mapped.size:
            mapped[index] = field_value
    return mapped


def _fit_edge_polynomial(values):
    x_values = np.asarray(values[0], dtype=float)
    y_values = np.asarray(values[1], dtype=float)
    if x_values.size < 4:
        return np.poly1d([0.0])
    return np.poly1d(np.polyfit(x_values, y_values, 3))


def _configure_tilted_vertical_cut(
    angles_deg,
    magnitude,
    phase_deg,
    projected_tilt_deg,
):
    shifted_angles = np.asarray(angles_deg, dtype=float).copy()
    shifted_magnitude = np.asarray(magnitude, dtype=float).copy()
    shifted_phase = np.asarray(phase_deg, dtype=float).copy()

    if projected_tilt_deg > 0.0:
        mag_fit = _fit_edge_polynomial((shifted_angles[:100], shifted_magnitude[:100]))
        phase_fit = _fit_edge_polynomial((shifted_angles[:100], shifted_phase[:100]))
        for index in range(shifted_angles.size):
            angle_value = shifted_angles[index] + projected_tilt_deg
            wrapped = False
            while angle_value > 90.0:
                angle_value -= 180.1
                wrapped = True
            if wrapped:
                source_angle = angle_value - projected_tilt_deg
                shifted_magnitude[index] = float(mag_fit(source_angle))
                shifted_phase[index] = float(phase_fit(source_angle))
            shifted_angles[index] = angle_value
    elif projected_tilt_deg < 0.0:
        mag_fit = _fit_edge_polynomial(
            (shifted_angles[1701:1801], shifted_magnitude[1701:1801])
        )
        phase_fit = _fit_edge_polynomial(
            (shifted_angles[1701:1801], shifted_phase[1701:1801])
        )
        for index in range(shifted_angles.size):
            angle_value = shifted_angles[index] + projected_tilt_deg
            wrapped = False
            while angle_value < -90.0:
                angle_value += 180.1
                wrapped = True
            if wrapped:
                source_angle = angle_value - projected_tilt_deg
                shifted_magnitude[index] = float(mag_fit(source_angle))
                shifted_phase[index] = float(phase_fit(source_angle))
            shifted_angles[index] = angle_value

    return shifted_angles, shifted_magnitude, shifted_phase


def configure_horizontal_pattern(
    source_angles_deg,
    magnitude,
    phase_deg,
    frequency_mhz,
    x_offset_m=0.0,
    y_offset_m=0.0,
    azimuth_shift_deg=0.0,
    panel_phase_deg=0.0,
    power_linear=1.0,
    configuration=0,
    design_frequency_mhz=None,
):
    target_angles = STANDARD_HRP_ANGLES.copy()
    magnitude = np.asarray(magnitude, dtype=float)
    phase_deg = np.asarray(phase_deg, dtype=float)
    angles_deg = np.asarray(source_angles_deg, dtype=float)

    if configuration in {1, 3, 5}:
        angles_deg, magnitude, phase_deg = _mirror_hrp_configuration(
            angles_deg, magnitude, phase_deg
        )
    else:
        angles_deg, magnitude, phase_deg = _sort_samples(angles_deg, magnitude, phase_deg)

    if power_linear <= 0:
        return target_angles, np.zeros_like(target_angles, dtype=complex)

    source_field = complex_from_mag_phase(magnitude, phase_deg)
    sample_angles = wrap_to_minus180_plus180(target_angles - azimuth_shift_deg)
    rotated_field = _interpolate_periodic_complex(angles_deg, source_field, sample_angles)

    rotated_magnitude = np.abs(rotated_field) * np.sqrt(power_linear)
    rotated_phase_deg = np.angle(rotated_field, deg=True)

    wavelength_m = 300.0 / frequency_mhz
    spatial_phase_deg = (
        y_offset_m * np.cos(np.deg2rad(sample_angles)) / wavelength_m * 360.0
        + x_offset_m * np.sin(np.deg2rad(sample_angles)) / wavelength_m * 360.0
    )
    configured_phase_deg = calculate_configuration_phase_deg(
        panel_phase_deg,
        configuration,
        frequency_mhz,
        design_frequency_mhz or frequency_mhz,
    )
    total_phase_deg = rotated_phase_deg + spatial_phase_deg + configured_phase_deg
    return target_angles, complex_from_mag_phase(rotated_magnitude, total_phase_deg)


def configure_vertical_pattern(
    source_angles_deg,
    magnitude,
    phase_deg,
    frequency_mhz,
    z_offset_m=0.0,
    x_offset_m=0.0,
    mechanical_tilt_deg=0.0,
    tilt_face_angle_deg=0.0,
    configuration=0,
):
    target_angles = STANDARD_VRP_ANGLES.copy()
    angles_deg, magnitude, phase_deg = _apply_vrp_configuration(
        source_angles_deg, magnitude, phase_deg, configuration
    )

    power_linear = 10.0 ** (compute_vrp_directivity_db(angles_deg, magnitude) / 10.0)
    scale = np.sqrt(power_linear)
    source_field = complex_from_mag_phase(magnitude, phase_deg)
    wavelength_m = 300.0 / frequency_mhz
    spatial_phase_deg = (
        z_offset_m * np.cos(np.deg2rad(target_angles + 90.0)) / wavelength_m * 360.0
        + x_offset_m * np.sin(np.deg2rad(target_angles + 90.0)) / wavelength_m * 360.0
    )

    if abs(mechanical_tilt_deg) < 1e-9:
        base_field = _interpolate_bounded_complex(angles_deg, source_field, target_angles)
        magnitude_interp = np.abs(base_field) * scale
        phase_interp_deg = np.angle(base_field, deg=True)
        return target_angles, complex_from_mag_phase(
            magnitude_interp,
            phase_interp_deg + spatial_phase_deg,
        )

    phi_angles = STANDARD_HRP_ANGLES.copy()
    tilted_fields = np.zeros((phi_angles.size, target_angles.size), dtype=complex)
    for phi_index, phi_deg in enumerate(phi_angles):
        projected_tilt_deg = round(
            mechanical_tilt_deg
            * math.cos(math.radians(phi_deg - tilt_face_angle_deg)),
            1,
        )
        cut_angles, cut_magnitude, cut_phase_deg = _configure_tilted_vertical_cut(
            angles_deg,
            magnitude,
            phase_deg,
            projected_tilt_deg,
        )
        cut_magnitude = cut_magnitude * scale
        cut_spatial_phase_deg = (
            z_offset_m * np.cos(np.deg2rad(cut_angles + 90.0)) / wavelength_m * 360.0
            + x_offset_m * np.sin(np.deg2rad(cut_angles + 90.0)) / wavelength_m * 360.0
        )
        cut_field = complex_from_mag_phase(
            cut_magnitude,
            cut_phase_deg + cut_spatial_phase_deg,
        )
        order = np.argsort(cut_angles)
        tilted_fields[phi_index, :] = _map_vrp_field_to_target(
            cut_angles[order],
            cut_field[order],
            target_angles,
        )

    return target_angles, tilted_fields


def build_single_panel_3d_pattern(hrp_complex, vrp_complex):
    hrp_complex = np.asarray(hrp_complex, dtype=complex)
    vrp_complex = np.asarray(vrp_complex, dtype=complex)

    if vrp_complex.ndim == 1:
        return hrp_complex[:, np.newaxis] * vrp_complex[np.newaxis, :]

    if vrp_complex.ndim == 2 and vrp_complex.shape[0] == hrp_complex.shape[0]:
        return hrp_complex[:, np.newaxis] * vrp_complex

    raise ValueError("VRP field must be 1D or azimuth-indexed 2D.")


def calculate_single_panel_3d(hrp_mag, hrp_phase_deg, vrp_mag, vrp_phase_deg):
    hrp_complex = complex_from_mag_phase(hrp_mag, hrp_phase_deg)
    vrp_complex = complex_from_mag_phase(vrp_mag, vrp_phase_deg)
    return build_single_panel_3d_pattern(hrp_complex, vrp_complex)


def calculate_array_3d(panel_3d_patterns):
    if not panel_3d_patterns:
        return np.zeros((1, 1)), np.zeros((1, 1))

    total_complex = np.sum(np.asarray(panel_3d_patterns), axis=0)
    # The recovered ADT flips the final theta sign when it builds Pattern3DCalPanelArray.
    total_complex = total_complex[:, ::-1]
    magnitude = np.abs(total_complex)
    phase = np.angle(total_complex, deg=True)

    max_magnitude = np.max(magnitude)
    if max_magnitude > 0:
        magnitude /= max_magnitude

    return magnitude, phase


def get_field_maximum_indices(pat_3d_mag):
    magnitude = np.asarray(pat_3d_mag)
    if magnitude.size == 0:
        return 0, 0

    return np.unravel_index(np.argmax(magnitude), magnitude.shape)


def get_maximum_field_angles(pat_3d_mag, azimuth_angles_deg, elevation_angles_deg):
    magnitude = np.asarray(pat_3d_mag, dtype=float)
    azimuth_angles = np.asarray(azimuth_angles_deg, dtype=float)
    elevation_angles = np.asarray(elevation_angles_deg, dtype=float)
    if magnitude.size == 0:
        return 0.0, 0.0, 0, 0

    max_magnitude = float(np.max(magnitude))
    max_positions = np.argwhere(np.round(magnitude, 8) == round(max_magnitude, 8))
    if max_positions.size == 0:
        az_index, el_index = get_field_maximum_indices(magnitude)
        return (
            float(azimuth_angles[az_index]),
            float(elevation_angles[el_index]),
            az_index,
            el_index,
        )

    azimuth_candidates = max_positions[:, 0]
    elevation_candidates = max_positions[:, 1]

    azimuth_values = azimuth_angles[azimuth_candidates]
    elevation_values = elevation_angles[elevation_candidates]

    azimuth_target = float(np.mean(azimuth_values))
    elevation_target = float(np.mean(elevation_values))

    az_index = int(
        azimuth_candidates[
            np.argmin(np.abs(azimuth_values - azimuth_target))
        ]
    )
    el_index = int(
        elevation_candidates[
            np.argmin(np.abs(elevation_values - elevation_target))
        ]
    )
    return (
        float(azimuth_angles[az_index]),
        float(elevation_angles[el_index]),
        az_index,
        el_index,
    )


def extract_hrp_cut(
    pat_3d_mag,
    azimuth_angles_deg,
    elevation_angles_deg,
    elevation_deg=None,
    elevation_index=None,
):
    magnitude = np.asarray(pat_3d_mag)
    azimuth_angles = np.asarray(azimuth_angles_deg, dtype=float)
    elevation_angles = np.asarray(elevation_angles_deg, dtype=float)

    if elevation_index is None:
        if elevation_deg is None:
            _, _, _, elevation_index = get_maximum_field_angles(
                magnitude,
                azimuth_angles,
                elevation_angles,
            )
        else:
            elevation_index = int(np.argmin(np.abs(elevation_angles - elevation_deg)))

    return azimuth_angles, magnitude[:, elevation_index], float(elevation_angles[elevation_index])


def extract_vrp_cut(
    pat_3d_mag,
    azimuth_angles_deg,
    elevation_angles_deg,
    azimuth_deg=None,
    azimuth_index=None,
):
    magnitude = np.asarray(pat_3d_mag)
    azimuth_angles = np.asarray(azimuth_angles_deg, dtype=float)
    elevation_angles = np.asarray(elevation_angles_deg, dtype=float)

    if azimuth_index is None:
        if azimuth_deg is None:
            _, _, azimuth_index, _ = get_maximum_field_angles(
                magnitude,
                azimuth_angles,
                elevation_angles,
            )
        else:
            azimuth_index = int(np.argmin(np.abs(azimuth_angles - azimuth_deg)))

    return elevation_angles, magnitude[azimuth_index, :], float(azimuth_angles[azimuth_index])


def get_vrp_beam_tilt_deg(elevation_angles_deg, magnitudes):
    elevation_angles = np.asarray(elevation_angles_deg, dtype=float)
    magnitude = np.asarray(magnitudes, dtype=float)
    if magnitude.size == 0:
        return 0.0

    max_magnitude = float(np.max(magnitude))
    maxima_mask = np.isclose(magnitude, max_magnitude, rtol=0.0, atol=1e-12)
    if not np.any(maxima_mask):
        return 0.0

    return round(float(np.mean(elevation_angles[maxima_mask])), 2)


def get_3d_directivity(pat_3d_mag, elevation_angles_deg):
    power = pat_3d_mag ** 2
    max_power = np.max(power)
    theta_rad = np.deg2rad(elevation_angles_deg + 90.0)
    weighted_power = power * np.sin(theta_rad)[np.newaxis, :]
    power_sum = np.sum(weighted_power)
    total_points = power.size

    if power_sum == 0:
        return 0.0

    return 10.0 * np.log10(
        max_power * total_points * 2.0 / power_sum / np.pi / 1.64
    )


def apply_panel_phase_shifts(
    angles_deg,
    mag,
    phase_deg,
    frequency_mhz,
    x_off=0.0,
    y_off=0.0,
    face_angle=0.0,
    panel_phase=0.0,
    power_ratio=1.0,
):
    wavelength = 300.0 / frequency_mhz
    shifted_mag = np.asarray(mag, dtype=float) * np.sqrt(power_ratio)
    angles_rad = np.deg2rad(angles_deg)
    spatial_phase = (
        y_off * np.cos(angles_rad) + x_off * np.sin(angles_rad)
    ) / wavelength * 360.0
    shifted_phase_deg = np.asarray(phase_deg, dtype=float) + spatial_phase + panel_phase
    shifted_phase_deg = (shifted_phase_deg + 180.0) % 360.0 - 180.0
    return shifted_mag, shifted_phase_deg
