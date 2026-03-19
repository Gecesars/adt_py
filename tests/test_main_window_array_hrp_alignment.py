import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from app.project_service import build_project_from_ui, project_to_array_design
from main import ADTMainWindow
from solver.pattern_synthesis import (
    STANDARD_HRP_ANGLES,
    _interpolate_periodic_complex,
    calculate_configuration_phase_deg,
    complex_from_mag_phase,
    compute_hrp_directivity_db,
    find_library_power_ratios,
    wrap_to_minus180_plus180,
)


class MainWindowArrayHrpAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_four_face_array_matches_original_hrp_directivity_baseline(self):
        window = ADTMainWindow()

        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.hrp_widget.angle_spin.setValue(0.0)
        window.on_calculate_clicked()

        self.assertAlmostEqual(window.hrp_widget.angle_spin.value(), 0.0, places=1)
        self.assertAlmostEqual(float(window.hrp_widget.dir_edit.text()), 1.49, places=1)

    def test_four_face_array_hrp_matches_original_algorithm_point_by_point(self):
        window = ADTMainWindow()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.hrp_widget.angle_spin.setValue(0.0)
        window.on_calculate_clicked()

        project = build_project_from_ui(
            window.design_info_widget,
            window.antenna_design_tab,
            window.pattern_library_widget,
        )
        array_design = project_to_array_design(project)
        magnitude_3d, _phase_3d = array_design.calculate_3d_pattern()
        hrp_current = magnitude_3d[:, 900]

        pattern_cache = {}
        for panel in array_design.panels:
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
            for panel in array_design.panels
        }
        power_ratio_map = find_library_power_ratios(hrp_patterns)

        hrp_angles = STANDARD_HRP_ANGLES.copy()
        combined = np.zeros(hrp_angles.shape, dtype=complex)
        wavelength_m = 300.0 / array_design.frequency

        for panel in array_design.panels:
            cache_key = (
                panel.hrp_path,
                panel.vrp_path,
                panel.type,
                panel.panel_type_name,
                round(float(panel.design_frequency), 6),
            )
            source_angles, magnitude, phase_deg, _vrp_angles, _vrp_mag, _vrp_phase = (
                pattern_cache[cache_key]
            )
            source_field = complex_from_mag_phase(magnitude, phase_deg)

            local_panel_angles = wrap_to_minus180_plus180(hrp_angles - panel.face_angle)
            rotated_field = _interpolate_periodic_complex(
                source_angles,
                source_field,
                local_panel_angles,
            )
            rotated_magnitude = np.abs(rotated_field) * np.sqrt(
                panel.power * power_ratio_map.get(panel.get_library_key(), 1.0)
            )
            rotated_phase_deg = np.angle(rotated_field, deg=True)
            spatial_phase_deg = (
                panel.y * np.cos(np.deg2rad(local_panel_angles)) / wavelength_m * 360.0
                + panel.x
                * np.sin(np.deg2rad(local_panel_angles))
                / wavelength_m
                * 360.0
            )
            total_phase_deg = rotated_phase_deg + spatial_phase_deg + (
                calculate_configuration_phase_deg(
                    panel.phase,
                    panel.configuration,
                    array_design.frequency,
                    panel.design_frequency,
                )
            )
            combined += complex_from_mag_phase(rotated_magnitude, total_phase_deg)

        hrp_original = np.abs(combined)
        hrp_original /= np.max(hrp_original)

        difference = np.abs(hrp_current - hrp_original)
        self.assertLess(float(np.max(difference)), 1e-12)
        self.assertAlmostEqual(
            compute_hrp_directivity_db(hrp_current),
            compute_hrp_directivity_db(hrp_original),
            places=12,
        )


if __name__ == "__main__":
    unittest.main()
