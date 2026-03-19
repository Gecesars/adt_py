import os

import numpy as np

from catalogs import lookup_generated_vrp_half_power_angle
from parsers.patterns import read_hrp_pattern, read_vrp_pattern
from solver.pattern_synthesis import (
    build_single_panel_3d_pattern,
    calculate_array_3d,
    configure_horizontal_pattern,
    configure_vertical_pattern,
    find_library_power_ratios,
    generate_synthetic_vrp_pattern,
)


class AntennaPanel:
    def __init__(self, panel_id, type="Standard"):
        self.panel_id = panel_id
        self.type = type
        self.panel_type_name = ""
        self.power = 1.0
        self.phase = 0.0
        self.tilt = 0.0
        self.azimuth = 0.0
        self.elevation = 0.0
        self.face_angle = 0.0
        self.configuration = 0
        self.design_frequency = 539.0
        self.library_power_ratio = 1.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.hrp_path = ""
        self.vrp_path = ""

    def get_radiation_pattern(self):
        if self.hrp_path and os.path.exists(self.hrp_path):
            hrp_angles, hrp_mag, hrp_phase = read_hrp_pattern(self.hrp_path)
        else:
            hrp_angles = np.arange(-180.0, 180.0, 1.0)
            hrp_mag = np.ones(360)
            hrp_phase = np.zeros(360)

        if self.vrp_path and os.path.exists(self.vrp_path):
            vrp_angles, vrp_mag, vrp_phase = read_vrp_pattern(self.vrp_path)
        elif self.type == "Standard" and self.panel_type_name:
            half_power_angle = lookup_generated_vrp_half_power_angle(
                self.panel_type_name,
                self.design_frequency,
            )
            if half_power_angle:
                vrp_angles, vrp_mag, vrp_phase = generate_synthetic_vrp_pattern(
                    half_power_angle
                )
            else:
                vrp_angles = np.linspace(-90.0, 90.0, 1801)
                vrp_mag = np.maximum(np.cos(np.deg2rad(vrp_angles)), 0.0)
                vrp_phase = np.zeros(1801)
        else:
            vrp_angles = np.linspace(-90.0, 90.0, 1801)
            vrp_mag = np.maximum(np.cos(np.deg2rad(vrp_angles)), 0.0)
            vrp_phase = np.zeros(1801)

        return hrp_angles, hrp_mag, hrp_phase, vrp_angles, vrp_mag, vrp_phase

    def get_library_key(self):
        return self.hrp_path or f"default::{self.type}"


class ArrayDesign:
    def __init__(self):
        self.panels = []
        self.frequency = 539.0

    def add_panel(self, panel):
        self.panels.append(panel)

    def calculate_3d_pattern(self):
        panel_3d_patterns = []
        pattern_cache = {}

        for panel in self.panels:
            cache_key = (
                panel.hrp_path,
                panel.vrp_path,
                panel.type,
                panel.panel_type_name,
                round(float(panel.design_frequency), 6),
            )
            if cache_key not in pattern_cache:
                pattern_cache[cache_key] = panel.get_radiation_pattern()

        hrp_patterns = {
            panel.get_library_key(): (
                pattern_cache[
                    (
                        panel.hrp_path,
                        panel.vrp_path,
                        panel.type,
                        panel.panel_type_name,
                        round(float(panel.design_frequency), 6),
                    )
                ][0],
                pattern_cache[
                    (
                        panel.hrp_path,
                        panel.vrp_path,
                        panel.type,
                        panel.panel_type_name,
                        round(float(panel.design_frequency), 6),
                    )
                ][1],
                pattern_cache[
                    (
                        panel.hrp_path,
                        panel.vrp_path,
                        panel.type,
                        panel.panel_type_name,
                        round(float(panel.design_frequency), 6),
                    )
                ][2],
            )
            for panel in self.panels
        }
        power_ratio_map = find_library_power_ratios(hrp_patterns)

        for panel in self.panels:
            cache_key = (
                panel.hrp_path,
                panel.vrp_path,
                panel.type,
                panel.panel_type_name,
                round(float(panel.design_frequency), 6),
            )
            (
                hrp_angles,
                hrp_mag,
                hrp_phase,
                vrp_angles,
                vrp_mag,
                vrp_phase,
            ) = pattern_cache[cache_key]

            library_power_ratio = power_ratio_map.get(panel.get_library_key(), 1.0)

            _hrp_target_angles, hrp_complex = configure_horizontal_pattern(
                hrp_angles,
                hrp_mag,
                hrp_phase,
                self.frequency,
                x_offset_m=panel.x,
                y_offset_m=panel.y,
                azimuth_shift_deg=panel.face_angle,
                panel_phase_deg=panel.phase,
                power_linear=panel.power * library_power_ratio,
                configuration=panel.configuration,
                design_frequency_mhz=panel.design_frequency,
            )

            _vrp_target_angles, vrp_complex = configure_vertical_pattern(
                vrp_angles,
                vrp_mag,
                vrp_phase,
                self.frequency,
                z_offset_m=panel.z,
                x_offset_m=0.0,
                mechanical_tilt_deg=panel.tilt,
                tilt_face_angle_deg=panel.face_angle,
                configuration=panel.configuration,
            )

            panel_3d_patterns.append(
                build_single_panel_3d_pattern(hrp_complex, vrp_complex)
            )

        return calculate_array_3d(panel_3d_patterns)
