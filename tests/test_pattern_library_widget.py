import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from catalogs import OriginalAdtCatalog
from widgets.pattern_library import PatternLibraryWidget


class PatternLibraryWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.catalog = OriginalAdtCatalog()

    def test_standard_selection_autofills_paths_and_dimensions(self):
        widget = PatternLibraryWidget()
        entries = self.catalog.get_standard_panel_entries(539.0, "Horizontal")
        entry = next(
            item for item in entries if item.display_name == "Panel Array_PHP4S"
        )

        widget.set_predefined_panel_options(entries, pattern_indices=[1])
        widget.section_widgets[1]["panel_type"].setCurrentText(entry.display_name)

        config = widget.get_pattern_configs()[1]

        self.assertEqual(config["mode"], "Standard")
        self.assertEqual(config["panel_type"], entry.display_name)
        self.assertEqual(config["hrp_path"], entry.hrp_path)
        self.assertEqual(config["vrp_path"], entry.vrp_path)
        self.assertEqual(float(config["width_m"]), entry.width_m)
        self.assertEqual(float(config["height_m"]), entry.height_m)
        self.assertEqual(float(config["depth_m"]), entry.depth_m)

    def test_custom_mode_preserves_manual_editing(self):
        widget = PatternLibraryWidget()
        widget.section_widgets[1]["mode"].setCurrentText("Custom")

        self.assertTrue(widget.section_widgets[1]["panel_type"].isEditable())
        self.assertFalse(widget.section_widgets[1]["elevation_spacing_m"].isReadOnly())
        self.assertTrue(widget.section_widgets[1]["hrp_path_button"].isEnabled())
        self.assertTrue(widget.section_widgets[1]["vrp_path_button"].isEnabled())


if __name__ == "__main__":
    unittest.main()
