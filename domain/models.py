from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class LossProfile:
    internal_db: float = 0.5
    polarization_db: float = 3.0
    filter_combiner_db: float = 0.8
    feeder_db: float = 1.2


@dataclass
class DesignMetadata:
    customer: str = ""
    site_name: str = ""
    antenna_model: str = ""
    design_frequency_mhz: float = 539.0
    channel_frequency_mhz: float = 539.0
    polarization: str = "Horizontal"
    signal_type: str = "Digital"
    designer_name: str = ""
    date_created: str = ""
    design_note: str = ""


@dataclass
class SiteConfig:
    tower_type: str = ""
    tower_heading_deg: float = 0.0
    feeder_type: str = ""
    feeder_length_m: float = 0.0
    branch_feeder_length_m: float = 0.0
    transmitter_power_kw: float = 0.0
    antenna_height_m: float = 0.0


@dataclass
class PatternDefinition:
    index: int
    mode: str = "Standard"
    panel_type: str = "Panel Array_PHP4S"
    elevation_spacing_m: float = 1.15
    width_m: float = 0.5
    height_m: float = 1.09
    depth_m: float = 0.22
    hrp_path: str = ""
    vrp_path: str = ""


@dataclass
class FaceExcitation:
    face: str
    phase_deg: float = 0.0
    power: float = 1.0


@dataclass
class LevelExcitation:
    level: int
    phase_deg: float = 0.0


@dataclass
class ArrayPanel:
    panel_id: int
    angle_deg: float = 0.0
    offset_m: float = 0.0
    elevation_m: float = 0.0
    azimuth_deg: float = 0.0
    power: float = 1.0
    phase_deg: float = 0.0
    tilt_deg: float = 0.0
    configuration: int = 0
    pattern_index: int = 1
    level: int = 1
    face: str = "A"
    input_number: int = 1


@dataclass
class Project:
    schema_version: int = 1
    metadata: DesignMetadata = field(default_factory=DesignMetadata)
    site: SiteConfig = field(default_factory=SiteConfig)
    losses: LossProfile = field(default_factory=LossProfile)
    patterns: list[PatternDefinition] = field(default_factory=list)
    panels: list[ArrayPanel] = field(default_factory=list)
    horizontal_groups: dict[str, FaceExcitation] = field(default_factory=dict)
    vertical_groups: dict[int, LevelExcitation] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "metadata": asdict(self.metadata),
            "site": asdict(self.site),
            "losses": asdict(self.losses),
            "patterns": [asdict(pattern) for pattern in self.patterns],
            "panels": [asdict(panel) for panel in self.panels],
            "horizontal_groups": {
                face: asdict(group) for face, group in self.horizontal_groups.items()
            },
            "vertical_groups": {
                str(level): asdict(group)
                for level, group in self.vertical_groups.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        horizontal_groups = {}
        for face, group_data in data.get("horizontal_groups", {}).items():
            payload = dict(group_data)
            payload.setdefault("face", face)
            horizontal_groups[face] = FaceExcitation(**payload)

        vertical_groups = {}
        for level_text, group_data in data.get("vertical_groups", {}).items():
            level = int(level_text)
            payload = dict(group_data)
            payload.setdefault("level", level)
            vertical_groups[level] = LevelExcitation(**payload)

        return cls(
            schema_version=int(data.get("schema_version", 1)),
            metadata=DesignMetadata(**data.get("metadata", {})),
            site=SiteConfig(**data.get("site", {})),
            losses=LossProfile(**data.get("losses", {})),
            patterns=[
                PatternDefinition(**pattern_data)
                for pattern_data in data.get("patterns", [])
            ],
            panels=[ArrayPanel(**panel_data) for panel_data in data.get("panels", [])],
            horizontal_groups=horizontal_groups,
            vertical_groups=vertical_groups,
        )

