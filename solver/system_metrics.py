import numpy as np

from solver.pattern_synthesis import (
    STANDARD_HRP_ANGLES,
    extract_hrp_cut,
    extract_vrp_cut,
    get_3d_directivity,
    get_maximum_field_angles,
    get_vrp_beam_tilt_deg,
)


def calculate_system_metrics(
    array_design,
    internal_loss=0.5,
    pol_loss=3.0,
    filter_loss=0.8,
    feeder_loss=1.2,
    tx_power_kw=None,
):
    """
    Compute system-level metrics from the synthesized 3D pattern.
    """
    frequency = array_design.frequency

    magnitude_3d, _phase_3d = array_design.calculate_3d_pattern()
    elevation_angles = np.linspace(-90, 90, magnitude_3d.shape[1])
    azimuth_angles = STANDARD_HRP_ANGLES.copy()
    directivity_dbd = get_3d_directivity(magnitude_3d, elevation_angles)

    azimuth_of_max, elevation_of_max, azimuth_index, elevation_index = (
        get_maximum_field_angles(magnitude_3d, azimuth_angles, elevation_angles)
    )
    hrp_angles, hrp_cut, hrp_cut_elevation = extract_hrp_cut(
        magnitude_3d,
        azimuth_angles,
        elevation_angles,
        elevation_index=elevation_index,
    )
    vrp_angles, vrp_cut, vrp_cut_azimuth = extract_vrp_cut(
        magnitude_3d,
        azimuth_angles,
        elevation_angles,
        azimuth_index=azimuth_index,
    )
    vrp_tilt_deg = get_vrp_beam_tilt_deg(vrp_angles, vrp_cut)

    total_loss = internal_loss + pol_loss + filter_loss + feeder_loss
    system_gain = directivity_dbd - total_loss

    if tx_power_kw is not None:
        tx_power = tx_power_kw
    else:
        tx_power = sum(panel.power for panel in array_design.panels)

    if tx_power > 0:
        erp_dbw = 10 * np.log10(tx_power * 1000) + system_gain
        erp_kw = (10 ** (erp_dbw / 10)) / 1000.0
    else:
        erp_dbw = 0.0
        erp_kw = 0.0

    results = {
        "Channel Frequency (MHz)": f"{frequency:.2f}",
        "3D Directivity (dBd)": f"{directivity_dbd:.2f}",
        "Azimuth Angle (Emax) (deg)": f"{azimuth_of_max:.1f}",
        "Elevation Angle (Emax) (deg)": f"{elevation_of_max:.1f}",
        "Internal Loss (dB)": f"{internal_loss:.2f}",
        "Polarisation Loss (dB)": f"{pol_loss:.2f}",
        "Filter/Combiner Loss (dB)": f"{filter_loss:.2f}",
        "Main Feeder Loss (dB)": f"{feeder_loss:.2f}",
        "System Gain (dBd)": f"{system_gain:.2f}",
        "Transmitter Power (kW)": f"{tx_power:.2f}",
        "ERP (dBW)": f"{erp_dbw:.2f}",
        "ERP (kW)": f"{erp_kw:.2f}",
        "_hrp_cut_angles_deg": hrp_angles,
        "_hrp_cut_magnitude": hrp_cut,
        "_hrp_cut_elevation_deg": hrp_cut_elevation,
        "_vrp_cut_angles_deg": vrp_angles,
        "_vrp_cut_magnitude": vrp_cut,
        "_vrp_cut_azimuth_deg": vrp_cut_azimuth,
        "_vrp_cut_tilt_deg": vrp_tilt_deg,
    }

    return results, magnitude_3d, azimuth_angles, elevation_angles
