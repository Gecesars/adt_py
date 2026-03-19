from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QSplitter,
    QSizePolicy,
)
from widgets.splitter_utils import enable_free_resize


class ResultSummaryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.params = [
            "Channel Frequency (MHz)",
            "3D Directivity (dBd)",
            "Azimuth Angle (Emax) (deg)",
            "Elevation Angle (Emax) (deg)",
            "Internal Loss (dB)",
            "Polarisation Loss (dB)",
            "Filter/Combiner Loss (dB)",
            "Main Feeder Loss (dB)",
            "System Gain (dBd)",
            "Transmitter Power (kW)",
            "Transmitter Power (dBW)",
            "ERP (dBW)",
            "ERP (dBk)",
            "ERP (kW)",
        ]

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(8)
        self.splitter = splitter

        self.table = QTableWidget(len(self.params), 2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        for i, param in enumerate(self.params):
            self.table.setItem(i, 0, QTableWidgetItem(param))
            self.table.setItem(i, 1, QTableWidgetItem(""))

        splitter.addWidget(self.table)

        point_widget = QWidget()
        point_widget.setMinimumHeight(0)
        point_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 0, 0, 0)
        point_layout.setSpacing(4)

        self.point_table = QTableWidget(1, 4)
        self.point_table.setHorizontalHeaderLabels(
            ["Azimuth\nAngle", "Elevation\nAngle", "Relative Field\n(E/Emax)", "Power from\nPeak (dB)"]
        )
        self.point_table.verticalHeader().setVisible(False)
        self.point_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.point_table.verticalHeader().setDefaultSectionSize(22)
        self.point_table.setItem(0, 0, QTableWidgetItem("359"))
        self.point_table.setItem(0, 1, QTableWidgetItem("0.0"))
        self.point_table.setItem(0, 2, QTableWidgetItem("1.0000"))
        self.point_table.setItem(0, 3, QTableWidgetItem("0.00"))
        point_layout.addWidget(self.point_table)

        self.find_btn = QPushButton("Find")
        self.find_btn.setStyleSheet(
            "background-color: #0078D7; color: white; font-weight: bold; min-width: 92px;"
        )
        point_layout.addWidget(self.find_btn, 0)

        splitter.addWidget(point_widget)
        splitter.setSizes([316, 155])
        enable_free_resize(splitter)

        layout.addWidget(splitter)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def sizeHint(self):
        return QSize(320, 500)

    def update_results(self, metrics_dict):
        for i, param in enumerate(self.params):
            val = metrics_dict.get(param, "")
            self.table.item(i, 1).setText(str(val))

    def clear_results(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, 1).setText("")
        self.set_point_info("", "", "", "")

    def set_point_info(
        self,
        azimuth_deg=None,
        elevation_deg=None,
        relative_field=None,
        power_from_peak_db=None,
    ):
        values = [
            "" if azimuth_deg is None else str(azimuth_deg),
            "" if elevation_deg is None else str(elevation_deg),
            "" if relative_field is None else str(relative_field),
            "" if power_from_peak_db is None else str(power_from_peak_db),
        ]
        for col, value in enumerate(values):
            item = self.point_table.item(0, col)
            if item is None:
                item = QTableWidgetItem("")
                self.point_table.setItem(0, col, item)
            item.setText(value)
