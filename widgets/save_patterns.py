from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QLocale, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class SavePatternsSettings:
    save_jpg: bool
    jpg_target: str
    save_tabdata: bool
    tabdata_target: str
    save_pat: bool
    pat_target: str
    save_txt: bool
    txt_target: str
    save_csv: bool
    csv_target: str
    save_vsoft: bool
    vsoft_target: str
    save_atdi: bool
    atdi_target: str
    save_3d_text: bool
    save_ngw3d: bool
    save_prn: bool
    save_edx: bool
    edx_file_type: str
    edx_hrp_used: str
    edx_start_deg: float
    edx_stop_deg: float
    edx_increment_deg: float
    image_resolution_label: str
    image_resolution_scale: float


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale.c())
        self.setGroupSeparatorShown(False)

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class SavePatternsWidget(QWidget):
    save_requested = pyqtSignal(object)
    error_requested = pyqtSignal(str)

    _TARGET_CHOICES = ["HRP", "VRP", "HRP & VRP"]
    _ATDI_CHOICES = ["HRP", "VRP", "HRP & VRP", "3D"]
    _EDX_FILE_TYPE_CHOICES = ["Simple file-1 VRP", "Complex file-72 VRP"]
    _EDX_HRP_CHOICES = ["Peak HRP", "Displayed HRP"]
    _INCREMENT_CHOICES = ["0.1 Degrees", "0.2 Degrees", "0.5 Degrees", "1.0 Degrees"]
    _IMAGE_RESOLUTION_CHOICES = [
        ("Legacy (1000 x 1400)", 1.0),
        ("High (2000 x 2800)", 2.0),
    ]
    _ROW_DESCRIPTIONS = {
        0: "Save the displayed pattern image in the legacy ADT style for HRP, VRP or both.",
        1: "Save the displayed pattern in the tabulated data table PDF layout.",
        2: "Save the displayed pattern in EFTX PAT format.",
        3: "Save the displayed pattern in plain text format.",
        4: "Save the displayed pattern in CSV format.",
        5: "Save the displayed pattern in V-Soft format.",
        6: "Save the selected pattern in ATDI format as HRP, VRP, both or 3D.",
        7: "Save the 3D pattern as text using 1 deg azimuth and 0.1 deg elevation steps.",
        8: "Save the 3D pattern in NGW3D format using 1 deg azimuth and 0.1 deg elevation steps.",
        9: "Save the 3D pattern in PRN format using 1 deg azimuth and 1 deg elevation steps.",
        10: "Save the pattern in Progira / EDX format using the options below.",
        11: "Choose between the simple EDX file with 1 VRP and the complex EDX file with 72 VRPs.",
        12: "Choose whether EDX uses the Peak HRP or the currently displayed HRP.",
        13: "Starting elevation angle used by the EDX export.",
        14: "Stopping elevation angle used by the EDX export.",
        15: "Angular sampling increment used by the EDX export.",
    }
    _ROW_LABELS = {
        0: "Save Displayed Pattern as JPG Format",
        1: "Save Displayed Pattern to Tabulated Data Table",
        2: "Save Displayed Pattern as EFTX PAT Format",
        3: "Save Displayed Pattern as Text Format",
        4: "Save Displayed Pattern as CSV Format",
        5: "Save Displayed Pattern as V-Soft Format",
        6: "Save Pattern as ATDI Format",
        7: "Save 3D Pattern as Text Format (1 deg Az, 0.1 deg El)",
        8: "Save 3D Pattern as NGW3D Format (1 deg Az, 0.1 deg El)",
        9: "Save 3D Pattern as PRN Format (1 deg Az, 1 deg El)",
        10: "Save Pattern as Progira / EDX Format",
        11: "File Type",
        12: "HRP Used",
        13: "Elevation Start Angle",
        14: "Elevation Stop Angle",
        15: "Increment",
    }
    _DEFAULT_CHECKED_ROWS = {0, 1, 2, 3, 4, 7, 8, 9, 10}

    def __init__(self):
        super().__init__()
        self._combo_widgets: dict[int, QComboBox] = {}
        self._check_widgets: dict[int, QCheckBox] = {}
        self._spin_widgets: dict[int, QDoubleSpinBox] = {}
        self._resolution_combo: QComboBox | None = None
        self._table: QTableWidget | None = None
        self._save_button: QPushButton | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        self.setMinimumWidth(520)

        group = QGroupBox("Save Patterns")
        group.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #a7a7a7;
                background: white;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            """
        )
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(4, 8, 4, 4)
        group_layout.setSpacing(6)

        self._table = QTableWidget(16, 3)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(True)
        self._table.setWordWrap(False)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._table.setFrameShape(QTableWidget.Shape.NoFrame)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setVisible(False)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setSizeAdjustPolicy(QAbstractItemView.SizeAdjustPolicy.AdjustToContents)
        self._table.setColumnWidth(0, 34)
        self._table.setColumnWidth(1, 340)
        self._table.setColumnWidth(2, 138)
        self._table.setMinimumHeight(490)
        self._table.setStyleSheet(
            """
            QTableWidget {
                background: white;
                gridline-color: #b8b8b8;
                border: 1px solid #a7a7a7;
            }
            QTableWidget::item {
                padding-left: 6px;
                padding-right: 6px;
                border: 0;
            }
            """
        )

        for row in range(16):
            self._table.setRowHeight(row, 29)

        self._init_rows()
        group_layout.addWidget(self._table)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)

        resolution_label = QLabel("Image/PDF Resolution")
        self._resolution_combo = QComboBox()
        for label, _scale in self._IMAGE_RESOLUTION_CHOICES:
            self._resolution_combo.addItem(label)
        self._resolution_combo.setCurrentIndex(0)
        self._resolution_combo.setToolTip("Control the image and PDF export resolution.")
        self._resolution_combo.setStyleSheet(self._combo_stylesheet())

        footer_layout.addWidget(resolution_label)
        footer_layout.addWidget(self._resolution_combo, 1)

        self._save_button = QPushButton("Save Patterns")
        self._save_button.setMinimumWidth(170)
        self._save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #1e88e5;
                color: white;
                font-weight: bold;
                min-height: 28px;
                padding: 4px 18px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            """
        )
        self._save_button.clicked.connect(self._emit_save_requested)
        footer_layout.addWidget(self._save_button)

        group_layout.addLayout(footer_layout)
        layout.addWidget(group)
        layout.addStretch(1)

    def _init_rows(self):
        for row, label in self._ROW_LABELS.items():
            self._set_label_item(row, label, right_align=row >= 11)

        for row in range(0, 11):
            self._set_check_widget(row, checked=row in self._DEFAULT_CHECKED_ROWS)

        for row in range(11, 16):
            gray_item = self._blank_item()
            gray_item.setBackground(Qt.GlobalColor.lightGray)
            self._table.setItem(row, 0, gray_item)

        for row in range(0, 6):
            self._set_combo_widget(row, self._TARGET_CHOICES, "HRP & VRP")

        self._set_combo_widget(6, self._ATDI_CHOICES, "HRP & VRP")

        for row in (7, 8, 9, 10):
            item = self._blank_item()
            item.setBackground(Qt.GlobalColor.white)
            self._table.setItem(row, 2, item)

        self._set_combo_widget(11, self._EDX_FILE_TYPE_CHOICES, "Simple file-1 VRP")
        self._set_combo_widget(12, self._EDX_HRP_CHOICES, "Peak HRP")

        self._spin_widgets[13] = self._make_spinbox(-90.0, 90.0, 1, -5.0)
        self._spin_widgets[14] = self._make_spinbox(-90.0, 90.0, 1, 15.0)
        self._table.setCellWidget(13, 2, self._spin_widgets[13])
        self._table.setCellWidget(14, 2, self._spin_widgets[14])

        self._set_combo_widget(15, self._INCREMENT_CHOICES, "0.1 Degrees")

    def _blank_item(self) -> QTableWidgetItem:
        item = QTableWidgetItem("")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        return item

    def _set_check_widget(self, row: int, checked: bool):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.setToolTip(self._ROW_DESCRIPTIONS.get(row, ""))
        checkbox.setStyleSheet(
            """
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #8b8b8b;
                border-radius: 2px;
                background: white;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0f5fb7;
                background: #0f5fb7;
            }
            """
        )
        layout.addWidget(checkbox)
        container.setStyleSheet("background: #d6d6d6;")
        self._check_widgets[row] = checkbox
        self._table.setCellWidget(row, 0, container)

    def _set_label_item(self, row: int, text: str, right_align: bool = False):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignVCenter
            | (Qt.AlignmentFlag.AlignRight if right_align else Qt.AlignmentFlag.AlignLeft)
        )
        item.setBackground(Qt.GlobalColor.white)
        item.setToolTip(self._ROW_DESCRIPTIONS.get(row, text))
        self._table.setItem(row, 1, item)

    def _combo_stylesheet(self) -> str:
        return """
            QComboBox {
                background: white;
                border: 1px solid #9c9c9c;
                padding: 2px 4px;
                min-height: 22px;
            }
            QComboBox::drop-down {
                width: 20px;
                border-left: 1px solid #b4b4b4;
            }
        """

    def _set_combo_widget(self, row: int, choices: list[str], current: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(choices)
        combo.setCurrentText(current)
        combo.setStyleSheet(self._combo_stylesheet())
        combo.setToolTip(self._ROW_DESCRIPTIONS.get(row, ""))
        self._combo_widgets[row] = combo
        self._table.setCellWidget(row, 2, combo)
        return combo

    def _make_spinbox(self, minimum: float, maximum: float, decimals: int, value: float) -> QDoubleSpinBox:
        spin = NoWheelDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setSingleStep(1.0 if decimals == 0 else 0.1)
        spin.setValue(value)
        spin.setStyleSheet(
            """
            QAbstractSpinBox {
                background: white;
                border: 1px solid #9c9c9c;
                padding: 2px 4px;
                min-height: 22px;
            }
            """
        )
        spin.setToolTip("Use '.' as the decimal separator.")
        return spin

    def _is_checked(self, row: int) -> bool:
        checkbox = self._check_widgets.get(row)
        return bool(checkbox and checkbox.isChecked())

    def _combo_value(self, row: int, default: str = "") -> str:
        combo = self._combo_widgets.get(row)
        if combo is None:
            return default
        return combo.currentText()

    def _spin_value(self, row: int, default: float) -> float:
        spin = self._spin_widgets.get(row)
        if spin is None:
            return default
        return float(spin.value())

    def get_settings(self) -> SavePatternsSettings:
        increment_text = self._combo_value(15, "0.1 Degrees")
        increment_deg = float(increment_text.split()[0])
        resolution_label = self._resolution_combo.currentText()
        resolution_scale = dict(self._IMAGE_RESOLUTION_CHOICES)[resolution_label]
        return SavePatternsSettings(
            save_jpg=self._is_checked(0),
            jpg_target=self._combo_value(0, "HRP & VRP"),
            save_tabdata=self._is_checked(1),
            tabdata_target=self._combo_value(1, "HRP & VRP"),
            save_pat=self._is_checked(2),
            pat_target=self._combo_value(2, "HRP & VRP"),
            save_txt=self._is_checked(3),
            txt_target=self._combo_value(3, "HRP & VRP"),
            save_csv=self._is_checked(4),
            csv_target=self._combo_value(4, "HRP & VRP"),
            save_vsoft=self._is_checked(5),
            vsoft_target=self._combo_value(5, "HRP & VRP"),
            save_atdi=self._is_checked(6),
            atdi_target=self._combo_value(6, "HRP & VRP"),
            save_3d_text=self._is_checked(7),
            save_ngw3d=self._is_checked(8),
            save_prn=self._is_checked(9),
            save_edx=self._is_checked(10),
            edx_file_type=self._combo_value(11, "Simple file-1 VRP"),
            edx_hrp_used=self._combo_value(12, "Peak HRP"),
            edx_start_deg=self._spin_value(13, -5.0),
            edx_stop_deg=self._spin_value(14, 15.0),
            edx_increment_deg=increment_deg,
            image_resolution_label=resolution_label,
            image_resolution_scale=resolution_scale,
        )

    def _emit_save_requested(self):
        settings = self.get_settings()
        if not any(
            (
                settings.save_jpg,
                settings.save_tabdata,
                settings.save_pat,
                settings.save_txt,
                settings.save_csv,
                settings.save_vsoft,
                settings.save_atdi,
                settings.save_3d_text,
                settings.save_ngw3d,
                settings.save_prn,
                settings.save_edx,
            )
        ):
            self.error_requested.emit("Tick at least one pattern file format")
            return
        if settings.save_edx and settings.edx_start_deg >= settings.edx_stop_deg:
            self.error_requested.emit("The Elevation Start/Stop Angle is out of range")
            return
        self.save_requested.emit(settings)
