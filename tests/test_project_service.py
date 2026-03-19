import unittest

from app.project_service import compose_panel_excitation, project_to_array_design
from domain import (
    ArrayPanel,
    DesignMetadata,
    FaceExcitation,
    LevelExcitation,
    PatternDefinition,
    Project,
)


class ProjectServiceTests(unittest.TestCase):
    def test_compose_panel_excitation_applies_face_and_level_groups(self):
        panel = ArrayPanel(
            panel_id=1,
            power=2.0,
            phase_deg=30.0,
            level=2,
            face="B",
        )
        horizontal_groups = {"B": FaceExcitation(face="B", phase_deg=10.0, power=0.5)}
        vertical_groups = {2: LevelExcitation(level=2, phase_deg=20.0)}

        effective_power, effective_phase = compose_panel_excitation(
            panel, horizontal_groups, vertical_groups
        )

        self.assertAlmostEqual(effective_power, 1.0)
        self.assertAlmostEqual(effective_phase, 60.0)

    def test_project_to_array_design_converts_geometry_and_pattern_binding(self):
        project = Project(
            metadata=DesignMetadata(channel_frequency_mhz=475.0),
            patterns=[
                PatternDefinition(
                    index=3,
                    mode="Custom",
                    hrp_path="hrp_file.pat",
                    vrp_path="vrp_file.pat",
                )
            ],
            panels=[
                ArrayPanel(
                    panel_id=7,
                    angle_deg=90.0,
                    offset_m=2.0,
                    elevation_m=15.0,
                    azimuth_deg=120.0,
                    power=3.0,
                    phase_deg=45.0,
                    tilt_deg=-1.5,
                    pattern_index=3,
                    level=1,
                    face="A",
                )
            ],
            horizontal_groups={"A": FaceExcitation(face="A", phase_deg=5.0, power=2.0)},
            vertical_groups={1: LevelExcitation(level=1, phase_deg=7.0)},
        )

        array_design = project_to_array_design(project)

        self.assertEqual(array_design.frequency, 475.0)
        self.assertEqual(len(array_design.panels), 1)

        runtime_panel = array_design.panels[0]
        self.assertEqual(runtime_panel.panel_id, 7)
        self.assertAlmostEqual(runtime_panel.x, 2.0, places=6)
        self.assertAlmostEqual(runtime_panel.y, 0.0, places=6)
        self.assertAlmostEqual(runtime_panel.z, 15.0)
        self.assertAlmostEqual(runtime_panel.power, 6.0)
        self.assertAlmostEqual(runtime_panel.phase, 57.0)
        self.assertAlmostEqual(runtime_panel.face_angle, 120.0)
        self.assertAlmostEqual(runtime_panel.tilt, 1.5)
        self.assertEqual(runtime_panel.panel_type_name, "Panel Array_PHP4S")
        self.assertEqual(runtime_panel.hrp_path, "hrp_file.pat")
        self.assertEqual(runtime_panel.vrp_path, "vrp_file.pat")


if __name__ == "__main__":
    unittest.main()
