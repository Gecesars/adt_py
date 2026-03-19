import unittest

from app.project_service import calculate_project_metrics
from domain import ArrayPanel, DesignMetadata, PatternDefinition, Project
from tests.helpers import find_sample_patterns


class SolverRegressionTests(unittest.TestCase):
    def test_two_panel_sample_design_produces_stable_metrics(self):
        hrp_file, vrp_file = find_sample_patterns()
        project = Project(
            metadata=DesignMetadata(
                design_frequency_mhz=475.0,
                channel_frequency_mhz=475.0,
            ),
            patterns=[
                PatternDefinition(
                    index=1,
                    mode="Standard",
                    panel_type="Panel Array_PCP-600",
                    hrp_path=str(hrp_file),
                    vrp_path=str(vrp_file),
                )
            ],
            panels=[
                ArrayPanel(
                    panel_id=1,
                    angle_deg=0.0,
                    offset_m=0.5,
                    azimuth_deg=0.0,
                    power=1.0,
                    phase_deg=0.0,
                    pattern_index=1,
                    level=1,
                    face="A",
                ),
                ArrayPanel(
                    panel_id=2,
                    angle_deg=180.0,
                    offset_m=0.5,
                    azimuth_deg=180.0,
                    power=1.0,
                    phase_deg=90.0,
                    pattern_index=1,
                    level=1,
                    face="A",
                ),
            ],
        )

        results, mag_3d, az_angles, el_angles = calculate_project_metrics(project)

        self.assertEqual(mag_3d.shape, (360, 1801))
        self.assertEqual(len(az_angles), 360)
        self.assertEqual(len(el_angles), 1801)
        self.assertAlmostEqual(float(results["3D Directivity (dBd)"]), 9.31, delta=0.25)
        self.assertAlmostEqual(float(results["ERP (kW)"]), 4.81, delta=0.25)


if __name__ == "__main__":
    unittest.main()
