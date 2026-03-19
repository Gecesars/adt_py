from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class PredefinedPanelEntry:
    display_name: str
    panel_type: str
    base_panel_type: str
    band: str
    polarization: str
    width_m: float
    height_m: float
    depth_m: float
    elevation_spacing_m: float
    elevation_unit: str
    hrp_path: str
    vrp_path: str
    half_power_vrp_angle_deg: float | None = None


@dataclass(frozen=True)
class _PanelSpec:
    panel_type: str
    band: str
    polarization: str
    width_m: float
    height_m: float
    depth_m: float
    elevation_spacing_m: float
    elevation_unit: str


def normalize_catalog_panel_type(panel_type: str) -> str:
    normalized = (panel_type or "").strip()
    if normalized.endswith("_Hpol") or normalized.endswith("_Vpol"):
        normalized = normalized[:-5]

    parts = normalized.split("_")
    if len(parts) > 2:
        normalized = "_".join(parts[:2])
    return normalized


def lookup_generated_vrp_half_power_angle(
    panel_type: str,
    frequency_mhz: float,
) -> float | None:
    normalized = normalize_catalog_panel_type(panel_type)
    num = (frequency_mhz - 470.0) / 50.0 + 1.0

    if normalized in {
        "Panel Array_PHP4S",
        "Panel Array_PHP5S",
        "Panel Array_PHPXS",
        "Panel Array_PVP",
        "Panel Array_PEPL",
        "Panel Array_PEPSIL",
        "Panel Array_PEP",
        "Panel Array_PCP-500",
        "Panel Array_PCP-600",
        "Panel Array_PSP",
    }:
        return -0.0122 * num * num * num + 0.2906 * num * num - 2.6561 * num + 18.985
    if normalized == "SDV":
        return 38.0
    if normalized in {
        "Dipole Array_UD-LP-470650",
        "Dipole Array_UD-LP-520720",
        "Dipole Array_UD-LP-620860",
        "Dipole Array_UD-HP-470650",
        "Dipole Array_UD-HP-620860",
        "Dipole Array_618",
        "Panel Array_904VP",
        "Panel Array_904CPX",
        "Panel Array_904SP",
        "Panel Array_903CP",
        "Panel Array_903VP",
        "CPF2500",
        "Dipole Array_828-8898",
        "Dipole Array_828-94104",
        "Dipole Array_828-98108",
        "Dipole Array_828HP",
        "Dipole Array_828DA-8898",
        "Dipole Array_828DA-94104",
        "Dipole Array_828DA-98108",
        "Dipole Array_828HPDA",
        "Dipole Array_818",
        "Panel Array_902CP",
    }:
        return 39.0
    if normalized in {"Slot Array_RD-470536", "Slot Array_EPR-470536"}:
        return -0.06333 * frequency_mhz + 44.65667
    if normalized in {"Slot Array_RD-488608", "Slot Array_EPR-488608"}:
        return -0.03586 * frequency_mhz + 33.85431
    if normalized in {"Slot Array_RD-578704", "Slot Array_EPR-578704"}:
        return -0.02291 * frequency_mhz + 27.56458
    if normalized in {"Slot Array_RD-662806", "Slot Array_EPR-662806"}:
        return -0.01994 * frequency_mhz + 27.63912
    if normalized == "Slot Array_RD-470578":
        return -0.03583 * frequency_mhz + 33.84065
    if normalized == "Slot Array_EPR-470578":
        return -0.0638 * frequency_mhz + 44.906
    if normalized == "Slot Array_RD-500620":
        return -0.03583 * frequency_mhz + 33.84065
    if normalized == "Slot Array_EPR-500620":
        return -0.0358 * frequency_mhz + 33.847
    if normalized == "Slot Array_LPR-488608":
        return -0.0358 * frequency_mhz + 33.847
    if normalized == "Slot Array_LPR-578704":
        return -0.0229 * frequency_mhz + 27.565
    if normalized == "Slot Array_LPR-622806":
        return -0.02 * frequency_mhz + 27.68
    if normalized in {
        "Superturnstile_STA-LLP",
        "Superturnstile_STA-LMP",
        "Superturnstile_STA-MP",
        "Superturnstile_STA-HP",
    }:
        return (
            -6.14e-08 * frequency_mhz * frequency_mhz * frequency_mhz
            + 0.0001341252 * frequency_mhz * frequency_mhz
            - 0.11 * frequency_mhz
            + 45.3774816899
        )
    if normalized in {"Panel Array_657-174202", "Panel Array_657-202230"}:
        return 29.0
    return None


class OriginalAdtCatalog:
    def __init__(self, root_path: str | Path | None = None):
        if root_path is None:
            root_path = Path(__file__).resolve().parents[1] / "assets" / "original_adt"
        self.root_path = Path(root_path)
        self.rating_xml_path = self.root_path / "Rating" / "PanelMechInfo.xml"
        self.unit_pattern_root = self.root_path / "UnitPattern"
        self._panel_specs = self._load_panel_specs()

    def _load_panel_specs(self) -> list[_PanelSpec]:
        tree = ET.parse(self.rating_xml_path)
        specs = []
        for panel in tree.getroot().findall("Panel"):
            specs.append(
                _PanelSpec(
                    panel_type=panel.findtext("Type", default=""),
                    band=panel.findtext("Band", default=""),
                    polarization=panel.findtext("Polarisation", default=""),
                    width_m=float(panel.findtext("Width", default="0")),
                    height_m=float(panel.findtext("Height", default="0")),
                    depth_m=float(panel.findtext("Depth", default="0")),
                    elevation_spacing_m=float(
                        panel.findtext("ElevationSpace", default="0")
                    ),
                    elevation_unit=panel.findtext("ElevationUnit", default=""),
                )
            )
        return specs

    def infer_band(self, frequency_mhz: float) -> str:
        if frequency_mhz < 120.0:
            return "FM"
        if frequency_mhz < 300.0:
            return "VHF"
        return "UHF"

    def _normalize_requested_polarization(self, requested: str) -> str:
        requested = (requested or "").strip()
        if requested == "Cross Polar":
            return "Mixed"
        return requested or "Horizontal"

    def _matches_requested_polarization(self, panel_pol: str, requested_pol: str) -> bool:
        requested = self._normalize_requested_polarization(requested_pol)
        panel_pol = (panel_pol or "").strip()

        if requested in {"Horizontal", "Vertical"}:
            return panel_pol == requested or panel_pol in {"Elliptical", "Circular", "Slant"}
        if requested in {"Elliptical", "Circular"}:
            return panel_pol in {"Elliptical", "Circular"}
        if requested == "Mixed":
            return panel_pol in {"Elliptical", "Circular", "Slant"}
        return panel_pol == requested

    def list_standard_panels(self, band: str, polarization: str) -> list[str]:
        return [
            entry.display_name
            for entry in self.get_standard_panel_entries_by_band(band, polarization, 539.0)
        ]

    def get_standard_panel_entries(
        self,
        frequency_mhz: float,
        polarization: str,
    ) -> list[PredefinedPanelEntry]:
        band = self.infer_band(frequency_mhz)
        return self.get_standard_panel_entries_by_band(band, polarization, frequency_mhz)

    def get_standard_panel_entries_by_band(
        self,
        band: str,
        polarization: str,
        frequency_mhz: float,
    ) -> list[PredefinedPanelEntry]:
        entries: list[PredefinedPanelEntry] = []
        for spec in self._panel_specs:
            if spec.band != band:
                continue
            if not self._matches_requested_polarization(spec.polarization, polarization):
                continue
            entries.extend(self._build_entries_for_spec(spec, polarization, frequency_mhz))

        entries.sort(key=lambda entry: entry.display_name)
        return entries

    def resolve_entry(
        self,
        display_name: str,
        frequency_mhz: float,
        polarization: str,
    ) -> PredefinedPanelEntry | None:
        for entry in self.get_standard_panel_entries(frequency_mhz, polarization):
            if entry.display_name == display_name or entry.panel_type == display_name:
                return entry
        return None

    def _build_entries_for_spec(
        self,
        spec: _PanelSpec,
        requested_pol: str,
        frequency_mhz: float,
    ) -> list[PredefinedPanelEntry]:
        hrp_root = self.unit_pattern_root / "HRP" / spec.panel_type
        vrp_root = self.unit_pattern_root / "VRP" / spec.panel_type
        if not hrp_root.exists():
            return []

        requested = self._normalize_requested_polarization(requested_pol)
        entries = []

        if any(token in spec.panel_type for token in ("RD", "LPR", "SBB-HP")):
            for subdir in self._iter_dirs(hrp_root):
                entries.append(
                    self._create_entry(
                        spec,
                        f"{spec.panel_type}_{subdir.name}",
                        subdir,
                        vrp_root,
                        frequency_mhz,
                    )
                )
            return entries

        if any(token in spec.panel_type for token in ("EPR", "SBB-EP", "NGS")):
            if requested in {"Horizontal", "Circular", "Elliptical", "Mixed"}:
                for subdir in self._iter_dirs(hrp_root / "Hpol"):
                    entries.append(
                        self._create_entry(
                            spec,
                            f"{spec.panel_type}_{subdir.name}_Hpol",
                            subdir,
                            vrp_root / "Hpol",
                            frequency_mhz,
                        )
                    )
            if requested in {"Vertical", "Circular", "Elliptical", "Mixed"}:
                for subdir in self._iter_dirs(hrp_root / "Vpol"):
                    entries.append(
                        self._create_entry(
                            spec,
                            f"{spec.panel_type}_{subdir.name}_Vpol",
                            subdir,
                            vrp_root / "Vpol",
                            frequency_mhz,
                        )
                    )
            return entries

        if (hrp_root / "Hpol").exists() and requested in {
            "Horizontal",
            "Circular",
            "Elliptical",
            "Mixed",
        }:
            entries.append(
                self._create_entry(
                    spec,
                    f"{spec.panel_type}_Hpol",
                    hrp_root / "Hpol",
                    vrp_root / "Hpol",
                    frequency_mhz,
                )
            )
        if (hrp_root / "Vpol").exists() and requested in {
            "Vertical",
            "Circular",
            "Elliptical",
            "Mixed",
        }:
            entries.append(
                self._create_entry(
                    spec,
                    f"{spec.panel_type}_Vpol",
                    hrp_root / "Vpol",
                    vrp_root / "Vpol",
                    frequency_mhz,
                )
            )
        if not (hrp_root / "Hpol").exists() and not (hrp_root / "Vpol").exists():
            entries.append(
                self._create_entry(
                    spec,
                    spec.panel_type,
                    hrp_root,
                    vrp_root,
                    frequency_mhz,
                )
            )

        return entries

    def _create_entry(
        self,
        spec: _PanelSpec,
        display_name: str,
        hrp_dir: Path,
        vrp_dir: Path,
        frequency_mhz: float,
    ) -> PredefinedPanelEntry:
        hrp_path = self._select_nearest_pattern_file(hrp_dir, {".pat", ".hup"}, frequency_mhz)
        vrp_path = self._select_nearest_pattern_file(vrp_dir, {".pat", ".vup"}, frequency_mhz)
        resolved_panel_type = display_name
        half_power_vrp_angle_deg = None
        if not vrp_path:
            half_power_vrp_angle_deg = lookup_generated_vrp_half_power_angle(
                resolved_panel_type,
                frequency_mhz,
            )
        return PredefinedPanelEntry(
            display_name=display_name,
            panel_type=resolved_panel_type,
            base_panel_type=spec.panel_type,
            band=spec.band,
            polarization=spec.polarization,
            width_m=spec.width_m,
            height_m=spec.height_m,
            depth_m=spec.depth_m,
            elevation_spacing_m=spec.elevation_spacing_m,
            elevation_unit=spec.elevation_unit,
            hrp_path=str(hrp_path) if hrp_path else "",
            vrp_path=str(vrp_path) if vrp_path else "",
            half_power_vrp_angle_deg=half_power_vrp_angle_deg,
        )

    def _iter_dirs(self, path: Path) -> list[Path]:
        if not path.exists():
            return []
        return sorted([item for item in path.iterdir() if item.is_dir()], key=lambda p: p.name)

    def _select_nearest_pattern_file(
        self,
        directory: Path,
        extensions: set[str],
        frequency_mhz: float,
    ) -> Path | None:
        if not directory.exists():
            return None

        files = sorted(
            [
                item
                for item in directory.iterdir()
                if item.is_file() and item.suffix.lower() in extensions
            ],
            key=lambda p: p.name,
        )
        if not files:
            return None

        return min(
            files,
            key=lambda path: abs(frequency_mhz - self._extract_pattern_frequency(path.stem)),
        )

    def _extract_pattern_frequency(self, pattern_name: str) -> float:
        match = re.search(r"(\d{2,5})$", pattern_name)
        if not match:
            return 0.0
        return float(match.group(1))
