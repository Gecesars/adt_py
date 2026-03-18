from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QLabel, QLineEdit
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from PyQt6.QtGui import QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsLineItem

class HrpPlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.draw_mock_pattern()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tools row
        tools_layout = QHBoxLayout()
        self.rb_e_emax = QRadioButton("E/Emax")
        self.rb_e_emax.setChecked(True)
        self.rb_40log = QRadioButton("40 Log Pwr")
        self.rb_e_emax.toggled.connect(self.draw_mock_pattern)
        
        self.lbl_angle = QLabel("El Angle (°):")
        self.le_angle = QLineEdit("0.0")
        self.le_angle.setFixedWidth(50)
        
        self.lbl_dir = QLabel("Dir (dB):")
        self.le_dir = QLineEdit("14.5")
        self.le_dir.setFixedWidth(50)
        
        tools_layout.addWidget(self.rb_e_emax)
        tools_layout.addWidget(self.rb_40log)
        tools_layout.addStretch()
        tools_layout.addWidget(self.lbl_angle)
        tools_layout.addWidget(self.le_angle)
        tools_layout.addWidget(self.lbl_dir)
        tools_layout.addWidget(self.le_dir)
        
        layout.addLayout(tools_layout)
        
        # Polar Plot using pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.hideAxis('left')
        self.plot_widget.setAspectLocked(True)
        
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        
    def draw_mock_pattern(self):
        self.plot_widget.clear()
        
        # Draw Circular Grid
        for r in np.arange(0.2, 1.2, 0.2):
            circle = QPainterPath()
            circle.addEllipse(pg.QtCore.QRectF(-r, -r, r*2, r*2))
            item = QGraphicsPathItem(circle)
            item.setPen(pg.mkPen(color='gray', width=1, style=Qt.PenStyle.DotLine))
            self.plot_widget.addItem(item)
            
            # Add radius labels
            text = pg.TextItem(f"{r:.1f}", color='k')
            text.setPos(0, -r)
            self.plot_widget.addItem(text)
            
        # Draw angular axis lines
        for angle in range(0, 360, 30):
            line = QGraphicsLineItem(0, 0, 1.0 * np.cos(np.radians(angle)), 1.0 * np.sin(np.radians(angle)))
            line.setPen(pg.mkPen(color='gray', width=1, style=Qt.PenStyle.DotLine))
            self.plot_widget.addItem(line)
            
            # Angular Labels
            text = pg.TextItem(f"{angle}", color='k')
            text.setPos(1.05 * np.cos(np.radians(angle)), 1.05 * np.sin(np.radians(angle)))
            self.plot_widget.addItem(text)
            
        # Generate radiation pattern using Math
        # Example: Cardioid/Directional pattern
        theta = np.linspace(0, 2 * np.pi, 360)
        
        if self.rb_e_emax.isChecked():
            r = np.abs(np.sin(theta/2)**2 + 0.1 * np.cos(3*theta)**2)
            r = r / np.max(r) # Normalize
        else:
            # 40 Log Mode (Simulation of dB)
            r = 20 * np.log10(np.abs(np.sin(theta/2)**2)) + 40
            r = np.clip(r / 40.0, 0, 1)  # Scale to fit 0-1 circle visually
            
        # Add polar plot curve
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        curve = pg.PlotCurveItem(x, y, pen=pg.mkPen('b', width=2))
        self.plot_widget.addItem(curve)
        

class VrpPlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.draw_mock_pattern()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Tools row
        tools_layout = QHBoxLayout()
        self.rb_e_emax = QRadioButton("E/Emax")
        self.rb_e_emax.setChecked(True)
        self.rb_40log = QRadioButton("40 Log Pwr")
        self.rb_e_emax.toggled.connect(self.draw_mock_pattern)
        
        self.lbl_angle = QLabel("Az Angle (°):")
        self.le_angle = QLineEdit("0")
        self.le_angle.setFixedWidth(50)
        
        self.lbl_dir = QLabel("Dir (dBd):")
        self.le_dir = QLineEdit("12.0")
        self.le_dir.setFixedWidth(50)
        
        self.lbl_tilt = QLabel("Tilt (°):")
        self.le_tilt = QLineEdit("2.0")
        self.le_tilt.setFixedWidth(50)
        
        tools_layout.addWidget(self.rb_e_emax)
        tools_layout.addWidget(self.rb_40log)
        tools_layout.addStretch()
        tools_layout.addWidget(self.lbl_angle)
        tools_layout.addWidget(self.le_angle)
        tools_layout.addWidget(self.lbl_dir)
        tools_layout.addWidget(self.le_dir)
        tools_layout.addWidget(self.lbl_tilt)
        tools_layout.addWidget(self.le_tilt)
        
        layout.addLayout(tools_layout)
        
        # Cartesian plot for Vertical Radiation Pattern
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('bottom', "Angle of Depression (degrees)")
        self.plot_widget.setLabel('left', "E/Emax")
        
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
        
    def draw_mock_pattern(self):
        self.plot_widget.clear()
        
        # X axis from -15 to +15 degrees
        x = np.linspace(-15, 15, 500)
        
        if self.rb_e_emax.isChecked():
            self.plot_widget.setYRange(0, 1)
            # Sinc function for vertical array pattern
            y = np.sinc(x/2.0)
            y = np.abs(y)
            self.plot_widget.setLabel('left', "E/Emax")
        else:
            self.plot_widget.setYRange(-40, 0)
            # Logarithmic pattern
            y = 20 * np.log10(np.abs(np.sinc(x/2.0)) + 1e-4)
            self.plot_widget.setLabel('left', "dB (40 Log Pwr)")
            
        curve = pg.PlotCurveItem(x, y, pen=pg.mkPen('b', width=2))
        self.plot_widget.addItem(curve)
