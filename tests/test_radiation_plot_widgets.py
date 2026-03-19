import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt6.QtWidgets import QApplication

from widgets.radiation_plots import (
    HrpPlotWidget,
    VrpPlotWidget,
    display_to_internal_azimuth,
    internal_to_display_azimuth,
)


class RadiationPlotWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hrp_plot_widget_accepts_data_and_switches_display_mode(self):
        widget = HrpPlotWidget()
        angles = np.arange(0.0, 360.0, 1.0)
        magnitudes = np.abs(np.cos(np.deg2rad(angles)))

        widget.plot_data(angles, magnitudes)
        widget.set_cut_metadata(elevation_deg=-0.1, directivity_dbd=11.27)
        widget.rb_db.setChecked(True)

        self.assertEqual(widget.dir_edit.text(), "11.27")
        self.assertAlmostEqual(widget.angle_spin.value(), -0.1, places=1)
        self.assertEqual(widget.db_combo.currentText(), "40 Log Pwr")
        self.assertEqual(internal_to_display_azimuth(-180.0), 180.0)
        self.assertEqual(internal_to_display_azimuth(-1.0), 359.0)
        self.assertEqual(internal_to_display_azimuth(0.0), 0.0)

        widget.clear_plot_display()

        self.assertEqual(widget.magnitudes.size, 0)
        self.assertEqual(widget.dir_edit.text(), "")

    def test_hrp_plot_widget_preserves_absolute_cut_level_like_original_adt(self):
        widget = HrpPlotWidget()
        angles = np.arange(-180.0, 180.0, 1.0)
        magnitudes = np.full(angles.shape, 0.5)

        widget.plot_data(angles, magnitudes)

        radii = widget._scaled_radius()
        self.assertAlmostEqual(float(np.max(radii)), 0.5, places=12)

        widget.rb_db.setChecked(True)
        db_radii = widget._scaled_radius()
        expected_db_radius = (20.0 * np.log10(0.5) - (-40.0)) / 40.0
        self.assertAlmostEqual(float(np.max(db_radii)), expected_db_radius, places=12)

    def test_vrp_plot_widget_accepts_data_metadata_and_range(self):
        widget = VrpPlotWidget()
        angles = np.linspace(-90.0, 90.0, 181)
        magnitudes = np.maximum(np.cos(np.deg2rad(angles)), 0.0)

        widget.plot_data(angles, magnitudes)
        widget.set_cut_metadata(azimuth_deg=-1.0, directivity_dbd=11.27, tilt_deg=-0.1)
        widget.start_spin.setValue(-5)
        widget.stop_spin.setValue(90)
        widget.rb_db.setChecked(True)

        self.assertEqual(widget.dir_edit.text(), "11.27")
        self.assertEqual(widget.tilt_edit.text(), "-0.1")
        self.assertEqual(widget.azimuth_spin.value(), 359)
        self.assertEqual(widget.start_spin.value(), -5)
        self.assertEqual(widget.stop_spin.value(), 90)
        self.assertEqual(display_to_internal_azimuth(359.0), -1.0)
        self.assertEqual(display_to_internal_azimuth(180.0), -180.0)
        self.assertEqual(display_to_internal_azimuth(0.0), 0.0)
        if widget.range_slider is not None:
            self.assertEqual(tuple(widget.range_slider.value()), (-5, 90))

        widget.clear_plot_display()

        self.assertEqual(widget.magnitudes.size, 0)
        self.assertEqual(widget.dir_edit.text(), "")
        self.assertEqual(widget.tilt_edit.text(), "")

    def test_vrp_plot_widget_preserves_absolute_cut_level_by_default(self):
        widget = VrpPlotWidget()
        angles = np.linspace(-90.0, 90.0, 181)
        magnitudes = np.full(angles.shape, 0.5)

        widget.plot_data(angles, magnitudes)

        values = widget._scaled_values()
        self.assertAlmostEqual(float(np.max(values)), 0.5, places=12)

        widget.normalise_vrp = True
        values_normalised = widget._scaled_values()
        self.assertAlmostEqual(float(np.max(values_normalised)), 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
