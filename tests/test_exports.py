import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PIL import Image
from pypdf import PdfReader
from PyQt6.QtWidgets import QApplication

from exports.pattern_exporters import export_to_format
from main import ADTMainWindow


class ExportersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _build_window_with_pattern(self):
        window = ADTMainWindow()
        window.show()
        self.app.processEvents()
        window.on_tower_geometry_generate_requested(4, 0.34, 0.0, 4, 1.15, False)
        window.on_calculate_clicked()
        self.app.processEvents()
        return window

    def test_engineering_exports_generate_legacy_style_files(self):
        window = self._build_window_with_pattern()
        context = window._build_export_context()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            targets = {
                "HRP PAT": temp_path / "hrp.pat",
                "VRP PAT": temp_path / "vrp.pat",
                "HRP Text": temp_path / "hrp.txt",
                "VRP Text": temp_path / "vrp.txt",
                "HRP CSV": temp_path / "hrp.csv",
                "VRP CSV": temp_path / "vrp.csv",
                "HRP V-Soft": temp_path / "hrp.vep",
                "VRP V-Soft": temp_path / "vrp.vep",
                "HRP ATDI": temp_path / "hrp.H_DIA.DIA",
                "VRP ATDI": temp_path / "vrp.V_DIA.DIA",
                "3D ATDI": temp_path / "pattern3d.csv",
                "3D Text": temp_path / "pattern.3dp",
                "NGW3D": temp_path / "pattern.ng3dant",
                "PRN": temp_path / "pattern.prn",
                "EDX": temp_path / "pattern.ProgiraEDX.pat",
                "Complex EDX": temp_path / "pattern_complex.ProgiraEDX.pat",
                "Directivity": temp_path / "pattern.dir",
            }

            for format_name, target in targets.items():
                export_to_format(format_name, target, context)
                self.assertTrue(target.exists(), format_name)
                self.assertGreater(target.stat().st_size, 0, format_name)

            self.assertTrue((temp_path / "hrp.pat").read_text(encoding="utf-8").startswith("Edited by Deglitch"))
            self.assertTrue((temp_path / "hrp.txt").read_text(encoding="utf-8").startswith("EFTX Horizontal Radiation Pattern Data"))
            self.assertIn("manufacturer:\tEFTX", (temp_path / "vrp.csv").read_text(encoding="utf-8"))
            self.assertTrue((temp_path / "pattern.prn").read_text(encoding="ascii").startswith("NAME"))
            self.assertIn("[3D-Data]", (temp_path / "pattern.ng3dant").read_text(encoding="utf-8"))
            self.assertIn("'By ADT'", (temp_path / "pattern.ProgiraEDX.pat").read_text(encoding="ascii"))
            self.assertEqual(
                (temp_path / "pattern.ng3dant").read_text(encoding="utf-8").splitlines()[1],
                "  By ADT",
            )
            self.assertTrue((temp_path / "pattern3d.csv").read_text(encoding="utf-8").endswith("\n"))
            self.assertEqual(
                (temp_path / "pattern.ProgiraEDX.pat").read_text(encoding="ascii").splitlines()[362],
                "1, 201",
            )
            self.assertEqual(
                (temp_path / "pattern_complex.ProgiraEDX.pat").read_text(encoding="ascii").splitlines()[362],
                "1, 161",
            )
            self.assertIn(b"\r\n", (temp_path / "hrp.pat").read_bytes())

    def test_image_and_pdf_exports_generate_files_with_logo_header(self):
        window = self._build_window_with_pattern()
        context = window._build_export_context()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            targets = {
                "HRP JPEG": temp_path / "hrp.jpg",
                "VRP JPEG": temp_path / "vrp.jpg",
                "Layout JPEG": temp_path / "layout.jpg",
                "HRP PDF": temp_path / "hrp.pdf",
                "VRP PDF": temp_path / "vrp.pdf",
                "Summary PDF": temp_path / "summary.pdf",
                "Panel PDF": temp_path / "panels.pdf",
                "All PDF": temp_path / "all.pdf",
            }

            for format_name, target in targets.items():
                export_to_format(format_name, target, context)
                self.assertTrue(target.exists(), format_name)
                self.assertGreater(target.stat().st_size, 256, format_name)

            self.assertTrue((temp_path / "hrp.jpg").read_bytes().startswith(b"GIF89a"))
            self.assertTrue((temp_path / "vrp.jpg").read_bytes().startswith(b"GIF89a"))
            self.assertTrue((temp_path / "layout.jpg").read_bytes().startswith(b"BM"))

            with Image.open(temp_path / "hrp.jpg") as hrp_img:
                self.assertEqual(hrp_img.size, (1000, 1400))
            with Image.open(temp_path / "vrp.jpg") as vrp_img:
                self.assertEqual(vrp_img.size, (1000, 1400))
            with Image.open(temp_path / "layout.jpg") as layout_img:
                self.assertEqual(layout_img.size, (1000, 1400))

            self.assertEqual(len(PdfReader(str(temp_path / "hrp.pdf")).pages), 1)
            self.assertEqual(len(PdfReader(str(temp_path / "vrp.pdf")).pages), 1)
            self.assertGreaterEqual(len(PdfReader(str(temp_path / "all.pdf")).pages), 8)
            with fitz.open(temp_path / "all.pdf") as doc:
                self.assertGreaterEqual(doc.page_count, 8)
                pix = doc[0].get_pixmap(alpha=False)
                self.assertGreater(pix.width, 500)
                self.assertGreater(pix.height, 700)

    def test_video_export_generates_avi_file(self):
        window = self._build_window_with_pattern()
        context = window._build_export_context()

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "vrp_animation.avi"
            export_to_format("Video", target, context)
            self.assertTrue(target.exists())
            self.assertGreater(target.stat().st_size, 1024)


if __name__ == "__main__":
    unittest.main()
