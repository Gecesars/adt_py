import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from app.project_service import build_project_from_ui, project_to_array_design
from main import ADTMainWindow
from solver.pattern_synthesis import (
    STANDARD_HRP_ANGLES,
    calculate_configuration_phase_deg,
    complex_from_mag_phase,
    compute_hrp_cut_directivity_db,
    find_library_power_ratios,
    wrap_to_minus180_plus180,
)


class MainWindowArrayHrpAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_four_face_array_matches_literal_horizontal_baseline(self):
        window = ADTMainWindow()

        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.hrp_widget.angle_spin.setValue(0.0)
        window.on_calculate_clicked()

        self.assertAlmostEqual(window.hrp_widget.angle_spin.value(), 0.0, places=1)
        self.assertAlmostEqual(float(window.hrp_widget.dir_edit.text()), 1.49, places=1)
        self.assertEqual(window.vrp_widget.azimuth_spin.value(), 314)

    def test_four_face_array_hrp_matches_literal_original_algorithm_point_by_point(self):
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

            source_angles = np.asarray(source_angles, dtype=float)
            magnitude = np.asarray(magnitude, dtype=float)
            phase_deg = np.asarray(phase_deg, dtype=float)

            if panel.configuration in {1, 3, 5}:
                mirrored_angles = source_angles.copy()
                mirrored_angles[~np.isclose(mirrored_angles, -180.0)] *= -1.0
                order = np.argsort(mirrored_angles)
                source_angles = mirrored_angles[order]
                magnitude = magnitude[order]
                phase_deg = phase_deg[order]
            else:
                order = np.argsort(source_angles)
                source_angles = source_angles[order]
                magnitude = magnitude[order]
                phase_deg = phase_deg[order]

            configured_angles = wrap_to_minus180_plus180(
                source_angles + round(panel.face_angle, 0)
            )
            configured_magnitude = magnitude * np.sqrt(
                panel.power * power_ratio_map.get(panel.get_library_key(), 1.0)
            )
            configured_phase = phase_deg + (
                panel.y * np.cos(np.deg2rad(configured_angles)) / wavelength_m * 360.0
                + panel.x * np.sin(np.deg2rad(configured_angles)) / wavelength_m * 360.0
                + calculate_configuration_phase_deg(
                    panel.phase,
                    panel.configuration,
                    array_design.frequency,
                    panel.design_frequency,
                )
            )

            configured_field = complex_from_mag_phase(
                configured_magnitude,
                configured_phase,
            )
            by_angle = {
                int(round(angle_deg)): field_value
                for angle_deg, field_value in zip(configured_angles, configured_field)
            }
            combined += np.asarray(
                [by_angle[int(round(angle_deg))] for angle_deg in hrp_angles]
            )

        hrp_original = np.abs(combined)
        hrp_original /= np.max(hrp_original)

        difference = np.abs(hrp_current - hrp_original)
        self.assertLess(float(np.max(difference)), 1e-12)
        self.assertAlmostEqual(
            compute_hrp_cut_directivity_db(hrp_current, hrp_original),
            compute_hrp_cut_directivity_db(hrp_original, hrp_original),
            places=12,
        )

    def test_four_face_array_preserves_quarter_wave_symmetry(self):
        window = ADTMainWindow()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.hrp_widget.angle_spin.setValue(0.0)
        window.on_calculate_clicked()

        angles = np.asarray(window.hrp_widget.angles_deg, dtype=float)
        magnitudes = np.asarray(window.hrp_widget.magnitudes, dtype=float)

        for base_angle in range(0, 90):
            quarter_shift_angle = ((base_angle + 90 + 180) % 360) - 180
            if quarter_shift_angle == 180:
                quarter_shift_angle = -180

            first_index = int(np.where(np.isclose(angles, float(base_angle)))[0][0])
            second_index = int(
                np.where(np.isclose(angles, float(quarter_shift_angle)))[0][0]
            )
            self.assertAlmostEqual(
                float(magnitudes[first_index]),
                float(magnitudes[second_index]),
                places=12,
            )


if __name__ == "__main__":
    unittest.main()
