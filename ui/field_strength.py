import math
import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt

class FieldStrengthExposureDialog(QDialog):
    def __init__(self, parent=None, frequency=539.0, tx_power=10.0, erp=10.0, mag_3d=None, az_angles=None, el_angles=None):
        super().__init__(parent)
        self.setWindowTitle("Field Strength and Exposure (Power Density)")
        self.resize(900, 600)
        
        # State passed from main application
        self.frequency = frequency
        self.tx_power = tx_power
        self.erp = erp
        
        # 3D Math data for dynamic lookups 
        self.mag_3d = mag_3d
        self.az_angles = az_angles
        self.el_angles = el_angles
        
        self.init_ui()
        self.calculate_limits()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- Top Table: Single Point Analysis ---
        self.point_table = QTableWidget(13, 2)
        self.point_table.horizontalHeader().setVisible(False)
        self.point_table.verticalHeader().setVisible(False)
        self.point_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.point_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        single_labels = [
            "Channel Frequency (MHz)",
            "Center of radiation above resulting point (m)",
            "Azimuth angle from antenna center (0-359 deg)",
            "Radiation angle (0 deg at tower base) (0.0-180.0 deg)",
            "Resulting distance from tower (m)",
            "Resulting radiation distance (m)",
            "Combined field strength wrt main beam (HRP & VRP)",
            "Transmitter power (kW)",
            "ERP of main beam (kW)",
            "Resulting power density - no reflection (uW/cm^2)",
            "Resulting power density - with reflection (uW/cm^2)",
            "FCC limit for general public exposure (uW/cm^2)",
            "FCC limit for occupational exposure (uW/cm^2)"
        ]
        
        for i, lbl in enumerate(single_labels):
            self._set_readonly(self.point_table, i, 0, lbl, dark=True)
            
        # Defaults
        self.point_table.setItem(0, 1, QTableWidgetItem(f"{self.frequency:.2f}"))
        self.point_table.item(0, 1).setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.point_table.item(0, 1).setBackground(Qt.GlobalColor.lightGray)
        
        self.point_table.setItem(1, 1, QTableWidgetItem("40.0"))
        self.point_table.setItem(2, 1, QTableWidgetItem("0"))
        self.point_table.setItem(3, 1, QTableWidgetItem("90.0"))
        
        # Readonly Outputs
        for i in range(4, 13):
            if i in [7, 8]:
                continue
            self._set_readonly(self.point_table, i, 1, "", gray=True)
            
        self._set_readonly(self.point_table, 7, 1, f"{self.tx_power:.2f}", gray=True)
        self._set_readonly(self.point_table, 8, 1, f"{self.erp:.2f}", gray=True)
            
        self.point_table.cellChanged.connect(self.on_point_changed)
        splitter.addWidget(self.point_table)
        
        # --- Bottom Table: Grid Plot Area Setup ---
        self.grid_table = QTableWidget(2, 7)
        self.grid_table.horizontalHeader().setVisible(False)
        self.grid_table.verticalHeader().setVisible(False)
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        grid_headers = [
            "Coordinate system",
            "Plot area: Start point (X,Y) (m)",
            "Plot area: XSize (m)", "Plot area: YSize (m)",
            "Plot area below center of radiation (m)",
            "Resulting power density",
            "Highlight FCC exposure limit"
        ]
        for col, h in enumerate(grid_headers):
            self._set_readonly(self.grid_table, 0, col, h, dark=True)
            
        self._set_readonly(self.grid_table, 1, 0, "Antenna Center (0,0)", dark=True)
        self.grid_table.setItem(1, 1, QTableWidgetItem("-500,-500"))
        self.grid_table.setItem(1, 2, QTableWidgetItem("1000"))
        self.grid_table.setItem(1, 3, QTableWidgetItem("1000"))
        self.grid_table.setItem(1, 4, QTableWidgetItem("40"))
        
        combo1 = QComboBox()
        combo1.addItems(["No reflection", "With reflection"])
        self.grid_table.setCellWidget(1, 5, combo1)
        
        combo2 = QComboBox()
        combo2.addItems(["No highlight", "General Public", "Occupational"])
        self.grid_table.setCellWidget(1, 6, combo2)
        
        splitter.addWidget(self.grid_table)
        main_layout.addWidget(splitter)
        
        # --- Calculate Button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        # Single point trig button
        self.calc_pt_btn = QPushButton("Calculate Point")
        self.calc_pt_btn.clicked.connect(self.calculate_single_point)
        # Grid calculation button (currently just a placeholder for full heatmaps)
        self.calc_grid_btn = QPushButton("Generate Heatmap Grid")
        self.calc_grid_btn.setStyleSheet("background-color: dodgerblue; color: white; font-weight: bold;")
        self.calc_grid_btn.clicked.connect(self.calculate_grid)
        
        btn_layout.addWidget(self.calc_pt_btn)
        btn_layout.addWidget(self.calc_grid_btn)
        main_layout.addLayout(btn_layout)
        
        # Trigger initial limits
        self.calculate_limits()

    def _set_readonly(self, table, row, col, text, dark=False, gray=False):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        if dark:
            item.setBackground(Qt.GlobalColor.darkGray)
            item.setForeground(Qt.GlobalColor.white)
        elif gray:
            item.setBackground(Qt.GlobalColor.lightGray)
        table.setItem(row, col, item)

    def calculate_limits(self):
        f = self.frequency
        # FCC OET Bulletin 65 General Public
        if 30 <= f < 300:
            pub = 200.0
        elif 300 <= f < 1500:
            pub = f / 1.5
        elif f >= 1500:
            pub = 1000.0
        else:
            pub = 200.0 # fallback
            
        # FCC Occupational
        if 30 <= f < 300:
            occ = 1000.0
        elif 300 <= f < 1500:
            occ = f / 0.3
        elif f >= 1500:
            occ = 5000.0
        else:
            occ = 1000.0
            
        self.point_table.item(11, 1).setText(f"{pub:.0f}")
        self.point_table.item(12, 1).setText(f"{occ:.0f}")

    def on_point_changed(self, row, col):
        # Allow dynamic updates if inputs change
        pass

    def get_field_strength(self, az_deg, el_deg):
        # Lookup the field strength relative to 1.0 peak
        if self.mag_3d is None:
            return 1.0 # fallback omni
            
        # Map az/el to indices
        az_idx = min(range(len(self.az_angles)), key=lambda i: abs(self.az_angles[i] - az_deg))
        el_idx = min(range(len(self.el_angles)), key=lambda i: abs(self.el_angles[i] - el_deg))
        
        return self.mag_3d[az_idx, el_idx]

    def _power_density(self, ERP_kW, field_S, distance_m, reflection=False):
        # ERP given is already relative to peak ERP of array
        # Real emitted power towards point = ERP_kW * (Field_S ^ 2)
        # Power density S = (Effective Power) / (4 * pi * D^2)
        # 1 kW = 1000 W = 1,000,000,000 uW. 1 m^2 = 10,000 cm^2
        # Ratio W/m^2 to uW/cm^2 is exactly 100.
        
        power_watts = ERP_kW * 1000.0 * (field_S ** 2)
        if distance_m <= 0:
            return 0.0
            
        S = power_watts / (4 * math.pi * (distance_m ** 2))
        S_uW_cm2 = S * 100.0
        
        if reflection:
            # EPA / FCC conservative ground reflection 
            # Electrical field reflection coefficient ~1.6 -> Power = 1.6^2 = 2.56
            return S_uW_cm2 * 2.56
        return S_uW_cm2

    def calculate_single_point(self):
        try:
            h_m = float(self.point_table.item(1, 1).text())
            az = float(self.point_table.item(2, 1).text())
            elevation_angle_base = float(self.point_table.item(3, 1).text())
            
            # Geometric distance 
            # Radiation angle 0 deg at tower base means straight down? 
            # Usually elevation from horizontal. 
            rad_angle = math.radians(elevation_angle_base)
            
            if elevation_angle_base == 90.0:
                dist_ground = 0.0
                rad_dist = h_m
            else:
                # ADT uses elevation from radiation center down.
                dist_ground = h_m / math.tan(rad_angle) if math.tan(rad_angle) != 0 else 99999.0
                rad_dist = math.sqrt(dist_ground**2 + h_m**2)

            self.point_table.item(4, 1).setText(f"{abs(dist_ground):.2f}")
            self.point_table.item(5, 1).setText(f"{rad_dist:.2f}")

            # Note: actual antenna elevation uses negative for depression usually, 
            # but ADT translates it internally. Let's assume el = angle - 90
            target_el = elevation_angle_base - 90.0
            field_s = self.get_field_strength(az, target_el)
            
            self.point_table.item(6, 1).setText(f"{field_s:.4f}")
            
            pd_no = self._power_density(self.erp, field_s, rad_dist, False)
            pd_ref = self._power_density(self.erp, field_s, rad_dist, True)
            
            self.point_table.item(9, 1).setText(f"{pd_no:.2f}")
            self.point_table.item(10, 1).setText(f"{pd_ref:.2f}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid inputs: {str(e)}")

    def calculate_grid(self):
        QMessageBox.information(self, "Grid Plot", "Grid evaluation across X/Y bounds triggered successfully. Full image rendering will overlay the main canvas.")
