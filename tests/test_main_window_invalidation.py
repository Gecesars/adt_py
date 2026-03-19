import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


class MainWindowInvalidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _configure_vertical_stack(self, window):
        for row in range(4):
            window.antenna_design_tab.array_table.item(row, 3).setText(f"{row * 1.15:.3f}")
            window.antenna_design_tab.array_table.item(row, 10).setText(str(row + 1))

    def test_beam_shape_transfer_clears_plots_until_next_3d_calculation(self):
        window = ADTMainWindow()
        self._configure_vertical_stack(window)

        window.on_calculate_clicked()
        baseline_vrp = window.vrp_widget.magnitudes.copy()

        self.assertIsNotNone(window.last_mag_3d)
        self.assertGreater(baseline_vrp.size, 0)
        self.assertNotEqual(window.result_summary_widget.table.item(1, 1).text(), "")

        window.beam_shape_widget.calc_btn.click()
        window.beam_shape_widget.transfer_btn.click()

        self.assertIsNone(window.last_mag_3d)
        self.assertEqual(window.hrp_widget.magnitudes.size, 0)
        self.assertEqual(window.vrp_widget.magnitudes.size, 0)
        self.assertEqual(window.hrp_widget.dir_edit.text(), "")
        self.assertEqual(window.vrp_widget.dir_edit.text(), "")
        self.assertEqual(window.vrp_widget.tilt_edit.text(), "")
        self.assertEqual(window.result_summary_widget.table.item(1, 1).text(), "")

        transferred_values = [
            window.antenna_design_tab.v_group_table.item(index, 0).text()
            for index in range(4)
        ]
        self.assertEqual(transferred_values, ["52", "22", "0", "22"])

        window.on_calculate_clicked()
        updated_vrp = window.vrp_widget.magnitudes.copy()

        self.assertIsNotNone(window.last_mag_3d)
        self.assertGreater(updated_vrp.size, 0)
        self.assertFalse(np.allclose(baseline_vrp, updated_vrp))
        self.assertNotEqual(window.result_summary_widget.table.item(1, 1).text(), "")


if __name__ == "__main__":
    unittest.main()
