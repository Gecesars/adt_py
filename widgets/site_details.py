from __future__ import annotations

from PyQt6.QtCore import QLocale, QSize, Qt, QSignalBlocker, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from catalogs import CableCatalog


class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale.c())
        self.setGroupSeparatorShown(False)
        self.setKeyboardTracking(False)

    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class NoWheelComboBox(QComboBox):
    def wheelEvent(self, event):  # noqa: N802
        event.ignore()


class SiteDetailsWidget(QWidget):
    values_changed = pyqtSignal()
    feeder_loss_changed = pyqtSignal(float)
    error_generated = pyqtSignal(str)

    TOWER_TYPES = [
        "Square",
        "Triangular",
        "Round",
        "Pentagonal",
        "Hexagonal",
        "Octagonal",
        "Other",
    ]

    ROW_LABELS = [
        "Tower Type",
        "Tower Face Width or Diameter (m)",
        "Tower Heading (deg)",
        "Main Feeder Size",
        "Feeder Length (m)",
        "Internal Loss (dB)",
        "Polarisation Loss (dB)",
        "Filter/Combiner Loss (dB)",
        "Transmitter Power (kW)",
        "Antenna Height (HAAT 10-1200m)",
        "Branch Feeder Base Length (m)",
    ]

    def __init__(self, cable_catalog: CableCatalog | None = None):
        super().__init__()
        self.cable_catalog = cable_catalog or CableCatalog()
        self._channel_frequency_mhz = 539.0
        self._computed_feeder_loss_db = 0.0
        self._building_ui = False
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)
        self._init_ui()
        self._load_feeder_types()
        self._apply_legacy_defaults()
        self.recalculate_feeder_loss()

    def _init_ui(self):
        self._building_ui = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.table = QTableWidget(len(self.ROW_LABELS), 2)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalHeaderLabels(["Item", "Selection"])
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 230)
        self.table.setShowGrid(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for row, label in enumerate(self.ROW_LABELS):
            item = QTableWidgetItem(label)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item)

        self.tower_type_combo = NoWheelComboBox()
        self.tower_type_combo.addItems(self.TOWER_TYPES)
        self.table.setCellWidget(0, 1, self.tower_type_combo)

        self.tower_size_spin = NoWheelDoubleSpinBox()
        self.tower_size_spin.setDecimals(2)
        self.tower_size_spin.setRange(0.01, 1000.0)
        self.tower_size_spin.setSingleStep(0.01)
        self.table.setCellWidget(1, 1, self.tower_size_spin)

        self.tower_heading_spin = NoWheelDoubleSpinBox()
        self.tower_heading_spin.setDecimals(1)
        self.tower_heading_spin.setRange(0.0, 359.9)
        self.tower_heading_spin.setSingleStep(0.1)
        self.table.setCellWidget(2, 1, self.tower_heading_spin)

        self.main_feeder_combo = NoWheelComboBox()
        self.main_feeder_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.table.setCellWidget(3, 1, self.main_feeder_combo)

        self.feeder_length_spin = NoWheelDoubleSpinBox()
        self.feeder_length_spin.setDecimals(2)
        self.feeder_length_spin.setRange(0.0, 100000.0)
        self.feeder_length_spin.setSingleStep(0.1)
        self.table.setCellWidget(4, 1, self.feeder_length_spin)

        self.internal_loss_spin = NoWheelDoubleSpinBox()
        self.internal_loss_spin.setDecimals(2)
        self.internal_loss_spin.setRange(0.0, 100.0)
        self.internal_loss_spin.setSingleStep(0.1)
        self.table.setCellWidget(5, 1, self.internal_loss_spin)

        self.polar_loss_spin = NoWheelDoubleSpinBox()
        self.polar_loss_spin.setDecimals(2)
        self.polar_loss_spin.setRange(0.0, 100.0)
        self.polar_loss_spin.setSingleStep(0.1)
        self.table.setCellWidget(6, 1, self.polar_loss_spin)

        self.filter_loss_spin = NoWheelDoubleSpinBox()
        self.filter_loss_spin.setDecimals(2)
        self.filter_loss_spin.setRange(0.0, 100.0)
        self.filter_loss_spin.setSingleStep(0.1)
        self.table.setCellWidget(7, 1, self.filter_loss_spin)

        self.tx_power_spin = NoWheelDoubleSpinBox()
        self.tx_power_spin.setDecimals(3)
        self.tx_power_spin.setRange(0.0, 100000.0)
        self.tx_power_spin.setSingleStep(0.1)
        self.table.setCellWidget(8, 1, self.tx_power_spin)

        self.antenna_height_spin = NoWheelDoubleSpinBox()
        self.antenna_height_spin.setDecimals(2)
        self.antenna_height_spin.setRange(0.0, 1200.0)
        self.antenna_height_spin.setSingleStep(1.0)
        self.table.setCellWidget(9, 1, self.antenna_height_spin)

        self.branch_feeder_length_spin = NoWheelDoubleSpinBox()
        self.branch_feeder_length_spin.setDecimals(2)
        self.branch_feeder_length_spin.setRange(0.0, 100000.0)
        self.branch_feeder_length_spin.setSingleStep(0.1)
        self.table.setCellWidget(10, 1, self.branch_feeder_length_spin)

        layout.addWidget(self.table)

        self.tower_type_combo.currentTextChanged.connect(self._on_user_changed_values)
        self.tower_size_spin.valueChanged.connect(self._on_user_changed_values)
        self.tower_heading_spin.valueChanged.connect(self._on_user_changed_values)
        self.main_feeder_combo.currentTextChanged.connect(self._on_user_changed_values)
        self.feeder_length_spin.valueChanged.connect(self._on_user_changed_values)
        self.internal_loss_spin.valueChanged.connect(self._on_user_changed_values)
        self.polar_loss_spin.valueChanged.connect(self._on_user_changed_values)
        self.filter_loss_spin.valueChanged.connect(self._on_user_changed_values)
        self.tx_power_spin.valueChanged.connect(self._on_user_changed_values)
        self.antenna_height_spin.valueChanged.connect(self._on_user_changed_values)
        self.branch_feeder_length_spin.valueChanged.connect(self._on_user_changed_values)
        self._building_ui = False

    def _load_feeder_types(self):
        blocker = QSignalBlocker(self.main_feeder_combo)
        self.main_feeder_combo.clear()
        self.main_feeder_combo.addItems(self.cable_catalog.feeder_names)
        del blocker

    def _apply_legacy_defaults(self):
        self.tower_type_combo.setCurrentText("Square")
        self.tower_size_spin.setValue(0.64)
        self.tower_heading_spin.setValue(0.0)
        if self.main_feeder_combo.findText(self.cable_catalog.default_feeder_name) >= 0:
            self.main_feeder_combo.setCurrentText(self.cable_catalog.default_feeder_name)
        self.feeder_length_spin.setValue(0.0)
        self.internal_loss_spin.setValue(0.1)
        self.polar_loss_spin.setValue(0.0)
        self.filter_loss_spin.setValue(0.0)
        self.tx_power_spin.setValue(1.0)
        self.antenna_height_spin.setValue(150.0)
        self.branch_feeder_length_spin.setValue(0.0)

    def _on_user_changed_values(self, *_args):
        if self._building_ui:
            return
        self.recalculate_feeder_loss()
        self.values_changed.emit()

    @property
    def computed_feeder_loss_db(self) -> float:
        return self._computed_feeder_loss_db

    def set_channel_frequency_mhz(self, channel_frequency_mhz: float):
        self._channel_frequency_mhz = max(float(channel_frequency_mhz or 0.0), 0.0)
        self.recalculate_feeder_loss()

    def recalculate_feeder_loss(self) -> float:
        try:
            self._computed_feeder_loss_db = self.cable_catalog.calculate_feeder_loss_db(
                self.main_feeder_combo.currentText(),
                self.feeder_length_spin.value(),
                self._channel_frequency_mhz,
            )
        except ValueError as exc:
            self._computed_feeder_loss_db = 0.0
            self.error_generated.emit(str(exc))
        self.feeder_loss_changed.emit(self._computed_feeder_loss_db)
        return self._computed_feeder_loss_db

    def get_feeder_index(self) -> int:
        return self.cable_catalog.get_feeder_index(self.main_feeder_combo.currentText())

    def get_main_feeder_types(self) -> list[str]:
        return self.cable_catalog.feeder_names

    def get_site_values(self) -> dict:
        return {
            "tower_type": self.tower_type_combo.currentText(),
            "tower_size_m": self.tower_size_spin.value(),
            "tower_heading_deg": self.tower_heading_spin.value(),
            "feeder_type": self.main_feeder_combo.currentText(),
            "feeder_length_m": self.feeder_length_spin.value(),
            "branch_feeder_length_m": self.branch_feeder_length_spin.value(),
            "transmitter_power_kw": self.tx_power_spin.value(),
            "antenna_height_m": self.antenna_height_spin.value(),
        }

    def get_loss_values(self) -> dict:
        return {
            "internal_db": self.internal_loss_spin.value(),
            "polarization_db": self.polar_loss_spin.value(),
            "filter_combiner_db": self.filter_loss_spin.value(),
            "feeder_db": self._computed_feeder_loss_db,
        }

    def apply_values(self, site: dict, losses: dict):
        blockers = [
            QSignalBlocker(self.tower_type_combo),
            QSignalBlocker(self.tower_size_spin),
            QSignalBlocker(self.tower_heading_spin),
            QSignalBlocker(self.main_feeder_combo),
            QSignalBlocker(self.feeder_length_spin),
            QSignalBlocker(self.internal_loss_spin),
            QSignalBlocker(self.polar_loss_spin),
            QSignalBlocker(self.filter_loss_spin),
            QSignalBlocker(self.tx_power_spin),
            QSignalBlocker(self.antenna_height_spin),
            QSignalBlocker(self.branch_feeder_length_spin),
        ]
        try:
            self.tower_type_combo.setCurrentText(site.get("tower_type") or "Square")
            self.tower_size_spin.setValue(float(site.get("tower_size_m", 0.64) or 0.64))
            self.tower_heading_spin.setValue(
                float(site.get("tower_heading_deg", 0.0) or 0.0)
            )
            feeder_type = site.get("feeder_type") or self.cable_catalog.default_feeder_name
            if self.main_feeder_combo.findText(feeder_type) >= 0:
                self.main_feeder_combo.setCurrentText(feeder_type)
            elif self.main_feeder_combo.count() > 0:
                self.main_feeder_combo.setCurrentIndex(0)
            self.feeder_length_spin.setValue(
                float(site.get("feeder_length_m", 0.0) or 0.0)
            )
            self.internal_loss_spin.setValue(
                float(losses.get("internal_db", 0.1) or 0.1)
            )
            self.polar_loss_spin.setValue(
                float(losses.get("polarization_db", 0.0) or 0.0)
            )
            self.filter_loss_spin.setValue(
                float(losses.get("filter_combiner_db", 0.0) or 0.0)
            )
            self.tx_power_spin.setValue(
                float(site.get("transmitter_power_kw", 1.0) or 1.0)
            )
            self.antenna_height_spin.setValue(
                float(site.get("antenna_height_m", 150.0) or 150.0)
            )
            self.branch_feeder_length_spin.setValue(
                float(site.get("branch_feeder_length_m", 0.0) or 0.0)
            )
        finally:
            for blocker in blockers:
                del blocker

        feeder_loss = losses.get("feeder_db")
        self.recalculate_feeder_loss()
        if feeder_loss is not None and not site.get("feeder_type"):
            self._computed_feeder_loss_db = float(feeder_loss or 0.0)
            self.feeder_loss_changed.emit(self._computed_feeder_loss_db)
        self.values_changed.emit()

    def minimumSizeHint(self):
        return QSize(0, 0)

    def sizeHint(self):
        return QSize(420, 320)
