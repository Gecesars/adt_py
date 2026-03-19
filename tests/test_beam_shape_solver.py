import unittest

from solver.beam_shape_solver import (
    calculate_beam_shape_phases,
    calculate_linear_phase_progression_deg,
    format_phase_value,
)


class BeamShapeSolverTests(unittest.TestCase):
    def test_linear_phase_progression_matches_recovered_formula(self):
        actual = calculate_linear_phase_progression_deg(539.0, 1.15, 1.0)
        self.assertAlmostEqual(actual, 12.980130804249145, places=9)

    def test_oscillatory_solution_matches_original_phase_tables(self):
        result = calculate_beam_shape_phases(
            frequency_mhz=539.0,
            bay_count=4,
            beam_tilt_deg=1.0,
            spacing_m=1.15,
            null_fill_percent=50,
            solution="Oscillatory",
        )

        expected = [51.7602616084983, 22.092630804249147, 0.0, 21.93236919575086]
        self.assertEqual(result.bay_count, 4)
        self.assertEqual(len(result.phases_deg), 4)
        for actual, reference in zip(result.phases_deg, expected):
            self.assertAlmostEqual(actual, reference, places=9)

    def test_phase_formatter_respects_decimal_places(self):
        self.assertEqual(format_phase_value(12.987, 0), "13")
        self.assertEqual(format_phase_value(12.987, 1), "13.0")
        self.assertEqual(format_phase_value(12.987, 2), "12.99")


if __name__ == "__main__":
    unittest.main()
