import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from main import ADTMainWindow


class MainWindowSiteDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_site_details_tab_replaces_placeholder_and_syncs_losses(self):
        window = ADTMainWindow()

        self.assertEqual(window.left_tabs.tabText(1), "Site Details")
        self.assertIs(window.left_tabs.widget(1), window.site_details_widget)
        self.assertEqual(window.design_info_widget.internal_loss_input.text(), "0.1")
        self.assertEqual(window.design_info_widget.pol_loss_input.text(), "0")
        self.assertEqual(window.design_info_widget.filter_loss_input.text(), "0")

        window.site_details_widget.feeder_length_spin.setValue(100.0)

        self.assertNotEqual(window.design_info_widget.feeder_loss_input.text(), "0")
        self.assertAlmostEqual(
            float(window.design_info_widget.feeder_loss_input.text()),
            window.site_details_widget.computed_feeder_loss_db,
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
