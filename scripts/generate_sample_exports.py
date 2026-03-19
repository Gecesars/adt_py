from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtWidgets import QApplication

from exports.pattern_exporters import export_to_format
from main import ADTMainWindow


EXPORT_TARGETS = {
    "HRP PAT": "hrp.pat",
    "VRP PAT": "vrp.pat",
    "HRP Text": "hrp.txt",
    "VRP Text": "vrp.txt",
    "HRP CSV": "hrp.csv",
    "VRP CSV": "vrp.csv",
    "HRP V-Soft": "hrp.vep",
    "VRP V-Soft": "vrp.vep",
    "HRP ATDI": "hrp.H_DIA.DIA",
    "VRP ATDI": "vrp.V_DIA.DIA",
    "3D ATDI": "pattern3d.csv",
    "3D Text": "pattern.3dp",
    "NGW3D": "pattern.ng3dant",
    "PRN": "pattern.prn",
    "EDX": "pattern.ProgiraEDX.pat",
    "Complex EDX": "pattern_complex.ProgiraEDX.pat",
    "Directivity": "pattern.dir",
    "HRP JPEG": "hrp.jpg",
    "VRP JPEG": "vrp.jpg",
    "Layout JPEG": "layout.jpg",
    "Summary PDF": "summary.pdf",
    "Panel PDF": "panels.pdf",
    "All PDF": "all.pdf",
    "Video": "vrp_animation.avi",
}


def _write_manifest(output_dir: Path, context) -> Path:
    metadata = context.project.metadata if context.project is not None else None
    manifest = {
        "case_name": "default_case_4face_4level",
        "generated_from": "scripts/generate_sample_exports.py",
        "export_count": len(EXPORT_TARGETS),
        "geometry": {
            "faces_per_level": 4,
            "panel_offset_m": 0.34,
            "first_panel_heading_deg": 0.0,
            "levels": 4,
            "vertical_spacing_m": 1.15,
            "alternate_levels_cogged": False,
        },
        "project_metadata": {
            "customer": metadata.customer if metadata is not None else "",
            "site_name": metadata.site_name if metadata is not None else "",
            "antenna_model": metadata.antenna_model if metadata is not None else "",
            "design_frequency_mhz": metadata.design_frequency_mhz if metadata is not None else 0.0,
            "channel_frequency_mhz": metadata.channel_frequency_mhz if metadata is not None else 0.0,
            "polarization": metadata.polarization if metadata is not None else "",
        },
        "metrics": {
            key: value
            for key, value in (context.metrics or {}).items()
            if not str(key).startswith("_")
        },
        "files": [
            {"format": format_name, "filename": filename}
            for format_name, filename in EXPORT_TARGETS.items()
        ],
    }
    target = output_dir / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def generate_sample_exports(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    window = ADTMainWindow()
    window.show()
    app.processEvents()

    window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
    window.on_calculate_clicked()
    app.processEvents()

    context = window._build_export_context()

    generated_paths: list[Path] = []
    for format_name, filename in EXPORT_TARGETS.items():
        target = output_dir / filename
        export_to_format(format_name, target, context)
        generated_paths.append(target)

    generated_paths.append(_write_manifest(output_dir, context))

    file_list = "\n".join(path.name for path in sorted(generated_paths))
    (output_dir / "generated_files.txt").write_text(file_list + "\n", encoding="utf-8")
    generated_paths.append(output_dir / "generated_files.txt")

    window.close()
    app.processEvents()
    return generated_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a complete sample export package.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "samples_exports" / "default_case_4face_4level"),
        help="Directory where the sample export package will be created.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    generated = generate_sample_exports(output_dir)
    print(f"Generated {len(generated)} files in {output_dir}")
    for path in generated:
        print(path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
