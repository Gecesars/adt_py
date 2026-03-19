from pathlib import Path
import unittest

from catalogs import OriginalAdtCatalog, lookup_generated_vrp_half_power_angle
from models.antenna import AntennaPanel


class OriginalAdtCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = OriginalAdtCatalog()

    def test_catalog_loads_entries_from_copied_original_adt_assets(self):
        entries = self.catalog.get_standard_panel_entries(539.0, "Horizontal")

        self.assertGreater(len(entries), 0)
        php4s = next(
            (entry for entry in entries if entry.display_name == "Panel Array_PHP4S"),
            None,
        )
        mtv = next((entry for entry in entries if entry.display_name == "MTV"), None)

        self.assertIsNotNone(php4s)
        self.assertIsNotNone(mtv)
        self.assertTrue(Path(php4s.hrp_path).exists())
        self.assertEqual(php4s.vrp_path, "")
        self.assertIsNotNone(php4s.half_power_vrp_angle_deg)
        self.assertTrue(Path(mtv.hrp_path).exists())
        self.assertTrue(Path(mtv.vrp_path).exists())

    def test_generated_vrp_angle_matches_recovered_formula(self):
        expected = (
            -0.0122 * (((539.0 - 470.0) / 50.0 + 1.0) ** 3)
            + 0.2906 * (((539.0 - 470.0) / 50.0 + 1.0) ** 2)
            - 2.6561 * (((539.0 - 470.0) / 50.0 + 1.0))
            + 18.985
        )
        actual = lookup_generated_vrp_half_power_angle("Panel Array_PHP4S", 539.0)

        self.assertIsNotNone(actual)
        self.assertAlmostEqual(actual, expected, places=6)

    def test_standard_panel_without_vrp_file_uses_generated_vertical_pattern(self):
        panel = AntennaPanel(1, type="Standard")
        panel.panel_type_name = "Panel Array_PHP4S"
        panel.design_frequency = 539.0

        (
            _hrp_angles,
            _hrp_mag,
            _hrp_phase,
            vrp_angles,
            vrp_mag,
            vrp_phase,
        ) = panel.get_radiation_pattern()

        self.assertEqual(vrp_angles.shape[0], 1801)
        self.assertEqual(vrp_mag.shape[0], 1801)
        self.assertEqual(vrp_phase.shape[0], 1801)
        self.assertAlmostEqual(float(vrp_mag.max()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
