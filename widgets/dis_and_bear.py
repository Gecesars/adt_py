import math
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt

class DistanceBearingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Distance and Bearing")
        self.resize(500, 450)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Point Coordinates Table ---
        self.coord_table = QTableWidget(14, 4)
        self.coord_table.horizontalHeader().setVisible(False)
        self.coord_table.verticalHeader().setVisible(False)
        self.coord_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Setup static labels and colors
        self._setup_coord_table()
        
        main_layout.addWidget(self.coord_table)
        
        # --- Results Table ---
        self.result_table = QTableWidget(4, 2)
        self.result_table.horizontalHeader().setVisible(False)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self._setup_result_table()
        
        main_layout.addWidget(self.result_table)
        
        # --- Calculate Button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.setStyleSheet("background-color: dodgerblue; color: white; font-weight: bold; width: 100px; height: 35px;")
        self.calc_btn.clicked.connect(self.calculate)
        btn_layout.addWidget(self.calc_btn)
        
        main_layout.addLayout(btn_layout)
        
    def _setup_coord_table(self):
        # Point A
        self._set_header_cell(0, 0, "Point A")
        self._set_cell(1, 0, "Latitude", bold=True)
        self._set_cell(2, 0, "Degrees")
        self._set_cell(2, 1, "Minutes")
        self._set_cell(2, 2, "Seconds")
        self._set_cell(2, 3, "Earth Surface Position")
        
        self._set_input_row(3, ["0", "0", "0", "North"])
        
        self._set_cell(4, 0, "Longitude", bold=True)
        self._set_cell(5, 0, "Degrees")
        self._set_cell(5, 1, "Minutes")
        self._set_cell(5, 2, "Seconds")
        self._set_cell(5, 3, "Earth Surface Position")
        
        self._set_input_row(6, ["0", "0", "0", "West"])
        
        # Point B
        self._set_header_cell(7, 0, "Point B")
        self._set_cell(8, 0, "Latitude", bold=True)
        self._set_cell(9, 0, "Degrees")
        self._set_cell(9, 1, "Minutes")
        self._set_cell(9, 2, "Seconds")
        self._set_cell(9, 3, "Earth Surface Position")
        
        self._set_input_row(10, ["0", "0", "0", "North"])
        
        self._set_cell(11, 0, "Longitude", bold=True)
        self._set_cell(12, 0, "Degrees")
        self._set_cell(12, 1, "Minutes")
        self._set_cell(12, 2, "Seconds")
        self._set_cell(12, 3, "Earth Surface Position")
        
        self._set_input_row(13, ["0", "0", "0", "West"])

        # Make unused cells uneditable and grey out
        for row in [0, 1, 2, 4, 5, 7, 8, 9, 11, 12]:
            for col in range(4):
                if not self.coord_table.item(row, col):
                    self._set_cell(row, col, "")

    def _set_header_cell(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setBackground(Qt.GlobalColor.lightGray)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.coord_table.setItem(row, col, item)
        # fill rest of row
        for c in range(1, 4):
            it = QTableWidgetItem("")
            it.setFlags(Qt.ItemFlag.ItemIsEnabled)
            it.setBackground(Qt.GlobalColor.lightGray)
            self.coord_table.setItem(row, c, it)

    def _set_cell(self, row, col, text, bold=False):
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled) # readonly
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        self.coord_table.setItem(row, col, item)

    def _set_input_row(self, row, defaults):
        for col, val in enumerate(defaults[:3]):
            item = QTableWidgetItem(val)
            self.coord_table.setItem(row, col, item)
            
        # Combo Box for Position
        combo = QComboBox()
        if "North" in defaults[3] or "South" in defaults[3]:
            combo.addItems(["North", "South"])
        else:
            combo.addItems(["West", "East"])
        combo.setCurrentText(defaults[3])
        self.coord_table.setCellWidget(row, 3, combo)

    def _setup_result_table(self):
        # Header
        item = QTableWidgetItem("Result")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setBackground(Qt.GlobalColor.lightGray)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.result_table.setItem(0, 0, item)
        
        it2 = QTableWidgetItem("")
        it2.setFlags(Qt.ItemFlag.ItemIsEnabled)
        it2.setBackground(Qt.GlobalColor.lightGray)
        self.result_table.setItem(0, 1, it2)
        
        self._set_result_row(1, "Distance Between Points (km)")
        self._set_result_row(2, "Bearing from Point A to B (Decimal Degrees)")
        self._set_result_row(3, "Bearing from Point A to B (Degrees Minutes Seconds)")

    def _set_result_row(self, row, label):
        lbl_item = QTableWidgetItem(label)
        lbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.result_table.setItem(row, 0, lbl_item)
        
        val_item = QTableWidgetItem("")
        val_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.result_table.setItem(row, 1, val_item)

    def _parse_dms(self, row):
        try:
            d = float(self.coord_table.item(row, 0).text())
            m = float(self.coord_table.item(row, 1).text())
            s = float(self.coord_table.item(row, 2).text())
            return d, m, s
        except Exception:
            raise ValueError("All inputs must be valid numbers.")

    def get_lat_lon(self, row, is_lat):
        d, m, s = self._parse_dms(row)
        val = d + (m / 60.0) + (s / 3600.0)
        
        combo = self.coord_table.cellWidget(row, 3)
        pos = combo.currentText()
        
        if pos == "South" or pos == "East":  # ADT treats East as negative for some reason? Let's check logic: C# says `if (wmP5AOydd == "East") cxiMSguAD = -1.0 * cxiMSguAD;` Yes, East is negative in ADT coordinates.
            val = -val
            
        return val

    def calculate(self):
        try:
            lat_A = self.get_lat_lon(3, True)
            lon_A = self.get_lat_lon(6, False)
            lat_B = self.get_lat_lon(10, True)
            lon_B = self.get_lat_lon(13, False)
            
            # Math conversions to radians
            lat1 = math.radians(lat_A)
            lon1 = math.radians(lon_A)
            lat2 = math.radians(lat_B)
            lon2 = math.radians(lon_B)
            
            dLat = lat2 - lat1
            dLon = lon2 - lon1
            
            # Haversine Distance
            R = 6371.0 # km
            a = math.sin(dLat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c
            
            # Bearing (ADT: -1.0 * Math.Atan2(num11, num12) / Math.PI * 180.0)
            num11 = math.sin(lon2 - lon1) * math.cos(lat2)
            num12 = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
            bearing_rad = math.atan2(num11, num12)
            
            # ADT inverts bearing direction
            bearing_deg = -bearing_rad * 180.0 / math.pi
            
            # wrap to 0-360
            bearing_deg = bearing_deg % 360.0
            if bearing_deg < 0:
                bearing_deg += 360.0
                
            # DMS
            b_d = int(bearing_deg)
            b_m = int((bearing_deg - b_d) * 60)
            b_s = int((bearing_deg - b_d - (b_m / 60.0)) * 3600)
            
            self.result_table.item(1, 1).setText(f"{distance:.3f}")
            self.result_table.item(2, 1).setText(f"{bearing_deg:.2f}")
            self.result_table.item(3, 1).setText(f"{b_d}°{b_m}'{b_s}\"")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
