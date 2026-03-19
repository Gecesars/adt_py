import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from catalogs import CableCatalog
from tests.helpers import PROJECT_ROOT
from widgets.site_details import SiteDetailsWidget


class SiteDetailsWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_widget_uses_legacy_defaults_and_real_feeder_list(self):
        widget = SiteDetailsWidget(
            CableCatalog(PROJECT_ROOT.parent / "Rating" / "CableRating.xml")
        )

        self.assertEqual(widget.tower_type_combo.currentText(), "Square")
        self.assertAlmostEqual(widget.tower_size_spin.value(), 0.64)
        self.assertAlmostEqual(widget.tower_heading_spin.value(), 0.0)
        self.assertEqual(widget.main_feeder_combo.currentText(), "HCA38-50")
        self.assertAlmostEqual(widget.internal_loss_spin.value(), 0.1)
        self.assertAlmostEqual(widget.polar_loss_spin.value(), 0.0)
        self.assertAlmostEqual(widget.filter_loss_spin.value(), 0.0)
        self.assertAlmostEqual(widget.tx_power_spin.value(), 1.0)
        self.assertAlmostEqual(widget.antenna_height_spin.value(), 150.0)
        self.assertGreater(widget.main_feeder_combo.count(), 5)

    def test_widget_calculates_feeder_loss_from_channel_frequency(self):
        catalog = CableCatalog(PROJECT_ROOT.parent / "Rating" / "CableRating.xml")
        widget = SiteDetailsWidget(catalog)

        widget.set_channel_frequency_mhz(539.0)
        widget.feeder_length_spin.setValue(100.0)

        self.assertAlmostEqual(
            widget.computed_feeder_loss_db,
            catalog.calculate_feeder_loss_db("HCA38-50", 100.0, 539.0),
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
