import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


class MainWindowAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_action_shortcuts_match_expected_keys(self):
        window = ADTMainWindow()

        self.assertEqual(window.act_action_calc_3d.shortcut().toString(), "F6")
        self.assertEqual(window.act_action_anim_vrp.shortcut().toString(), "F7")
        self.assertEqual(window.act_action_anim_hrp.shortcut().toString(), "F8")

    def test_vrp_animation_updates_plot_and_restores_original_cut(self):
        window = ADTMainWindow()
        window.on_calculate_clicked()

        original_display_azimuth = window.vrp_widget.azimuth_spin.value()
        baseline_vrp = np.asarray(window.vrp_widget.magnitudes, dtype=float).copy()

        window._start_pattern_animation(
            "vrp",
            327,
            328,
            delay_index=2,
            scan_peer=True,
            start_timer=False,
        )
        window._advance_pattern_animation_frame()

        self.assertEqual(window.vrp_widget.azimuth_spin.value(), 327)
        self.assertAlmostEqual(window.hrp_widget.selected_azimuth_deg, -33.0, places=6)
        self.assertFalse(
            np.allclose(baseline_vrp, np.asarray(window.vrp_widget.magnitudes, dtype=float))
        )

        while window.animation_state is not None:
            window._advance_pattern_animation_frame()

        self.assertEqual(window.vrp_widget.azimuth_spin.value(), original_display_azimuth)

    def test_hrp_animation_updates_plot_and_restores_original_cut(self):
        window = ADTMainWindow()
        window.on_calculate_clicked()

        original_elevation = float(window.hrp_widget.angle_spin.value())
        baseline_hrp = np.asarray(window.hrp_widget.magnitudes, dtype=float).copy()

        window._start_pattern_animation(
            "hrp",
            6.6,
            6.7,
            delay_index=2,
            scan_peer=True,
            start_timer=False,
        )
        window._advance_pattern_animation_frame()

        self.assertAlmostEqual(float(window.hrp_widget.angle_spin.value()), 6.6, places=1)
        self.assertAlmostEqual(window.vrp_widget.selected_elevation_deg, 6.6, places=1)
        self.assertFalse(
            np.allclose(baseline_hrp, np.asarray(window.hrp_widget.magnitudes, dtype=float))
        )

        while window.animation_state is not None:
            window._advance_pattern_animation_frame()

        self.assertAlmostEqual(float(window.hrp_widget.angle_spin.value()), original_elevation, places=1)


if __name__ == "__main__":
    unittest.main()
