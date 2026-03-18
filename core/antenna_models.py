# core/antenna_models.py

import numpy as np
from core.math_funcs import calculate_single_panel_3d, calculate_array_3d, get_3d_directivity

def calculate_system_metrics(array_design, 
                             internal_loss=0.5, 
                             pol_loss=3.0, 
                             filter_loss=0.8, 
                             feeder_loss=1.2, 
                             tx_power_kw=None):
    """
    Computes system parameters based on the simulated 3D directivity.
    """
    freq = array_design.frequency
    
    # Calculate Array 3D Pattern
    mag_3d, phase_3d = array_design.calculate_3d_pattern()
    elevation_angles = np.linspace(-90, 90, mag_3d.shape[1])
    
    # Get 3D Directivity
    directivity_dbd = get_3d_directivity(mag_3d, elevation_angles)
    
    # Calculate Peak Angles
    max_idx = np.unravel_index(np.argmax(mag_3d), mag_3d.shape)
    az_angles = np.linspace(0, 359, mag_3d.shape[0])
    az_max = az_angles[max_idx[0]]
    el_max = elevation_angles[max_idx[1]]
    
    # Determine system gain metrics
    system_loss = internal_loss + pol_loss + filter_loss + feeder_loss
    system_gain = directivity_dbd - system_loss
    
    if tx_power_kw is not None:
        tx_power = tx_power_kw
    else:
        # Default fallback to panel nominal power sum
        tx_power = sum(p.power for p in array_design.panels)
        
    if tx_power > 0:
        erp_dbw = 10 * np.log10(tx_power * 1000) + system_gain
        erp_kw = (10 ** (erp_dbw / 10)) / 1000.0
    else:
        erp_dbw = 0.0
        erp_kw = 0.0
    
    results = {
        "Channel Frequency (MHz)": f"{freq:.2f}",
        "3D Directivity (dBd)": f"{directivity_dbd:.2f}",
        "Azimuth Angle (Emax) (deg)": f"{az_max:.1f}",
        "Elevation Angle (Emax) (deg)": f"{el_max:.1f}",
        "Internal Loss (dB)": f"{internal_loss:.2f}",
        "Polarisation Loss (dB)": f"{pol_loss:.2f}",
        "Filter/Combiner Loss (dB)": f"{filter_loss:.2f}",
        "Main Feeder Loss (dB)": f"{feeder_loss:.2f}",
        "System Gain (dBd)": f"{system_gain:.2f}",
        "Transmitter Power (kW)": f"{tx_power:.2f}",
        "ERP (dBW)": f"{erp_dbw:.2f}",
        "ERP (kW)": f"{erp_kw:.2f}"
    }
    
    return results, mag_3d, az_angles, elevation_angles

import os
from core.pattern_parser import read_hrp_pattern, read_vrp_pattern

class AntennaPanel:
    def __init__(self, panel_id, type="Standard"):
        self.panel_id = panel_id
        self.type = type
        self.power = 1.0
        self.phase = 0.0
        self.tilt = 0.0
        self.azimuth = 0.0
        self.elevation = 0.0
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
        self.frequency = 539.0 # MHz
        
    def add_panel(self, panel):
        self.panels.append(panel)
        
    def calculate_3d_pattern(self):
        from core.math_funcs import apply_panel_phase_shifts
        panel_3d_patterns = []
        for panel in self.panels:
            # 1. Load baseline Unit pattern
            hrp_mag, hrp_phase, vrp_mag, vrp_phase = panel.get_radiation_pattern()
            
            hrp_angles = np.linspace(-180, 179, 360)
            vrp_angles = np.linspace(-90, 90, 1801)
            
            # 2. Add spatial shifts and power multipliers based on Array Geometry
            # This simulates what HPatternFunction and VPatternFunction do in ADT.
            hrp_mag_sq, hrp_phase_sh = apply_panel_phase_shifts(
                hrp_angles, hrp_mag, hrp_phase, self.frequency, 
                x_off=panel.x, y_off=panel.y, face_angle=panel.face_angle if hasattr(panel, 'face_angle') else 0.0, 
                panel_phase=panel.phase, power_ratio=panel.power
            )
            
            vrp_mag_sq, vrp_phase_sh = apply_panel_phase_shifts(
                vrp_angles, vrp_mag, vrp_phase, self.frequency, 
                x_off=0.0, y_off=panel.z, face_angle=panel.tilt, 
                panel_phase=0.0, power_ratio=1.0  # VRP usually relies on HRP for power multiplier in synthesis
            )
            
            # 3. Calculate Synthesis
            pat_3d = calculate_single_panel_3d(hrp_mag_sq, hrp_phase_sh, vrp_mag_sq, vrp_phase_sh)
            panel_3d_patterns.append(pat_3d)
            
        return calculate_array_3d(panel_3d_patterns)
        return calculate_array_3d(panel_3d_patterns)
