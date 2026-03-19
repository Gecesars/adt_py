import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow
from widgets.save_patterns import SavePatternsWidget


class SavePatternsWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_widget_defaults_match_legacy_pattern_save_grid(self):
        widget = SavePatternsWidget()
        settings = widget.get_settings()

        self.assertTrue(settings.save_jpg)
        self.assertEqual(settings.jpg_target, "HRP & VRP")
        self.assertTrue(settings.save_tabdata)
        self.assertTrue(settings.save_pat)
        self.assertTrue(settings.save_txt)
        self.assertTrue(settings.save_csv)
        self.assertFalse(settings.save_vsoft)
        self.assertFalse(settings.save_atdi)
        self.assertTrue(settings.save_3d_text)
        self.assertTrue(settings.save_ngw3d)
        self.assertTrue(settings.save_prn)
        self.assertTrue(settings.save_edx)
        self.assertEqual(settings.edx_file_type, "Simple file-1 VRP")
        self.assertEqual(settings.edx_hrp_used, "Peak HRP")
        self.assertEqual(settings.edx_start_deg, -5.0)
        self.assertEqual(settings.edx_stop_deg, 15.0)
        self.assertEqual(settings.edx_increment_deg, 0.1)

    def test_batch_export_uses_legacy_suffixes_and_save_pattern_options(self):
        window = ADTMainWindow()
        window.show()
        self.app.processEvents()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.on_calculate_clicked()
        self.app.processEvents()

        settings = window.save_patterns_widget.get_settings()
        settings.save_jpg = True
        settings.jpg_target = "HRP"
        settings.save_pat = True
        settings.pat_target = "HRP & VRP"
        settings.save_edx = True
        settings.edx_file_type = "Simple file-1 VRP"
        settings.edx_hrp_used = "Displayed HRP"
        settings.edx_start_deg = -5.0
        settings.edx_stop_deg = 5.0
        settings.edx_increment_deg = 0.5
        settings.image_resolution_scale = 2.0

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "caseA"
            saved_paths = window.export_selected_patterns(base_path, settings)

            self.assertIn(base_path.with_name("caseA_HRP.jpg"), saved_paths)
            self.assertIn(base_path.with_name("caseA_HRP.pat"), saved_paths)
            self.assertIn(base_path.with_name("caseA_VRP.pat"), saved_paths)
            self.assertIn(base_path.with_name("caseA.ProgiraEDX.pat"), saved_paths)

            with Image.open(base_path.with_name("caseA_HRP.jpg")) as image:
                self.assertEqual(image.size, (2000, 2800))

            edx_lines = base_path.with_name("caseA.ProgiraEDX.pat").read_text(encoding="ascii").splitlines()
            self.assertEqual(edx_lines[362], "1, 21")

    def test_batch_export_requires_calculated_pattern_first(self):
        window = ADTMainWindow()
        window.show()
        self.app.processEvents()

        settings = window.save_patterns_widget.get_settings()
        with self.assertRaisesRegex(ValueError, "Please calculate a 3D pattern first."):
            window.export_selected_patterns(Path("caseA"), settings)

    def test_batch_export_rejects_invalid_base_name(self):
        window = ADTMainWindow()
        window.show()
        self.app.processEvents()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.on_calculate_clicked()
        self.app.processEvents()

        settings = window.save_patterns_widget.get_settings()
        with self.assertRaisesRegex(ValueError, "Invalid file name"):
            window.export_selected_patterns(Path(tempfile.gettempdir()), settings)

    def test_batch_export_uses_base_name_even_if_user_types_extension(self):
        window = ADTMainWindow()
        window.show()
        self.app.processEvents()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.on_calculate_clicked()
        self.app.processEvents()

        settings = window.save_patterns_widget.get_settings()
        settings.save_jpg = True
        settings.jpg_target = "HRP"
        settings.save_pat = False
        settings.save_txt = False
        settings.save_csv = False
        settings.save_3d_text = False
        settings.save_ngw3d = False
        settings.save_prn = False
        settings.save_edx = False
        settings.save_tabdata = False

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "caseA.any.extension"
            saved_paths = window.export_selected_patterns(base_path, settings)
            self.assertEqual(saved_paths, [base_path.with_name("caseA_HRP.jpg")])


if __name__ == "__main__":
    unittest.main()
