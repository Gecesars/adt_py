from __future__ import annotations

import math

from domain import (
    ArrayPanel,
    DesignMetadata,
    FaceExcitation,
    LevelExcitation,
    LossProfile,
    PatternDefinition,
    Project,
    SiteConfig,
)
from models.antenna import AntennaPanel, ArrayDesign
from solver.system_metrics import calculate_system_metrics


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _set_combo_value(combo_box, value):
    if value is None:
        return
    index = combo_box.findText(value)
    if index >= 0:
        combo_box.setCurrentIndex(index)


def polar_to_cartesian(angle_deg: float, offset_m: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    x = offset_m * math.sin(angle_rad)
    y = offset_m * math.cos(angle_rad)
    return x, y


def compose_panel_excitation(
    panel: ArrayPanel,
    horizontal_groups: dict[str, FaceExcitation],
    vertical_groups: dict[int, LevelExcitation],
) -> tuple[float, float]:
    face_key = panel.face.upper()
    face_group = horizontal_groups.get(face_key, FaceExcitation(face=face_key))
    level_group = vertical_groups.get(panel.level, LevelExcitation(level=panel.level))

    effective_power = panel.power * face_group.power
    effective_phase = panel.phase_deg + face_group.phase_deg + level_group.phase_deg
    return effective_power, effective_phase


def build_project_from_ui(
    design_info_widget,
    antenna_design_widget,
    pattern_library_widget,
) -> Project:
    metadata = DesignMetadata(
        customer=design_info_widget.customer_input.text().strip(),
        site_name=design_info_widget.site_name_input.text().strip(),
        antenna_model=design_info_widget.antenna_model_input.text().strip(),
        design_frequency_mhz=_safe_float(
            design_info_widget.design_freq_input.text(), 539.0
        ),
        channel_frequency_mhz=_safe_float(
            design_info_widget.channel_freq_input.text(), 539.0
        ),
        polarization=design_info_widget.polarisation_combo.currentText(),
        signal_type=design_info_widget.signal_type_combo.currentText(),
        designer_name=design_info_widget.designer_name_input.text().strip(),
        date_created=design_info_widget.date_created_input.text().strip(),
        design_note=design_info_widget.design_note_input.text().strip(),
    )
    losses = LossProfile(
        internal_db=_safe_float(design_info_widget.internal_loss_input.text(), 0.5),
        polarization_db=_safe_float(design_info_widget.pol_loss_input.text(), 3.0),
        filter_combiner_db=_safe_float(
            design_info_widget.filter_loss_input.text(), 0.8
        ),
        feeder_db=_safe_float(design_info_widget.feeder_loss_input.text(), 1.2),
    )

    pattern_configs = pattern_library_widget.get_pattern_configs()
    patterns = [
        PatternDefinition(
            index=index,
            mode=config.get("mode", "Standard"),
            panel_type=config.get("panel_type", "Panel Array_PHP4S"),
            elevation_spacing_m=_safe_float(config.get("elevation_spacing_m"), 1.15),
            width_m=_safe_float(config.get("width_m"), 0.5),
            height_m=_safe_float(config.get("height_m"), 1.09),
            depth_m=_safe_float(config.get("depth_m"), 0.22),
            hrp_path=config.get("hrp_path", ""),
            vrp_path=config.get("vrp_path", ""),
        )
        for index, config in sorted(pattern_configs.items())
    ]

    panels = [
        ArrayPanel(
            panel_id=_safe_int(panel_data.get("panel_id"), 1),
            angle_deg=_safe_float(panel_data.get("angle_deg"), 0.0),
            offset_m=_safe_float(panel_data.get("offset_m"), 0.0),
            elevation_m=_safe_float(panel_data.get("elevation_m"), 0.0),
            azimuth_deg=_safe_float(panel_data.get("azimuth_deg"), 0.0),
            power=_safe_float(panel_data.get("power"), 1.0),
            phase_deg=_safe_float(panel_data.get("phase_deg"), 0.0),
            tilt_deg=_safe_float(panel_data.get("tilt_deg"), 0.0),
            configuration=_safe_int(panel_data.get("configuration"), 0),
            pattern_index=_safe_int(panel_data.get("pattern_index"), 1),
            level=_safe_int(panel_data.get("level"), 1),
            face=str(panel_data.get("face", "A") or "A").upper(),
            input_number=_safe_int(panel_data.get("input_number"), 1),
        )
        for panel_data in antenna_design_widget.get_array_data()
    ]

    horizontal_groups = {
        face.upper(): FaceExcitation(
            face=face.upper(),
            phase_deg=_safe_float(group.get("phase_deg"), 0.0),
            power=_safe_float(group.get("power"), 1.0),
        )
        for face, group in antenna_design_widget.get_horizontal_group_data().items()
    }
    vertical_groups = {
        int(level): LevelExcitation(
            level=int(level),
            phase_deg=_safe_float(group.get("phase_deg"), 0.0),
        )
        for level, group in antenna_design_widget.get_vertical_group_data().items()
    }

    return Project(
        schema_version=1,
        metadata=metadata,
        site=SiteConfig(),
        losses=losses,
        patterns=patterns,
        panels=panels,
        horizontal_groups=horizontal_groups,
        vertical_groups=vertical_groups,
    )


def apply_project_to_ui(
    project: Project,
    design_info_widget,
    antenna_design_widget,
    pattern_library_widget,
):
    metadata = project.metadata
    losses = project.losses

    design_info_widget.customer_input.setText(metadata.customer)
    design_info_widget.site_name_input.setText(metadata.site_name)
    design_info_widget.antenna_model_input.setText(metadata.antenna_model)
    design_info_widget.design_freq_input.setText(
        f"{metadata.design_frequency_mhz:g}"
    )
    design_info_widget.channel_freq_input.setText(
        f"{metadata.channel_frequency_mhz:g}"
    )
    _set_combo_value(design_info_widget.polarisation_combo, metadata.polarization)
    _set_combo_value(design_info_widget.signal_type_combo, metadata.signal_type)
    design_info_widget.num_panels_spin.setValue(max(1, len(project.panels) or 1))
    design_info_widget.designer_name_input.setText(metadata.designer_name)
    design_info_widget.date_created_input.setText(metadata.date_created)
    design_info_widget.design_note_input.setText(metadata.design_note)
    design_info_widget.internal_loss_input.setText(f"{losses.internal_db:g}")
    design_info_widget.pol_loss_input.setText(f"{losses.polarization_db:g}")
    design_info_widget.filter_loss_input.setText(f"{losses.filter_combiner_db:g}")
    design_info_widget.feeder_loss_input.setText(f"{losses.feeder_db:g}")

    pattern_library_widget.set_pattern_configs(
        {
            pattern.index: {
                "mode": pattern.mode,
                "panel_type": pattern.panel_type,
                "elevation_spacing_m": pattern.elevation_spacing_m,
                "width_m": pattern.width_m,
                "height_m": pattern.height_m,
                "depth_m": pattern.depth_m,
                "hrp_path": pattern.hrp_path,
                "vrp_path": pattern.vrp_path,
            }
            for pattern in project.patterns
        }
    )
    antenna_design_widget.set_horizontal_group_data(
        {
            face: {"phase_deg": group.phase_deg, "power": group.power}
            for face, group in project.horizontal_groups.items()
        }
    )
    antenna_design_widget.set_vertical_group_data(
        {
            level: {"phase_deg": group.phase_deg}
            for level, group in project.vertical_groups.items()
        }
    )
    antenna_design_widget.set_array_data(
        [
            {
                "panel_id": panel.panel_id,
                "angle_deg": panel.angle_deg,
                "offset_m": panel.offset_m,
                "elevation_m": panel.elevation_m,
                "azimuth_deg": panel.azimuth_deg,
                "power": panel.power,
                "phase_deg": panel.phase_deg,
                "tilt_deg": panel.tilt_deg,
                "configuration": panel.configuration,
                "pattern_index": panel.pattern_index,
                "level": panel.level,
                "face": panel.face,
                "input_number": panel.input_number,
            }
            for panel in project.panels
        ]
    )


def project_to_array_design(project: Project) -> ArrayDesign:
    pattern_map = {pattern.index: pattern for pattern in project.patterns}
    array_design = ArrayDesign()
    array_design.frequency = project.metadata.channel_frequency_mhz

    for panel in project.panels:
        pattern = pattern_map.get(panel.pattern_index, PatternDefinition(index=1))
        effective_power, effective_phase = compose_panel_excitation(
            panel, project.horizontal_groups, project.vertical_groups
        )
        x, y = polar_to_cartesian(panel.angle_deg, panel.offset_m)

        runtime_panel = AntennaPanel(panel.panel_id, type=pattern.mode)
        runtime_panel.panel_type_name = pattern.panel_type
        runtime_panel.x = x
        runtime_panel.y = y
        runtime_panel.z = panel.elevation_m
        runtime_panel.power = effective_power
        runtime_panel.phase = effective_phase
        # ADT stores the Array Data tilt with the opposite sign of the runtime AntPanel tilt.
        runtime_panel.tilt = -panel.tilt_deg
        runtime_panel.face_angle = round(panel.azimuth_deg, 0)
        runtime_panel.configuration = panel.configuration
        runtime_panel.design_frequency = project.metadata.design_frequency_mhz
        runtime_panel.hrp_path = pattern.hrp_path
        runtime_panel.vrp_path = pattern.vrp_path

        array_design.add_panel(runtime_panel)

    return array_design


def calculate_project_metrics(project: Project):
    tx_power_kw = project.site.transmitter_power_kw
    if tx_power_kw <= 0:
        tx_power_kw = None

    return calculate_system_metrics(
        project_to_array_design(project),
        internal_loss=project.losses.internal_db,
        pol_loss=project.losses.polarization_db,
        filter_loss=project.losses.filter_combiner_db,
        feeder_loss=project.losses.feeder_db,
        tx_power_kw=tx_power_kw,
    )
