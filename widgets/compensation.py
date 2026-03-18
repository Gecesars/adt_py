from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QLabel, QHBoxLayout, QPushButton, QGroupBox)
from PyQt6.QtCore import Qt

class CompensationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Side: Panel Impedance Table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_panel = QLabel("<b>Panel Impedance Data (Ohms)</b>")
        left_layout.addWidget(lbl_panel)
        
        self.panel_table = QTableWidget(4, 4)
        self.panel_table.setHorizontalHeaderLabels(["Panel", "Real (R)", "Imag (X)", "Magnitude"])
        self.panel_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.panel_table.verticalHeader().setVisible(False)
        
        mock_impedance = [
            ("1", "49.5", "-1.2", "49.5"),
            ("2", "50.1", "0.5", "50.1"),
            ("3", "48.9", "-2.1", "49.0"),
            ("4", "51.0", "1.1", "51.0"),
        ]
        
        for r, row_data in enumerate(mock_impedance):
            for c, val in enumerate(row_data):
                self.panel_table.setItem(r, c, QTableWidgetItem(val))
                
        left_layout.addWidget(self.panel_table)
        
        # Tools
        btn_layout = QHBoxLayout()
        self.btn_calc = QPushButton("Calculate Network / VSWR")
        btn_layout.addWidget(self.btn_calc)
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        
        left_widget.setLayout(left_layout)
        
        # Right Side: Combiner and System Info
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        gb_results = QGroupBox("Compensation Results")
        gb_layout = QVBoxLayout()
        
        lbl_vswr = QLabel("<b>System VSWR:</b> 1.05:1")
        lbl_rl = QLabel("<b>Return Loss:</b> 32.2 dB")
        lbl_comp_cap = QLabel("<b>Compensation Capacitor:</b> 1.2 pF")
        lbl_comp_ind = QLabel("<b>Compensation Inductor:</b> 4.5 nH")
        
        gb_layout.addWidget(lbl_vswr)
        gb_layout.addWidget(lbl_rl)
        gb_layout.addWidget(lbl_comp_cap)
        gb_layout.addWidget(lbl_comp_ind)
        gb_layout.addStretch()
        
        gb_results.setLayout(gb_layout)
        right_layout.addWidget(gb_results)
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
