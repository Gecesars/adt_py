import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class BlackSpotViewer(QDialog):
    def __init__(self, parent=None, mag_3d=None):
        super().__init__(parent)
        self.setWindowTitle("Blackspot Viewer")
        self.resize(800, 600)
        
        self.mag_3d = mag_3d
        
        self.init_ui()
        self.plot_heatmap()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Help label
        lbl = QLabel("This view represents the 3D Radiation Pattern magnitude projected out across Azimuth (X) and Elevation (Y).")
        main_layout.addWidget(lbl)
        
        # Setup pyqtgraph GraphicsLayout
        self.glw = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.glw)
        
        self.plot = self.glw.addPlot()
        self.plot.setLabels(bottom=('Azimuth (Degrees)'), left=('Elevation (Degrees)'))
        # Adjusting limits roughly Az: -180 to 180, El: -90 to 90
        # Given mag_3d is natively [0..359, 0..1800] corresponding to Az (0..359) and El (-90 to 90)
        self.plot.setXRange(-180, 180)
        self.plot.setYRange(-90, 90)
        
        self.img = pg.ImageItem()
        self.plot.addItem(self.img)
        
        # Color scale bar
        self.colorbar = pg.ColorBarItem(interactive=False)
        self.colorbar.setImageItem(self.img, insert_in=self.plot)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def plot_heatmap(self):
        if self.mag_3d is None:
            return
            
        # The ADT mapping aligns:
        # 1.0 = White
        # 0.75 = Yellow
        # 0.5 = Red
        # 0.25 = Blue
        # 0.0 = Black
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array([
            (0, 0, 0, 255),       # Black
            (0, 0, 255, 255),     # Blue
            (255, 0, 0, 255),     # Red
            (255, 255, 0, 255),   # Yellow
            (255, 255, 255, 255)  # White
        ], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        
        self.img.setColorMap(cmap)
        
        # Transpose mag_3d to match pyqtgraph image coordinate expectations (usually (x,y))
        # C# app plotted: bitmap.SetPixel(Az + 180, El*10 + 900)
        # Assuming our main `mag_3d` is shape (360, 1801). We just pass it in.
        heatmap_data = self.mag_3d.copy()
        
        # Scale and render 
        # Shift azimuth bounds to -180 to 180 visual space bounds via QTransform
        from PyQt6.QtGui import QTransform
        tr = QTransform()
        tr.translate(-180, -90)  # Origin to the bottom left (-180 Az, -90 El)
        # Because we have 1801 elevation points spanning 180 degrees, scale Y by 0.1
        tr.scale(1.0, 0.1)
        self.img.setTransform(tr)
        
        self.img.setImage(heatmap_data, autoLevels=False, levels=(0.0, 1.0))
