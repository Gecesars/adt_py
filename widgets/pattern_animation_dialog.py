from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)


@dataclass
class PatternAnimationSettings:
    axis: str
    start_angle: float
    stop_angle: float
    delay_index: int = 2
    scan_peer: bool = True


class NoWheelSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale.c())

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale.c())
        self.setGroupSeparatorShown(False)

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class PatternAnimationDialog(QDialog):
    DELAY_OPTIONS = [
        ("0 - Fastest (10 ms)", 0),
        ("1 - Fast (20 ms)", 1),
        ("2 - Normal (40 ms)", 2),
        ("3 - Slow (60 ms)", 3),
        ("4 - Slowest (80 ms)", 4),
    ]

    def __init__(self, settings: PatternAnimationSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Pattern Animation")
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        axis_name = "VRP" if self.settings.axis == "vrp" else "HRP"

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(8)

        info = QLabel(
            "Animate VRP across azimuth cuts like the legacy ADT."
            if self.settings.axis == "vrp"
            else "Animate HRP across elevation cuts while updating the corresponding VRP scan line."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        if self.settings.axis == "vrp":
            self.start_spin = NoWheelSpinBox()
            self.start_spin.setRange(0, 359)
            self.start_spin.setValue(int(round(self.settings.start_angle)) % 360)

            self.stop_spin = NoWheelSpinBox()
            self.stop_spin.setRange(0, 359)
            self.stop_spin.setValue(int(round(self.settings.stop_angle)) % 360)
        else:
            self.start_spin = NoWheelDoubleSpinBox()
            self.start_spin.setRange(-90.0, 90.0)
            self.start_spin.setDecimals(1)
            self.start_spin.setSingleStep(0.1)
            self.start_spin.setValue(float(self.settings.start_angle))

            self.stop_spin = NoWheelDoubleSpinBox()
            self.stop_spin.setRange(-90.0, 90.0)
            self.stop_spin.setDecimals(1)
            self.stop_spin.setSingleStep(0.1)
            self.stop_spin.setValue(float(self.settings.stop_angle))

        self.delay_combo = QComboBox()
        for label, delay_index in self.DELAY_OPTIONS:
            self.delay_combo.addItem(label, delay_index)
        delay_combo_index = max(0, min(self.delay_combo.count() - 1, int(self.settings.delay_index)))
        self.delay_combo.setCurrentIndex(delay_combo_index)

        scan_label = (
            "Show Scan Line on HRP when Viewing VRP"
            if self.settings.axis == "vrp"
            else "Show Scan Line on VRP when Viewing HRP"
        )
        self.scan_checkbox = QCheckBox(scan_label)
        self.scan_checkbox.setChecked(bool(self.settings.scan_peer))

        angle_label = "Azimuth Angle Range (°)" if self.settings.axis == "vrp" else "Elevation Angle Range (°)"
        form.addRow(QLabel(f"{axis_name} Animation"), QLabel(angle_label))
        form.addRow("Start (°)", self.start_spin)
        form.addRow("Stop (°)", self.stop_spin)
        form.addRow("Animation Delay", self.delay_combo)
        form.addRow("", self.scan_checkbox)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> PatternAnimationSettings:
        return PatternAnimationSettings(
            axis=self.settings.axis,
            start_angle=float(self.start_spin.value()),
            stop_angle=float(self.stop_spin.value()),
            delay_index=int(self.delay_combo.currentData()),
            scan_peer=bool(self.scan_checkbox.isChecked()),
        )
