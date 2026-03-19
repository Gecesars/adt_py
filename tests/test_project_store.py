import tempfile
import unittest
from pathlib import Path

from domain import (
    ArrayPanel,
    DesignMetadata,
    FaceExcitation,
    LevelExcitation,
    LossProfile,
    PatternDefinition,
    Project,
    SiteConfig,
)
from infra.project_store import load_project, save_project


class ProjectStoreTests(unittest.TestCase):
    def test_project_round_trip_preserves_structure(self):
        project = Project(
            metadata=DesignMetadata(
                customer="RFS",
                site_name="Test Site",
                antenna_model="ADT-PY",
                design_frequency_mhz=470.0,
                channel_frequency_mhz=475.0,
                designer_name="Codex",
                date_created="2026-03-18",
            ),
            site=SiteConfig(
                feeder_type="7/8 coax",
                feeder_length_m=42.0,
                transmitter_power_kw=12.5,
            ),
            losses=LossProfile(
                internal_db=0.4,
                polarization_db=2.8,
                filter_combiner_db=0.7,
                feeder_db=1.1,
            ),
            patterns=[
                PatternDefinition(
                    index=1,
                    mode="Custom",
                    panel_type="Panel Array_PCP-600",
                    hrp_path="hrp.pat",
                    vrp_path="vrp.pat",
                )
            ],
            panels=[
                ArrayPanel(
                    panel_id=1,
                    angle_deg=10.0,
                    offset_m=1.2,
                    elevation_m=50.0,
                    azimuth_deg=0.0,
                    power=1.0,
                    phase_deg=0.0,
                    pattern_index=1,
                    level=1,
                    face="A",
                    input_number=1,
                )
            ],
            horizontal_groups={"A": FaceExcitation(face="A", phase_deg=5.0, power=0.8)},
            vertical_groups={1: LevelExcitation(level=1, phase_deg=12.0)},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project.adpy.json"
            save_project(path, project)
            loaded = load_project(path)

        self.assertEqual(loaded.to_dict(), project.to_dict())


if __name__ == "__main__":
    unittest.main()

