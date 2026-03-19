import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from widgets.antenna_design import AntennaDesignWidget


class AntennaDesignGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_build_geometry_matches_recovered_faces_levels_and_inputs(self):
        widget = AntennaDesignWidget()
        widget.build_geometry(4, 0.34, 0.0, 4, 1.15, False)

        self.assertEqual(widget.array_table.rowCount(), 16)
        self.assertEqual(widget.array_table.item(0, 1).text(), "0.0")
        self.assertEqual(widget.array_table.item(0, 2).text(), "0.340")
        self.assertEqual(widget.array_table.item(0, 3).text(), "0.000")
        self.assertEqual(widget.array_table.item(0, 4).text(), "0.0")
        self.assertEqual(widget.array_table.item(0, 10).text(), "1")
        self.assertEqual(widget.array_table.item(0, 11).text(), "A")
        self.assertEqual(widget.array_table.item(0, 12).text(), "1")

        self.assertEqual(widget.array_table.item(3, 1).text(), "270.0")
        self.assertEqual(widget.array_table.item(3, 4).text(), "270.0")
        self.assertEqual(widget.array_table.item(3, 11).text(), "D")

        self.assertEqual(widget.array_table.item(4, 3).text(), "1.150")
        self.assertEqual(widget.array_table.item(4, 10).text(), "2")
        self.assertEqual(widget.array_table.item(4, 11).text(), "A")
        self.assertEqual(widget.array_table.item(8, 12).text(), "2")

    def test_build_geometry_applies_heading_and_cogging_like_original(self):
        widget = AntennaDesignWidget()
        widget.build_geometry(2, 0.34, 30.0, 2, 1.0, True)

        self.assertEqual(widget.array_table.rowCount(), 4)
        self.assertEqual(widget.array_table.item(0, 1).text(), "30.0")
        self.assertEqual(widget.array_table.item(1, 1).text(), "210.0")
        self.assertEqual(widget.array_table.item(2, 1).text(), "120.0")
        self.assertEqual(widget.array_table.item(3, 1).text(), "300.0")
        self.assertEqual(widget.array_table.item(2, 4).text(), "120.0")
        self.assertEqual(widget.array_table.item(3, 4).text(), "300.0")

    def test_mech_tilt_array_updates_offsets_and_tilt(self):
        widget = AntennaDesignWidget()
        widget.build_geometry(1, 0.34, 0.0, 2, 1.15, False)

        original_offset = float(widget.array_table.item(0, 2).text())
        widget.mech_tilt_array(2.0, 0.0)

        self.assertGreater(float(widget.array_table.item(0, 2).text()), original_offset)
        self.assertAlmostEqual(float(widget.array_table.item(0, 7).text()), 2.0, places=1)
        self.assertAlmostEqual(float(widget.array_table.item(1, 7).text()), 2.0, places=1)


if __name__ == "__main__":
    unittest.main()
