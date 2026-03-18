import numpy as np

def calculate_single_panel_3d(hrp_mag, hrp_phase_deg, vrp_mag, vrp_phase_deg):
    """
    Computes the 3D complex radiation pattern for a single panel.
    Returns a 2D complex numpy array of shape (len(hrp_mag), len(vrp_mag)).
    """
    # Convert phase to radians
    hrp_phase_rad = np.deg2rad(hrp_phase_deg)
    vrp_phase_rad = np.deg2rad(vrp_phase_deg)
    
    # Create complex 1D arrays
    hrp_complex = hrp_mag * np.exp(1j * hrp_phase_rad)
    vrp_complex = vrp_mag * np.exp(1j * vrp_phase_rad)
    
    # The 3D pattern of a single panel is the outer product of HRP and VRP
    # C# equivalent: 
    # Real = hrp.Real * vrp.Real - hrp.Imag * vrp.Imag
    # Imag = hrp.Imag * vrp.Real + hrp.Real * vrp.Imag
    # This is exactly the complex multiplication of the outer product.
    pat_3d = np.outer(hrp_complex, vrp_complex)
    return pat_3d

def calculate_array_3d(panel_3d_patterns):
    """
    Sums the 3D complex patterns of all panels to get the array pattern.
    Normalizes the final magnitude so the peak is 1.0 (0 dB).
    Returns the magnitude (shape: N_phi x N_theta) and phase (in degrees).
    """
    if not panel_3d_patterns:
        return np.zeros((1, 1)), np.zeros((1, 1))
        
    # Sum all complex panel patterns
    total_complex = sum(panel_3d_patterns)
    
    # Get magnitude and phase
    mag = np.abs(total_complex)
    phase = np.angle(total_complex, deg=True)
    
    # Normalize by max magnitude
    max_mag = np.max(mag)
    if max_mag > 0:
        mag /= max_mag
        
    return mag, phase

def get_3d_directivity(pat_3d_mag, elevation_angles_deg):
    """
    Calculates the 3D directivity of the array in dBd.
    pat_3d_mag: 2D array of normalized magnitudes (linear, max 1.0).
                shape should be (len(azimuth), len(elevation)).
    elevation_angles_deg: 1D array of elevation angles corresponding to columns.
                          (typically 90 to -90, or -90 to 90)
    """
    # Power is magnitude squared
    power = pat_3d_mag ** 2
    max_power = np.max(power)
    
    # The integration weighting factor is Sin((Theta + 90) * PI / 180)
    # where Theta is the elevation angle.
    theta_rad = np.deg2rad(elevation_angles_deg + 90.0)
    
    # Broadcast weighting across azimuth angles
    # Resulting shape of power_sin matches power (N_phi, N_theta)
    power_sin = power * np.sin(theta_rad)[np.newaxis, :]
    
    num2 = np.sum(power_sin)
    total_points = power.size
    
    if num2 == 0:
        return 0.0
        
    # Formula from C# GFunctions.Get3Ddirectivity:
    # 10.0 * Math.Log10(max_power * total_points * 2.0 / num2 / Math.PI / 1.64)
    directivity_dbd = 10.0 * np.log10(max_power * total_points * 2.0 / num2 / np.pi / 1.64)
    return directivity_dbd

def apply_panel_phase_shifts(angles_deg, mag, phase_deg, frequency_mhz, x_off=0.0, y_off=0.0, face_angle=0.0, panel_phase=0.0, power_ratio=1.0):
    """
    Applies spatial phase shifts to an HRP or VRP pattern based on panel position.
    
    angles_deg: 1D array of angles (Azimuth for HRP, Elevation for VRP)
    mag: linear magnitude array
    phase_deg: intrinsic phase array in degrees
    frequency_mhz: frequency in MHz to calculate wavelength
    x_off, y_off: positional offsets of the panel (in meters)
    face_angle: tilt/face angle of the panel
    panel_phase: electrical feed phase
    power_ratio: power coefficient for the panel
    
    Returns: shifted_mag, shifted_phase_deg
    """
    wavelength = 300.0 / frequency_mhz
    
    # Adjust angles by face/tilt angle
    # We assume pattern mag/phase are interpolated or aligned. 
    # For a synthesized discrete calculation, usually the baseline angle array is fixed
    # and we evaluate the spatial phase shift at each angle.
    
    shifted_mag = mag * np.sqrt(power_ratio)
    
    # Spatial phaseshift formula from C#:
    # phase += y_off * cos(angle) / lambda * 360 + x_off * sin(angle) / lambda * 360 + panel_phase
    # For HRP, x_off = panel.x, y_off = panel.y
    # For VRP, x_off = 0, y_off = panel.z, and angle is adjusted by +90 in the cos/sin
    
    angles_rad = np.deg2rad(angles_deg)
    spatial_phase = (y_off * np.cos(angles_rad) + x_off * np.sin(angles_rad)) / wavelength * 360.0
    
    shifted_phase_deg = phase_deg + spatial_phase + panel_phase
    
    # Keep phase in [-180, 180] if necessary, though exp(j*phi) handles it automatically
    shifted_phase_deg = (shifted_phase_deg + 180) % 360 - 180
    
    return shifted_mag, shifted_phase_deg
