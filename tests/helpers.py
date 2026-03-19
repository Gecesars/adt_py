from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARENT_ROOT = PROJECT_ROOT.parent


def find_sample_patterns():
    vrp_candidates = [
        PARENT_ROOT
        / "UnitPattern"
        / "VRP"
        / "Slot Array_VHF-NGS"
        / "Hpol"
        / "VRP 2bay hpol 216_216.pat",
    ]
    hrp_candidates = [
        PARENT_ROOT
        / "UnitPattern"
        / "HRP"
        / "Panel Array_PCP-600"
        / "Hpol"
        / "PCP600_IMUA_HP_475.pat",
    ]

    vrp_file = next((path for path in vrp_candidates if path.exists()), None)
    hrp_file = next((path for path in hrp_candidates if path.exists()), None)

    if vrp_file is None or hrp_file is None:
        missing = []
        if vrp_file is None:
            missing.append("VRP")
        if hrp_file is None:
            missing.append("HRP")
        raise FileNotFoundError(
            "Sample pattern file(s) not found for: "
            + ", ".join(missing)
            + f". Expected parent assets under: {PARENT_ROOT / 'UnitPattern'}"
        )

    return hrp_file, vrp_file

