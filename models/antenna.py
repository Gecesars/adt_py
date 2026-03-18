import os
import numpy as np
from parsers.patterns import read_hrp_pattern, read_vrp_pattern
from solver.pattern_synthesis import (
    apply_panel_phase_shifts,
    calculate_array_3d,
    calculate_single_panel_3d,
)

class AntennaPanel:
    def __init__(self, panel_id, type="Standard"):
        self.panel_id = panel_id
        self.type = type
        self.power = 1.0
        self.phase = 0.0
        self.tilt = 0.0
        self.azimuth = 0.0
        self.elevation = 0.0
        self.face_angle = 0.0
        # Positional offsets usually in meters:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
        # File paths for patterns
        self.hrp_path = ""
        self.vrp_path = ""
        
    def get_radiation_pattern(self):
        """
        Reads the unit pattern from the referenced .pat files.
        Falls back to a mock pattern if no valid path is provided.
        """
        if self.hrp_path and os.path.exists(self.hrp_path):
            _, hrp_mag, hrp_phase = read_hrp_pattern(self.hrp_path)
        else:
            # Fallback Omni mock
            hrp_mag = np.ones(360) 
            hrp_phase = np.zeros(360)
            
        if self.vrp_path and os.path.exists(self.vrp_path):
            _, vrp_mag, vrp_phase = read_vrp_pattern(self.vrp_path)
        else:
            # Fallback simple cardioid VRP mock
            elevations = np.linspace(-90, 90, 1801)
            vrp_mag = np.cos(np.deg2rad(elevations))
            vrp_phase = np.zeros(1801)
            
        return hrp_mag, hrp_phase, vrp_mag, vrp_phase

class ArrayDesign:
    def __init__(self):
        self.panels = []
        self.frequency = 539.0  # MHz
        
    def add_panel(self, panel):
        self.panels.append(panel)
        
    def calculate_3d_pattern(self):
        panel_3d_patterns = []
        for panel in self.panels:
            # 1. Load baseline Unit pattern
            hrp_mag, hrp_phase, vrp_mag, vrp_phase = panel.get_radiation_pattern()
            
            hrp_angles = np.linspace(-180, 179, 360)
            vrp_angles = np.linspace(-90, 90, 1801)
            
            # 2. Add spatial shifts and power multipliers based on Array Geometry
            # This simulates what HPatternFunction and VPatternFunction do in ADT.
            hrp_mag_sq, hrp_phase_sh = apply_panel_phase_shifts(
                hrp_angles,
                hrp_mag,
                hrp_phase,
                self.frequency,
                x_off=panel.x,
                y_off=panel.y,
                face_angle=panel.face_angle,
                panel_phase=panel.phase,
                power_ratio=panel.power,
            )
            
            vrp_mag_sq, vrp_phase_sh = apply_panel_phase_shifts(
                vrp_angles,
                vrp_mag,
                vrp_phase,
                self.frequency,
                x_off=0.0,
                y_off=panel.z,
                face_angle=panel.tilt,
                panel_phase=0.0,
                power_ratio=1.0,
            )
            
            # 3. Calculate Synthesis
            pat_3d = calculate_single_panel_3d(hrp_mag_sq, hrp_phase_sh, vrp_mag_sq, vrp_phase_sh)
            panel_3d_patterns.append(pat_3d)
            
        return calculate_array_3d(panel_3d_patterns)
