from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt, QLocale, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QSpinBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


BUTTON_STYLESHEET = """
QPushButton {
    background-color: #2f8edb;
    color: white;
    font-weight: bold;
    border: 1px solid #7cb8eb;
    border-radius: 3px;
    padding: 6px 10px;
}
QPushButton:hover {
    background-color: #3b99e4;
}
QPushButton:pressed {
    background-color: #247bc0;
}
"""

TABLE_STYLESHEET = """
QTableWidget {
    background: white;
    gridline-color: #cfcfcf;
    border: 1px solid #b9b9b9;
}
QTableWidget::item {
    padding: 2px 4px;
}
QHeaderView::section {
    background-color: #efefef;
    border: 1px solid #c0c0c0;
    padding: 2px;
}
QComboBox, QLineEdit, QAbstractSpinBox {
    background: white;
    border: 1px solid #b8b8b8;
    padding: 1px 4px;
    min-height: 20px;
}
"""


def _safe_float(value, default):
    try:
        text = str(value).strip().replace(",", ".")
        return float(text)
    except (TypeError, ValueError):
        return default


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


@dataclass
class PreviewPanel:
    x: float
    y: float
    z: float
    width: float
    height: float
    depth: float
    face_angle_deg: float
    tilt_deg: float


class TowerPreviewWidget(QWidget):
    VIEW_PRESETS = {
        "Side View (Left)": (-90.0, 0.0),
        "Side View (Right)": (90.0, 0.0),
        "Side View (Front)": (180.0, 0.0),
        "Side View (Back)": (0.0, 0.0),
        "Top View": (0.0, 90.0),
        "Bottom View": (0.0, -90.0),
    }

    def __init__(self):
        super().__init__()
        self.panels: list[PreviewPanel] = []
        self.tower_half_width_m = 0.17
        self.view_preset = "Side View (Back)"
        self.view_rotation_deg = 0.0
        self.view_elevation_deg = 0.0
        self.zoom_percent = 100.0
        self.setMinimumHeight(360)
        self.setAutoFillBackground(True)
        self.setObjectName("towerPreviewWidget")

    def _topdown_tower_half_width(self):
        # The original ADT top view is slightly schematic rather than a strict
        # physical projection, so keep the tower a bit more prominent.
        return self.tower_half_width_m * 1.08

    def set_scene(self, panels, tower_half_width_m=None):
        self.panels = list(panels)
        if tower_half_width_m is not None:
            self.tower_half_width_m = max(0.06, float(tower_half_width_m))
        self.update()

    def set_view_preset(self, preset_name):
        self.view_preset = preset_name
        self.update()

    def set_view_controls(self, rotation_deg, elevation_deg, zoom_percent):
        self.view_rotation_deg = float(rotation_deg)
        self.view_elevation_deg = float(elevation_deg)
        self.zoom_percent = float(zoom_percent)
        self.update()

    def _rotate_point(self, x_value, y_value, z_value, yaw_deg, pitch_deg):
        yaw_rad = math.radians(yaw_deg)
        pitch_rad = math.radians(pitch_deg)

        x_yaw = x_value * math.cos(yaw_rad) - y_value * math.sin(yaw_rad)
        y_yaw = x_value * math.sin(yaw_rad) + y_value * math.cos(yaw_rad)
        z_yaw = z_value

        y_pitch = y_yaw * math.cos(pitch_rad) - z_yaw * math.sin(pitch_rad)
        z_pitch = y_yaw * math.sin(pitch_rad) + z_yaw * math.cos(pitch_rad)
        return x_yaw, y_pitch, z_pitch

    def _panel_corners(self, panel):
        half_width = panel.width / 2.0
        half_depth = panel.depth / 2.0
        half_height = panel.height / 2.0
        tilt_rad = math.radians(panel.tilt_deg)
        yaw_rad = math.radians(panel.face_angle_deg)

        corners = []
        for local_x in (-half_width, half_width):
            for local_y in (-half_depth, half_depth):
                for local_z in (-half_height, half_height):
                    tilted_y = local_y * math.cos(tilt_rad) - local_z * math.sin(tilt_rad)
                    tilted_z = local_y * math.sin(tilt_rad) + local_z * math.cos(tilt_rad)

                    global_x = local_x * math.cos(yaw_rad) - tilted_y * math.sin(yaw_rad)
                    global_y = local_x * math.sin(yaw_rad) + tilted_y * math.cos(yaw_rad)
                    global_z = tilted_z
                    corners.append(
                        (
                            panel.x + global_x,
                            panel.y + global_y,
                            panel.z + global_z,
                        )
                    )
        return corners

    def _scene_points(self):
        if not self.panels:
            return []

        points = []
        points.extend(self._tower_corners())

        for panel in self.panels:
            points.extend(self._panel_corners(panel))

        return points

    def _project_3d(self, point):
        base_yaw, base_pitch = self.VIEW_PRESETS.get(self.view_preset, (0.0, 0.0))
        return self._rotate_point(
            point[0],
            point[1],
            point[2],
            base_yaw + self.view_rotation_deg,
            base_pitch + self.view_elevation_deg,
        )

    def _project(self, point):
        x_value, _y_value, z_value = self._project_3d(point)
        return x_value, z_value

    def _tower_corners(self):
        if not self.panels:
            return []

        min_z = min(panel.z - panel.height / 2.0 for panel in self.panels)
        max_z = max(panel.z + panel.height / 2.0 for panel in self.panels)
        half_width = self.tower_half_width_m
        return [
            (-half_width, -half_width, min_z),
            (half_width, -half_width, min_z),
            (half_width, half_width, min_z),
            (-half_width, half_width, min_z),
            (-half_width, -half_width, max_z),
            (half_width, -half_width, max_z),
            (half_width, half_width, max_z),
            (-half_width, half_width, max_z),
        ]

    def _fit_transform(self):
        points = self._scene_points()
        if not points:
            return 1.0, QPointF(self.width() / 2.0, self.height() / 2.0)

        projected = [self._project(point) for point in points]
        min_x = min(point[0] for point in projected)
        max_x = max(point[0] for point in projected)
        min_y = min(point[1] for point in projected)
        max_y = max(point[1] for point in projected)

        width = max(max_x - min_x, 1e-6)
        height = max(max_y - min_y, 1e-6)
        padding = 40.0
        scale = min(
            (self.width() - padding * 2.0) / width,
            (self.height() - padding * 2.0) / height,
        )
        scale *= self.zoom_percent / 100.0

        center = QPointF((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        return scale, center

    def _is_topdown_view(self):
        return self.view_preset in {"Top View", "Bottom View"}

    def _rotate_topdown_point(self, x_value, y_value):
        rotation_deg = float(self.view_rotation_deg)
        if self.view_preset == "Bottom View":
            rotation_deg += 180.0
        rotation_rad = math.radians(rotation_deg)
        rotated_x = x_value * math.cos(rotation_rad) - y_value * math.sin(rotation_rad)
        rotated_y = x_value * math.sin(rotation_rad) + y_value * math.cos(rotation_rad)
        return rotated_x, rotated_y

    def _tower_topdown_polygon(self):
        half_width = self._topdown_tower_half_width()
        points = [
            (-half_width, half_width),
            (half_width, half_width),
            (half_width, -half_width),
            (-half_width, -half_width),
        ]
        return [self._rotate_topdown_point(x_value, y_value) for x_value, y_value in points]

    def _panel_topdown_polygon(self, panel):
        face_angle_rad = math.radians(panel.face_angle_deg)
        radial_x = math.sin(face_angle_rad)
        radial_y = math.cos(face_angle_rad)
        tangent_x = math.cos(face_angle_rad)
        tangent_y = -math.sin(face_angle_rad)

        actual_radius = math.hypot(panel.x, panel.y)
        visual_tower_half_width = self._topdown_tower_half_width()

        # Match the original ADT preview better: the top view compresses panel
        # depth and width visually while preserving orientation and relative order.
        display_width = panel.width * 0.78
        display_depth = max(panel.depth * 0.58, panel.width * 0.18)
        inner_half_width = display_width / 2.0
        outer_half_width = max(display_width * 0.28, inner_half_width * 0.68)

        actual_inner_gap = max(
            0.0,
            actual_radius - panel.depth / 2.0 - self.tower_half_width_m,
        )
        display_inner_gap = min(0.014, 0.004 + actual_inner_gap * 0.35)
        display_radius = (
            visual_tower_half_width
            + display_inner_gap
            + display_depth / 2.0
            + actual_inner_gap * 0.25
        )

        inner_center_x = radial_x * (display_radius - display_depth / 2.0)
        inner_center_y = radial_y * (display_radius - display_depth / 2.0)
        outer_center_x = radial_x * (display_radius + display_depth / 2.0)
        outer_center_y = radial_y * (display_radius + display_depth / 2.0)

        points = [
            (
                inner_center_x - tangent_x * inner_half_width,
                inner_center_y - tangent_y * inner_half_width,
            ),
            (
                inner_center_x + tangent_x * inner_half_width,
                inner_center_y + tangent_y * inner_half_width,
            ),
            (
                outer_center_x + tangent_x * outer_half_width,
                outer_center_y + tangent_y * outer_half_width,
            ),
            (
                outer_center_x - tangent_x * outer_half_width,
                outer_center_y - tangent_y * outer_half_width,
            ),
        ]
        return [self._rotate_topdown_point(x_value, y_value) for x_value, y_value in points]

    def _topdown_scene_points(self):
        if not self.panels:
            return []

        points = list(self._tower_topdown_polygon())
        for panel in self.panels:
            points.extend(self._panel_topdown_polygon(panel))
        return points

    def _fit_topdown_transform(self):
        points = self._topdown_scene_points()
        if not points:
            return 1.0, QPointF(self.width() / 2.0, self.height() / 2.0)

        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_y = max(point[1] for point in points)

        width = max(max_x - min_x, 1e-6)
        height = max(max_y - min_y, 1e-6)
        padding = 42.0
        scale = min(
            (self.width() - padding * 2.0) / width,
            (self.height() - padding * 2.0) / height,
        )
        scale *= self.zoom_percent / 100.0
        center = QPointF((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        return scale, center

    def _to_topdown_screen(self, point, scale, center):
        screen_x = self.width() / 2.0 + (point[0] - center.x()) * scale
        screen_y = self.height() / 2.0 - (point[1] - center.y()) * scale
        return QPointF(screen_x, screen_y)

    def _draw_topdown_scene(self, painter):
        scale, center = self._fit_topdown_transform()

        tower_pen = QPen(QColor("#31aab1"), 1.6)
        tower_fill = QColor("#f5f5f5")
        panel_pen = QPen(QColor("#2d2d2d"), 1.25)
        panel_fill = QColor("#ffffff")
        cross_pen = QPen(QColor("#787878"), 1.1)

        tower_points = [
            self._to_topdown_screen(point, scale, center)
            for point in self._tower_topdown_polygon()
        ]
        painter.setPen(tower_pen)
        painter.setBrush(tower_fill)
        painter.drawPolygon(QPolygonF(tower_points))

        left = min(point.x() for point in tower_points)
        right = max(point.x() for point in tower_points)
        top = min(point.y() for point in tower_points)
        bottom = max(point.y() for point in tower_points)
        inner_margin = min(right - left, bottom - top) * 0.16
        left += inner_margin
        right -= inner_margin
        top += inner_margin
        bottom -= inner_margin
        painter.setPen(cross_pen)
        painter.drawLine(QPointF(left, top), QPointF(right, bottom))
        painter.drawLine(QPointF(left, bottom), QPointF(right, top))

        painter.setPen(panel_pen)
        painter.setBrush(panel_fill)
        for panel in self.panels:
            panel_points = [
                self._to_topdown_screen(point, scale, center)
                for point in self._panel_topdown_polygon(panel)
            ]
            painter.drawPolygon(QPolygonF(panel_points))

    def _to_screen(self, point, scale, center):
        projected_x, projected_y = self._project(point)
        screen_x = self.width() / 2.0 + (projected_x - center.x()) * scale
        screen_y = self.height() / 2.0 - (projected_y - center.y()) * scale
        return QPointF(screen_x, screen_y)

    def _draw_box(self, painter, corners, scale, center, pen):
        edges = [
            (0, 1), (1, 3), (3, 2), (2, 0),
            (4, 5), (5, 7), (7, 6), (6, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        painter.setPen(pen)
        screen_points = [self._to_screen(point, scale, center) for point in corners]
        for start_index, end_index in edges:
            painter.drawLine(screen_points[start_index], screen_points[end_index])

    def _draw_solid_box(self, painter, corners, scale, center, edge_pen, fill_color):
        faces = [
            (0, 1, 3, 2),
            (4, 5, 7, 6),
            (0, 1, 5, 4),
            (1, 3, 7, 5),
            (3, 2, 6, 7),
            (2, 0, 4, 6),
        ]

        projected_3d = [self._project_3d(point) for point in corners]
        screen_points = [self._to_screen(point, scale, center) for point in corners]

        ordered_faces = sorted(
            faces,
            key=lambda face: sum(projected_3d[index][1] for index in face) / len(face),
        )

        for face in ordered_faces:
            polygon = QPolygonF([screen_points[index] for index in face])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill_color)
            painter.drawPolygon(polygon)

        self._draw_box(painter, corners, scale, center, edge_pen)

    def _draw_axes(self, painter):
        origin = QPointF(self.width() - 92.0, 62.0)
        painter.setFont(QFont("Segoe UI", 8))

        axis_specs = [
            ("X", (1.0, 0.0, 0.0), QColor("#3ba83d")),
            ("Y (N)", (0.0, 1.0, 0.0), QColor("#3557ff")),
            ("Z", (0.0, 0.0, 1.0), QColor("#d63b3b")),
        ]

        for label, vector, color in axis_specs:
            projected = self._project_3d(vector)
            screen_vector = QPointF(projected[0], -projected[2])
            length = math.hypot(screen_vector.x(), screen_vector.y())
            if length < 1e-9:
                continue

            scale = 34.0 / length
            end_point = QPointF(
                origin.x() + screen_vector.x() * scale,
                origin.y() + screen_vector.y() * scale,
            )
            painter.setPen(QPen(color, 2))
            painter.drawLine(origin, end_point)
            painter.drawRect(
                QRectF(end_point.x() - 3.0, end_point.y() - 3.0, 6.0, 6.0)
            )
            painter.drawText(
                QPointF(end_point.x() + 6.0, end_point.y() + 3.0),
                label,
            )

    def _view_heading_deg(self):
        base_yaw, _base_pitch = self.VIEW_PRESETS.get(self.view_preset, (0.0, 0.0))
        return float((180.0 - (base_yaw + self.view_rotation_deg)) % 360.0)

    def _draw_view_caption(self, painter):
        painter.setPen(QColor("#404040"))
        painter.setFont(QFont("Segoe UI", 8))

        if "Top" in self.view_preset or "Bottom" in self.view_preset:
            text = self.view_preset
        else:
            text = f"Side View: Looking Towards {int(round(self._view_heading_deg()))} degrees"

        painter.drawText(
            QRectF(10.0, self.height() - 24.0, self.width() - 20.0, 16.0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            text,
        )

    def _draw_viewport_frame(self, painter):
        painter.setPen(QPen(QColor("#c4c4c4"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        if not self.panels:
            painter.setPen(QPen(QColor("#7a7a7a"), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No tower layout data")
            self._draw_viewport_frame(painter)
            return

        if self._is_topdown_view():
            self._draw_topdown_scene(painter)
            self._draw_axes(painter)
            self._draw_viewport_frame(painter)
            return

        scale, center = self._fit_transform()
        tower_pen = QPen(QColor("#6c6c6c"), 1.0)
        panel_pen = QPen(QColor("#188f95"), 1.3)
        tower_fill = QColor("#f3f3f3")
        tower_fill.setAlpha(255)
        panel_fill = QColor("#d9fbfc")
        panel_fill.setAlpha(180)

        self._draw_solid_box(painter, self._tower_corners(), scale, center, tower_pen, tower_fill)

        for panel in self.panels:
            self._draw_solid_box(
                painter,
                self._panel_corners(panel),
                scale,
                center,
                panel_pen,
                panel_fill,
            )

        self._draw_axes(painter)
        self._draw_viewport_frame(painter)


class TowerLayoutWidget(QWidget):
    rotation_apply_requested = pyqtSignal(float)
    tilt_apply_requested = pyqtSignal(float, float)
    geometry_generate_requested = pyqtSignal(int, float, float, int, float, bool)
    rotation_reset_requested = pyqtSignal()
    tilt_reset_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.preview_panels = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: normal;
                border: 1px solid #c9c9c9;
                margin-top: 6px;
                background: #f8f8f8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 2px 0 2px;
            }
            QToolButton {
                background: #f4f4f4;
                border: 1px solid #c4c4c4;
                min-width: 24px;
                min-height: 22px;
            }
            QToolButton:disabled {
                color: #8d8d8d;
            }
            QLabel {
                color: #222222;
            }
            QWidget#viewControlPanel {
                background: transparent;
            }
            QWidget#previewHost {
                background: white;
                border: 1px solid #c4c4c4;
            }
            """
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(8)

        rotation_group = QGroupBox()
        rotation_layout = QVBoxLayout(rotation_group)
        rotation_layout.setContentsMargins(6, 6, 6, 6)
        rotation_layout.setSpacing(6)

        self.rotation_table = QTableWidget(1, 2)
        self.rotation_table.setStyleSheet(TABLE_STYLESHEET)
        self.rotation_table.horizontalHeader().setVisible(False)
        self.rotation_table.verticalHeader().setVisible(False)
        self.rotation_table.setShowGrid(True)
        self.rotation_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.rotation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rotation_table.setItem(0, 0, QTableWidgetItem("Rotate Array (deg)"))
        self.rotation_spin = NoWheelDoubleSpinBox()
        self.rotation_spin.setRange(-720.0, 720.0)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSingleStep(0.1)
        self.rotation_spin.setValue(0.0)
        self.rotation_spin.setStyleSheet(TABLE_STYLESHEET)
        self.rotation_table.setCellWidget(0, 1, self.rotation_spin)
        rotation_layout.addWidget(self.rotation_table)

        rotation_buttons = QHBoxLayout()
        self.rotation_reset_btn = QPushButton("Reset")
        self.rotation_apply_btn = QPushButton("Apply")
        self.rotation_reset_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.rotation_apply_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.rotation_reset_btn.clicked.connect(self.rotation_reset_requested.emit)
        self.rotation_apply_btn.clicked.connect(self._emit_rotation_apply)
        rotation_buttons.addWidget(self.rotation_reset_btn)
        rotation_buttons.addWidget(self.rotation_apply_btn)
        rotation_layout.addLayout(rotation_buttons)
        left_layout.addWidget(rotation_group)

        tilt_group = QGroupBox("Mechanical Tilt")
        tilt_layout = QVBoxLayout(tilt_group)
        tilt_layout.setContentsMargins(6, 6, 6, 6)
        tilt_layout.setSpacing(6)

        self.tilt_table = QTableWidget(2, 2)
        self.tilt_table.setStyleSheet(TABLE_STYLESHEET)
        self.tilt_table.horizontalHeader().setVisible(False)
        self.tilt_table.verticalHeader().setVisible(False)
        self.tilt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tilt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tilt_table.setItem(0, 0, QTableWidgetItem("Mechanical Tilt (deg)"))
        self.tilt_table.setItem(1, 0, QTableWidgetItem("Direction of Tilt (deg)"))

        self.mech_tilt_spin = NoWheelDoubleSpinBox()
        self.mech_tilt_spin.setRange(-10.0, 10.0)
        self.mech_tilt_spin.setDecimals(1)
        self.mech_tilt_spin.setSingleStep(0.1)
        self.mech_tilt_spin.setValue(0.0)
        self.mech_tilt_spin.setStyleSheet(TABLE_STYLESHEET)

        self.tilt_direction_spin = NoWheelDoubleSpinBox()
        self.tilt_direction_spin.setRange(0.0, 360.0)
        self.tilt_direction_spin.setDecimals(1)
        self.tilt_direction_spin.setSingleStep(0.1)
        self.tilt_direction_spin.setValue(0.0)
        self.tilt_direction_spin.setStyleSheet(TABLE_STYLESHEET)

        self.tilt_table.setCellWidget(0, 1, self.mech_tilt_spin)
        self.tilt_table.setCellWidget(1, 1, self.tilt_direction_spin)
        tilt_layout.addWidget(self.tilt_table)

        tilt_buttons = QHBoxLayout()
        self.tilt_reset_btn = QPushButton("Reset")
        self.tilt_apply_btn = QPushButton("Apply")
        self.tilt_reset_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.tilt_apply_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.tilt_reset_btn.clicked.connect(self.tilt_reset_requested.emit)
        self.tilt_apply_btn.clicked.connect(self._emit_tilt_apply)
        tilt_buttons.addWidget(self.tilt_reset_btn)
        tilt_buttons.addWidget(self.tilt_apply_btn)
        tilt_layout.addLayout(tilt_buttons)
        left_layout.addWidget(tilt_group)

        geometry_group = QGroupBox()
        geometry_layout = QVBoxLayout(geometry_group)
        geometry_layout.setContentsMargins(6, 6, 6, 6)
        geometry_layout.setSpacing(6)

        self.geometry_table = QTableWidget(6, 2)
        self.geometry_table.setStyleSheet(TABLE_STYLESHEET)
        self.geometry_table.horizontalHeader().setVisible(False)
        self.geometry_table.verticalHeader().setVisible(False)
        self.geometry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.geometry_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        labels = [
            "Number of faces on each level",
            "Panel offset from array centre (m)",
            "First panel at heading (deg)",
            "Number of levels",
            "Vertical spacing between levels (m)",
            "Alternate levels cogged",
        ]
        for row, label in enumerate(labels):
            self.geometry_table.setItem(row, 0, QTableWidgetItem(label))

        self.face_count_spin = NoWheelSpinBox()
        self.face_count_spin.setRange(1, 20)
        self.face_count_spin.setValue(4)
        self.face_count_spin.setStyleSheet(TABLE_STYLESHEET)

        self.offset_spin = NoWheelDoubleSpinBox()
        self.offset_spin.setRange(0.0, 100.0)
        self.offset_spin.setDecimals(3)
        self.offset_spin.setSingleStep(0.001)
        self.offset_spin.setValue(0.340)
        self.offset_spin.setStyleSheet(TABLE_STYLESHEET)

        self.heading_spin = NoWheelDoubleSpinBox()
        self.heading_spin.setRange(-359.99, 359.99)
        self.heading_spin.setDecimals(1)
        self.heading_spin.setSingleStep(0.1)
        self.heading_spin.setValue(0.0)
        self.heading_spin.setStyleSheet(TABLE_STYLESHEET)

        self.level_count_spin = NoWheelSpinBox()
        self.level_count_spin.setRange(1, 20)
        self.level_count_spin.setValue(4)
        self.level_count_spin.setStyleSheet(TABLE_STYLESHEET)

        self.spacing_spin = NoWheelDoubleSpinBox()
        self.spacing_spin.setRange(0.001, 100.0)
        self.spacing_spin.setDecimals(3)
        self.spacing_spin.setSingleStep(0.001)
        self.spacing_spin.setValue(1.150)
        self.spacing_spin.setStyleSheet(TABLE_STYLESHEET)

        self.cogged_checkbox = QCheckBox()
        self.cogged_checkbox.setChecked(False)

        self.geometry_table.setCellWidget(0, 1, self.face_count_spin)
        self.geometry_table.setCellWidget(1, 1, self.offset_spin)
        self.geometry_table.setCellWidget(2, 1, self.heading_spin)
        self.geometry_table.setCellWidget(3, 1, self.level_count_spin)
        self.geometry_table.setCellWidget(4, 1, self.spacing_spin)
        self.geometry_table.setCellWidget(5, 1, self.cogged_checkbox)
        geometry_layout.addWidget(self.geometry_table)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.generate_btn.clicked.connect(self._emit_generate_geometry)
        geometry_layout.addWidget(self.generate_btn)
        left_layout.addWidget(geometry_group)
        left_layout.addStretch(1)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        top_toolbar = QHBoxLayout()
        top_toolbar.setContentsMargins(0, 0, 0, 0)
        top_toolbar.setSpacing(4)

        for icon in (
            QStyle.StandardPixmap.SP_FileDialogContentsView,
            QStyle.StandardPixmap.SP_DialogSaveButton,
            QStyle.StandardPixmap.SP_ArrowUp,
            QStyle.StandardPixmap.SP_BrowserReload,
            QStyle.StandardPixmap.SP_DialogResetButton,
        ):
            button = QToolButton()
            button.setEnabled(False)
            button.setIcon(self.style().standardIcon(icon))
            button.setFixedSize(24, 22)
            top_toolbar.addWidget(button)

        self.view_combo = QComboBox()
        self.view_combo.setStyleSheet(TABLE_STYLESHEET)
        self.view_combo.addItems(list(TowerPreviewWidget.VIEW_PRESETS.keys()))
        self.view_combo.setCurrentText("Side View (Back)")
        self.view_combo.setFixedWidth(190)
        self.view_combo.currentTextChanged.connect(self._update_preview_view)
        top_toolbar.addWidget(self.view_combo)

        self.secondary_view_combo = QComboBox()
        self.secondary_view_combo.setStyleSheet(TABLE_STYLESHEET)
        self.secondary_view_combo.addItems(["Top View", "Bottom View"])
        self.secondary_view_combo.setFixedWidth(120)
        self.secondary_view_combo.currentTextChanged.connect(
            self._sync_secondary_view_preset
        )
        top_toolbar.addWidget(self.secondary_view_combo)
        top_toolbar.addStretch(1)
        right_layout.addLayout(top_toolbar)

        view_controls_layout = QGridLayout()
        view_controls_layout.setContentsMargins(0, 0, 0, 0)
        view_controls_layout.setHorizontalSpacing(6)
        view_controls_layout.setVerticalSpacing(4)

        self.view_rotation_spin = NoWheelSpinBox()
        self.view_rotation_spin.setRange(-180, 180)
        self.view_rotation_spin.setValue(0)
        self.view_rotation_spin.setStyleSheet(TABLE_STYLESHEET)
        self.view_rotation_spin.valueChanged.connect(self._update_preview_view)

        self.view_elevation_spin = NoWheelSpinBox()
        self.view_elevation_spin.setRange(-90, 90)
        self.view_elevation_spin.setValue(0)
        self.view_elevation_spin.setStyleSheet(TABLE_STYLESHEET)
        self.view_elevation_spin.valueChanged.connect(self._update_preview_view)

        self.view_zoom_spin = NoWheelSpinBox()
        self.view_zoom_spin.setRange(10, 400)
        self.view_zoom_spin.setValue(100)
        self.view_zoom_spin.setStyleSheet(TABLE_STYLESHEET)
        self.view_zoom_spin.valueChanged.connect(self._update_preview_view)
        for spin_box in (
            self.view_rotation_spin,
            self.view_elevation_spin,
            self.view_zoom_spin,
        ):
            spin_box.setFixedWidth(60)

        view_controls_layout.addWidget(QLabel("Rotation"), 0, 0)
        view_controls_layout.addWidget(self.view_rotation_spin, 0, 1)
        view_controls_layout.addWidget(QLabel("Elevation"), 1, 0)
        view_controls_layout.addWidget(self.view_elevation_spin, 1, 1)
        view_controls_layout.addWidget(QLabel("Zoom"), 2, 0)
        view_controls_layout.addWidget(self.view_zoom_spin, 2, 1)

        self.reset_view_btn = QPushButton("Reset View")
        self.reset_view_btn.setStyleSheet(BUTTON_STYLESHEET)
        self.reset_view_btn.clicked.connect(self.reset_view)
        view_controls_layout.addWidget(self.reset_view_btn, 3, 0, 1, 2)
        self.reset_view_btn.setFixedWidth(98)

        view_panel = QWidget()
        view_panel.setObjectName("viewControlPanel")
        view_panel.setFixedWidth(118)
        view_panel_layout = QVBoxLayout(view_panel)
        view_panel_layout.setContentsMargins(0, 6, 0, 0)
        view_panel_layout.setSpacing(6)
        view_panel_layout.addLayout(view_controls_layout)
        view_panel_layout.addStretch(1)

        preview_host = QWidget()
        preview_host.setObjectName("previewHost")
        preview_host_layout = QVBoxLayout(preview_host)
        preview_host_layout.setContentsMargins(0, 0, 0, 0)
        preview_host_layout.setSpacing(0)

        self.preview_widget = TowerPreviewWidget()
        preview_host_layout.addWidget(self.preview_widget)

        preview_body_layout = QHBoxLayout()
        preview_body_layout.setContentsMargins(0, 0, 0, 0)
        preview_body_layout.setSpacing(8)
        preview_body_layout.addWidget(view_panel, 0, Qt.AlignmentFlag.AlignTop)
        preview_body_layout.addWidget(preview_host, 1)

        right_layout.addLayout(preview_body_layout, 1)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([410, 690])
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 7)

        layout.addWidget(splitter)

    def _emit_rotation_apply(self):
        self.rotation_apply_requested.emit(float(self.rotation_spin.value()))

    def _emit_tilt_apply(self):
        self.tilt_apply_requested.emit(
            float(self.mech_tilt_spin.value()),
            float(self.tilt_direction_spin.value()),
        )

    def _emit_generate_geometry(self):
        self.geometry_generate_requested.emit(
            int(self.face_count_spin.value()),
            float(self.offset_spin.value()),
            float(self.heading_spin.value()),
            int(self.level_count_spin.value()),
            float(self.spacing_spin.value()),
            bool(self.cogged_checkbox.isChecked()),
        )

    def reset_rotation_to_zero(self):
        self.rotation_spin.setValue(0.0)

    def reset_tilt_to_zero(self):
        self.mech_tilt_spin.setValue(0.0)
        self.tilt_direction_spin.setValue(0.0)

    def reset_view(self):
        self.view_combo.setCurrentText("Side View (Back)")
        self.view_rotation_spin.setValue(0)
        self.view_elevation_spin.setValue(0)
        self.view_zoom_spin.setValue(100)
        self._update_preview_view()

    def _update_preview_view(self, *_args):
        self.preview_widget.set_view_preset(self.view_combo.currentText())
        self.preview_widget.set_view_controls(
            self.view_rotation_spin.value(),
            self.view_elevation_spin.value(),
            self.view_zoom_spin.value(),
        )

    def _sync_secondary_view_preset(self, preset_name):
        if preset_name and preset_name in TowerPreviewWidget.VIEW_PRESETS:
            self.view_combo.setCurrentText(preset_name)

    def update_preview(self, array_data, pattern_configs):
        panels = []
        tower_clearances = []
        for panel in array_data:
            pattern_config = pattern_configs.get(int(panel.get("pattern_index", 1)), {})
            width_m = _safe_float(pattern_config.get("width_m"), 0.5)
            height_m = _safe_float(pattern_config.get("height_m"), 1.09)
            depth_m = _safe_float(pattern_config.get("depth_m"), 0.22)

            angle_deg = _safe_float(panel.get("angle_deg"), 0.0)
            offset_m = _safe_float(panel.get("offset_m"), 0.0)
            x_value = offset_m * math.sin(math.radians(angle_deg))
            y_value = offset_m * math.cos(math.radians(angle_deg))
            tower_clearances.append(max(0.06, offset_m - depth_m / 2.0))
            panels.append(
                PreviewPanel(
                    x=x_value,
                    y=y_value,
                    z=_safe_float(panel.get("elevation_m"), 0.0),
                    width=width_m,
                    height=height_m,
                    depth=depth_m,
                    face_angle_deg=_safe_float(panel.get("azimuth_deg"), 0.0),
                    tilt_deg=_safe_float(panel.get("tilt_deg"), 0.0),
                )
            )

        tower_half_width_m = min(tower_clearances, default=0.17) * 0.95
        self.preview_widget.set_scene(panels, tower_half_width_m=tower_half_width_m)
        self._update_preview_view()
