from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QVBoxLayout,
)

from catalogs import CustomAntennaDefinition
from parsers import read_pattern_frequency


def _browse_pattern_file(parent, title):
    path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        "",
        "Pattern Files (*.pat *.hup *.vup *.prn *.txt *.csv *.dat *.dia);;All Files (*)",
    )
    return path


class _NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale.c())
        self.setGroupSeparatorShown(False)

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class NewAntennaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Antenna")
        self.setModal(True)
        self.resize(720, 520)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        info_label = QLabel(
            "Import HRP/VRP from text-based antenna files and save them into the ADT "
            "catalog format used by the application."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        meta_group = QGroupBox("Antenna Data")
        meta_form = QFormLayout(meta_group)
        meta_form.setSpacing(6)

        self.name_input = QLineEdit()
        self.freq_spin = _NoWheelDoubleSpinBox()
        self.freq_spin.setRange(1.0, 10000.0)
        self.freq_spin.setDecimals(3)
        self.freq_spin.setValue(539.0)

        self.band_combo = QComboBox()
        self.band_combo.addItems(["FM", "VHF", "UHF"])
        self.band_combo.setCurrentText("UHF")

        self.polarization_combo = QComboBox()
        self.polarization_combo.addItems(
            ["Horizontal", "Vertical", "Circular", "Elliptical", "Slant", "Mixed"]
        )

        self.width_spin = _NoWheelDoubleSpinBox()
        self.width_spin.setRange(0.001, 100.0)
        self.width_spin.setDecimals(3)
        self.width_spin.setValue(0.5)

        self.height_spin = _NoWheelDoubleSpinBox()
        self.height_spin.setRange(0.001, 100.0)
        self.height_spin.setDecimals(3)
        self.height_spin.setValue(1.09)

        self.depth_spin = _NoWheelDoubleSpinBox()
        self.depth_spin.setRange(0.0, 100.0)
        self.depth_spin.setDecimals(3)
        self.depth_spin.setValue(0.22)

        self.spacing_spin = _NoWheelDoubleSpinBox()
        self.spacing_spin.setRange(0.0, 100.0)
        self.spacing_spin.setDecimals(3)
        self.spacing_spin.setValue(1.15)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["One Panel", "One Bay", "Two Bays", "Four Bays"])

        meta_form.addRow("Display Name", self.name_input)
        meta_form.addRow("Reference Frequency (MHz)", self.freq_spin)
        meta_form.addRow("Band", self.band_combo)
        meta_form.addRow("Polarisation", self.polarization_combo)
        meta_form.addRow("Width (m)", self.width_spin)
        meta_form.addRow("Height (m)", self.height_spin)
        meta_form.addRow("Depth (m)", self.depth_spin)
        meta_form.addRow("Elevation Spacing (m)", self.spacing_spin)
        meta_form.addRow("Elevation Unit", self.unit_combo)
        layout.addWidget(meta_group)

        pattern_group = QGroupBox("Pattern Files")
        pattern_layout = QGridLayout(pattern_group)
        pattern_layout.setHorizontalSpacing(6)
        pattern_layout.setVerticalSpacing(6)

        self.hrp_path_input = QLineEdit()
        self.vrp_path_input = QLineEdit()
        self.synthetic_vrp_spin = _NoWheelDoubleSpinBox()
        self.synthetic_vrp_spin.setRange(0.0, 180.0)
        self.synthetic_vrp_spin.setDecimals(3)
        self.synthetic_vrp_spin.setValue(0.0)

        hrp_browse = QPushButton("Browse...")
        vrp_browse = QPushButton("Browse...")
        hrp_browse.clicked.connect(self._browse_hrp)
        vrp_browse.clicked.connect(self._browse_vrp)

        pattern_layout.addWidget(QLabel("HRP File"), 0, 0)
        pattern_layout.addWidget(self.hrp_path_input, 0, 1)
        pattern_layout.addWidget(hrp_browse, 0, 2)
        pattern_layout.addWidget(QLabel("VRP File"), 1, 0)
        pattern_layout.addWidget(self.vrp_path_input, 1, 1)
        pattern_layout.addWidget(vrp_browse, 1, 2)
        pattern_layout.addWidget(QLabel("Synthetic VRP 3 dB Angle (optional)"), 2, 0)
        pattern_layout.addWidget(self.synthetic_vrp_spin, 2, 1)
        pattern_layout.addWidget(QLabel("Use this only when no VRP file is available."), 2, 2)
        layout.addWidget(pattern_group)

        details_label = QLabel(
            "Accepted inputs: ADT .pat/.hup/.vup and generic text/CSV tables with angle + "
            "magnitude (+ optional phase). Imported patterns are normalized and saved in the "
            "internal ADT format."
        )
        details_label.setWordWrap(True)
        layout.addWidget(details_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_hrp(self):
        path = _browse_pattern_file(self, "Select HRP File")
        if not path:
            return
        self.hrp_path_input.setText(path)
        if not self.name_input.text().strip():
            self.name_input.setText(Path(path).stem)
        try:
            self.freq_spin.setValue(read_pattern_frequency(path, self.freq_spin.value()))
        except Exception:
            pass

    def _browse_vrp(self):
        path = _browse_pattern_file(self, "Select VRP File")
        if path:
            self.vrp_path_input.setText(path)

    def get_definition(self):
        synthetic_vrp = float(self.synthetic_vrp_spin.value())
        return CustomAntennaDefinition(
            display_name=self.name_input.text().strip(),
            frequency_mhz=float(self.freq_spin.value()),
            band=self.band_combo.currentText(),
            polarization=self.polarization_combo.currentText(),
            width_m=float(self.width_spin.value()),
            height_m=float(self.height_spin.value()),
            depth_m=float(self.depth_spin.value()),
            elevation_spacing_m=float(self.spacing_spin.value()),
            elevation_unit=self.unit_combo.currentText(),
            hrp_source_path=self.hrp_path_input.text().strip(),
            vrp_source_path=self.vrp_path_input.text().strip(),
            synthetic_vrp_half_power_angle_deg=synthetic_vrp if synthetic_vrp > 0.0 else None,
        )

    def accept(self):
        definition = self.get_definition()
        if not definition.display_name:
            QMessageBox.warning(self, "New Antenna", "Please enter an antenna name.")
            return
        if not definition.hrp_source_path:
            QMessageBox.warning(self, "New Antenna", "Please select an HRP file.")
            return
        if not Path(definition.hrp_source_path).exists():
            QMessageBox.warning(self, "New Antenna", "The selected HRP file was not found.")
            return
        if definition.vrp_source_path and not Path(definition.vrp_source_path).exists():
            QMessageBox.warning(self, "New Antenna", "The selected VRP file was not found.")
            return
        if not definition.vrp_source_path and definition.synthetic_vrp_half_power_angle_deg is None:
            QMessageBox.warning(
                self,
                "New Antenna",
                "Please select a VRP file or provide a synthetic VRP 3 dB angle.",
            )
            return
        super().accept()
