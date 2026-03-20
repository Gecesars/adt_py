import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from parsers.patterns import load_pattern_for_import, read_hrp_pattern, read_pattern_frequency, read_vrp_pattern


class PatternParserTests(unittest.TestCase):
    def test_hrp_parser_applies_original_file_offsets_to_phase(self):
        pattern_path = Path(
            "D:/dev/Antenna Design Tool (ADT) V1.5.3 Test version/ADT_PY/assets/original_adt/UnitPattern/HRP/Panel Array_PHP4S/1_pan_2L_RS_LC-538.pat"
        )

        angles_deg, _magnitude, phase_deg = read_hrp_pattern(pattern_path)

        with pattern_path.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()

        frequency_mhz = float(lines[1].strip())
        header_parts = lines[3].split()
        original_xoff_m = float(header_parts[0])
        original_yoff_m = float(header_parts[1])
        file_phase_deg = float(header_parts[4])

        voltage_index = next(
            index for index, line in enumerate(lines) if line.strip().lower() == "voltage"
        )
        data_lines = [
            line.strip().split()
            for line in lines[voltage_index + 1 :]
            if len(line.strip().split()) >= 3
        ][:360]
        raw_angles_deg = np.asarray([float(parts[0]) for parts in data_lines], dtype=float)
        raw_phase_deg = np.asarray([float(parts[2]) for parts in data_lines], dtype=float)

        sample_angle_deg = 0.0
        parsed_index = int(np.where(np.isclose(angles_deg, sample_angle_deg))[0][0])
        raw_index = int(np.where(np.isclose(raw_angles_deg, sample_angle_deg))[0][0])

        wavelength_m = 300.0 / frequency_mhz
        expected_phase_deg = raw_phase_deg[raw_index] + (
            (-original_yoff_m) * math.cos(math.radians(sample_angle_deg)) / wavelength_m * 360.0
            + (-original_xoff_m) * math.sin(math.radians(sample_angle_deg)) / wavelength_m * 360.0
            + file_phase_deg
        )

        self.assertAlmostEqual(float(phase_deg[parsed_index]), expected_phase_deg, places=9)

    def test_vrp_parser_matches_original_sparse_fill_and_linear_interpolation(self):
        pattern_path = Path(
            "D:/dev/Antenna Design Tool (ADT) V1.5.3 Test version/ADT_PY/assets/original_adt/UnitPattern/VRP/MTV/MTV-4 Measured Vertical pattern  470.pat"
        )

        angles_deg, magnitude, phase_deg = read_vrp_pattern(pattern_path)

        with pattern_path.open("r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()

        voltage_index = next(
            index for index, line in enumerate(lines) if line.strip().lower() == "voltage"
        )
        first_angle_deg = float(lines[voltage_index + 1].split()[0])
        second_angle_deg = float(lines[voltage_index + 2].split()[0])
        step_index = int(abs(second_angle_deg - first_angle_deg) / 0.1)

        start_index = next(
            index for index, line in enumerate(lines) if line.strip().startswith("-90")
        )
        start_parts = lines[start_index].split()
        next_parts = lines[start_index + 1].split()

        self.assertEqual(len(angles_deg), 1801)
        self.assertAlmostEqual(float(angles_deg[0]), -90.0, places=9)
        self.assertAlmostEqual(float(angles_deg[-1]), 90.0, places=9)
        self.assertEqual(step_index, 10)

        self.assertAlmostEqual(float(magnitude[0]), float(start_parts[1]), places=9)
        self.assertAlmostEqual(float(phase_deg[0]), float(start_parts[2]), places=9)
        self.assertAlmostEqual(float(magnitude[step_index]), float(next_parts[1]), places=9)
        self.assertAlmostEqual(float(phase_deg[step_index]), float(next_parts[2]), places=9)

        expected_mid_mag = float(start_parts[1]) + (
            float(next_parts[1]) - float(start_parts[1])
        ) / step_index
        expected_mid_phase = float(start_parts[2]) + (
            float(next_parts[2]) - float(start_parts[2])
        ) / step_index
        self.assertAlmostEqual(float(angles_deg[1]), -89.9, places=9)
        self.assertAlmostEqual(float(magnitude[1]), expected_mid_mag, places=9)
        self.assertAlmostEqual(float(phase_deg[1]), expected_mid_phase, places=9)

    def test_generic_hrp_csv_ignores_info_columns_and_uses_theta_as_angle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pattern_path = Path(temp_dir) / "azimute_hpol.csv"
            pattern_path.write_text(
                "\n".join(
                    [
                        '"Freq [GHz]","Phi [deg]","Theta [deg]","10^(dB10normalize(GainL3y)/20) []"',
                        "0.471,90,-180,0.765423809360821",
                        "0.471,90,-179,0.765369844098952",
                        "0.471,90,-178,0.765240321126155",
                        "0.471,90,0,1.000000000000000",
                        "0.471,90,1,0.999500000000000",
                        "0.471,90,179,0.765369844098952",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            angles_deg, magnitude, phase_deg = load_pattern_for_import(pattern_path, "HRP")

            self.assertEqual(len(angles_deg), 360)
            self.assertAlmostEqual(float(angles_deg[0]), -180.0, places=9)
            self.assertAlmostEqual(float(magnitude[0]), 0.765423809360821, places=9)
            zero_index = int(np.where(np.isclose(angles_deg, 0.0))[0][0])
            self.assertAlmostEqual(float(magnitude[zero_index]), 1.0, places=6)
            self.assertTrue(np.allclose(phase_deg, 0.0))

    def test_generic_vrp_csv_ignores_info_columns_and_converts_db_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pattern_path = Path(temp_dir) / "elevacao_v.csv"
            pattern_path.write_text(
                "\n".join(
                    [
                        '"Freq [GHz]","Phi [deg]","Theta [deg]","dB10normalize(GainL3X) []"',
                        "0.186,90,-2,-0.0118115213671719",
                        "0.186,90,-1,-0.00218568255865022",
                        "0.186,90,0,0",
                        "0.186,90,1,-0.00525649721008869",
                        "0.186,90,2,-0.0179427147779443",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            angles_deg, magnitude, phase_deg = load_pattern_for_import(pattern_path, "VRP")

            self.assertEqual(len(angles_deg), 1801)
            zero_index = int(np.where(np.isclose(angles_deg, 0.0))[0][0])
            self.assertAlmostEqual(float(magnitude[zero_index]), 1.0, places=6)
            self.assertLess(float(magnitude[zero_index - 10]), 1.0)
            self.assertLess(float(magnitude[zero_index + 10]), 1.0)
            self.assertTrue(np.allclose(phase_deg, 0.0))

    def test_read_pattern_frequency_and_prn_section_import(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pattern_path = Path(temp_dir) / "sample.prn"
            pattern_path.write_text(
                "\n".join(
                    [
                        "NAME TEST",
                        "MAKE EFTX",
                        "FREQUENCY 99.50 MHz",
                        "HORIZONTAL 360",
                        "0\t1.0",
                        "1\t0.9",
                        "2\t0.8",
                        "3\t0.7",
                        "4\t0.6",
                        "5\t0.5",
                        "6\t0.4",
                        "7\t0.3",
                        "8\t0.2",
                        "9\t0.1",
                        "VERTICAL 360",
                        "-4\t0.6",
                        "-3\t0.7",
                        "-2\t0.8",
                        "-1\t0.9",
                        "0\t1.0",
                        "1\t0.9",
                        "2\t0.8",
                        "3\t0.7",
                        "4\t0.6",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertAlmostEqual(read_pattern_frequency(pattern_path), 99.5, places=6)

            hrp_angles, hrp_magnitude, _ = load_pattern_for_import(pattern_path, "HRP")
            vrp_angles, vrp_magnitude, _ = load_pattern_for_import(pattern_path, "VRP")

            hrp_zero_index = int(np.where(np.isclose(hrp_angles, 0.0))[0][0])
            vrp_zero_index = int(np.where(np.isclose(vrp_angles, 0.0))[0][0])
            self.assertAlmostEqual(float(hrp_magnitude[hrp_zero_index]), 1.0, places=6)
            self.assertAlmostEqual(float(vrp_magnitude[vrp_zero_index]), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
