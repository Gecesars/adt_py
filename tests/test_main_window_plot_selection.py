import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


if __name__ == "__main__":
    unittest.main()
