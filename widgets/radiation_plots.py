from __future__ import annotations

from PyQt6.QtCore import Qt, QLocale, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
import numpy as np
import pyqtgraph as pg

try:
    from superqt import QRangeSlider
except ImportError:  # pragma: no cover - optional runtime enhancement
    QRangeSlider = None


DB_OPTIONS = [
    ("40 Log Pwr", -40.0),
    ("30 Log Pwr", -30.0),
    ("20 Log Pwr", -20.0),
    ("10 Log Pwr", -10.0),
]
DEGREE = "\N{DEGREE SIGN}"
CONTROL_STYLESHEET = """
QComboBox, QLineEdit, QAbstractSpinBox {
    background: white;
    border: 1px solid #b8b8b8;
    padding: 1px 4px;
    min-height: 20px;
}
QRadioButton {
    spacing: 4px;
}
"""


def internal_to_display_azimuth(angle_deg: float) -> float:
    return float(float(angle_deg) % 360.0)


def display_to_internal_azimuth(angle_deg: float) -> float:
    return float(((float(angle_deg) + 180.0) % 360.0) - 180.0)


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


class HrpPlotWidget(QWidget):
    elevation_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.angles_deg = np.array([])
        self.magnitudes = np.array([])
        self.selected_azimuth_deg = 0.0
        self.show_selected_azimuth_line = True
        self._setting_angle_programmatically = False
        self.init_ui()
        self.redraw_plot()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(2, 0, 2, 0)
        tools_layout.setSpacing(6)

        self.rb_e_emax = QRadioButton("E/Emax")
        self.rb_e_emax.setChecked(True)
        self.rb_db = QRadioButton("dB")
        self.rb_e_emax.toggled.connect(self.redraw_plot)
        self.rb_db.toggled.connect(self.redraw_plot)

        self.db_combo = QComboBox()
        self.db_combo.setStyleSheet(CONTROL_STYLESHEET)
        self.db_combo.setFixedWidth(116)
        for label, _value in DB_OPTIONS:
            self.db_combo.addItem(label)
        self.db_combo.currentIndexChanged.connect(self.redraw_plot)

        self.angle_spin = NoWheelDoubleSpinBox()
        self.angle_spin.setStyleSheet(CONTROL_STYLESHEET)
        self.angle_spin.setRange(-90.0, 90.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSingleStep(0.1)
        self.angle_spin.setValue(0.0)
        self.angle_spin.setFixedWidth(64)
        self.angle_spin.valueChanged.connect(self._emit_elevation_changed)

        self.dir_edit = QLineEdit("")
        self.dir_edit.setStyleSheet(CONTROL_STYLESHEET)
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setFixedWidth(62)

        tools_layout.addWidget(self.rb_e_emax)
        tools_layout.addWidget(self.rb_db)
        tools_layout.addWidget(self.db_combo)
        tools_layout.addStretch(1)
        tools_layout.addWidget(QLabel(f"El Angle ({DEGREE}):"))
        tools_layout.addWidget(self.angle_spin)
        tools_layout.addWidget(QLabel("Dir (dB):"))
        tools_layout.addWidget(self.dir_edit)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.hideAxis("left")
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setXRange(-1.12, 1.12, padding=0.0)
        self.plot_widget.setYRange(-1.12, 1.12, padding=0.0)

        layout.addLayout(tools_layout)
        layout.addWidget(self.plot_widget)

    def _emit_elevation_changed(self, value):
        if not self._setting_angle_programmatically:
            self.elevation_changed.emit(round(float(value), 1))

    def _selected_db_floor(self):
        return DB_OPTIONS[self.db_combo.currentIndex()][1]

    def _scaled_radius(self):
        if self.magnitudes.size == 0:
            return np.array([])

        values = np.asarray(self.magnitudes, dtype=float)

        if self.rb_e_emax.isChecked():
            return np.clip(values, 0.0, 1.0)

        floor_db = self._selected_db_floor()
        db_values = 20.0 * np.log10(np.maximum(values, 1e-12))
        db_values = np.clip(db_values, floor_db, 0.0)
        return (db_values - floor_db) / abs(floor_db)

    def _radius_label(self, radius):
        if self.rb_e_emax.isChecked():
            return f"{radius:.1f}"

        floor_db = self._selected_db_floor()
        db_value = radius * abs(floor_db) + floor_db
        return f"{db_value:.0f}"

    def _draw_polar_grid(self):
        outer_pen = pg.mkPen(color="#000000", width=1.7)
        major_pen = pg.mkPen(color="#000000", width=1.0)
        minor_pen = pg.mkPen(color="#d8d8d8", width=0.7)
        radial_label_color = "#8b4a00" if self.rb_e_emax.isChecked() else "black"
        label_font = QFont("Segoe UI", 8)

        for ring_index in range(1, 11):
            radius = ring_index / 10.0
            item = QGraphicsEllipseItem(-radius, -radius, radius * 2.0, radius * 2.0)
            item.setPen(outer_pen if ring_index == 10 else minor_pen)
            self.plot_widget.addItem(item)

            label = pg.TextItem(
                self._radius_label(radius),
                color=radial_label_color,
                anchor=(0.5, 1.0),
            )
            label.setFont(label_font)
            label.setPos(0.0, radius - 0.005)
            self.plot_widget.addItem(label)

        for angle_deg in range(0, 360, 10):
            theta = np.deg2rad(angle_deg)
            x = np.sin(theta)
            y = np.cos(theta)
            line = QGraphicsLineItem(0.0, 0.0, x, y)
            line.setPen(major_pen if angle_deg % 30 == 0 else minor_pen)
            self.plot_widget.addItem(line)

            if angle_deg % 30 == 0:
                anchor = (0.5, 0.5)
                if angle_deg == 0:
                    anchor = (0.5, 1.0)
                elif angle_deg == 180:
                    anchor = (0.5, 0.0)
                text = pg.TextItem(str(angle_deg), color="black", anchor=anchor)
                text.setFont(QFont("Segoe UI", 10))
                text.setPos(1.085 * x, 1.085 * y)
                self.plot_widget.addItem(text)

    def _draw_selected_azimuth_line(self):
        if not self.show_selected_azimuth_line:
            return
        theta = np.deg2rad(float(self.selected_azimuth_deg) % 360.0)
        x = np.sin(theta)
        y = np.cos(theta)
        line = QGraphicsLineItem(0.0, 0.0, x, y)
        line.setPen(pg.mkPen(color="#d83a3a", width=1.8))
        self.plot_widget.addItem(line)

    def redraw_plot(self, *_args):
        self.plot_widget.clear()
        self._draw_polar_grid()

        radius = self._scaled_radius()
        if radius.size == 0:
            self._draw_selected_azimuth_line()
            return

        theta = np.deg2rad(
            np.mod(np.asarray(self.angles_deg, dtype=float), 360.0)
        )
        x = radius * np.sin(theta)
        y = radius * np.cos(theta)
        curve = pg.PlotCurveItem(x, y, pen=pg.mkPen("#2f55ff", width=1.5))
        self.plot_widget.addItem(curve)
        self._draw_selected_azimuth_line()

    def plot_data(self, angles_deg, magnitudes):
        self.angles_deg = np.asarray(angles_deg, dtype=float)
        self.magnitudes = np.asarray(magnitudes, dtype=float)
        self.redraw_plot()

    def set_selected_azimuth(self, azimuth_deg):
        if azimuth_deg is None:
            azimuth_deg = 0.0
        self.selected_azimuth_deg = float(azimuth_deg)
        self.redraw_plot()

    def clear_plot_display(self):
        self.angles_deg = np.array([])
        self.magnitudes = np.array([])
        self.dir_edit.clear()
        self.redraw_plot()

    def set_cut_metadata(self, elevation_deg=None, directivity_dbd=None):
        if elevation_deg is not None:
            self._setting_angle_programmatically = True
            self.angle_spin.setValue(float(elevation_deg))
            self._setting_angle_programmatically = False
        if directivity_dbd is not None:
            self.dir_edit.setText(f"{float(directivity_dbd):.2f}")
        else:
            self.dir_edit.clear()


class VrpPlotWidget(QWidget):
    azimuth_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.angles_deg = np.array([])
        self.magnitudes = np.array([])
        self._setting_azimuth_programmatically = False
        self._syncing_range_controls = False
        self.init_ui()
        self.redraw_plot()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(2, 0, 2, 0)
        tools_layout.setSpacing(6)

        self.rb_e_emax = QRadioButton("E/Emax")
        self.rb_e_emax.setChecked(True)
        self.rb_db = QRadioButton("dB")
        self.rb_e_emax.toggled.connect(self.redraw_plot)
        self.rb_db.toggled.connect(self.redraw_plot)

        self.db_combo = QComboBox()
        self.db_combo.setStyleSheet(CONTROL_STYLESHEET)
        self.db_combo.setFixedWidth(116)
        for label, _value in DB_OPTIONS:
            self.db_combo.addItem(label)
        self.db_combo.currentIndexChanged.connect(self.redraw_plot)

        self.azimuth_spin = NoWheelSpinBox()
        self.azimuth_spin.setStyleSheet(CONTROL_STYLESHEET)
        self.azimuth_spin.setRange(0, 359)
        self.azimuth_spin.setValue(0)
        self.azimuth_spin.setFixedWidth(64)
        self.azimuth_spin.valueChanged.connect(self._emit_azimuth_changed)

        self.dir_edit = QLineEdit("")
        self.dir_edit.setStyleSheet(CONTROL_STYLESHEET)
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setFixedWidth(62)

        self.tilt_edit = QLineEdit("")
        self.tilt_edit.setStyleSheet(CONTROL_STYLESHEET)
        self.tilt_edit.setReadOnly(True)
        self.tilt_edit.setFixedWidth(62)

        tools_layout.addWidget(self.rb_e_emax)
        tools_layout.addWidget(self.rb_db)
        tools_layout.addWidget(self.db_combo)
        tools_layout.addStretch(1)
        tools_layout.addWidget(QLabel(f"Az Angle ({DEGREE}):"))
        tools_layout.addWidget(self.azimuth_spin)
        tools_layout.addWidget(QLabel("Dir (dBd):"))
        tools_layout.addWidget(self.dir_edit)
        tools_layout.addWidget(QLabel(f"Tilt ({DEGREE}):"))
        tools_layout.addWidget(self.tilt_edit)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.22)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setLabel("bottom", "Angle of Depression (degrees)")
        self.plot_widget.setLabel("left", "")

        for axis_name in ("left", "bottom"):
            axis = self.plot_widget.getPlotItem().getAxis(axis_name)
            axis.setPen(pg.mkPen("#000000", width=1.4))
            axis.setTextPen(pg.mkPen("#000000"))
            axis.setStyle(tickTextOffset=6)

        range_layout = QHBoxLayout()
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(6)

        self.start_spin = NoWheelSpinBox()
        self.start_spin.setStyleSheet(CONTROL_STYLESHEET)
        self.start_spin.setRange(-90, 89)
        self.start_spin.setValue(-5)
        self.start_spin.setFixedWidth(62)
        self.start_spin.valueChanged.connect(self._on_range_changed)

        self.stop_spin = NoWheelSpinBox()
        self.stop_spin.setStyleSheet(CONTROL_STYLESHEET)
        self.stop_spin.setRange(-89, 90)
        self.stop_spin.setValue(90)
        self.stop_spin.setFixedWidth(62)
        self.stop_spin.valueChanged.connect(self._on_range_changed)

        range_layout.addWidget(QLabel("Start (deg):"))
        range_layout.addWidget(self.start_spin)

        self.range_slider = None
        if QRangeSlider is not None:
            self.range_slider = QRangeSlider(Qt.Orientation.Horizontal)
            self.range_slider.setRange(-90, 90)
            self.range_slider.setSingleStep(1)
            self.range_slider.setValue((-5, 90))
            self.range_slider.valueChanged.connect(self._on_slider_range_changed)
            self.range_slider.setStyleSheet(
                """
                QSlider::groove:horizontal {
                    background: #d8d8d8;
                    height: 4px;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #f0f0f0;
                    border: 1px solid #8d8d8d;
                    width: 12px;
                    margin: -5px 0;
                    border-radius: 2px;
                }
                """
            )
            range_layout.addWidget(self.range_slider, 1)
        else:
            range_layout.addStretch(1)

        range_layout.addWidget(QLabel("Stop (deg):"))
        range_layout.addWidget(self.stop_spin)

        layout.addLayout(tools_layout)
        layout.addWidget(self.plot_widget)
        layout.addLayout(range_layout)

    def _emit_azimuth_changed(self, value):
        if not self._setting_azimuth_programmatically:
            self.azimuth_changed.emit(float(value))

    def _selected_db_floor(self):
        return DB_OPTIONS[self.db_combo.currentIndex()][1]

    def _update_x_axis_spacing(self):
        start = self.start_spin.value()
        stop = self.stop_spin.value()
        span = stop - start
        axis = self.plot_widget.getPlotItem().getAxis("bottom")

        if span > 150:
            axis.setTickSpacing(15.0, 5.0)
        elif span > 75:
            axis.setTickSpacing(10.0, 5.0)
        elif span > 50:
            axis.setTickSpacing(5.0, 2.0)
        elif span > 30:
            axis.setTickSpacing(5.0, 1.0)
        elif span > 17:
            axis.setTickSpacing(2.0, 1.0)
        else:
            axis.setTickSpacing(1.0, 0.5)

    def _apply_axis_mode(self):
        left_axis = self.plot_widget.getPlotItem().getAxis("left")
        if self.rb_e_emax.isChecked():
            self.plot_widget.setYRange(0.0, 1.0, padding=0.0)
            left_axis.setTickSpacing(0.1, 0.05)
            return

        floor_db = self._selected_db_floor()
        self.plot_widget.setYRange(floor_db, 0.0, padding=0.0)
        major_step = abs(floor_db) / 10.0
        left_axis.setTickSpacing(major_step, 1.0)

    def _scaled_values(self):
        if self.magnitudes.size == 0:
            return np.array([])

        values = np.asarray(self.magnitudes, dtype=float)
        peak = float(np.max(values))
        if peak > 0:
            values = values / peak

        if self.rb_e_emax.isChecked():
            return np.clip(values, 0.0, 1.0)

        floor_db = self._selected_db_floor()
        db_values = 20.0 * np.log10(np.maximum(values, 1e-12))
        return np.clip(db_values, floor_db, 0.0)

    def _sync_slider_from_spinboxes(self):
        if self.range_slider is None:
            return
        self._syncing_range_controls = True
        self.range_slider.setValue((self.start_spin.value(), self.stop_spin.value()))
        self._syncing_range_controls = False

    def _on_slider_range_changed(self, values):
        if self._syncing_range_controls:
            return

        start, stop = (int(values[0]), int(values[1]))
        self._syncing_range_controls = True
        self.start_spin.setValue(start)
        self.stop_spin.setValue(stop)
        self._syncing_range_controls = False
        self.redraw_plot()

    def _on_range_changed(self, _value=None):
        if self._syncing_range_controls:
            return

        if self.start_spin.value() >= self.stop_spin.value():
            if self.sender() is self.start_spin:
                self.stop_spin.blockSignals(True)
                self.stop_spin.setValue(self.start_spin.value() + 1)
                self.stop_spin.blockSignals(False)
            else:
                self.start_spin.blockSignals(True)
                self.start_spin.setValue(self.stop_spin.value() - 1)
                self.start_spin.blockSignals(False)

        self._sync_slider_from_spinboxes()
        self.redraw_plot()

    def redraw_plot(self, *_args):
        self.plot_widget.clear()
        self._apply_axis_mode()
        self._update_x_axis_spacing()

        start = self.start_spin.value()
        stop = self.stop_spin.value()
        self.plot_widget.setXRange(start, stop, padding=0.0)

        values = self._scaled_values()
        if values.size == 0:
            return

        curve = pg.PlotCurveItem(
            np.asarray(self.angles_deg, dtype=float),
            values,
            pen=pg.mkPen("#2f55ff", width=1.5),
        )
        self.plot_widget.addItem(curve)

    def plot_data(self, angles_deg, magnitudes):
        self.angles_deg = np.asarray(angles_deg, dtype=float)
        self.magnitudes = np.asarray(magnitudes, dtype=float)
        self.redraw_plot()

    def clear_plot_display(self):
        self.angles_deg = np.array([])
        self.magnitudes = np.array([])
        self.dir_edit.clear()
        self.tilt_edit.clear()
        self.redraw_plot()

    def set_cut_metadata(self, azimuth_deg=None, directivity_dbd=None, tilt_deg=None):
        if azimuth_deg is not None:
            self._setting_azimuth_programmatically = True
            azimuth_value = int(round(internal_to_display_azimuth(float(azimuth_deg)))) % 360
            self.azimuth_spin.setValue(azimuth_value)
            self._setting_azimuth_programmatically = False
        if directivity_dbd is not None:
            self.dir_edit.setText(f"{float(directivity_dbd):.2f}")
        else:
            self.dir_edit.clear()
        if tilt_deg is not None:
            self.tilt_edit.setText(f"{float(tilt_deg):.1f}")
        else:
            self.tilt_edit.clear()
