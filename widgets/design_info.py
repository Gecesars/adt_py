import sys
from PyQt6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QComboBox, 
                             QSpinBox, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QSize

class DesignInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(4)
        
        # Customer
        self.customer_input = QLineEdit()
        form_layout.addRow("Customer", self.customer_input)
        
        # Site Name
        self.site_name_input = QLineEdit()
        form_layout.addRow("Site Name", self.site_name_input)
        
        # Antenna Model
        self.antenna_model_input = QLineEdit()
        form_layout.addRow("Antenna Model", self.antenna_model_input)
        
        # Design Frequency (MHz)
        self.design_freq_input = QLineEdit("539")
        form_layout.addRow("Design Frequency (MHz)", self.design_freq_input)
        
        # Polarisation
        self.polarisation_combo = QComboBox()
        self.polarisation_combo.addItems(["Horizontal", "Vertical", "Circular", "Cross Polar"])
        form_layout.addRow("Polarisation", self.polarisation_combo)
        
        # Analogue or Digital
        self.signal_type_combo = QComboBox()
        self.signal_type_combo.addItems(["Digital", "Analogue"])
        form_layout.addRow("Analogue or Digital", self.signal_type_combo)
        
        # Number of Panels
        self.num_panels_spin = QSpinBox()
        self.num_panels_spin.setRange(1, 100)
        self.num_panels_spin.setValue(4)
        form_layout.addRow("Number of Panels", self.num_panels_spin)
        
        # Channel Frequency (MHz)
        self.channel_freq_input = QLineEdit("539")
        form_layout.addRow("Channel Frequency (MHz)", self.channel_freq_input)
        
        # Designer Name
        self.designer_name_input = QLineEdit()
        form_layout.addRow("Designer Name", self.designer_name_input)
        
        # Date Created
        self.date_created_input = QLineEdit("March 16, 2026")
        form_layout.addRow("Date Created", self.date_created_input)
        
        # Design Note
        self.design_note_input = QLineEdit()
        form_layout.addRow("Design Note", self.design_note_input)
        
        # --- System Losses ---
        self.internal_loss_input = QLineEdit("0.5")
        self.internal_loss_input.setReadOnly(True)
        self.internal_loss_input.setToolTip("Managed by Site Details")
        form_layout.addRow("Internal Loss (dB)", self.internal_loss_input)
        
        self.pol_loss_input = QLineEdit("3.0")
        self.pol_loss_input.setReadOnly(True)
        self.pol_loss_input.setToolTip("Managed by Site Details")
        form_layout.addRow("Polarisation Loss (dB)", self.pol_loss_input)
        
        self.filter_loss_input = QLineEdit("0.8")
        self.filter_loss_input.setReadOnly(True)
        self.filter_loss_input.setToolTip("Managed by Site Details")
        form_layout.addRow("Filter/Combiner Loss (dB)", self.filter_loss_input)
        
        self.feeder_loss_input = QLineEdit("1.2")
        self.feeder_loss_input.setReadOnly(True)
        self.feeder_loss_input.setToolTip("Calculated from Site Details")
        form_layout.addRow("Main Feeder Loss (dB)", self.feeder_loss_input)
        
        layout.addLayout(form_layout)
        
        # Calculate 3D Pattern Button
        calc_layout = QVBoxLayout()
        self.calc_btn = QPushButton("Calculate 3D Pattern")
        self.calc_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.calc_btn.setStyleSheet("""
            background-color: #00A651; 
            color: white; 
            font-weight: bold; 
            padding: 3px;
            font-size: 10px;
        """)
        calc_layout.addWidget(self.calc_btn)
        calc_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addLayout(calc_layout)
        layout.addStretch()
        
        self.setLayout(layout)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def sizeHint(self):
        return QSize(420, 320)
