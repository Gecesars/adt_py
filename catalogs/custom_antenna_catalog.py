from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from catalogs.original_adt_catalog import PredefinedPanelEntry
from parsers.patterns import import_pattern_to_standard, write_standard_pattern
from solver.pattern_synthesis import generate_synthetic_vrp_pattern


@dataclass(frozen=True)
class CustomAntennaDefinition:
    display_name: str
    frequency_mhz: float
    band: str
    polarization: str
    width_m: float
    height_m: float
    depth_m: float
    elevation_spacing_m: float
    elevation_unit: str
    hrp_source_path: str
    vrp_source_path: str = ""
    synthetic_vrp_half_power_angle_deg: float | None = None


def _safe_panel_slug(text: str) -> str:
    cleaned = re.sub(r"[^\w .-]+", "_", (text or "").strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("._")
    return cleaned or "Custom_Antenna"


class CustomAntennaCatalog:
    def __init__(self, root_path: str | Path | None = None):
        if root_path is None:
            root_path = Path(__file__).resolve().parents[1] / "assets" / "original_adt"
        self.root_path = Path(root_path)
        self.rating_dir = self.root_path / "Rating"
        self.hrp_root = self.root_path / "UnitPattern" / "HRP"
        self.vrp_root = self.root_path / "UnitPattern" / "VRP"
        self.xml_path = self.rating_dir / "antenas_perso.xml"
        self._ensure_storage()

    def _ensure_storage(self):
        self.rating_dir.mkdir(parents=True, exist_ok=True)
        self.hrp_root.mkdir(parents=True, exist_ok=True)
        self.vrp_root.mkdir(parents=True, exist_ok=True)
        if self.xml_path.exists():
            return
        root = ET.Element("CustomPanels")
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ")
        except AttributeError:
            pass
        tree.write(self.xml_path, encoding="utf-8", xml_declaration=True)

    def _load_root(self):
        self._ensure_storage()
        tree = ET.parse(self.xml_path)
        return tree, tree.getroot()

    def _matches_requested_polarization(self, panel_pol: str, requested_pol: str) -> bool:
        requested = (requested_pol or "").strip() or "Horizontal"
        panel_pol = (panel_pol or "").strip()
        if requested == "Cross Polar":
            requested = "Mixed"

        if requested in {"Horizontal", "Vertical"}:
            return panel_pol == requested or panel_pol in {"Elliptical", "Circular", "Slant"}
        if requested in {"Elliptical", "Circular"}:
            return panel_pol in {"Elliptical", "Circular"}
        if requested == "Mixed":
            return panel_pol in {"Elliptical", "Circular", "Slant"}
        return panel_pol == requested

    def get_standard_panel_entries(self, frequency_mhz: float, polarization: str) -> list[PredefinedPanelEntry]:
        tree, root = self._load_root()
        _ = tree
        entries: list[PredefinedPanelEntry] = []
        panels = list(root.findall("Panel"))
        for panel in reversed(panels):
            display_name = panel.findtext("DisplayName", default="") or panel.findtext("Type", default="")
            panel_type = panel.findtext("Type", default=display_name)
            hrp_rel = panel.findtext("HRPPath", default="")
            vrp_rel = panel.findtext("VRPPath", default="")
            half_power_text = panel.findtext("HalfPowerVRPAngle", default="")
            entries.append(
                PredefinedPanelEntry(
                    display_name=display_name,
                    panel_type=panel_type,
                    base_panel_type=panel_type,
                    band=panel.findtext("Band", default="UHF"),
                    polarization=panel.findtext("Polarisation", default="Horizontal"),
                    width_m=float(panel.findtext("Width", default="0")),
                    height_m=float(panel.findtext("Height", default="0")),
                    depth_m=float(panel.findtext("Depth", default="0")),
                    elevation_spacing_m=float(panel.findtext("ElevationSpace", default="0")),
                    elevation_unit=panel.findtext("ElevationUnit", default="One Panel"),
                    hrp_path=str(self.root_path / hrp_rel) if hrp_rel else "",
                    vrp_path=str(self.root_path / vrp_rel) if vrp_rel else "",
                    half_power_vrp_angle_deg=float(half_power_text) if half_power_text.strip() else None,
                )
            )
        entries.sort(key=lambda entry: entry.display_name.lower())
        return entries

    def save_custom_antenna(self, definition: CustomAntennaDefinition) -> PredefinedPanelEntry:
        tree, root = self._load_root()

        panel_slug = _safe_panel_slug(definition.display_name)
        frequency_tag = str(int(round(float(definition.frequency_mhz))))
        hrp_dir = self.hrp_root / panel_slug
        vrp_dir = self.vrp_root / panel_slug
        hrp_dir.mkdir(parents=True, exist_ok=True)
        vrp_dir.mkdir(parents=True, exist_ok=True)

        hrp_filename = f"{panel_slug}_{frequency_tag}.pat"
        vrp_filename = f"{panel_slug}_{frequency_tag}.vup"
        hrp_target = hrp_dir / hrp_filename
        vrp_target = vrp_dir / vrp_filename

        import_pattern_to_standard(
            definition.hrp_source_path,
            hrp_target,
            "HRP",
            definition.frequency_mhz,
        )

        half_power_vrp_angle_deg = None
        if definition.vrp_source_path:
            import_pattern_to_standard(
                definition.vrp_source_path,
                vrp_target,
                "VRP",
                definition.frequency_mhz,
            )
        elif definition.synthetic_vrp_half_power_angle_deg:
            half_power_vrp_angle_deg = float(definition.synthetic_vrp_half_power_angle_deg)
            vrp_angles, vrp_mag, vrp_phase = generate_synthetic_vrp_pattern(
                half_power_vrp_angle_deg
            )
            write_standard_pattern(
                vrp_target,
                vrp_angles,
                vrp_mag,
                vrp_phase,
                definition.frequency_mhz,
                title="Generated",
                engineer="EFTX",
            )
        else:
            raise ValueError("A custom antenna needs a VRP file or a synthetic VRP angle.")

        existing = None
        for panel in root.findall("Panel"):
            if panel.findtext("Type", default="") == definition.display_name:
                existing = panel
                break
        if existing is None:
            existing = ET.SubElement(root, "Panel")

        values = {
            "DisplayName": definition.display_name,
            "Type": definition.display_name,
            "Band": definition.band,
            "Polarisation": definition.polarization,
            "Width": f"{definition.width_m:g}",
            "Height": f"{definition.height_m:g}",
            "Depth": f"{definition.depth_m:g}",
            "ElevationSpace": f"{definition.elevation_spacing_m:g}",
            "ElevationUnit": definition.elevation_unit,
            "ReferenceFrequencyMHz": f"{definition.frequency_mhz:g}",
            "HRPPath": str(Path("UnitPattern") / "HRP" / panel_slug / hrp_filename),
            "VRPPath": str(Path("UnitPattern") / "VRP" / panel_slug / vrp_filename),
            "HalfPowerVRPAngle": f"{half_power_vrp_angle_deg:g}" if half_power_vrp_angle_deg is not None else "",
        }

        for tag_name, tag_value in values.items():
            child = existing.find(tag_name)
            if child is None:
                child = ET.SubElement(existing, tag_name)
            child.text = tag_value

        try:
            ET.indent(tree, space="  ")
        except AttributeError:
            pass
        tree.write(self.xml_path, encoding="utf-8", xml_declaration=True)

        return PredefinedPanelEntry(
            display_name=definition.display_name,
            panel_type=definition.display_name,
            base_panel_type=definition.display_name,
            band=definition.band,
            polarization=definition.polarization,
            width_m=definition.width_m,
            height_m=definition.height_m,
            depth_m=definition.depth_m,
            elevation_spacing_m=definition.elevation_spacing_m,
            elevation_unit=definition.elevation_unit,
            hrp_path=str(hrp_target),
            vrp_path=str(vrp_target),
            half_power_vrp_angle_deg=half_power_vrp_angle_deg,
        )
