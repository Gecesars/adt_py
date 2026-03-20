import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QTextBrowser

from app_metadata import APP_EMAIL, APP_NAME, APP_VERSION, APP_WINDOW_TITLE, app_logo_path
from main import ADTMainWindow
from widgets.about_dialog import AboutDialog
from widgets.help_dialog import HelpDialog


class BrandingAndHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_uses_eftx_branding(self):
        window = ADTMainWindow()
        self.assertEqual(window.windowTitle(), APP_WINDOW_TITLE)
        self.assertTrue(app_logo_path().exists())
        window.close()

    def test_about_dialog_contains_developer_information(self):
        dialog = AboutDialog(app_logo_path())
        self.assertIn(APP_NAME, dialog.windowTitle())
        labels_text = "\n".join(label.text() for label in dialog.findChildren(QLabel))
        self.assertIn(APP_VERSION, labels_text)
        self.assertIn(APP_EMAIL, labels_text)
        dialog.close()

    def test_help_dialog_contains_english_manual_sections(self):
        dialog = HelpDialog(app_logo_path())
        browser = dialog.findChild(QTextBrowser)
        self.assertIsNotNone(browser)
        html = browser.toHtml()
        self.assertIn("Typical Workflow", html)
        self.assertIn("Keyboard Shortcuts", html)
        self.assertIn("Calculate 3D Pattern", html)
        dialog.close()
