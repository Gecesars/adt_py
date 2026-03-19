from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from solver.beam_shape_solver import (
    BeamShapeResult,
    calculate_beam_shape_phases,
    format_phase_value,
)
from widgets.splitter_utils import enable_free_resize


class BeamShapeWidget(QWidget):
    message_generated = pyqtSignal(str)
    phase_transfer_requested = pyqtSignal(list, int)

    DEFINE_ROWS = {
        "frequency_mhz": 0,
        "number_of_bays": 1,
        "beam_tilt_deg": 2,
        "spacing_m": 3,
        "null_fill_percent": 4,
    }

    def __init__(self):
        super().__init__()
        self.current_result: BeamShapeResult | None = None
        self.init_ui()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter = splitter
        splitter.setHandleWidth(12)
        splitter.setOpaqueResize(True)
        splitter.setStyleSheet(
            """
            QSplitter::handle {
                background: #b4b4b4;
                border-left: 1px solid #878787;
                border-right: 1px solid #dcdcdc;
            }
            QSplitter::handle:hover {
                background: #6f9cd6;
            }
            """
        )

        left_panel = QWidget()
        left_panel.setMinimumWidth(0)
        left_panel.setMinimumHeight(0)
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 2, 0)
        left_layout.setSpacing(4)

        self.define_table = QTableWidget(5, 2)
        self.define_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.define_table.verticalHeader().setVisible(False)
        self.define_table.horizontalHeader().setVisible(False)
        self.define_table.setShowGrid(True)
        self.define_table.setMinimumWidth(0)
        self.define_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.define_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.define_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.define_table.verticalHeader().setDefaultSectionSize(22)
        self.define_table.setStyleSheet(
            """
            QTableWidget {
                background: white;
                gridline-color: #c8c8c8;
                border: 1px solid #b5b5b5;
            }
            QTableWidget::item {
                padding: 2px;
            }
            """
        )

        self._set_define_row("frequency_mhz", "Frequency (MHz)", "539")
        self._set_define_row("beam_tilt_deg", "Required Beam Tilt (deg)", "1.00")
        self._set_define_row("spacing_m", "Element Spacing (m)", "1.15")

        self.bays_spin = QSpinBox()
        self.bays_spin.setRange(1, 40)
        self.bays_spin.setValue(4)
        self.bays_spin.valueChanged.connect(self._clear_phase_table)
        self.define_table.setCellWidget(self.DEFINE_ROWS["number_of_bays"], 1, self.bays_spin)
        self.define_table.setItem(
            self.DEFINE_ROWS["number_of_bays"],
            0,
            QTableWidgetItem("Number of Bays"),
        )

        self.null_fill_spin = QSpinBox()
        self.null_fill_spin.setRange(0, 100)
        self.null_fill_spin.setValue(50)
        self.null_fill_spin.valueChanged.connect(self._clear_phase_table)
        self.define_table.setCellWidget(
            self.DEFINE_ROWS["null_fill_percent"], 1, self.null_fill_spin
        )
        self.define_table.setItem(
            self.DEFINE_ROWS["null_fill_percent"],
            0,
            QTableWidgetItem("Degree of Null Fill (%)"),
        )

        left_layout.addWidget(self.define_table)

        element_group = QGroupBox("Element Type")
        element_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        element_layout = QVBoxLayout(element_group)
        element_layout.setContentsMargins(6, 8, 6, 8)
        element_layout.addWidget(QLabel("Point Source"), alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(element_group)

        solution_group = QGroupBox("Solution")
        solution_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        solution_layout = QHBoxLayout(solution_group)
        solution_layout.setContentsMargins(6, 6, 6, 6)
        self.rb_oscillatory = QRadioButton("Oscillatory")
        self.rb_non_oscillatory = QRadioButton("Non-Oscillatory")
        self.rb_oscillatory.setChecked(True)
        self.rb_oscillatory.toggled.connect(self._clear_phase_table)
        self.rb_non_oscillatory.toggled.connect(self._clear_phase_table)
        solution_layout.addWidget(self.rb_oscillatory)
        solution_layout.addWidget(self.rb_non_oscillatory)
        left_layout.addWidget(solution_group)

        self.calc_btn = QPushButton("Calculate Phases")
        self.calc_btn.clicked.connect(self._on_calculate_clicked)
        self.calc_btn.setStyleSheet(self._button_stylesheet())
        self.calc_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(self.calc_btn)

        decimal_group = QGroupBox("Decimal Places to Vertical Group Phi")
        decimal_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        decimal_layout = QHBoxLayout(decimal_group)
        decimal_layout.setContentsMargins(6, 6, 6, 6)
        self.decimal_group = QButtonGroup(self)
        self.rb_dec0 = QRadioButton("0 (0)")
        self.rb_dec1 = QRadioButton("1 (0.0)")
        self.rb_dec2 = QRadioButton("2 (0.00)")
        self.rb_dec0.setChecked(True)
        self.decimal_group.addButton(self.rb_dec0, 0)
        self.decimal_group.addButton(self.rb_dec1, 1)
        self.decimal_group.addButton(self.rb_dec2, 2)
        decimal_layout.addWidget(self.rb_dec0)
        decimal_layout.addWidget(self.rb_dec1)
        decimal_layout.addWidget(self.rb_dec2)
        left_layout.addWidget(decimal_group)

        self.transfer_btn = QPushButton("Transfer to Vertical Group Phi")
        self.transfer_btn.clicked.connect(self._on_transfer_clicked)
        self.transfer_btn.setStyleSheet(self._button_stylesheet())
        self.transfer_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(self.transfer_btn)

        left_layout.addStretch(1)

        self.phase_table = QTableWidget(40, 2)
        self.phase_table.setMinimumWidth(0)
        self.phase_table.setMinimumHeight(0)
        self.phase_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.phase_table.setHorizontalHeaderLabels(["Bay", "Phase"])
        self.phase_table.verticalHeader().setVisible(False)
        self.phase_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.phase_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.phase_table.setColumnWidth(0, 42)
        self.phase_table.verticalHeader().setDefaultSectionSize(22)
        self.phase_table.setStyleSheet(
            """
            QTableWidget {
                background: white;
                gridline-color: #d0d0d0;
                border: 1px solid #b5b5b5;
            }
            QHeaderView::section {
                background-color: white;
                border: 1px solid #d0d0d0;
                padding: 2px;
                font-weight: bold;
            }
            """
        )
        for row in range(self.phase_table.rowCount()):
            bay_item = QTableWidgetItem(str(row + 1))
            bay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bay_item.setBackground(Qt.GlobalColor.lightGray)
            self.phase_table.setItem(row, 0, bay_item)
            phase_item = QTableWidgetItem("")
            phase_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.phase_table.setItem(row, 1, phase_item)

        splitter.addWidget(left_panel)
        splitter.addWidget(self.phase_table)
        splitter.setSizes([260, 180])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        enable_free_resize(splitter)

        main_layout.addWidget(splitter)

    def _button_stylesheet(self):
        return """
        QPushButton {
            background-color: #2f8edb;
            color: white;
            font-weight: bold;
            border: 1px solid #7cb8eb;
            border-radius: 3px;
            padding: 5px 8px;
        }
        QPushButton:hover {
            background-color: #3b99e4;
        }
        QPushButton:pressed {
            background-color: #247bc0;
        }
        """

    def _set_define_row(self, key, label, value):
        row = self.DEFINE_ROWS[key]
        label_item = QTableWidgetItem(label)
        value_item = QTableWidgetItem(value)
        self.define_table.setItem(row, 0, label_item)
        self.define_table.setItem(row, 1, value_item)

    def _clear_phase_table(self, *_args):
        self.current_result = None
        for row in range(self.phase_table.rowCount()):
            self.phase_table.item(row, 1).setText("")

    def _safe_table_float(self, row, default=0.0):
        item = self.define_table.item(row, 1)
        if item is None:
            return default
        try:
            return float(item.text().strip())
        except (TypeError, ValueError):
            return default

    def _current_solution(self):
        return "Oscillatory" if self.rb_oscillatory.isChecked() else "Non-Oscillatory"

    def _current_decimal_places(self):
        return self.decimal_group.checkedId() if self.decimal_group.checkedId() >= 0 else 0

    def _populate_phase_table(self, phases_deg, decimal_places):
        for row in range(self.phase_table.rowCount()):
            text = ""
            if row < len(phases_deg):
                text = format_phase_value(phases_deg[row], decimal_places)
            self.phase_table.item(row, 1).setText(text)

    def _collect_inputs(self):
        return {
            "frequency_mhz": self._safe_table_float(self.DEFINE_ROWS["frequency_mhz"], 539.0),
            "bay_count": self.bays_spin.value(),
            "beam_tilt_deg": self._safe_table_float(self.DEFINE_ROWS["beam_tilt_deg"], 1.0),
            "spacing_m": self._safe_table_float(self.DEFINE_ROWS["spacing_m"], 1.15),
            "null_fill_percent": self.null_fill_spin.value(),
            "solution": self._current_solution(),
        }

    def _on_calculate_clicked(self):
        try:
            self.current_result = calculate_beam_shape_phases(**self._collect_inputs())
            self._populate_phase_table(
                self.current_result.phases_deg,
                2,
            )
            self.message_generated.emit(
                f"Beam Shape calculated for {self.current_result.bay_count} bays using {self.current_result.solution.lower()} solution."
            )
        except Exception as error:
            self.current_result = None
            self._clear_phase_table()
            self.message_generated.emit(f"Beam Shape error: {error}")

    def _on_transfer_clicked(self):
        if self.current_result is None:
            self.message_generated.emit("Beam Shape phases must be calculated before transfer.")
            return

        decimal_places = self._current_decimal_places()
        self.phase_transfer_requested.emit(list(self.current_result.phases_deg), decimal_places)
        self.message_generated.emit("Beam Shape phases transferred to Vertical Group Phi.")

    def set_frequency(self, frequency_mhz: float):
        self.define_table.item(self.DEFINE_ROWS["frequency_mhz"], 1).setText(f"{float(frequency_mhz):g}")
        self._clear_phase_table()

    def update_frequency(self, frequency_mhz: float):
        self.set_frequency(frequency_mhz)

    def get_phase_values(self):
        if self.current_result is None:
            return []
        return list(self.current_result.phases_deg)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def sizeHint(self):
        return QSize(520, 320)
