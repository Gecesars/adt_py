from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

class ResultSummaryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.params = [
            "Channel Frequency (MHz)",
            "3D Directivity (dBd)",
            "Azimuth Angle (Emax) (deg)",
            "Elevation Angle (Emax) (deg)",
            "Internal Loss (dB)",
            "Polarisation Loss (dB)",
            "Filter/Combiner Loss (dB)",
            "Main Feeder Loss (dB)",
            "System Gain (dBd)",
            "Transmitter Power (kW)",
            "Transmitter Power (dBW)",
            "ERP (dBW)",
            "ERP (dBk)",
            "ERP (kW)"
        ]
        
        self.table = QTableWidget(len(self.params), 2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        for i, param in enumerate(self.params):
            self.table.setItem(i, 0, QTableWidgetItem(param))
            self.table.setItem(i, 1, QTableWidgetItem(""))
            
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_results(self, metrics_dict):
        """Update table based on a dictionary of metrics."""
        for i, param in enumerate(self.params):
            val = metrics_dict.get(param, "")
            self.table.item(i, 1).setText(str(val))
