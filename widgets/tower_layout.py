import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QSplitter, QLabel, QPushButton)
from PyQt6.QtCore import Qt
import pyqtgraph.opengl as gl
import numpy as np

class TowerLayoutWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Side: Data Table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0,0,0,0)
        
        lbl_data = QLabel("<b>Tower Geometric Layout Data</b>")
        left_layout.addWidget(lbl_data)
        
        self.table = QTableWidget(4, 5)
        self.table.setHorizontalHeaderLabels(["Level", "Face", "Azimuth (°)", "Height (m)", "Mech Tilt (°)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        # Mock Data
        mock_data = [
            ("1", "A", "0.0", "50.0", "0.0"),
            ("1", "B", "120.0", "50.0", "0.0"),
            ("1", "C", "240.0", "50.0", "0.0"),
            ("2", "A", "0.0", "48.0", "-2.0"),
        ]
        
        for r, row_data in enumerate(mock_data):
            for c, val in enumerate(row_data):
                self.table.setItem(r, c, QTableWidgetItem(val))
                
        left_layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("Apply to 3D View")
        self.btn_reset = QPushButton("Reset Angles")
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_reset)
        left_layout.addLayout(btn_layout)
        
        left_widget.setLayout(left_layout)
        
        # Right Side: 3D Visualization
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0,0,0,0)
        
        lbl_3d = QLabel("<b>3D Tower View Preview</b>")
        right_layout.addWidget(lbl_3d)
        
        self.gl_widget = gl.GLViewWidget()
        self.gl_widget.setCameraPosition(distance=40)
        
        # Add basic grid
        grid = gl.GLGridItem()
        grid.scale(2, 2, 2)
        self.gl_widget.addItem(grid)
        
        # Add a fake tower (cylinder)
        md = gl.MeshData.cylinder(rows=10, cols=20, radius=[1.0, 1.0], length=30.0)
        tower = gl.GLMeshItem(meshdata=md, smooth=True, color=(0.4, 0.4, 0.4, 0.8), shader='balloon')
        
        # We need to rotate the tower so it stands up
        tower.rotate(90, 1, 0, 0)
        tower.translate(0, 0, 30)
        
        self.gl_widget.addItem(tower)
        
        # Add some "panels" (small red boxes)
        for i in range(3):
            angle = i * 120 * np.pi / 180
            x = 1.2 * np.cos(angle)
            y = 1.2 * np.sin(angle)
            z = 25.0
            panel_md = gl.MeshData.cylinder(rows=2, cols=4, radius=[0.5, 0.5], length=2.0)
            panel = gl.GLMeshItem(meshdata=panel_md, smooth=False, color=(1, 0, 0, 1), shader='balloon')
            panel.rotate(90, 1, 0, 0)
            panel.translate(x, y, z)
            self.gl_widget.addItem(panel)
            
        right_layout.addWidget(self.gl_widget)
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
