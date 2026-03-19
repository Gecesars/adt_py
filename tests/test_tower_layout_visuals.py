import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from widgets.radiation_plots import HrpPlotWidget
from widgets.tower_layout import TowerLayoutWidget


class TowerLayoutVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_decimal_spinboxes_use_dot_separator(self):
        tower_widget = TowerLayoutWidget()
        tower_widget.offset_spin.setValue(1.5)
        tower_widget.spacing_spin.setValue(2.75)

        hrp_widget = HrpPlotWidget()
        hrp_widget.angle_spin.setValue(-0.5)

        self.assertIn(".", tower_widget.offset_spin.text())
        self.assertIn(".", tower_widget.spacing_spin.text())
        self.assertIn(".", hrp_widget.angle_spin.text())
        self.assertNotIn(",", tower_widget.offset_spin.text())
        self.assertNotIn(",", hrp_widget.angle_spin.text())

    def test_preview_uses_real_panel_dimensions_and_inferred_tower_width(self):
        widget = TowerLayoutWidget()
        widget.update_preview(
            [
                {
                    "pattern_index": 1,
                    "angle_deg": 0.0,
                    "offset_m": 0.34,
                    "elevation_m": 0.0,
                    "azimuth_deg": 0.0,
                    "tilt_deg": 0.0,
                }
            ],
            {
                1: {
                    "width_m": 0.50,
                    "height_m": 1.09,
                    "depth_m": 0.22,
                }
            },
        )

        self.assertEqual(len(widget.preview_widget.panels), 1)
        preview_panel = widget.preview_widget.panels[0]
        self.assertAlmostEqual(preview_panel.width, 0.50, places=6)
        self.assertAlmostEqual(preview_panel.height, 1.09, places=6)
        self.assertAlmostEqual(preview_panel.depth, 0.22, places=6)
        self.assertAlmostEqual(widget.preview_widget.tower_half_width_m, 0.2185, places=3)

    def test_top_view_preview_uses_tapered_panel_shapes(self):
        widget = TowerLayoutWidget()
        widget.view_combo.setCurrentText("Top View")
        widget.update_preview(
            [
                {
                    "pattern_index": 1,
                    "angle_deg": 0.0,
                    "offset_m": 0.34,
                    "elevation_m": 0.0,
                    "azimuth_deg": 0.0,
                    "tilt_deg": 0.0,
                }
            ],
            {
                1: {
                    "width_m": 0.50,
                    "height_m": 1.09,
                    "depth_m": 0.22,
                }
            },
        )

        polygon = widget.preview_widget._panel_topdown_polygon(widget.preview_widget.panels[0])
        inner_edge = ((polygon[1][0] - polygon[0][0]) ** 2 + (polygon[1][1] - polygon[0][1]) ** 2) ** 0.5
        outer_edge = ((polygon[2][0] - polygon[3][0]) ** 2 + (polygon[2][1] - polygon[3][1]) ** 2) ** 0.5

        self.assertGreater(inner_edge, outer_edge)


if __name__ == "__main__":
    unittest.main()
