import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from widgets.beam_shape import BeamShapeWidget


class BeamShapeWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_calculate_and_transfer_populates_phase_table(self):
        widget = BeamShapeWidget()
        transfers = []
        widget.phase_transfer_requested.connect(
            lambda phases, decimals: transfers.append((list(phases), decimals))
        )

        widget.calc_btn.click()

        self.assertIsNotNone(widget.current_result)
        self.assertEqual(widget.phase_table.item(0, 1).text(), "51.76")
        self.assertEqual(widget.phase_table.item(1, 1).text(), "22.09")
        self.assertEqual(widget.phase_table.item(2, 1).text(), "0.00")
        self.assertEqual(widget.phase_table.item(3, 1).text(), "21.93")

        widget.transfer_btn.click()

        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0][1], 0)
        self.assertEqual(len(transfers[0][0]), 4)

    def test_update_frequency_rewrites_input_table(self):
        widget = BeamShapeWidget()

        widget.update_frequency(601.25)

        self.assertEqual(widget.define_table.item(0, 1).text(), "601.25")

    def test_splitter_is_fully_collapsible(self):
        widget = BeamShapeWidget()

        self.assertTrue(widget.main_splitter.childrenCollapsible())
        self.assertEqual(widget.minimumSizeHint().width(), 0)
        self.assertEqual(widget.minimumSizeHint().height(), 0)


if __name__ == "__main__":
    unittest.main()
