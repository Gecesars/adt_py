from __future__ import annotations

import difflib
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtWidgets import QApplication

from exports.pattern_exporters import export_to_format
from main import ADTMainWindow


MANUAL_EXPORTS_DIR = REPO_ROOT / "adt_exports"
OUTPUT_ROOT = REPO_ROOT / "legacy_vs_python_exports" / "manual_adt_exports_compare"


@dataclass
class ComparisonResult:
    filename: str
    format_name: str
    status: str
    details: str
    diff_path: str = ""


TEXT_FORMATS = {
    "HRP PAT",
    "VRP PAT",
    "HRP Text",
    "VRP Text",
    "HRP CSV",
    "VRP CSV",
    "HRP V-Soft",
    "VRP V-Soft",
    "HRP ATDI",
    "VRP ATDI",
    "3D ATDI",
    "3D Text",
    "NGW3D",
    "PRN",
    "EDX",
    "Complex EDX",
    "Directivity",
}


def infer_format(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith("_hrp.pat"):
        return "HRP PAT"
    if name.endswith("_vrp.pat"):
        return "VRP PAT"
    if name.endswith("_hrp.txt"):
        return "HRP Text"
    if name.endswith("_vrp.txt"):
        return "VRP Text"
    if name.endswith("_hrp.csv"):
        return "HRP CSV"
    if name.endswith("_vrp.csv"):
        return "VRP CSV"
    if name.endswith("_hrp.vep"):
        return "HRP V-Soft"
    if name.endswith("_vrp.vep"):
        return "VRP V-Soft"
    if name.endswith(".h_dia.dia"):
        return "HRP ATDI"
    if name.endswith(".v_dia.dia"):
        return "VRP ATDI"
    if name.endswith(".3dp"):
        return "3D Text"
    if name.endswith(".ng3dant"):
        return "NGW3D"
    if name.endswith(".prn"):
        return "PRN"
    if name.endswith(".progiraedx.pat"):
        if "complex" in name:
            return "Complex EDX"
        return "EDX"
    if name.endswith(".dir"):
        return "Directivity"
    if name.endswith("_hrp.jpg"):
        return "HRP JPEG"
    if name.endswith("_vrp.jpg"):
        return "VRP JPEG"
    if name == "layout.jpg":
        return "Layout JPEG"
    if name.endswith("_hrp.pdf"):
        return "HRP PDF"
    if name.endswith("_vrp.pdf"):
        return "VRP PDF"
    return None


def build_window():
    app = QApplication.instance() or QApplication([])
    window = ADTMainWindow()
    window.show()
    app.processEvents()
    window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
    window.on_calculate_clicked()
    app.processEvents()
    return app, window


def normalize_legacy_text(text: str) -> str:
    return text.replace("RFS", "EFTX")


def compare_text_files(legacy_path: Path, python_path: Path, report_dir: Path) -> ComparisonResult:
    legacy_text = legacy_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    python_text = python_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    expected_text = normalize_legacy_text(legacy_text)
    if expected_text == python_text:
        return ComparisonResult(legacy_path.name, infer_format(legacy_path) or "", "OK", "conteúdo textual idêntico após normalização RFS→EFTX")

    diff = "\n".join(
        difflib.unified_diff(
            expected_text.splitlines(),
            python_text.splitlines(),
            fromfile=f"legacy_normalized/{legacy_path.name}",
            tofile=f"eftx_python/{python_path.name}",
            lineterm="",
        )
    )
    diff_path = report_dir / f"{legacy_path.name}.diff.txt"
    diff_path.write_text(diff, encoding="utf-8", newline="\n")
    return ComparisonResult(
        legacy_path.name,
        infer_format(legacy_path) or "",
        "DIFF",
        "conteúdo textual diferente",
        diff_path.name,
    )


def compare_image_files(legacy_path: Path, python_path: Path) -> ComparisonResult:
    with Image.open(legacy_path) as legacy_img, Image.open(python_path) as python_img:
        legacy_rgb = legacy_img.convert("RGB")
        python_rgb = python_img.convert("RGB")
        if legacy_rgb.size != python_rgb.size:
            return ComparisonResult(
                legacy_path.name,
                infer_format(legacy_path) or "",
                "DIFF",
                f"tamanho legado={legacy_rgb.size} python={python_rgb.size}",
            )

        legacy_array = np.asarray(legacy_rgb, dtype=np.int16)
        python_array = np.asarray(python_rgb, dtype=np.int16)
        mean_abs_diff = float(np.mean(np.abs(legacy_array - python_array)))
        status = "OK" if mean_abs_diff < 8.0 else "DIFF"
        return ComparisonResult(
            legacy_path.name,
            infer_format(legacy_path) or "",
            status,
            f"formato legado={legacy_img.format} python={python_img.format}; mean_abs_diff={mean_abs_diff:.2f}",
        )


def compare_pdf_files(legacy_path: Path, python_path: Path) -> ComparisonResult:
    legacy_reader = PdfReader(str(legacy_path))
    python_reader = PdfReader(str(python_path))
    legacy_pages = len(legacy_reader.pages)
    python_pages = len(python_reader.pages)
    legacy_box = tuple(float(value) for value in legacy_reader.pages[0].mediabox)
    python_box = tuple(float(value) for value in python_reader.pages[0].mediabox)
    status = "OK" if legacy_pages == python_pages and legacy_box == python_box else "DIFF"
    return ComparisonResult(
        legacy_path.name,
        infer_format(legacy_path) or "",
        status,
        f"pages legado={legacy_pages} python={python_pages}; mediabox legado={legacy_box} python={python_box}",
    )


def generate_python_exports(target_dir: Path):
    app, window = build_window()
    context = window._build_export_context()
    for legacy_path in sorted(MANUAL_EXPORTS_DIR.iterdir()):
        if not legacy_path.is_file():
            continue
        format_name = infer_format(legacy_path)
        if format_name is None:
            continue
        export_to_format(format_name, target_dir / legacy_path.name, context)
    app.processEvents()


def main():
    if not MANUAL_EXPORTS_DIR.exists():
        raise SystemExit(f"Pasta não encontrada: {MANUAL_EXPORTS_DIR}")

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    legacy_dir = OUTPUT_ROOT / "adt_legacy"
    python_dir = OUTPUT_ROOT / "eftx_python"
    report_dir = OUTPUT_ROOT / "diffs"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    python_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    for legacy_path in MANUAL_EXPORTS_DIR.iterdir():
        if legacy_path.is_file():
            shutil.copy2(legacy_path, legacy_dir / legacy_path.name)

    generate_python_exports(python_dir)

    results: list[ComparisonResult] = []
    for legacy_path in sorted(legacy_dir.iterdir()):
        if not legacy_path.is_file():
            continue
        format_name = infer_format(legacy_path)
        if format_name is None:
            results.append(ComparisonResult(legacy_path.name, "-", "SKIP", "arquivo não mapeado"))
            continue

        python_path = python_dir / legacy_path.name
        if not python_path.exists():
            results.append(ComparisonResult(legacy_path.name, format_name, "MISSING", "export não gerado"))
            continue

        if format_name in TEXT_FORMATS:
            results.append(compare_text_files(legacy_path, python_path, report_dir))
        elif format_name.endswith("JPEG"):
            results.append(compare_image_files(legacy_path, python_path))
        elif format_name.endswith("PDF"):
            results.append(compare_pdf_files(legacy_path, python_path))
        else:
            results.append(ComparisonResult(legacy_path.name, format_name, "SKIP", "comparação não implementada"))

    report_lines = [
        "# Manual ADT vs EFTX Python",
        "",
        f"Legado: `{legacy_dir}`",
        f"Python: `{python_dir}`",
        "",
        "| Arquivo | Formato | Status | Detalhes | Diff |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        diff_label = result.diff_path if result.diff_path else ""
        report_lines.append(
            f"| {result.filename} | {result.format_name} | {result.status} | {result.details} | {diff_label} |"
        )

    (OUTPUT_ROOT / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Relatório gerado em: {OUTPUT_ROOT / 'report.md'}")


if __name__ == "__main__":
    main()
