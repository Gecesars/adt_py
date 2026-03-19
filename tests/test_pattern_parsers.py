import math
import unittest
from pathlib import Path

import numpy as np

from parsers.patterns import read_hrp_pattern, read_vrp_pattern


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


if __name__ == "__main__":
    unittest.main()
