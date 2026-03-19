import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


class MainWindowPlotSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_manual_plot_selection_is_preserved_across_recalculation(self):
        window = ADTMainWindow()

        window.vrp_widget.azimuth_spin.setValue(314)
        window.hrp_widget.angle_spin.setValue(1.3)

        self.assertTrue(window.lock_vrp_azimuth)
        self.assertTrue(window.lock_hrp_elevation)
        self.assertAlmostEqual(window.selected_vrp_azimuth_deg, -46.0, places=6)
        self.assertAlmostEqual(window.selected_hrp_elevation_deg, 1.3, places=6)

        window.on_calculate_clicked()

        self.assertEqual(window.vrp_widget.azimuth_spin.value(), 314)
        self.assertAlmostEqual(window.hrp_widget.angle_spin.value(), 1.3, places=1)
        self.assertAlmostEqual(window.hrp_widget.selected_azimuth_deg, -46.0, places=6)
        self.assertIsNotNone(window.last_metrics)

    def test_elevation_and_azimuth_controls_refresh_displayed_cuts_dynamically(self):
        window = ADTMainWindow()
        window.on_calculate_clicked()

        baseline_hrp = np.asarray(window.hrp_widget.magnitudes, dtype=float).copy()
        baseline_vrp = np.asarray(window.vrp_widget.magnitudes, dtype=float).copy()

        window.hrp_widget.angle_spin.setValue(6.7)
        hrp_after_elevation = np.asarray(window.hrp_widget.magnitudes, dtype=float)
        self.assertFalse(np.allclose(baseline_hrp, hrp_after_elevation))
        self.assertEqual(window.result_summary_widget.point_table.item(0, 1).text(), "6.7")
        self.assertAlmostEqual(window.vrp_widget.selected_elevation_deg, 6.7, places=1)

        window.vrp_widget.azimuth_spin.setValue(327)
        vrp_after_azimuth = np.asarray(window.vrp_widget.magnitudes, dtype=float)
        self.assertFalse(np.allclose(baseline_vrp, vrp_after_azimuth))
        self.assertAlmostEqual(window.hrp_widget.selected_azimuth_deg, -33.0, places=6)
        self.assertEqual(window.result_summary_widget.point_table.item(0, 0).text(), "327")


if __name__ == "__main__":
    unittest.main()
