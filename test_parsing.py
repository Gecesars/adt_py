import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent
PARENT_ROOT = PROJECT_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from models.antenna import AntennaPanel, ArrayDesign
from parsers.patterns import read_hrp_pattern, read_vrp_pattern
from solver.system_metrics import calculate_system_metrics


def find_sample_patterns():
    vrp_candidates = [
        PARENT_ROOT / "UnitPattern" / "VRP" / "Slot Array_VHF-NGS" / "Hpol" / "VRP 2bay hpol 216_216.pat",
    ]
    hrp_candidates = [
        PARENT_ROOT / "UnitPattern" / "HRP" / "Panel Array_PCP-600" / "Hpol" / "PCP600_IMUA_HP_475.pat",
    ]

    vrp_file = next((path for path in vrp_candidates if path.exists()), None)
    hrp_file = next((path for path in hrp_candidates if path.exists()), None)

    if vrp_file is None or hrp_file is None:
        missing = []
        if vrp_file is None:
            missing.append("VRP")
        if hrp_file is None:
            missing.append("HRP")
        names = ", ".join(missing)
        raise FileNotFoundError(
            f"Sample pattern file(s) not found for: {names}. "
            f"Expected parent assets under: {PARENT_ROOT / 'UnitPattern'}"
        )

    return hrp_file, vrp_file


def main():
    hrp_file, vrp_file = find_sample_patterns()

    print(f"Testing reading VRP: {vrp_file.name}")
    angles, mags, phases = read_vrp_pattern(str(vrp_file))
    print(f"VRP Max Mag: {np.max(mags):.4f}, Points: {len(angles)}")

    print(f"Testing reading HRP: {hrp_file.name}")
    angles_h, mags_h, phases_h = read_hrp_pattern(str(hrp_file))
    print(f"HRP Max Mag: {np.max(mags_h):.4f}, Points: {len(angles_h)}")

    print("Testing array integration...")
    array = ArrayDesign()
    array.frequency = 475.0

    p1 = AntennaPanel(1, "Standard")
    p1.hrp_path = str(hrp_file)
    p1.vrp_path = str(vrp_file)
    p1.power = 1.0
    p1.y = 0.5
    p1.phase = 0.0
    p1.face_angle = 0.0

    p2 = AntennaPanel(2, "Standard")
    p2.hrp_path = str(hrp_file)
    p2.vrp_path = str(vrp_file)
    p2.power = 1.0
    p2.y = -0.5
    p2.phase = 90.0
    p2.face_angle = 180.0

    array.add_panel(p1)
    array.add_panel(p2)

    results, mag_3d, az_angles, el_angles = calculate_system_metrics(array)

    print("Synthesis Complete!")
    print("Results Dict:")
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
