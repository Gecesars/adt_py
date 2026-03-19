import unittest

import numpy as np

from solver.pattern_synthesis import (
    calculate_configuration_phase_deg,
    compute_hrp_cut_directivity_db,
    compute_vrp_cut_directivity_db,
    configure_vertical_pattern,
    extract_hrp_cut,
    extract_vrp_cut,
    find_library_power_ratios,
    get_maximum_field_angles,
    get_vrp_beam_tilt_deg,
)


class PatternConfigurationTests(unittest.TestCase):
    def test_configuration_phase_mapping_matches_recovered_rules(self):
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(45.0, 0, 500.0, 500.0),
            45.0,
        )
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(45.0, 1, 500.0, 500.0),
            -135.0,
        )
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(135.0, 2, 500.0, 500.0),
            135.0,
        )
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(135.0, 3, 500.0, 500.0),
            -45.0,
        )
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(225.0, 4, 500.0, 500.0),
            225.0,
        )
        self.assertAlmostEqual(
            calculate_configuration_phase_deg(225.0, 5, 500.0, 500.0),
            45.0,
        )

    def test_find_library_power_ratios_uses_least_directive_pattern_as_reference(self):
        broad_angles = np.arange(-180.0, 180.0, 1.0)
        broad_mag = np.ones(360)
        narrow_mag = np.zeros(360)
        narrow_mag[150:210] = 1.0
        phase = np.zeros(360)

        ratios = find_library_power_ratios(
            {
                "broad": (broad_angles, broad_mag, phase),
                "narrow": (broad_angles, narrow_mag, phase),
            }
        )

        self.assertAlmostEqual(ratios["broad"], 1.0, places=6)
        self.assertGreater(ratios["narrow"], ratios["broad"])

    def test_vertical_tilt_builds_azimuth_indexed_vrp(self):
        angles = np.linspace(-90.0, 90.0, 181)
        magnitude = np.maximum(np.cos(np.deg2rad(angles)), 0.0)
        phase = np.zeros_like(angles)

        target_angles, tilted = configure_vertical_pattern(
            angles,
            magnitude,
            phase,
            frequency_mhz=500.0,
            z_offset_m=10.0,
            mechanical_tilt_deg=2.0,
            tilt_face_angle_deg=90.0,
            configuration=0,
        )

        self.assertEqual(target_angles.shape[0], 1801)
        self.assertEqual(tilted.shape, (360, 1801))

    def test_cut_extraction_uses_maximum_field_location(self):
        azimuth_angles = np.array([0.0, 90.0, 180.0])
        elevation_angles = np.array([-1.0, 0.0, 1.0])
        magnitude_3d = np.array(
            [
                [0.1, 0.2, 0.1],
                [0.3, 0.4, 0.3],
                [0.5, 1.0, 0.8],
            ]
        )

        az_deg, el_deg, az_index, el_index = get_maximum_field_angles(
            magnitude_3d, azimuth_angles, elevation_angles
        )
        hrp_angles, hrp_cut, hrp_el = extract_hrp_cut(
            magnitude_3d,
            azimuth_angles,
            elevation_angles,
            elevation_index=el_index,
        )
        vrp_angles, vrp_cut, vrp_az = extract_vrp_cut(
            magnitude_3d,
            azimuth_angles,
            elevation_angles,
            azimuth_index=az_index,
        )

        self.assertEqual(az_deg, 180.0)
        self.assertEqual(el_deg, 0.0)
        self.assertEqual(hrp_el, 0.0)
        self.assertEqual(vrp_az, 180.0)
        np.testing.assert_allclose(hrp_angles, azimuth_angles)
        np.testing.assert_allclose(vrp_angles, elevation_angles)
        np.testing.assert_allclose(hrp_cut, np.array([0.2, 0.4, 1.0]))
        np.testing.assert_allclose(vrp_cut, np.array([0.5, 1.0, 0.8]))

    def test_peak_angle_selection_matches_original_average_of_maxima_rule(self):
        azimuth_angles = np.array([-174.0, -84.0, 6.0, 96.0])
        elevation_angles = np.array([-1.0, 0.0, 1.0])
        magnitude_3d = np.zeros((4, 3))
        magnitude_3d[:, 1] = 1.0

        az_deg, el_deg, az_index, el_index = get_maximum_field_angles(
            magnitude_3d, azimuth_angles, elevation_angles
        )

        self.assertEqual(az_deg, -84.0)
        self.assertEqual(el_deg, 0.0)
        self.assertEqual(az_index, 1)
        self.assertEqual(el_index, 1)

    def test_cut_directivity_helpers_match_recovered_formulas(self):
        hrp_cut = np.array([0.5, 1.0, 0.5])
        peak_hrp_cut = np.array([0.5, 1.0, 0.5])
        hrp_dir = compute_hrp_cut_directivity_db(hrp_cut, peak_hrp_cut)
        self.assertAlmostEqual(hrp_dir, 10.0 * np.log10(3.0 / 1.5), places=6)

        vrp_angles = np.array([-90.0, 0.0, 90.0])
        vrp_cut = np.array([0.0, 1.0, 0.0])
        peak_vrp_cut = np.array([0.0, 1.0, 0.0])
        vrp_dir = compute_vrp_cut_directivity_db(vrp_angles, vrp_cut, peak_vrp_cut)
        expected = 10.0 * np.log10(3.0 * 2.0 / np.pi / 1.64)
        self.assertAlmostEqual(vrp_dir, expected, places=6)

    def test_vrp_beam_tilt_averages_all_maxima_like_original(self):
        vrp_angles = np.array([-5.0, 0.0, 5.0, 10.0])
        vrp_cut = np.array([0.5, 1.0, 1.0, 0.25])

        tilt = get_vrp_beam_tilt_deg(vrp_angles, vrp_cut)

        self.assertAlmostEqual(tilt, 2.5, places=6)


if __name__ == "__main__":
    unittest.main()
