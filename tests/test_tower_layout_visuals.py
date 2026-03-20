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

    def test_preview_uses_site_details_tower_size_when_provided(self):
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
            site_values={
                "tower_type": "Square",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )

        self.assertAlmostEqual(widget.preview_widget.tower_half_width_m, 0.32, places=6)
        self.assertEqual(widget.preview_widget.tower_type, "Square")

    def test_preview_uses_face_width_to_compute_hexagonal_half_span(self):
        widget = TowerLayoutWidget()
        widget.update_preview(
            [],
            {},
            site_values={
                "tower_type": "Hexagonal",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )

        self.assertAlmostEqual(widget.preview_widget.tower_half_width_m, 0.64, places=6)
        self.assertEqual(widget.preview_widget.tower_type, "Hexagonal")

    def test_preview_uses_tower_type_to_change_tower_outline(self):
        widget = TowerLayoutWidget()
        widget.update_preview(
            [],
            {},
            site_values={
                "tower_type": "Round",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )
        round_polygon = widget.preview_widget._tower_topdown_polygon()

        widget.update_preview(
            [],
            {},
            site_values={
                "tower_type": "Hexagonal",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )
        hex_polygon = widget.preview_widget._tower_topdown_polygon()

        self.assertGreaterEqual(len(round_polygon), 16)
        self.assertEqual(len(hex_polygon), 6)

    def test_preview_rotates_tower_outline_with_tower_heading(self):
        widget = TowerLayoutWidget()
        widget.update_preview(
            [],
            {},
            site_values={
                "tower_type": "Square",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )
        base_polygon = widget.preview_widget._tower_topdown_polygon()

        widget.update_preview(
            [],
            {},
            site_values={
                "tower_type": "Square",
                "tower_size_m": 0.64,
                "tower_heading_deg": 45.0,
            },
        )
        rotated_polygon = widget.preview_widget._tower_topdown_polygon()

        self.assertNotAlmostEqual(base_polygon[0][0], rotated_polygon[0][0], places=6)
        self.assertNotAlmostEqual(base_polygon[0][1], rotated_polygon[0][1], places=6)

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

    def test_top_view_preview_uses_compact_schematic_panel_proportions(self):
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

        preview = widget.preview_widget
        panel = preview.panels[0]
        polygon = preview._panel_topdown_polygon(panel)
        inner_edge = ((polygon[1][0] - polygon[0][0]) ** 2 + (polygon[1][1] - polygon[0][1]) ** 2) ** 0.5
        panel_depth = (((polygon[2][0] + polygon[3][0]) / 2.0 - (polygon[0][0] + polygon[1][0]) / 2.0) ** 2 + (((polygon[2][1] + polygon[3][1]) / 2.0) - ((polygon[0][1] + polygon[1][1]) / 2.0)) ** 2) ** 0.5

        self.assertAlmostEqual(inner_edge, panel.width, places=6)
        self.assertLess(panel_depth, panel.depth)

    def test_top_view_preview_preserves_square_face_to_panel_width_ratio(self):
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
            site_values={
                "tower_type": "Square",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )

        preview = widget.preview_widget
        tower_polygon = preview._tower_world_polygon()
        panel_polygon = preview._panel_topdown_polygon(preview.panels[0])

        tower_face_width = (
            (tower_polygon[1][0] - tower_polygon[0][0]) ** 2
            + (tower_polygon[1][1] - tower_polygon[0][1]) ** 2
        ) ** 0.5
        panel_inner_edge = (
            (panel_polygon[1][0] - panel_polygon[0][0]) ** 2
            + (panel_polygon[1][1] - panel_polygon[0][1]) ** 2
        ) ** 0.5

        self.assertAlmostEqual(tower_face_width, 0.64, places=6)
        self.assertAlmostEqual(panel_inner_edge, 0.50, places=6)
        self.assertAlmostEqual(panel_inner_edge / tower_face_width, 0.50 / 0.64, places=6)

    def test_top_view_preview_preserves_clearance_for_large_offset(self):
        widget = TowerLayoutWidget()
        widget.view_combo.setCurrentText("Top View")
        widget.update_preview(
            [
                {
                    "pattern_index": 1,
                    "angle_deg": 0.0,
                    "offset_m": 1.0,
                    "elevation_m": 0.0,
                    "azimuth_deg": 0.0,
                    "tilt_deg": 0.0,
                }
            ],
            {
                1: {
                    "width_m": 1.30,
                    "height_m": 2.00,
                    "depth_m": 0.20,
                }
            },
            site_values={
                "tower_type": "Square",
                "tower_size_m": 0.64,
                "tower_heading_deg": 0.0,
            },
        )

        preview = widget.preview_widget
        panel_polygon = preview._panel_topdown_polygon(preview.panels[0])
        inner_edge_y = (panel_polygon[0][1] + panel_polygon[1][1]) / 2.0
        tower_face_radius = preview._tower_face_radius(0.0)

        self.assertGreater(inner_edge_y, tower_face_radius)
        self.assertAlmostEqual(inner_edge_y - tower_face_radius, 0.58, places=6)


if __name__ == "__main__":
    unittest.main()
