from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class CableRatingPoint:
    name: str
    frequency_mhz: float
    attenuation_db_per_100m: float
    attenuation_db_per_100ft: float
    avpower_kw: float
    velocity_factor: float
    peak_power_kw: float
    peak_voltage_kv: float
    impedance_ohm: float
    customised: bool


class CableCatalog:
    def __init__(self, xml_path: str | Path | None = None):
        if xml_path is None:
            xml_path = (
                Path(__file__).resolve().parents[2] / "Rating" / "CableRating.xml"
            )
        self.xml_path = Path(xml_path)
        self.points = self._load_points()
        self._feeder_names = self._build_feeder_names()

    def _load_points(self) -> list[CableRatingPoint]:
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        points: list[CableRatingPoint] = []
        for cable in root.findall("Cable"):
            points.append(
                CableRatingPoint(
                    name=(cable.findtext("Name", default="") or "").strip(),
                    frequency_mhz=float(cable.findtext("Frequency", default="0") or 0.0),
                    attenuation_db_per_100m=float(
                        cable.findtext("AttenuationdBm", default="0") or 0.0
                    ),
                    attenuation_db_per_100ft=float(
                        cable.findtext("AttenuationdBft", default="0") or 0.0
                    ),
                    avpower_kw=float(cable.findtext("Avpower", default="0") or 0.0),
                    velocity_factor=float(
                        cable.findtext("VelocityFactor", default="0") or 0.0
                    ),
                    peak_power_kw=float(
                        cable.findtext("PeakPower", default="0") or 0.0
                    ),
                    peak_voltage_kv=float(cable.findtext("PeakVol", default="0") or 0.0)
                    / 1000.0,
                    impedance_ohm=float(cable.findtext("Impedance", default="0") or 0.0),
                    customised=(cable.findtext("Customerised", default="0") or "0") == "1",
                )
            )
        return points

    def _build_feeder_names(self) -> list[str]:
        seen: set[str] = set()
        names: list[str] = []
        for point in self.points:
            if point.name and point.name not in seen:
                names.append(point.name)
                seen.add(point.name)
        return names

    @property
    def feeder_names(self) -> list[str]:
        return list(self._feeder_names)

    @property
    def default_feeder_name(self) -> str:
        if "HCA38-50" in self._feeder_names:
            return "HCA38-50"
        return self._feeder_names[0] if self._feeder_names else ""

    def get_feeder_index(self, feeder_name: str) -> int:
        try:
            return self._feeder_names.index(feeder_name)
        except ValueError:
            return 0

    def _find_attenuation_per_m_sqrt_f(self, feeder_name: str, frequency_mhz: float) -> float:
        nearest_distance = float("inf")
        nearest_attenuation = 0.0
        for point in self.points:
            if point.name != feeder_name:
                continue
            distance = abs(point.frequency_mhz - frequency_mhz)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_attenuation = point.attenuation_db_per_100m

        # The recovered ADT code checks the global file frequency range rather than
        # filtering by cable name. We mirror that behavior here.
        for point in self.points:
            if point.frequency_mhz >= frequency_mhz:
                return nearest_attenuation / math.sqrt(frequency_mhz)
        return 0.0

    def _find_invert_avpower_sqrt_f(self, feeder_name: str, frequency_mhz: float) -> float:
        nearest_distance = float("inf")
        nearest_avpower = 0.0
        for point in self.points:
            if point.name != feeder_name:
                continue
            distance = abs(point.frequency_mhz - frequency_mhz)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_avpower = point.avpower_kw

        for point in self.points:
            if point.frequency_mhz >= frequency_mhz:
                if nearest_avpower <= 0 or frequency_mhz <= 0:
                    return 0.0
                return math.sqrt(frequency_mhz) / nearest_avpower / frequency_mhz
        return 0.0

    def calculate_feeder_loss_db(
        self,
        feeder_name: str,
        feeder_length_m: float,
        channel_frequency_mhz: float,
    ) -> float:
        feeder_name = (feeder_name or "").strip()
        if not feeder_name or feeder_length_m <= 0 or channel_frequency_mhz <= 0:
            return 0.0

        attenuation = self._find_attenuation_per_m_sqrt_f(
            feeder_name,
            channel_frequency_mhz,
        )
        invert_avpower = self._find_invert_avpower_sqrt_f(
            feeder_name,
            channel_frequency_mhz,
        )
        if attenuation == 0.0 or invert_avpower == 0.0:
            raise ValueError(
                "The antenna operating frequency is beyond the cable operating frequency range"
            )

        return attenuation * math.sqrt(channel_frequency_mhz) * feeder_length_m / 100.0
