# core/pattern_parser.py
import numpy as np

def read_hrp_pattern(filepath):
    """
    Parses a .pat or .hup HRP antenna pattern file.
    Returns:
        angles_deg: 1D numpy array of angles (-180 to 179)
        mag: 1D numpy array of linear voltage magnitudes
        phase_deg: 1D numpy array of phases in degrees
    """
    angles = []
    mags = []
    phases = []
    
    with open(filepath, 'r') as f:
        # Read headers until we hit "voltage"
        for line in f:
            if line.strip().lower() == "voltage":
                break
        
        # Read the data lines
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                angle = float(parts[0])
                mag = float(parts[1])
                phase = float(parts[2])
                
                angles.append(angle)
                mags.append(mag)
                phases.append(phase)
                
    # Keep only the first 360 points if there's overlap
    if len(angles) > 360:
        angles = angles[:360]
        mags = mags[:360]
        phases = phases[:360]
        
    # Convert to numpy arrays
    angles = np.array(angles)
    mags = np.array(mags)
    phases = np.array(phases)
    
    return angles, mags, phases

def read_vrp_pattern(filepath):
    """
    Parses a .pat or .vup VRP antenna pattern file.
    Interpolates the data linearly to a 0.1 degree resolution from -90 to +90.
    Returns:
        angles_deg: 1D numpy array of angles (-90 to +90)
        mag: 1D numpy array of linear voltage magnitudes
        phase_deg: 1D numpy array of phases in degrees
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    start_angle = float(lines[6].strip().split()[0])
    stop_angle = float(lines[7].strip().split()[0])
    step_size = abs(stop_angle - start_angle)
    
    # Normally, we'd calculate interpolation steps if step_size > 0.1
    # For robust python, scipy's interp1d is cleaner, but we can do linear directly or use numpy
    
    # Find the start of the data (after finding -90)
    data_start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("-90"):
            data_start_idx = i
            break
            
    raw_angles = []
    raw_mags = []
    raw_phases = []
    
    # In VRP files, line indexing can wrap around 180 or go -90 to 90 directly.
    # The ADT loop breaks or wraps. Standard ADT VRP files usually map -90 up to +90.
    for line in lines[data_start_idx:]:
        parts = line.strip().split()
        if len(parts) >= 3:
            raw_angles.append(float(parts[0]))
            raw_mags.append(float(parts[1]))
            raw_phases.append(float(parts[2]))
            
    raw_angles = np.array(raw_angles)
    raw_mags = np.array(raw_mags)
    raw_phases = np.array(raw_phases)
    
    # We want a standard grid of -90 to 90 exactly at 0.1 degree increments (1801 points)
    target_angles = np.linspace(-90, 90, 1801)
    
    # If the raw data doesn't span exactly -90 to 90, interpolation will fail, 
    # but the original ADT code assumes there is mapping from -90 to 90.
    # We'll use numpy piecewise linear interpolation `numpy.interp`
    interp_mags = np.interp(target_angles, raw_angles, raw_mags)
    interp_phases = np.interp(target_angles, raw_angles, raw_phases)
    
    return target_angles, interp_mags, interp_phases
