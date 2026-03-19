import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets.splitter_utils import enable_free_resize


def _format_angle(value):
    return f"{float(value):0.1f}"


def _format_offset(value):
    return f"{float(value):0.3f}"


def _format_power(value):
    return f"{float(value):0.3f}"


def _azimuth_angle_deg(x_value, y_value):
    angle = math.degrees(math.atan2(float(x_value), float(y_value)))
    if angle < 0.0:
        angle += 360.0
    return angle


class AntennaDesignWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.face_labels = [chr(ord("A") + index) for index in range(26)]
        self.vertical_group_count = 100
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        self.main_splitter = splitter

        left_widget = QWidget()
        left_widget.setMinimumWidth(0)
        left_widget.setMinimumHeight(0)
        left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(4)

        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.setHandleWidth(8)
        self.left_splitter = left_splitter

        table_style = """
            QTableWidget { font-size: 9pt; }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 2px;
                border: 1px solid #c0c0c0;
                font-size: 9pt;
            }
        """

        h_group_box = QGroupBox("Horizontal Group Phi & Power")
        h_group_box.setMinimumHeight(0)
        h_group_layout = QVBoxLayout(h_group_box)
        h_group_layout.setContentsMargins(0, 5, 0, 0)

        self.h_group_table = QTableWidget(2, len(self.face_labels))
        self.h_group_table.setHorizontalHeaderLabels(self.face_labels)
        self.h_group_table.setVerticalHeaderLabels(["Phi", "Pwr"])
        self.h_group_table.setStyleSheet(table_style)
        self.h_group_table.verticalHeader().setDefaultSectionSize(20)
        self.h_group_table.horizontalHeader().setDefaultSectionSize(42)
        self.h_group_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        for col in range(len(self.face_labels)):
            self.h_group_table.setItem(0, col, QTableWidgetItem("0.0"))
            self.h_group_table.setItem(1, col, QTableWidgetItem("1.000"))

        h_group_layout.addWidget(self.h_group_table)
        left_splitter.addWidget(h_group_box)

        array_box = QGroupBox("Array Data")
        array_box.setMinimumHeight(0)
        array_layout = QVBoxLayout(array_box)
        array_layout.setContentsMargins(0, 5, 0, 0)

        self.array_table = QTableWidget(4, 13)
        headers = [
            "Panel",
            "Angle",
            "Offset",
            "Elev",
            "Az",
            "Pwr",
            "Phi",
            "Tilt",
            "Config\n(0-5)*",
            "Pat",
            "Level",
            "Face",
            "Input",
        ]
        self.array_table.setHorizontalHeaderLabels(headers)
        self.array_table.verticalHeader().setVisible(False)
        self.array_table.setStyleSheet(table_style)
        self.array_table.verticalHeader().setDefaultSectionSize(20)
        self.array_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.array_table.horizontalHeader().setStretchLastSection(False)

        for row in range(self.array_table.rowCount()):
            self._initialize_array_row(row)

        array_layout.addWidget(self.array_table)
        left_splitter.addWidget(array_box)
        left_splitter.setSizes([120, 420])
        enable_free_resize(left_splitter)
        left_layout.addWidget(left_splitter, 1)

        right_widget = QWidget()
        right_widget.setMinimumWidth(0)
        right_widget.setMinimumHeight(0)
        right_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        v_group_box = QGroupBox("Vertical Group Phi")
        v_group_box.setMinimumHeight(0)
        v_group_layout = QVBoxLayout(v_group_box)
        v_group_layout.setContentsMargins(0, 5, 0, 0)

        self.v_group_table = QTableWidget(self.vertical_group_count, 1)
        self.v_group_table.setVerticalHeaderLabels(
            [str(i) for i in range(1, self.vertical_group_count + 1)]
        )
        self.v_group_table.setHorizontalHeaderLabels(["Phi"])
        self.v_group_table.setStyleSheet(table_style)
        self.v_group_table.verticalHeader().setDefaultSectionSize(20)
        self.v_group_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        self.v_group_table.setColumnWidth(0, 76)

        for row in range(self.v_group_table.rowCount()):
            self.v_group_table.setItem(row, 0, QTableWidgetItem("0.0"))

        v_group_layout.addWidget(self.v_group_table)
        right_layout.addWidget(v_group_box)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([940, 140])
        splitter.setStretchFactor(0, 9)
        splitter.setStretchFactor(1, 3)
        enable_free_resize(splitter)

        main_layout.addWidget(splitter)

    def _ensure_item(self, table, row, col, text=""):
        item = table.item(row, col)
        if item is None:
            item = QTableWidgetItem(text)
            table.setItem(row, col, item)
        return item

    def _get_text(self, table, row, col, default=""):
        item = table.item(row, col)
        if item is None:
            return default
        value = item.text().strip()
        return value if value else default

    def _get_float(self, table, row, col, default=0.0):
        try:
            return float(str(self._get_text(table, row, col, default)).replace(",", "."))
        except ValueError:
            return default

    def _get_int(self, table, row, col, default=0):
        try:
            return int(float(self._get_text(table, row, col, default)))
        except ValueError:
            return default

    def _initialize_array_row(self, row):
        panel_item = self._ensure_item(self.array_table, row, 0, str(row + 1))
        panel_item.setText(str(row + 1))
        panel_item.setBackground(Qt.GlobalColor.lightGray)
        panel_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        defaults = [
            "0.0",
            "0.000",
            "0.000",
            "0.0",
            "1.000",
            "0.0",
            "0.0",
            "0",
            "1",
            "1",
            "A",
            "1",
        ]
        for col, value in enumerate(defaults, start=1):
            self._ensure_item(self.array_table, row, col, value).setText(value)

    def panel_number_changed(self, count):
        row_count = max(1, int(count))
        current_count = self.array_table.rowCount()
        self.array_table.setRowCount(row_count)
        for row in range(current_count, row_count):
            self._initialize_array_row(row)
        for row in range(row_count):
            self._initialize_array_row(row)

    def _row_count(self):
        return self.array_table.rowCount()

    def _get_row_geometry(self, row):
        angle_deg = self._get_float(self.array_table, row, 1, 0.0)
        offset_m = self._get_float(self.array_table, row, 2, 0.0)
        elevation_m = self._get_float(self.array_table, row, 3, 0.0)
        azimuth_deg = self._get_float(self.array_table, row, 4, 0.0)
        tilt_deg = self._get_float(self.array_table, row, 7, 0.0)

        x_value = offset_m * math.sin(math.radians(angle_deg))
        y_value = offset_m * math.cos(math.radians(angle_deg))
        return x_value, y_value, elevation_m, azimuth_deg, tilt_deg

    def _set_row_polar_geometry(self, row, x_value, y_value):
        angle_deg = _azimuth_angle_deg(x_value, y_value)
        offset_m = math.sqrt(x_value * x_value + y_value * y_value)
        self._ensure_item(self.array_table, row, 1, "0.0").setText(_format_angle(angle_deg))
        self._ensure_item(self.array_table, row, 2, "0.000").setText(_format_offset(offset_m))

    def get_horizontal_group_data(self):
        groups = {}
        for col, face in enumerate(self.face_labels):
            groups[face] = {
                "phase_deg": self._get_float(self.h_group_table, 0, col, 0.0),
                "power": self._get_float(self.h_group_table, 1, col, 1.0),
            }
        return groups

    def set_horizontal_group_data(self, groups):
        for col, face in enumerate(self.face_labels):
            group = groups.get(face, {})
            self._ensure_item(self.h_group_table, 0, col, "0.0").setText(
                f"{float(group.get('phase_deg', 0.0)):g}"
            )
            self._ensure_item(self.h_group_table, 1, col, "1.0").setText(
                f"{float(group.get('power', 1.0)):g}"
            )

    def get_vertical_group_data(self):
        groups = {}
        for row in range(self.v_group_table.rowCount()):
            level = row + 1
            groups[level] = {
                "phase_deg": self._get_float(self.v_group_table, row, 0, 0.0),
            }
        return groups

    def set_vertical_group_data(self, groups):
        row_count = max(self.vertical_group_count, max(groups.keys(), default=1))
        self.v_group_table.setRowCount(row_count)
        self.v_group_table.setVerticalHeaderLabels(
            [str(i) for i in range(1, row_count + 1)]
        )
        for row in range(row_count):
            level = row + 1
            group = groups.get(level, {})
            self._ensure_item(self.v_group_table, row, 0, "0.0").setText(
                f"{float(group.get('phase_deg', 0.0)):g}"
            )

    def update_v_group_phases(self, phases, decimal_places):
        row_count = max(self.v_group_table.rowCount(), len(phases), self.vertical_group_count)
        self.v_group_table.setRowCount(row_count)
        self.v_group_table.setVerticalHeaderLabels(
            [str(i) for i in range(1, row_count + 1)]
        )

        for row, phase in enumerate(phases):
            if decimal_places == 0:
                text = f"{round(float(phase), 0):0.0f}"
            elif decimal_places == 1:
                text = f"{round(float(phase), 1):0.1f}"
            else:
                text = f"{round(float(phase), 2):0.2f}"
            self._ensure_item(self.v_group_table, row, 0, text).setText(text)

    def rotate_array(self, rotarrayangle):
        for row in range(self._row_count()):
            current_angle = self._get_float(self.array_table, row, 1, 0.0)
            current_azimuth = self._get_float(self.array_table, row, 4, 0.0)
            self._ensure_item(self.array_table, row, 1, "0.0").setText(
                _format_angle(current_angle + rotarrayangle)
            )
            self._ensure_item(self.array_table, row, 4, "0.0").setText(
                _format_angle(current_azimuth + rotarrayangle)
            )

    def cog_array(self, cogarrayangle):
        for row in range(self._row_count()):
            level = self._get_int(self.array_table, row, 10, 1)
            if level % 2 != 0:
                continue

            current_angle = self._get_float(self.array_table, row, 1, 0.0)
            current_azimuth = self._get_float(self.array_table, row, 4, 0.0)
            self._ensure_item(self.array_table, row, 1, "0.0").setText(
                _format_angle(current_angle + cogarrayangle)
            )
            self._ensure_item(self.array_table, row, 4, "0.0").setText(
                _format_angle(current_azimuth + cogarrayangle)
            )

    def mech_tilt_array(self, mechtiltangle, tiltdir):
        if self._row_count() == 0:
            return

        max_z = max(self._get_float(self.array_table, row, 3, 0.0) for row in range(self._row_count()))
        max_z += 1e-5

        for row in range(self._row_count()):
            x_value, y_value, z_value, face_angle_deg, current_tilt = self._get_row_geometry(row)
            delta = (max_z - z_value) * math.tan(math.radians(mechtiltangle))
            delta_x = round(delta * math.sin(math.radians(tiltdir)), 5)
            delta_y = round(delta * math.cos(math.radians(tiltdir)), 5)

            x_value += delta_x
            y_value += delta_y
            self._set_row_polar_geometry(row, x_value, y_value)

            height_delta = max_z - z_value
            if abs(height_delta) < 1e-9:
                tilt_delta = mechtiltangle * math.cos(math.radians(tiltdir - face_angle_deg))
            else:
                projected_delta = delta * math.cos(math.radians(tiltdir - face_angle_deg))
                tilt_delta = math.degrees(math.atan(projected_delta / height_delta))

            self._ensure_item(self.array_table, row, 7, "0.0").setText(
                _format_angle(-1.0 * current_tilt + tilt_delta)
            )

    def build_geometry(self, faceno, offset, headingangle, levelno, spacing, cogged):
        faceno = max(1, int(faceno))
        levelno = max(1, int(levelno))
        self.panel_number_changed(faceno * levelno)

        step_angle = 360.0 / faceno
        cogarrayangle = step_angle / 2.0

        for row in range(self._row_count()):
            level = row // faceno + 1
            face_index = row % faceno
            face_label = self.face_labels[face_index]

            self._ensure_item(self.array_table, row, 2, "0.000").setText(_format_offset(offset))
            self._ensure_item(self.array_table, row, 3, "0.000").setText(
                _format_offset((row // faceno) * spacing)
            )
            self._ensure_item(self.array_table, row, 4, "0.0").setText(
                _format_angle(face_index * step_angle)
            )
            self._ensure_item(self.array_table, row, 10, "1").setText(str(level))
            self._ensure_item(self.array_table, row, 11, "A").setText(face_label)
            self._ensure_item(self.array_table, row, 12, "1").setText(
                "1" if row < self._row_count() / 2 else "2"
            )
            self._ensure_item(self.array_table, row, 5, "1.000").setText(_format_power(1.0))
            self._ensure_item(self.array_table, row, 6, "0.0").setText(_format_angle(0.0))
            self._ensure_item(self.array_table, row, 7, "0.0").setText(_format_angle(0.0))
            self._ensure_item(self.array_table, row, 8, "0").setText("0")
            self._ensure_item(self.array_table, row, 9, "1").setText("1")
            self._ensure_item(self.array_table, row, 1, "0.0").setText(
                _format_angle(face_index * step_angle)
            )

        if headingangle != 0.0:
            self.rotate_array(headingangle)
        if cogged:
            self.cog_array(cogarrayangle)

    def get_array_data(self):
        panels_data = []
        for row in range(self.array_table.rowCount()):
            has_content = any(
                self._get_text(self.array_table, row, col, "") for col in range(1, 13)
            )
            if not has_content:
                continue

            panel_id = self._get_int(self.array_table, row, 0, row + 1)
            angle_deg = self._get_float(self.array_table, row, 1, 0.0)
            offset_m = self._get_float(self.array_table, row, 2, 0.0)
            elevation_m = self._get_float(self.array_table, row, 3, 0.0)
            azimuth_deg = self._get_float(self.array_table, row, 4, 0.0)
            power = self._get_float(self.array_table, row, 5, 1.0)
            phase_deg = self._get_float(self.array_table, row, 6, 0.0)
            tilt_deg = self._get_float(self.array_table, row, 7, 0.0)
            configuration = self._get_int(self.array_table, row, 8, 0)
            pattern_index = self._get_int(self.array_table, row, 9, 1)
            level = self._get_int(self.array_table, row, 10, 1)
            face = self._get_text(
                self.array_table,
                row,
                11,
                self.face_labels[(level - 1) % len(self.face_labels)],
            ).upper()
            input_number = self._get_int(self.array_table, row, 12, 1)

            panels_data.append(
                {
                    "panel_id": panel_id,
                    "angle_deg": angle_deg,
                    "offset_m": offset_m,
                    "elevation_m": elevation_m,
                    "azimuth_deg": azimuth_deg,
                    "power": power,
                    "phase_deg": phase_deg,
                    "tilt_deg": tilt_deg,
                    "configuration": configuration,
                    "pattern_index": pattern_index,
                    "level": level,
                    "face": face,
                    "input_number": input_number,
                    "y": offset_m,
                    "phase": phase_deg,
                    "tilt": tilt_deg,
                    "pat": pattern_index,
                }
            )

        return panels_data

    def set_array_data(self, panels_data):
        row_count = max(4, len(panels_data))
        self.array_table.setRowCount(row_count)

        for row in range(row_count):
            self._initialize_array_row(row)

            if row >= len(panels_data):
                continue

            panel = panels_data[row]
            values = [
                panel.get("panel_id", row + 1),
                panel.get("angle_deg", 0.0),
                panel.get("offset_m", 0.0),
                panel.get("elevation_m", 0.0),
                panel.get("azimuth_deg", 0.0),
                panel.get("power", 1.0),
                panel.get("phase_deg", 0.0),
                panel.get("tilt_deg", 0.0),
                panel.get("configuration", 0),
                panel.get("pattern_index", 1),
                panel.get("level", 1),
                panel.get("face", "A"),
                panel.get("input_number", 1),
            ]

            for col, value in enumerate(values):
                item = self._ensure_item(self.array_table, row, col, str(value))
                item.setText(str(value))
