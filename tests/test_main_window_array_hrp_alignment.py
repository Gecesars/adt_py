import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


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


if __name__ == "__main__":
    unittest.main()
