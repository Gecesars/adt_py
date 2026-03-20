from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from catalogs import CustomAntennaCatalog, CustomAntennaDefinition
from parsers import read_hrp_pattern, read_vrp_pattern


class CustomAntennaCatalogTests(unittest.TestCase):
    def _write_generic_hrp_csv(self, path: Path):
        lines = ["angle_db"]
        for angle in range(360):
            db_value = -abs(((angle + 180) % 360) - 180) / 30.0
            lines.append(f"{angle},{db_value:.6f}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_generic_vrp_txt(self, path: Path):
        lines = ["Angle Magnitude"]
        for angle in range(-90, 91):
            magnitude = max(math.cos(math.radians(angle)), 0.0)
            lines.append(f"{angle} {magnitude:.6f}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_save_custom_antenna_persists_xml_and_standardized_pattern_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "original_adt"
            source_hrp = Path(temp_dir) / "generic_hrp.csv"
            source_vrp = Path(temp_dir) / "generic_vrp.txt"
            self._write_generic_hrp_csv(source_hrp)
            self._write_generic_vrp_txt(source_vrp)

            catalog = CustomAntennaCatalog(root_path)
            entry = catalog.save_custom_antenna(
                CustomAntennaDefinition(
                    display_name="Custom Panel A",
                    frequency_mhz=539.0,
                    band="UHF",
                    polarization="Horizontal",
                    width_m=0.5,
                    height_m=1.09,
                    depth_m=0.22,
                    elevation_spacing_m=1.15,
                    elevation_unit="One Panel",
                    hrp_source_path=str(source_hrp),
                    vrp_source_path=str(source_vrp),
                )
            )

            self.assertTrue((root_path / "Rating" / "antenas_perso.xml").exists())
            self.assertTrue(Path(entry.hrp_path).exists())
            self.assertTrue(Path(entry.vrp_path).exists())

            hrp_angles, hrp_mag, _hrp_phase = read_hrp_pattern(entry.hrp_path)
            vrp_angles, vrp_mag, _vrp_phase = read_vrp_pattern(entry.vrp_path)

            self.assertEqual(hrp_angles.shape[0], 360)
            self.assertEqual(vrp_angles.shape[0], 1801)
            self.assertAlmostEqual(float(hrp_mag.max()), 1.0, places=6)
            self.assertAlmostEqual(float(vrp_mag.max()), 1.0, places=6)

            entries = catalog.get_standard_panel_entries(539.0, "Horizontal")
            reloaded = next(
                entry for entry in entries if entry.display_name == "Custom Panel A"
            )
            self.assertEqual(reloaded.panel_type, "Custom Panel A")
            self.assertEqual(reloaded.band, "UHF")

    def test_save_custom_antenna_can_generate_synthetic_vrp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "original_adt"
            source_hrp = Path(temp_dir) / "generic_hrp.csv"
            self._write_generic_hrp_csv(source_hrp)

            catalog = CustomAntennaCatalog(root_path)
            entry = catalog.save_custom_antenna(
                CustomAntennaDefinition(
                    display_name="Custom Panel B",
                    frequency_mhz=600.0,
                    band="UHF",
                    polarization="Horizontal",
                    width_m=0.52,
                    height_m=1.1,
                    depth_m=0.21,
                    elevation_spacing_m=1.15,
                    elevation_unit="One Panel",
                    hrp_source_path=str(source_hrp),
                    synthetic_vrp_half_power_angle_deg=18.5,
                )
            )

            self.assertTrue(Path(entry.vrp_path).exists())
            entries = catalog.get_standard_panel_entries(600.0, "Horizontal")
            reloaded = next(
                entry for entry in entries if entry.display_name == "Custom Panel B"
            )
            self.assertAlmostEqual(reloaded.half_power_vrp_angle_deg, 18.5, places=6)

    def test_custom_entries_are_returned_even_when_frequency_and_polarization_filter_differs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir) / "original_adt"
            source_hrp = Path(temp_dir) / "generic_hrp.csv"
            source_vrp = Path(temp_dir) / "generic_vrp.txt"
            self._write_generic_hrp_csv(source_hrp)
            self._write_generic_vrp_txt(source_vrp)

            catalog = CustomAntennaCatalog(root_path)
            catalog.save_custom_antenna(
                CustomAntennaDefinition(
                    display_name="Painel MIMO DTV",
                    frequency_mhz=300.0,
                    band="VHF",
                    polarization="Slant",
                    width_m=0.9,
                    height_m=1.8,
                    depth_m=0.35,
                    elevation_spacing_m=1.8,
                    elevation_unit="One Panel",
                    hrp_source_path=str(source_hrp),
                    vrp_source_path=str(source_vrp),
                )
            )

            entries = catalog.get_standard_panel_entries(539.0, "Horizontal")
            self.assertEqual(entries[0].display_name, "Painel MIMO DTV")


if __name__ == "__main__":
    unittest.main()
