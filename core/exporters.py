import numpy as np

def export_txt(path, mag_3d, az_angles, el_angles, delimiter='\t'):
    """
    Export 3D radiation pattern to a standard tabulated text file.
    Rows = Azimuth, Columns = Elevation.
    """
    with open(path, 'w') as f:
        # Header row: Elevations
        f.write("Az / El" + delimiter)
        f.write(delimiter.join([f"{el:.1f}" for el in el_angles]) + "\n")
        
        for i, az in enumerate(az_angles):
            row_data = [f"{mag_3d[i, j]:.4f}" for j in range(len(el_angles))]
            f.write(f"{az:.1f}" + delimiter + delimiter.join(row_data) + "\n")

def export_prn(path, mag_3d, az_angles, el_angles):
    """
    Export 3D radiation pattern to PRN format.
    Usually PRN files space format specifically for antenna modelling tools.
    For this phase, writing as formatted text grid.
    """
    with open(path, 'w') as f:
        f.write("PRN 3D Antenna Pattern\n")
        f.write(f"Resolution: Az {len(az_angles)}, El {len(el_angles)}\n")
        f.write("-" * 50 + "\n")
        for i, az in enumerate(az_angles):
            for j, el in enumerate(el_angles):
                # Write if magnitude is somewhat significant to save space, or write all
                f.write(f"{az:05.1f} {el:05.1f} {mag_3d[i, j]:.4f}\n")

def export_atdi(path, mag_3d, az_angles, el_angles):
    """
    Export to ATDI standard. Typically columns of Az, El, Gain.
    """
    with open(path, 'w') as f:
        f.write("REV\n")
        f.write("FPAT\n")
        # Mock header for ATDI
        for i, az in enumerate(az_angles):
            for j, el in enumerate(el_angles):
                val = mag_3d[i, j]
                # Log scale usually for ATDI
                db_val = 20 * np.log10(val) if val > 1e-5 else -100.0
                f.write(f"{az:.1f}\t{el:.1f}\t{db_val:.2f}\n")

def export_to_format(format_name, path, mag_3d, az_angles, el_angles):
    """
    Router for all export types defined.
    """
    if mag_3d is None or az_angles is None or el_angles is None:
        raise ValueError("3D Pattern data is empty. Calculate 3D Pattern first.")
        
    if "Text" in format_name or "NGW3D" in format_name:
        export_txt(path, mag_3d, az_angles, el_angles, delimiter='\t')
    elif "CSV" in format_name:
        export_txt(path, mag_3d, az_angles, el_angles, delimiter=',')
    elif "PRN" in format_name:
        export_prn(path, mag_3d, az_angles, el_angles)
    elif "ATDI" in format_name:
        export_atdi(path, mag_3d, az_angles, el_angles)
    else:
        # Fallback
        export_txt(path, mag_3d, az_angles, el_angles, delimiter='\t')
