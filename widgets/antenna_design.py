from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QLabel, QHBoxLayout, QSplitter)
from PyQt6.QtCore import Qt

class AntennaDesignWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT SIDE ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        # Horizontal Group
        from PyQt6.QtWidgets import QGroupBox, QHeaderView
        h_group_box = QGroupBox("Horizontal Group Φ & Power")
        h_group_layout = QVBoxLayout(h_group_box)
        h_group_layout.setContentsMargins(0, 5, 0, 0)
        
        self.h_group_table = QTableWidget(2, 12)
        faces = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
        self.h_group_table.setHorizontalHeaderLabels(faces)
        self.h_group_table.setVerticalHeaderLabels(["Φ", "Pwr"])
        
        table_style = """
            QTableWidget { font-size: 11px; }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 2px;
                border: 1px solid #c0c0c0;
                font-size: 11px;
            }
        """
        self.h_group_table.setStyleSheet(table_style)
        self.h_group_table.verticalHeader().setDefaultSectionSize(22)
        self.h_group_table.setFixedHeight(82) # Approximate height for header + 2 rows
        self.h_group_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for col in range(12):
            self.h_group_table.setItem(0, col, QTableWidgetItem("0.0"))
            self.h_group_table.setItem(1, col, QTableWidgetItem("1.000"))
            
        h_group_layout.addWidget(self.h_group_table)
        left_layout.addWidget(h_group_box, stretch=0)
        
        # Array Data
        array_box = QGroupBox("Array Data")
        array_layout = QVBoxLayout(array_box)
        array_layout.setContentsMargins(0, 5, 0, 0)
        
        self.array_table = QTableWidget(16, 13) # Show 16 rows to match empty rows in ref
        headers = ["Panel", "Angle", "Offset", "Elev", "Az", "Pwr", "Φ", "Tilt", "Config\n(0-5)*", "Pat", "Level", "Face", "Input"]
        self.array_table.setHorizontalHeaderLabels(headers)
        self.array_table.verticalHeader().setVisible(False)
        self.array_table.setStyleSheet(table_style)
        self.array_table.verticalHeader().setDefaultSectionSize(22)
        
        for row in range(16):
            # To match the reference, panel column is grayed out/centered
            panel_item = QTableWidgetItem(str(row+1))
            panel_item.setBackground(Qt.GlobalColor.lightGray)
            panel_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.array_table.setItem(row, 0, panel_item)
            
            if row < 4:
                self.array_table.setItem(row, 1, QTableWidgetItem("0.0"))
                self.array_table.setItem(row, 2, QTableWidgetItem("0.000"))
                self.array_table.setItem(row, 3, QTableWidgetItem("0.000"))
                self.array_table.setItem(row, 4, QTableWidgetItem("0.0"))
                self.array_table.setItem(row, 5, QTableWidgetItem("1.000"))
                self.array_table.setItem(row, 6, QTableWidgetItem("0.0"))
                self.array_table.setItem(row, 7, QTableWidgetItem("0.0"))
                self.array_table.setItem(row, 8, QTableWidgetItem("0"))
                self.array_table.setItem(row, 9, QTableWidgetItem("1"))
                self.array_table.setItem(row, 10, QTableWidgetItem("1"))
                self.array_table.setItem(row, 11, QTableWidgetItem("A"))
                self.array_table.setItem(row, 12, QTableWidgetItem("1"))
            
        array_layout.addWidget(self.array_table)
        left_layout.addWidget(array_box, stretch=1)
        
        # --- RIGHT SIDE ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        v_group_box = QGroupBox("Vertical Group Φ")
        v_group_layout = QVBoxLayout(v_group_box)
        v_group_layout.setContentsMargins(0, 5, 0, 0)
        
        self.v_group_table = QTableWidget(16, 1)
        self.v_group_table.setVerticalHeaderLabels([str(i) for i in range(1, 17)])
        self.v_group_table.setHorizontalHeaderLabels(["Φ"])
        self.v_group_table.setStyleSheet(table_style)
        self.v_group_table.verticalHeader().setDefaultSectionSize(22)
        
        # Make the single column take up the remaining space
        self.v_group_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Color vertical header slightly gray like the panel column
        for row in range(16):
            self.v_group_table.setItem(row, 0, QTableWidgetItem("0.0"))
            
        v_group_layout.addWidget(self.v_group_table)
        right_layout.addWidget(v_group_box)
        
        # Assemble Splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([800, 120]) # Force the right panel to be small
        
        main_layout.addWidget(splitter)

    def get_array_data(self):
        """
        Parses the physical array configuration from the QTableWidget.
        Returns a list of dicts, each representing a single AntennaPanel configuration.
        """
        panels_data = []
        for row in range(self.array_table.rowCount()):
            # Fallbacks in case cells are empty / None
            def get_val(col, default=0.0):
                item = self.array_table.item(row, col)
                if not item or not item.text(): return default
                try: return float(item.text())
                except ValueError: return default
            
            # Columns match `headers = ["Panel", "Angle", "Offset", "Elev", "Az", "Pwr", "Φ", "Tilt", "Config\n(0-5)*", "Pat", "Level", "Face", "Input"]`
            panel_id = int(get_val(0, default=row+1))
            offset_y = get_val(2)  # Treating Offset as Y offset (vertical height)
            power = get_val(5, default=1.0)
            phase = get_val(6)     # Φ
            tilt = get_val(7)      # Tilt
            pat_index = int(get_val(9, default=1)) # Pattern index (1, 2, 3...)
            
            panels_data.append({
                'panel_id': panel_id,
                'y': offset_y,
                'power': power,
                'phase': phase,
                'tilt': tilt,
                'pat': pat_index
            })
            
        return panels_data
