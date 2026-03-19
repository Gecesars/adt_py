import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


class MainWindowLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_save_layout_writes_state_file(self):
        window = ADTMainWindow()
        with tempfile.TemporaryDirectory() as temp_dir:
            window.layout_file_path = Path(temp_dir) / "layout.json"
            window.left_tabs.setCurrentIndex(2)
            window.central_tabs.setCurrentIndex(1)
            window.right_bottom_tabs.setCurrentIndex(1)

            window._save_layout_to_disk()

            self.assertTrue(window.layout_file_path.exists())
            text = window.layout_file_path.read_text(encoding="utf-8")
            self.assertIn('"left_tab_index": 2', text)
            self.assertIn('"central_tab_index": 1', text)
            self.assertIn('"right_bottom_tab_index": 1', text)

    def test_splitters_allow_full_collapse(self):
        window = ADTMainWindow()

        self.assertTrue(window.main_horizontal_splitter.childrenCollapsible())
        self.assertTrue(window.left_column_splitter.childrenCollapsible())
        self.assertTrue(window.right_column_splitter.childrenCollapsible())
        self.assertTrue(window.central_splitter.childrenCollapsible())
        self.assertTrue(window.plots_splitter.childrenCollapsible())

        self.assertEqual(window.left_tabs.minimumWidth(), 0)
        self.assertEqual(window.right_bottom_tabs.minimumWidth(), 0)
        self.assertEqual(window.result_summary_widget.minimumWidth(), 0)
        self.assertEqual(window.message_list_widget.minimumWidth(), 0)


if __name__ == "__main__":
    unittest.main()
