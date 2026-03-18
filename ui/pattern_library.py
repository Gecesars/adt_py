import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QComboBox, QLineEdit,
                             QHBoxLayout, QPushButton, QFileDialog)
from PyQt6.QtCore import Qt

class PatternLibraryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # In the screenshot, the "Pattern Library" is a repeating list of patterns, 
        # looking much like a property grid or a table with two columns:
        # e.g., "Pattern 1" -> "Standard"
        #       "Panel Type" -> "Panel Array_PHP4S"
        # Since it repeats, a QTableWidget is a good fit.
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Populate with mock data based on screenshot
        patterns = 4
        
        for i in range(1, patterns + 1):
            self.add_pattern_group(i)
            
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def add_pattern_group(self, index):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Title "Pattern 1"
        item_title = QTableWidgetItem(f"Pattern {index}")
        item_title.setBackground(Qt.GlobalColor.lightGray)
        # item_title.setFlags(Qt.ItemFlag.ItemIsEnabled)
        
        combo_standard = QComboBox()
        combo_standard.addItems(["Standard", "Custom", "Imported"])
        
        self.table.setItem(row, 0, item_title)
        self.table.setCellWidget(row, 1, combo_standard)
        
        # Properties
        props = [
            ("Panel Type", "Panel Array_PHP4S"),
            ("Elevation Spacing (m)", "1.15"),
            ("Width (m)", "0.5"),
            ("Height (m)", "1.09"),
            ("Depth (m)", "0.22"),
            ("HRP File", ""),
            ("VRP File", "")
        ]
        
        for p_name, p_val in props:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(p_name))
            
            if "File" in p_name:
                # Custom widget with text box and browse button
                file_widget = QWidget()
                h_layout = QHBoxLayout(file_widget)
                h_layout.setContentsMargins(0, 0, 0, 0)
                h_layout.setSpacing(2)
                
                txt_path = QLineEdit(p_val)
                txt_path.setObjectName(f"txt_{index}_{p_name.split()[0]}")
                txt_path.setReadOnly(True)
                txt_path.setStyleSheet("border: 1px solid #ccc;")
                
                from PyQt6.QtWidgets import QPushButton, QFileDialog
                btn_browse = QPushButton("...")
                btn_browse.setFixedWidth(30)
                
                # Connect lambda properly passing txt_path to update it
                btn_browse.clicked.connect(lambda checked, t=txt_path: self.browse_file(t))
                
                h_layout.addWidget(txt_path)
                h_layout.addWidget(btn_browse)
                
                self.table.setCellWidget(r, 1, file_widget)
            else:
                # Value field
                val_input = QLineEdit(p_val)
                val_input.setStyleSheet("border: none; background: transparent;")
                self.table.setCellWidget(r, 1, val_input)

    def browse_file(self, line_edit):
        from PyQt6.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Pattern File", "", "Pattern Files (*.pat *.hup *.vup);;All Files (*)")
        if file_name:
            line_edit.setText(file_name)
            
    def get_pattern_configs(self):
        """
        Scrape the table to find the assigned File paths per pattern index.
        Returns a dict: { 1: {'hrp_path': '...', 'vrp_path': '...'}, 2: {...} }
        """
        configs = {}
        current_pattern = None
        
        for r in range(self.table.rowCount()):
            key_item = self.table.item(r, 0)
            if not key_item:
                continue
                
            key_text = key_item.text()
            
            if key_text.startswith("Pattern "):
                current_pattern = int(key_text.split(" ")[1])
                if current_pattern not in configs:
                    configs[current_pattern] = {'hrp_path': '', 'vrp_path': ''}
            elif current_pattern is not None:
                if key_text == "HRP File" or key_text == "VRP File":
                    # The widget is a layout with QLineEdit and QPushButton
                    cell_widget = self.table.cellWidget(r, 1)
                    if cell_widget:
                        # Find the QLineEdit inside
                        txt_path = cell_widget.findChild(QLineEdit)
                        if txt_path:
                            if key_text == "HRP File":
                                configs[current_pattern]['hrp_path'] = txt_path.text()
                            else:
                                configs[current_pattern]['vrp_path'] = txt_path.text()
                                
        return configs
