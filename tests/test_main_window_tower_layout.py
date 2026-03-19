import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from app.project_service import build_project_from_ui, project_to_array_design
from main import ADTMainWindow


class MainWindowTowerLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tower_geometry_generation_feeds_panel_groups_into_runtime_design(self):
        window = ADTMainWindow()

        window.antenna_design_tab.h_group_table.item(0, 1).setText("15.0")
        window.antenna_design_tab.h_group_table.item(1, 1).setText("0.500")
        window.antenna_design_tab.v_group_table.item(1, 0).setText("20.0")

        window.on_tower_geometry_generate_requested(2, 0.34, 30.0, 2, 1.15, True)

        self.assertEqual(window.design_info_widget.num_panels_spin.value(), 4)
        self.assertEqual(window.antenna_design_tab.array_table.rowCount(), 4)
        self.assertEqual(window.antenna_design_tab.array_table.item(0, 11).text(), "A")
        self.assertEqual(window.antenna_design_tab.array_table.item(1, 11).text(), "B")
        self.assertEqual(window.antenna_design_tab.array_table.item(2, 10).text(), "2")
        self.assertEqual(window.antenna_design_tab.array_table.item(3, 1).text(), "300.0")

        project = build_project_from_ui(
            window.design_info_widget,
            window.antenna_design_tab,
            window.pattern_library_widget,
        )
        runtime_design = project_to_array_design(project)

        panel_b_level_2 = runtime_design.panels[3]
        self.assertAlmostEqual(panel_b_level_2.power, 0.5, places=6)
        self.assertAlmostEqual(panel_b_level_2.phase, 35.0, places=6)
        self.assertAlmostEqual(panel_b_level_2.face_angle, 300.0, places=6)
        self.assertAlmostEqual(panel_b_level_2.z, 1.15, places=6)


if __name__ == "__main__":
    unittest.main()
