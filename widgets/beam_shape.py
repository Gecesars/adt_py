from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QSpinBox, QRadioButton, 
                             QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QButtonGroup)
from PyQt6.QtCore import Qt

class BeamShapeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- LEFT SIDE: INPUTS ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        # Top Form
        form_group = QGroupBox()
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(5, 5, 5, 5)
        
        self.freq_input = QLineEdit("539")
        self.bays_spin = QSpinBox()
        self.bays_spin.setRange(1, 100)
        self.bays_spin.setValue(4)
        self.tilt_input = QLineEdit("1.00")
        self.spacing_input = QLineEdit("1.15")
        self.null_fill_spin = QSpinBox()
        self.null_fill_spin.setRange(0, 100)
        self.null_fill_spin.setValue(50)
        
        form_layout.addRow("Frequency (MHz)", self.freq_input)
        form_layout.addRow("Number of Bays", self.bays_spin)
        form_layout.addRow("Required Beam Tilt (deg)", self.tilt_input)
        form_layout.addRow("Element Spacing (m)", self.spacing_input)
        form_layout.addRow("Degree of Null Fill (%)", self.null_fill_spin)
        
        # Mock empty box below it
        empty_box = QLineEdit()
        empty_box.setReadOnly(True)
        empty_box.setMinimumHeight(30)
        form_layout.addRow(empty_box)
        
        left_layout.addWidget(form_group)
        
        # Element Type
        elem_group = QGroupBox("Element Type")
        elem_layout = QHBoxLayout(elem_group)
        elem_layout.setContentsMargins(5, 5, 5, 5)
        elem_layout.addWidget(QLabel("Point Source"), alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(elem_group)
        
        # Solution
        sol_group = QGroupBox("Solution")
        sol_layout = QHBoxLayout(sol_group)
        sol_layout.setContentsMargins(5, 5, 5, 5)
        self.rb_osc = QRadioButton("Oscillatory")
        self.rb_non_osc = QRadioButton("Non-Oscillatory")
        self.rb_osc.setChecked(True)
        sol_layout.addWidget(self.rb_osc)
        sol_layout.addWidget(self.rb_non_osc)
        left_layout.addWidget(sol_group)
        
        # Calculate Button
        self.calc_btn = QPushButton("Calculate Phases")
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b88d8;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
        """)
        left_layout.addWidget(self.calc_btn)
        
        # Decimal Places
        dec_group = QGroupBox("Decimal Places to Vertical Group Φ")
        dec_layout = QHBoxLayout(dec_group)
        dec_layout.setContentsMargins(5, 5, 5, 5)
        self.rb_dec0 = QRadioButton("0 (0)")
        self.rb_dec1 = QRadioButton("1 (0.0)")
        self.rb_dec2 = QRadioButton("2 (0.00)")
        self.rb_dec0.setChecked(True)
        dec_layout.addWidget(self.rb_dec0)
        dec_layout.addWidget(self.rb_dec1)
        dec_layout.addWidget(self.rb_dec2)
        left_layout.addWidget(dec_group)
        
        # Transfer Button
        self.transfer_btn = QPushButton("Transfer to Vertical Group Φ")
        self.transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b88d8;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
        """)
        left_layout.addWidget(self.transfer_btn)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget, stretch=1)
        
        # --- RIGHT SIDE: TABLE ---
        self.table = QTableWidget(22, 2)
        self.table.setHorizontalHeaderLabels(["Bay", "Phase"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Populate Bay column
        for i in range(22):
            bay_item = QTableWidgetItem(str(i + 1))
            bay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bay_item.setBackground(Qt.GlobalColor.lightGray)
            self.table.setItem(i, 0, bay_item)
            self.table.setItem(i, 1, QTableWidgetItem(""))
            
        main_layout.addWidget(self.table, stretch=1)
