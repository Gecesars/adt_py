import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from base64 import b64decode, b64encode
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTabWidget, QDockWidget, QMenuBar, QMenu, QStatusBar,
                             QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QLabel, QSplitter, QSizePolicy,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QLocale, QTimer, QByteArray
from PyQt6.QtGui import QCloseEvent, QFont

from catalogs import CableCatalog, OriginalAdtCatalog
from solver.pattern_synthesis import (
    compute_hrp_cut_directivity_db,
    compute_vrp_cut_directivity_db,
    extract_hrp_cut,
    extract_vrp_cut,
    get_vrp_beam_tilt_deg,
)

# Import widget components
from widgets.design_info import DesignInfoWidget
from widgets.pattern_library import PatternLibraryWidget
from widgets.site_details import SiteDetailsWidget
from widgets.antenna_design import AntennaDesignWidget
from widgets.tower_layout import TowerLayoutWidget
from widgets.compensation import CompensationWidget
from widgets.radiation_plots import (
    HrpPlotWidget,
    VrpPlotWidget,
    display_to_internal_azimuth,
    internal_to_display_azimuth,
)
from widgets.result_summary import ResultSummaryWidget
from widgets.save_patterns import SavePatternsSettings, SavePatternsWidget
from widgets.message_list import MessageListWidget
from widgets.beam_shape import BeamShapeWidget
from widgets.pattern_animation_dialog import (
    PatternAnimationDialog,
    PatternAnimationSettings,
)
from widgets.splitter_utils import enable_free_resize


def _parse_float_text(value, default):
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


class ADTMainWindow(QMainWindow):
    CURRENT_LAYOUT_VERSION = 7

    def __init__(self):
        super().__init__()
        QLocale.setDefault(QLocale.c())
        self.setWindowTitle("Antenna Design Tool (ADT) - Python Version")
        self.resize(1700, 980)
        self.layout_file_path = Path(__file__).resolve().with_name(".adt_py_layout.json")
        self.last_project = None
        self.last_mag_3d = None
        self.last_az_angles = None
        self.last_el_angles = None
        self.last_metrics = None
        self.selected_hrp_elevation_deg = None
        self.selected_vrp_azimuth_deg = None
        self.lock_hrp_elevation = False
        self.lock_vrp_azimuth = False
        self.total_rotation_angle = 0.0
        self.total_tilt_actions = []
        self.animation_delay_index = 2
        self.animation_vrp_start_angle = 0
        self.animation_vrp_stop_angle = 359
        self.animation_hrp_start_angle = -90.0
        self.animation_hrp_stop_angle = 90.0
        self.scan_hrp_during_vrp_animation = True
        self.scan_vrp_during_hrp_animation = True
        self.animation_state = None
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._advance_pattern_animation_frame)
        try:
            self.original_adt_catalog = OriginalAdtCatalog()
        except Exception:
            self.original_adt_catalog = None
        try:
            self.cable_catalog = CableCatalog()
        except Exception:
            self.cable_catalog = None

        self._apply_visual_style()
        self.init_menu()
        self.init_ui()
        self.init_catalog_bindings()
        self.refresh_predefined_panel_catalog()
        self.refresh_beam_shape_frequency()
        self._sync_design_panel_count_from_array()
        self.refresh_tower_layout_preview()
        QTimer.singleShot(0, self._restore_saved_layout_or_defaults)

    def _apply_visual_style(self):
        app = QApplication.instance()
        if app is not None:
            font = QFont("Segoe UI")
            font.setPointSizeF(8.5)
            app.setFont(font)
            app.setStyleSheet(
                """
                QMainWindow, QWidget {
                    color: #000000;
                    font-size: 8.5pt;
                }
                QMenuBar {
                    background: #f0f0f0;
                    border-bottom: 1px solid #ababab;
                }
                QMenuBar::item {
                    padding: 2px 7px;
                    background: transparent;
                }
                QMenuBar::item:selected {
                    background: #dbe6f5;
                }
                QMenu {
                    background: #ffffff;
                    border: 1px solid #b8b8b8;
                }
                QMenu::item:selected {
                    background: #dbe6f5;
                }
                QDockWidget::title {
                    background: #d6d6d6;
                    border: 1px solid #a7a7a7;
                    padding: 2px 6px;
                    font-weight: 600;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #afafaf;
                    background: #f7f7f7;
                    top: -1px;
                }
                QTabBar::tab {
                    background: #ededed;
                    border: 1px solid #afafaf;
                    padding: 3px 8px;
                    min-width: 76px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                }
                QGroupBox {
                    font-weight: 600;
                }
                QHeaderView::section {
                    background: #efefef;
                    color: #000000;
                    border: 1px solid #b6b6b6;
                    padding: 2px 4px;
                }
                QTableWidget, QTableView, QLineEdit, QAbstractSpinBox, QComboBox {
                    background: #ffffff;
                    color: #000000;
                    border: 1px solid #afafaf;
                    selection-background-color: #dbeafe;
                    selection-color: #000000;
                }
                QTableWidget::item, QTableView::item {
                    padding: 1px 3px;
                }
                QLineEdit, QAbstractSpinBox, QComboBox {
                    min-height: 20px;
                    padding: 1px 4px;
                }
                QLabel {
                    color: #000000;
                }
                QSplitter::handle {
                    background: #b0b0b0;
                    border: 1px solid #7e7e7e;
                }
                QSplitter::handle:hover {
                    background: #5f8fcf;
                }
                QSplitter::handle:horizontal {
                    width: 10px;
                    margin: 0 1px;
                }
                QSplitter::handle:vertical {
                    height: 10px;
                    margin: 1px 0;
                }
                QMainWindow::separator {
                    background: #b0b0b0;
                    width: 10px;
                    height: 10px;
                    border: 1px solid #7e7e7e;
                }
                QMainWindow::separator:hover {
                    background: #5f8fcf;
                }
                """
            )
        
    def init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        view_menu = menubar.addMenu("View")
        plot_menu = menubar.addMenu("Plot")
        setup_menu = menubar.addMenu("Setup")
        action_menu = menubar.addMenu("Action")
        memory_menu = menubar.addMenu("Memory")
        spec_menu = menubar.addMenu("Spec")
        util_menu = menubar.addMenu("Utilities")
        help_menu = menubar.addMenu("Help")
        
        # --- FILE MENU ---
        from PyQt6.QtGui import QAction
        
        act_open_proj = QAction("Open Project.ant", self)
        act_save_proj = QAction("Save Project.ant", self)
        act_save_proj_as = QAction("Save Project.ant As", self)
        
        save_pat_menu = file_menu.addMenu("Save Displayed Pattern as EFTX PAT Format")
        act_save_hrp_pat = QAction("HRP", self)
        act_save_vrp_pat = QAction("VRP", self)
        save_pat_menu.addAction(act_save_hrp_pat)
        save_pat_menu.addAction(act_save_vrp_pat)

        save_txt_menu = file_menu.addMenu("Save Displayed Pattern as Text Format")
        act_save_hrp_txt = QAction("HRP", self)
        act_save_vrp_txt = QAction("VRP", self)
        save_txt_menu.addAction(act_save_hrp_txt)
        save_txt_menu.addAction(act_save_vrp_txt)

        save_csv_menu = file_menu.addMenu("Save Displayed Pattern as CSV Format")
        act_save_hrp_csv = QAction("HRP", self)
        act_save_vrp_csv = QAction("VRP", self)
        save_csv_menu.addAction(act_save_hrp_csv)
        save_csv_menu.addAction(act_save_vrp_csv)

        save_vsoft_menu = file_menu.addMenu("Save Displayed Pattern as V-Soft Format")
        act_save_hrp_vsoft = QAction("HRP", self)
        act_save_vrp_vsoft = QAction("VRP", self)
        save_vsoft_menu.addAction(act_save_hrp_vsoft)
        save_vsoft_menu.addAction(act_save_vrp_vsoft)

        save_atdi_menu = file_menu.addMenu("Save Pattern as ATDI Format")
        act_save_hrp_atdi = QAction("HRP", self)
        act_save_vrp_atdi = QAction("VRP", self)
        act_save_3d_atdi = QAction("3D", self)
        save_atdi_menu.addAction(act_save_hrp_atdi)
        save_atdi_menu.addAction(act_save_vrp_atdi)
        save_atdi_menu.addAction(act_save_3d_atdi)
        act_save_3d_txt = QAction("Save 3D Pattern as Text Format (1° Az, 0.1° El)", self)
        act_save_3d_ngw = QAction("Save 3D Pattern as NGW3D Format (1° Az, 0.1° El)", self)
        act_save_3d_prn = QAction("Save 3D Pattern as PRN Format (1° Az, 1° El)", self)
        act_save_edx = QAction("Save Pattern as Progira / EDX Format", self)
        act_save_complex_edx = QAction("Save Pattern as Complex Progira / EDX Format", self)
        act_save_directivity = QAction("Save Directivity File", self)
        act_save_anim_video = QAction("Save VRP Animation as Video (.avi)", self)
        act_exit = QAction("Exit", self)
        
        file_menu.addAction(act_open_proj)
        file_menu.addAction(act_save_proj)
        file_menu.addAction(act_save_proj_as)
        file_menu.addSeparator()
        file_menu.addAction(act_save_3d_txt)
        file_menu.addAction(act_save_3d_ngw)
        file_menu.addAction(act_save_3d_prn)
        file_menu.addAction(act_save_edx)
        file_menu.addAction(act_save_complex_edx)
        file_menu.addAction(act_save_directivity)
        file_menu.addAction(act_save_anim_video)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        # Wire Exit
        act_exit.triggered.connect(self.close)
        
        # --- VIEW MENU ---
        act_view_design_info = QAction("Design Information", self)
        act_view_site_details = QAction("Site Details", self)
        act_view_save_patterns = QAction("Save Patterns", self)
        act_view_antenna_details = QAction("Antenna Design Details", self)
        act_view_tower_layout = QAction("Tower and Panel Layout", self)
        act_view_imp_comp = QAction("Impedance Compensation / Array Impedance", self)
        act_view_result_summary = QAction("Result Summary", self)
        act_view_memory_trace = QAction("Memory Trace", self)
        act_view_vrp_ii = QAction("Vertical Radiation Pattern II", self)
        act_view_blackspot = QAction("Blackspot Viewer", self)
        act_view_exposure = QAction("Power Density Calculation and Human Exposure Level Analysis", self)
        act_view_save_layout = QAction("Save Layout", self)
        
        view_menu.addAction(act_view_design_info)
        view_menu.addAction(act_view_site_details)
        view_menu.addAction(act_view_save_patterns)
        view_menu.addAction(act_view_antenna_details)
        view_menu.addAction(act_view_tower_layout)
        view_menu.addAction(act_view_imp_comp)
        view_menu.addAction(act_view_result_summary)
        view_menu.addAction(act_view_memory_trace)
        view_menu.addAction(act_view_vrp_ii)
        view_menu.addAction(act_view_blackspot)
        view_menu.addAction(act_view_exposure)
        view_menu.addSeparator()
        view_menu.addAction(act_view_save_layout)
        
        # Wire View actions to lambda functions targeting the tabs/docks
        # Note: the lambda uses a trick passing `self` to avoid late-binding issues, though not strictly necessary here
        act_view_design_info.triggered.connect(lambda: self._focus_tab(self.left_tabs, 0))
        act_view_site_details.triggered.connect(lambda: self._focus_tab(self.left_tabs, 1))
        act_view_save_patterns.triggered.connect(lambda: self._focus_tab(self.left_tabs, 2))
        
        act_view_antenna_details.triggered.connect(lambda: self._focus_tab(self.central_tabs, 0))
        act_view_tower_layout.triggered.connect(lambda: self._focus_tab(self.central_tabs, 1))
        act_view_imp_comp.triggered.connect(lambda: self._focus_tab(self.central_tabs, 2))
        
        act_view_result_summary.triggered.connect(lambda: self._focus_tab(self.right_bottom_tabs, 0))
        
        act_view_memory_trace.triggered.connect(lambda: self._focus_tab(self.right_bottom_tabs, 2))
        act_view_save_layout.triggered.connect(self.on_view_save_layout)
        
        # --- PLOT MENU ---
        act_plot_save_hrp_jpg = QAction("Save Displayed HRP to File (jpg)", self)
        act_plot_save_vrp_jpg = QAction("Save Displayed VRP to File (jpg)", self)
        act_plot_save_layout_jpg = QAction("Save Layout to File (jpg)", self)
        act_plot_save_hrp_pdf = QAction("Save Displayed HRP to File (pdf)", self)
        act_plot_save_vrp_pdf = QAction("Save Displayed VRP to File (pdf)", self)
        act_plot_save_summary_pdf = QAction("Save Result Summary to File (pdf)", self)
        act_plot_save_panel_pdf = QAction("Save Panel Positions and Electrical Data to File (pdf)", self)
        act_plot_save_all_pdf = QAction("Save All to File (pdf)", self)
        
        plot_save_pattern_menu = plot_menu.addMenu("Save Displayed Pattern to File (jpg)")
        plot_save_pattern_menu.addAction(act_plot_save_hrp_jpg)
        plot_save_pattern_menu.addAction(act_plot_save_vrp_jpg)
        plot_menu.addAction(act_plot_save_hrp_pdf)
        plot_menu.addAction(act_plot_save_vrp_pdf)
        plot_menu.addSeparator()
        plot_menu.addAction(act_plot_save_layout_jpg)
        plot_menu.addAction(act_plot_save_summary_pdf)
        plot_menu.addAction(act_plot_save_panel_pdf)
        plot_menu.addSeparator()
        plot_menu.addAction(act_plot_save_all_pdf)
        
        # --- SETUP MENU ---
        act_setup_coords_polar = QAction("Polar", self)
        act_setup_coords_cart = QAction("Cartesian", self)
        setup_coords_menu = setup_menu.addMenu("Co-ordinates")
        setup_coords_menu.addAction(act_setup_coords_polar)
        setup_coords_menu.addAction(act_setup_coords_cart)
        
        setup_menu.addSeparator()
        act_setup_feed = QAction("Add / Edit Feeder", self)
        setup_menu.addAction(act_setup_feed)
        
        # --- ACTION MENU ---
        act_action_calc_3d = QAction("Calculate 3D Pattern (1 deg Az, 0.1 deg El)", self)
        act_action_anim_vrp = QAction("Animate VRP", self)
        act_action_anim_hrp = QAction("Animate HRP", self)
        act_action_hpat = QAction("Launch HPAT", self)
        act_action_vpat = QAction("Launch VPAT", self)
        act_action_calc_3d.setShortcut("F6")
        act_action_anim_vrp.setShortcut("F7")
        act_action_anim_hrp.setShortcut("F8")
        self.act_action_calc_3d = act_action_calc_3d
        self.act_action_anim_vrp = act_action_anim_vrp
        self.act_action_anim_hrp = act_action_anim_hrp
        action_menu.addAction(act_action_calc_3d)
        action_menu.addAction(act_action_anim_vrp)
        action_menu.addAction(act_action_anim_hrp)
        action_menu.addSeparator()
        action_menu.addAction(act_action_hpat)
        action_menu.addAction(act_action_vpat)
        
        # Wire Calculate 3D Pattern to our existing physics backend
        act_action_calc_3d.triggered.connect(self.on_calculate_clicked)
        
        # --- MEMORY MENU ---
        act_mem_save_both = QAction("Save Both HRP and VRP to Memory", self)
        act_mem_save_active = QAction("Save Active Trace to Memory", self)
        act_mem_recall = QAction("Recall Selected Memory Design", self)
        act_mem_clear = QAction("Clear All Memory Traces", self)
        memory_menu.addAction(act_mem_save_both)
        memory_menu.addAction(act_mem_save_active)
        memory_menu.addAction(act_mem_recall)
        memory_menu.addSeparator()
        memory_menu.addAction(act_mem_clear)
        
        # --- SPEC MENU ---
        act_spec_create_hrp = QAction("Create HRP Spec .spc File", self)
        act_spec_load_hrp = QAction("Load HRP Spec .spc File", self)
        act_spec_set_hrp = QAction("Set Current HRP as Spec", self)
        act_spec_clear_hrp = QAction("Clear HRP Spec", self)
        spec_menu.addAction(act_spec_create_hrp)
        spec_menu.addAction(act_spec_load_hrp)
        spec_menu.addAction(act_spec_set_hrp)
        spec_menu.addAction(act_spec_clear_hrp)
        spec_menu.addSeparator()
        act_spec_def_vrp = QAction("Define VRP Spec", self)
        act_spec_set_vrp = QAction("Set Current VRP as Spec", self)
        act_spec_clear_vrp = QAction("Clear VRP Spec", self)
        spec_menu.addAction(act_spec_def_vrp)
        spec_menu.addAction(act_spec_set_vrp)
        spec_menu.addAction(act_spec_clear_vrp)
        
        # --- UTILITIES MENU ---
        act_util_beam = QAction("Beam Shape", self)
        act_util_blackspot = QAction("Blackspot Viewer", self)
        act_util_geom = QAction("Geometry Builder", self)
        act_util_dist = QAction("Distance and Bearing", self)
        act_util_pd = QAction("PD Network and Cable Set", self)
        act_util_exposure = QAction("Field Strength Exposure", self)
        util_menu.addAction(act_util_beam)
        util_menu.addAction(act_util_blackspot)
        util_menu.addAction(act_util_geom)
        util_menu.addAction(act_util_dist)
        util_menu.addAction(act_util_exposure)
        util_menu.addAction(act_util_pd)
        
        # --- HELP MENU ---
        act_help_about = QAction("About ADT", self)
        act_help_update = QAction("Check the Latest Version", self)
        help_menu.addAction(act_help_about)
        help_menu.addAction(act_help_update)
            
        # --- CONNECT MENU ACTIONS ---
        act_open_proj.triggered.connect(self.on_file_open)
        act_save_proj.triggered.connect(self.on_file_save)
        act_save_proj_as.triggered.connect(self.on_file_save)
        
        act_save_hrp_pat.triggered.connect(lambda: self.on_export_file("HRP PAT"))
        act_save_vrp_pat.triggered.connect(lambda: self.on_export_file("VRP PAT"))
        act_save_hrp_txt.triggered.connect(lambda: self.on_export_file("HRP Text"))
        act_save_vrp_txt.triggered.connect(lambda: self.on_export_file("VRP Text"))
        act_save_hrp_csv.triggered.connect(lambda: self.on_export_file("HRP CSV"))
        act_save_vrp_csv.triggered.connect(lambda: self.on_export_file("VRP CSV"))
        act_save_hrp_vsoft.triggered.connect(lambda: self.on_export_file("HRP V-Soft"))
        act_save_vrp_vsoft.triggered.connect(lambda: self.on_export_file("VRP V-Soft"))
        act_save_hrp_atdi.triggered.connect(lambda: self.on_export_file("HRP ATDI"))
        act_save_vrp_atdi.triggered.connect(lambda: self.on_export_file("VRP ATDI"))
        act_save_3d_atdi.triggered.connect(lambda: self.on_export_file("3D ATDI"))
        act_save_3d_txt.triggered.connect(lambda: self.on_export_file("3D Text"))
        act_save_3d_ngw.triggered.connect(lambda: self.on_export_file("NGW3D"))
        act_save_3d_prn.triggered.connect(lambda: self.on_export_file("PRN"))
        act_save_edx.triggered.connect(lambda: self.on_export_file("EDX"))
        act_save_complex_edx.triggered.connect(lambda: self.on_export_file("Complex EDX"))
        act_save_directivity.triggered.connect(lambda: self.on_export_file("Directivity"))
        act_save_anim_video.triggered.connect(lambda: self.on_export_file("Video"))
        
        act_plot_save_hrp_jpg.triggered.connect(lambda: self.on_export_file("HRP JPEG"))
        act_plot_save_vrp_jpg.triggered.connect(lambda: self.on_export_file("VRP JPEG"))
        act_plot_save_layout_jpg.triggered.connect(lambda: self.on_export_file("Layout JPEG"))
        act_plot_save_hrp_pdf.triggered.connect(lambda: self.on_export_file("HRP PDF"))
        act_plot_save_vrp_pdf.triggered.connect(lambda: self.on_export_file("VRP PDF"))
        act_plot_save_summary_pdf.triggered.connect(lambda: self.on_export_file("Summary PDF"))
        act_plot_save_panel_pdf.triggered.connect(lambda: self.on_export_file("Panel PDF"))
        act_plot_save_all_pdf.triggered.connect(lambda: self.on_export_file("All PDF"))
        
        act_setup_coords_polar.triggered.connect(self.on_not_implemented)
        act_setup_coords_cart.triggered.connect(self.on_not_implemented)
        act_setup_feed.triggered.connect(self.on_not_implemented)
        
        act_action_anim_vrp.triggered.connect(self.on_action_animate_vrp)
        act_action_anim_hrp.triggered.connect(self.on_action_animate_hrp)
        act_action_hpat.triggered.connect(self.on_not_implemented)
        act_action_vpat.triggered.connect(self.on_not_implemented)
        
        act_mem_save_both.triggered.connect(self.on_not_implemented)
        act_mem_save_active.triggered.connect(self.on_not_implemented)
        act_mem_recall.triggered.connect(self.on_not_implemented)
        act_mem_clear.triggered.connect(self.on_not_implemented)
        
        act_spec_create_hrp.triggered.connect(self.on_not_implemented)
        act_spec_load_hrp.triggered.connect(self.on_not_implemented)
        act_spec_set_hrp.triggered.connect(self.on_not_implemented)
        act_spec_clear_hrp.triggered.connect(self.on_not_implemented)
        act_spec_def_vrp.triggered.connect(self.on_not_implemented)
        act_spec_set_vrp.triggered.connect(self.on_not_implemented)
        act_spec_clear_vrp.triggered.connect(self.on_not_implemented)
        
        act_util_beam.triggered.connect(lambda: self._focus_tab(self.right_bottom_tabs, 1))
        act_util_blackspot.triggered.connect(self.on_util_blackspot)
        act_util_geom.triggered.connect(self.on_not_implemented)
        act_util_dist.triggered.connect(self.on_util_dist)
        act_util_exposure.triggered.connect(self.on_util_exposure)
        act_util_pd.triggered.connect(self.on_not_implemented)
        
        act_help_about.triggered.connect(self.on_not_implemented)
        act_help_update.triggered.connect(self.on_not_implemented)

        self.setStatusBar(QStatusBar(self))
        
    def _focus_tab(self, tab_widget, index):
        tab_widget.setCurrentIndex(index)

    def _create_side_section(self, title, widget):
        section = QWidget()
        section.setMinimumWidth(0)
        section.setMinimumHeight(0)
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title)
        header.setStyleSheet(
            """
            QLabel {
                background: #d6d6d6;
                color: #000000;
                border: 1px solid #a7a7a7;
                border-bottom: none;
                font-weight: 600;
                padding: 2px 6px;
                min-height: 18px;
            }
            """
        )
        layout.addWidget(header)
        widget.setMinimumWidth(0)
        widget.setMinimumHeight(0)
        layout.addWidget(widget, 1)
        section.section_header = header
        return section

    def init_ui(self):
        self.setDockNestingEnabled(False)
        central_splitter = QSplitter(Qt.Orientation.Vertical)
        central_splitter.setHandleWidth(8)
        self.central_splitter = central_splitter

        # Central Top Tabs
        self.central_tabs = QTabWidget()
        self._configure_tab_widget(self.central_tabs)
        self.central_tabs.setMinimumWidth(0)
        self.central_tabs.setMinimumHeight(0)
        self.antenna_design_tab = AntennaDesignWidget()
        self.central_tabs.addTab(self.antenna_design_tab, "Antenna Design Details")
        self.tower_layout_tab = TowerLayoutWidget()
        self.central_tabs.addTab(self.tower_layout_tab, "Tower and Panel Layout")
        self.compensation_tab = CompensationWidget()
        self.central_tabs.addTab(self.compensation_tab, "Imp Compensation / Array Imp")
        central_splitter.addWidget(self.central_tabs)

        # Central Bottom Plots (Horizontal Split)
        plots_splitter = QSplitter(Qt.Orientation.Horizontal)
        plots_splitter.setHandleWidth(8)
        self.plots_splitter = plots_splitter

        self.hrp_widget = HrpPlotWidget()
        # Mocking a group box look for the plots to match ADT
        from PyQt6.QtWidgets import QGroupBox
        hrp_group = QGroupBox("Horizontal Radiation Pattern")
        hl1 = QVBoxLayout(hrp_group)
        hl1.setContentsMargins(6, 10, 6, 6)
        hl1.addWidget(self.hrp_widget)
        plots_splitter.addWidget(hrp_group)

        self.vrp_widget = VrpPlotWidget()
        vrp_group = QGroupBox("Vertical Radiation Pattern")
        hl2 = QVBoxLayout(vrp_group)
        hl2.setContentsMargins(6, 10, 6, 6)
        hl2.addWidget(self.vrp_widget)
        plots_splitter.addWidget(vrp_group)

        plots_splitter.setSizes([700, 700])
        plots_splitter.setStretchFactor(0, 1)
        plots_splitter.setStretchFactor(1, 1)
        enable_free_resize(plots_splitter)
        central_splitter.addWidget(plots_splitter)
        central_splitter.setSizes([560, 340])
        central_splitter.setStretchFactor(0, 5)
        central_splitter.setStretchFactor(1, 3)
        enable_free_resize(central_splitter)

        # --- LEFT COLUMN ---
        self.left_tabs = QTabWidget()
        self._configure_tab_widget(self.left_tabs)
        self.left_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.left_tabs.setMinimumWidth(0)
        self.left_tabs.setMinimumHeight(0)
        self.design_info_widget = DesignInfoWidget()
        self.site_details_widget = SiteDetailsWidget(self.cable_catalog)
        self.save_patterns_widget = SavePatternsWidget()
        self.left_tabs.addTab(self.design_info_widget, "Design Information")
        self.left_tabs.addTab(self.site_details_widget, "Site Details")
        self.left_tabs.addTab(self.save_patterns_widget, "Save Patterns")
        self.pattern_library_widget = PatternLibraryWidget()

        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(0)
        self.left_column_splitter = QSplitter(Qt.Orientation.Vertical)
        self.left_column_splitter.setHandleWidth(10)
        self.left_top_section = self._create_side_section("Design Information", self.left_tabs)
        self.left_library_section = self._create_side_section("Pattern Library", self.pattern_library_widget)
        self.left_column_splitter.addWidget(self.left_top_section)
        self.left_column_splitter.addWidget(self.left_library_section)
        enable_free_resize(self.left_column_splitter)
        left_column_layout.addWidget(self.left_column_splitter)
        left_column_widget.setMinimumWidth(0)

        # --- RIGHT COLUMN (Top: Result Summary / Beam Shape / Memory / Distance, Bottom: Message List) ---
        self.result_summary_widget = ResultSummaryWidget()
        self.result_summary_widget.setMinimumWidth(0)
        self.result_summary_widget.setMinimumHeight(0)
        self.result_summary_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Ignored,
        )
        self.right_bottom_tabs = QTabWidget()
        self._configure_tab_widget(self.right_bottom_tabs)
        self.right_bottom_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.right_bottom_tabs.setMinimumWidth(0)
        self.right_bottom_tabs.setMinimumHeight(0)
        self.beam_shape_widget = BeamShapeWidget()
        self.right_bottom_tabs.addTab(self.result_summary_widget, "Result Su...")
        self.right_bottom_tabs.addTab(self.beam_shape_widget, "Beam Sh...")
        self.right_bottom_tabs.addTab(QWidget(), "Memory...")
        self.right_bottom_tabs.addTab(QWidget(), "Distance...")
        self.right_bottom_tabs.currentChanged.connect(self._sync_right_pane_title)
        self.message_list_widget = MessageListWidget()
        self.message_list_widget.setMinimumWidth(0)
        self.message_list_widget.setMinimumHeight(0)
        self.message_list_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Ignored,
        )
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(0)
        self.right_column_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_column_splitter.setHandleWidth(10)
        self.right_top_section = self._create_side_section("Result Summary", self.right_bottom_tabs)
        self.right_message_section = self._create_side_section("Message List", self.message_list_widget)
        self.right_column_splitter.addWidget(self.right_top_section)
        self.right_column_splitter.addWidget(self.right_message_section)
        enable_free_resize(self.right_column_splitter)
        right_column_layout.addWidget(self.right_column_splitter)
        right_column_widget.setMinimumWidth(0)

        # --- ROOT HORIZONTAL SPLITTER (Left / Center / Right) ---
        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_horizontal_splitter.setHandleWidth(12)
        self.main_horizontal_splitter.setStyleSheet(
            """
            QSplitter::handle {
                background: #b0b0b0;
                border-left: 1px solid #7e7e7e;
                border-right: 1px solid #e4e4e4;
            }
            QSplitter::handle:hover {
                background: #5f8fcf;
            }
            """
        )
        self.main_horizontal_splitter.addWidget(left_column_widget)
        self.main_horizontal_splitter.addWidget(central_splitter)
        self.main_horizontal_splitter.addWidget(right_column_widget)
        self.main_horizontal_splitter.setStretchFactor(0, 0)
        self.main_horizontal_splitter.setStretchFactor(1, 1)
        self.main_horizontal_splitter.setStretchFactor(2, 0)
        enable_free_resize(self.main_horizontal_splitter)
        root_layout.addWidget(self.main_horizontal_splitter)
        self.setCentralWidget(root_widget)

        # Compatibility aliases for existing logic
        self.dock_left_top = self.left_top_section
        self.dock_pattern_lib = self.left_library_section
        self.dock_result_summary = self.right_top_section
        self.dock_point_info = self.result_summary_widget
        self.dock_messages = self.right_message_section
        self._sync_right_pane_title()

        # Wiring logic
        # DesignInfo is now inside a QTabWidget which is inside self.dock_left_top
        self.design_info_widget.calc_btn.clicked.connect(self.on_calculate_clicked)
        self.site_details_widget.values_changed.connect(self._on_site_details_changed)
        self.site_details_widget.feeder_loss_changed.connect(
            lambda _value: self._sync_site_details_to_design_info()
        )
        self.site_details_widget.error_generated.connect(
            lambda message: self._add_message(f"Site details: {message}")
        )
        self.save_patterns_widget.save_requested.connect(self.on_save_patterns_requested)
        self.save_patterns_widget.error_requested.connect(self.on_save_patterns_error)
        self.hrp_widget.elevation_changed.connect(self.on_hrp_elevation_changed)
        self.vrp_widget.azimuth_changed.connect(self.on_vrp_azimuth_changed)
        self.beam_shape_widget.message_generated.connect(self.on_beam_shape_message)
        self.beam_shape_widget.phase_transfer_requested.connect(
            self.on_beam_shape_transfer_requested
        )
        self.tower_layout_tab.rotation_apply_requested.connect(
            self.on_tower_rotation_apply_requested
        )
        self.tower_layout_tab.rotation_reset_requested.connect(
            self.on_tower_rotation_reset_requested
        )
        self.tower_layout_tab.tilt_apply_requested.connect(
            self.on_tower_tilt_apply_requested
        )
        self.tower_layout_tab.tilt_reset_requested.connect(
            self.on_tower_tilt_reset_requested
        )
        self.tower_layout_tab.geometry_generate_requested.connect(
            self.on_tower_geometry_generate_requested
        )
        self.central_tabs.currentChanged.connect(self._on_central_tab_changed)
        self._refresh_site_feeder_loss()
        self._sync_site_details_to_design_info()

    def _apply_legacy_window_proportions(self):
        self.main_horizontal_splitter.setSizes([430, 980, 300])
        self.left_column_splitter.setSizes([530, 310])
        self.right_column_splitter.setSizes([620, 260])
        self.central_splitter.setSizes([620, 280])
        self.plots_splitter.setSizes([1, 1])

    def _sync_right_pane_title(self, *_args):
        titles = [
            "Result Summary",
            "Beam Shape",
            "Memory Trace",
            "Distance and Bearing",
        ]
        index = self.right_bottom_tabs.currentIndex() if hasattr(self, "right_bottom_tabs") else 0
        if hasattr(self, "right_top_section"):
            self.right_top_section.section_header.setText(
                titles[index] if 0 <= index < len(titles) else "Result Summary"
            )

    def _configure_tab_widget(self, tab_widget):
        tab_widget.setUsesScrollButtons(True)
        tab_widget.tabBar().setMovable(False)
        tab_widget.tabBar().setExpanding(False)
        tab_widget.tabBar().setDocumentMode(False)

    def _layout_payload(self):
        return {
            "layout_version": self.CURRENT_LAYOUT_VERSION,
            "geometry": b64encode(bytes(self.saveGeometry())).decode("ascii"),
            "main_horizontal_state": b64encode(bytes(self.main_horizontal_splitter.saveState())).decode("ascii"),
            "left_column_state": b64encode(bytes(self.left_column_splitter.saveState())).decode("ascii"),
            "right_column_state": b64encode(bytes(self.right_column_splitter.saveState())).decode("ascii"),
            "central_state": b64encode(bytes(self.central_splitter.saveState())).decode("ascii"),
            "plots_state": b64encode(bytes(self.plots_splitter.saveState())).decode("ascii"),
            "left_tab_index": self.left_tabs.currentIndex(),
            "central_tab_index": self.central_tabs.currentIndex(),
            "right_bottom_tab_index": self.right_bottom_tabs.currentIndex(),
        }

    def _save_layout_to_disk(self):
        self.layout_file_path.write_text(
            json.dumps(self._layout_payload(), indent=2),
            encoding="utf-8",
        )

    def _restore_saved_layout(self):
        if not self.layout_file_path.exists():
            return False
        try:
            payload = json.loads(self.layout_file_path.read_text(encoding="utf-8"))
            if int(payload.get("layout_version", 0)) != self.CURRENT_LAYOUT_VERSION:
                return False
            geometry_data = payload.get("geometry")
            main_horizontal_state = payload.get("main_horizontal_state")
            left_column_state = payload.get("left_column_state")
            right_column_state = payload.get("right_column_state")
            central_state = payload.get("central_state")
            plots_state = payload.get("plots_state")
            if geometry_data:
                self.restoreGeometry(QByteArray(b64decode(geometry_data)))
            restored = False
            if main_horizontal_state:
                restored = self.main_horizontal_splitter.restoreState(
                    QByteArray(b64decode(main_horizontal_state))
                )
            if left_column_state:
                self.left_column_splitter.restoreState(QByteArray(b64decode(left_column_state)))
            if right_column_state:
                self.right_column_splitter.restoreState(QByteArray(b64decode(right_column_state)))
            if central_state:
                self.central_splitter.restoreState(QByteArray(b64decode(central_state)))
            if plots_state:
                self.plots_splitter.restoreState(QByteArray(b64decode(plots_state)))
            self.left_tabs.setCurrentIndex(int(payload.get("left_tab_index", 0)))
            self.central_tabs.setCurrentIndex(int(payload.get("central_tab_index", 0)))
            self.right_bottom_tabs.setCurrentIndex(int(payload.get("right_bottom_tab_index", 0)))
            return restored or bool(geometry_data)
        except Exception:
            return False

    def _restore_saved_layout_or_defaults(self):
        if not self._restore_saved_layout():
            self._apply_legacy_window_proportions()
        self.showMaximized()

    def on_view_save_layout(self):
        try:
            self._save_layout_to_disk()
            self._add_message("Layout saved.")
            QMessageBox.information(
                self,
                "Save Layout",
                f"Layout saved to\n{self.layout_file_path}",
            )
        except Exception as exc:
            QMessageBox.warning(self, "Save Layout", f"Could not save layout:\n{exc}")

    def closeEvent(self, event: QCloseEvent):
        try:
            self._save_layout_to_disk()
        except Exception:
            pass
        super().closeEvent(event)

    def init_catalog_bindings(self):
        self.design_info_widget.design_freq_input.editingFinished.connect(
            self._on_design_frequency_changed
        )
        self.design_info_widget.channel_freq_input.editingFinished.connect(
            self._on_channel_frequency_changed
        )
        self.design_info_widget.polarisation_combo.currentTextChanged.connect(
            lambda _text: self.refresh_predefined_panel_catalog()
        )

    def _on_design_frequency_changed(self):
        self.refresh_predefined_panel_catalog()
        self.refresh_beam_shape_frequency()

    def _on_channel_frequency_changed(self):
        self.refresh_predefined_panel_catalog()
        self._refresh_site_feeder_loss()

    def _refresh_site_feeder_loss(self):
        if not hasattr(self, "site_details_widget"):
            return
        frequency_mhz = _parse_float_text(
            self.design_info_widget.channel_freq_input.text(),
            539.0,
        )
        self.site_details_widget.set_channel_frequency_mhz(frequency_mhz)
        self._sync_site_details_to_design_info()

    def _sync_site_details_to_design_info(self):
        if not hasattr(self, "site_details_widget") or not hasattr(self, "design_info_widget"):
            return
        self.design_info_widget.internal_loss_input.setText(
            f"{self.site_details_widget.internal_loss_spin.value():g}"
        )
        self.design_info_widget.pol_loss_input.setText(
            f"{self.site_details_widget.polar_loss_spin.value():g}"
        )
        self.design_info_widget.filter_loss_input.setText(
            f"{self.site_details_widget.filter_loss_spin.value():g}"
        )
        self.design_info_widget.feeder_loss_input.setText(
            f"{self.site_details_widget.computed_feeder_loss_db:g}"
        )

    def _on_site_details_changed(self):
        self._sync_site_details_to_design_info()
        self.refresh_tower_layout_preview()

    def _on_central_tab_changed(self, index):
        if self.central_tabs.widget(index) is self.tower_layout_tab:
            self.refresh_tower_layout_preview()

    def refresh_beam_shape_frequency(self):
        frequency_mhz = _parse_float_text(
            self.design_info_widget.design_freq_input.text(),
            539.0,
        )
        self.beam_shape_widget.update_frequency(frequency_mhz)

    def refresh_tower_layout_preview(self):
        if not hasattr(self, "tower_layout_tab"):
            return
        site_values = (
            self.site_details_widget.get_site_values()
            if hasattr(self, "site_details_widget")
            else None
        )
        self.tower_layout_tab.update_preview(
            self.antenna_design_tab.get_array_data(),
            self.pattern_library_widget.get_pattern_configs(),
            site_values=site_values,
        )

    def _sync_design_panel_count_from_array(self):
        if not hasattr(self, "design_info_widget") or not hasattr(self, "antenna_design_tab"):
            return

        panel_count = max(1, len(self.antenna_design_tab.get_array_data()))
        if self.design_info_widget.num_panels_spin.value() == panel_count:
            return

        previous_state = self.design_info_widget.num_panels_spin.blockSignals(True)
        try:
            self.design_info_widget.num_panels_spin.setValue(panel_count)
        finally:
            self.design_info_widget.num_panels_spin.blockSignals(previous_state)

    def _add_message(self, description):
        import datetime

        time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.message_list_widget.add_message(time_str, description)

    def _invalidate_calculation_outputs(self, reason=None):
        self.last_project = None
        self.last_mag_3d = None
        self.last_az_angles = None
        self.last_el_angles = None
        self.last_metrics = None
        self.selected_hrp_elevation_deg = None
        self.selected_vrp_azimuth_deg = None
        self.lock_hrp_elevation = False
        self.lock_vrp_azimuth = False
        self.hrp_widget.clear_plot_display()
        self.hrp_widget.set_selected_azimuth(0.0)
        self.vrp_widget.clear_plot_display()
        self.result_summary_widget.clear_results()
        if reason:
            self._add_message(reason)

    def _refresh_hrp_plot(self, elevation_deg=None):
        if self.last_mag_3d is None or self.last_az_angles is None or self.last_el_angles is None:
            return

        hrp_angles, hrp_cut, hrp_elevation = extract_hrp_cut(
            self.last_mag_3d,
            self.last_az_angles,
            self.last_el_angles,
            elevation_deg=elevation_deg,
        )
        peak_hrp_cut = (
            self.last_metrics.get("_hrp_cut_magnitude")
            if isinstance(self.last_metrics, dict)
            else hrp_cut
        )
        hrp_directivity = compute_hrp_cut_directivity_db(hrp_cut, peak_hrp_cut)
        self.hrp_widget.plot_data(hrp_angles, hrp_cut)
        self.hrp_widget.set_cut_metadata(
            elevation_deg=hrp_elevation,
            directivity_dbd=hrp_directivity,
        )
        if not self.lock_hrp_elevation:
            self.selected_hrp_elevation_deg = hrp_elevation

        selected_azimuth = self.selected_vrp_azimuth_deg
        if selected_azimuth is None and isinstance(self.last_metrics, dict):
            selected_azimuth = self.last_metrics.get("_vrp_cut_azimuth_deg", 0.0)
        self.hrp_widget.set_selected_azimuth(selected_azimuth)

    def _refresh_vrp_plot(self, azimuth_deg=None):
        if self.last_mag_3d is None or self.last_az_angles is None or self.last_el_angles is None:
            return

        vrp_angles, vrp_cut, vrp_azimuth = extract_vrp_cut(
            self.last_mag_3d,
            self.last_az_angles,
            self.last_el_angles,
            azimuth_deg=azimuth_deg,
        )
        peak_vrp_cut = (
            self.last_metrics.get("_vrp_cut_magnitude")
            if isinstance(self.last_metrics, dict)
            else vrp_cut
        )
        vrp_directivity = compute_vrp_cut_directivity_db(
            vrp_angles,
            vrp_cut,
            peak_vrp_cut,
        )
        vrp_tilt_deg = get_vrp_beam_tilt_deg(vrp_angles, vrp_cut)
        self.vrp_widget.plot_data(vrp_angles, vrp_cut)
        self.vrp_widget.set_cut_metadata(
            azimuth_deg=vrp_azimuth,
            directivity_dbd=vrp_directivity,
            tilt_deg=vrp_tilt_deg,
        )
        if not self.lock_vrp_azimuth:
            self.selected_vrp_azimuth_deg = vrp_azimuth
        self.hrp_widget.set_selected_azimuth(vrp_azimuth)

    def _current_displayed_elevation(self):
        if self.selected_hrp_elevation_deg is not None:
            return float(self.selected_hrp_elevation_deg)
        if isinstance(self.last_metrics, dict):
            return float(self.last_metrics.get("_hrp_cut_elevation_deg", 0.0))
        return 0.0

    def _current_displayed_azimuth(self):
        if self.selected_vrp_azimuth_deg is not None:
            return float(self.selected_vrp_azimuth_deg)
        if isinstance(self.last_metrics, dict):
            return float(self.last_metrics.get("_vrp_cut_azimuth_deg", 0.0))
        return 0.0

    def _update_point_info_from_current_cuts(self):
        if self.last_mag_3d is None or self.last_az_angles is None or self.last_el_angles is None:
            self.result_summary_widget.set_point_info("", "", "", "")
            return

        azimuth_deg = self._current_displayed_azimuth()
        elevation_deg = self._current_displayed_elevation()
        azimuth_angles = self.last_az_angles
        elevation_angles = self.last_el_angles

        azimuth_index = int(np.argmin(np.abs(azimuth_angles - azimuth_deg)))
        elevation_index = int(np.argmin(np.abs(elevation_angles - elevation_deg)))

        actual_azimuth_deg = float(azimuth_angles[azimuth_index])
        actual_elevation_deg = float(elevation_angles[elevation_index])
        relative_field = float(self.last_mag_3d[azimuth_index, elevation_index])
        power_from_peak_db = 20.0 * np.log10(max(relative_field, 1e-12))

        self.result_summary_widget.set_point_info(
            f"{internal_to_display_azimuth(actual_azimuth_deg):.0f}",
            f"{actual_elevation_deg:.1f}",
            f"{relative_field:.4f}",
            f"{power_from_peak_db:.2f}",
        )

    def _refresh_displayed_pattern_cuts(self, elevation_deg=None, azimuth_deg=None):
        current_elevation = (
            self._current_displayed_elevation() if elevation_deg is None else float(elevation_deg)
        )
        current_azimuth = (
            self._current_displayed_azimuth() if azimuth_deg is None else float(azimuth_deg)
        )

        self._refresh_hrp_plot(current_elevation)
        self._refresh_vrp_plot(current_azimuth)
        self.vrp_widget.set_selected_elevation(float(self.hrp_widget.angle_spin.value()))
        self._update_point_info_from_current_cuts()

    def on_hrp_elevation_changed(self, elevation_deg):
        self.selected_hrp_elevation_deg = float(elevation_deg)
        self.lock_hrp_elevation = True
        self._refresh_displayed_pattern_cuts(elevation_deg=elevation_deg)

    def on_vrp_azimuth_changed(self, azimuth_deg):
        internal_azimuth_deg = display_to_internal_azimuth(azimuth_deg)
        self.selected_vrp_azimuth_deg = float(internal_azimuth_deg)
        self.lock_vrp_azimuth = True
        self._refresh_displayed_pattern_cuts(azimuth_deg=internal_azimuth_deg)

    def on_beam_shape_message(self, message):
        self._add_message(message)

    def on_beam_shape_transfer_requested(self, phases, decimal_places):
        self.antenna_design_tab.update_v_group_phases(phases, decimal_places)
        self._invalidate_calculation_outputs(
            "Vertical Group Phi updated from Beam Shape. HRP/VRP cleared; run Calculate 3D Pattern to refresh the diagrams."
        )

    def on_tower_rotation_apply_requested(self, rotation_deg):
        self.total_rotation_angle += float(rotation_deg)
        self.antenna_design_tab.rotate_array(float(rotation_deg))
        self.refresh_tower_layout_preview()
        self._invalidate_calculation_outputs(
            f"Tower layout rotation of {float(rotation_deg):0.1f}° applied to the array."
        )

    def on_tower_rotation_reset_requested(self):
        if abs(self.total_rotation_angle) > 1e-9:
            self.antenna_design_tab.rotate_array(-self.total_rotation_angle)
            self.total_rotation_angle = 0.0
        self.tower_layout_tab.reset_rotation_to_zero()
        self.refresh_tower_layout_preview()
        self._invalidate_calculation_outputs(
            "Tower layout rotation reset to zero."
        )

    def on_tower_tilt_apply_requested(self, tilt_deg, direction_deg):
        tilt_value = float(tilt_deg)
        direction_value = float(direction_deg)
        self.total_tilt_actions.append((tilt_value, direction_value))
        self.antenna_design_tab.mech_tilt_array(tilt_value, direction_value)
        self.refresh_tower_layout_preview()
        self._invalidate_calculation_outputs(
            f"Mechanical tilt of {tilt_value:0.1f}° at {direction_value:0.1f}° applied to the array."
        )

    def on_tower_tilt_reset_requested(self):
        for tilt_deg, direction_deg in reversed(self.total_tilt_actions):
            self.antenna_design_tab.mech_tilt_array(-tilt_deg, direction_deg)
        self.total_tilt_actions.clear()
        self.tower_layout_tab.reset_tilt_to_zero()
        self.refresh_tower_layout_preview()
        self._invalidate_calculation_outputs(
            "Mechanical tilt reset to zero."
        )

    def on_tower_geometry_generate_requested(
        self,
        face_count,
        offset_m,
        heading_deg,
        level_count,
        spacing_m,
        cogged,
    ):
        self.total_rotation_angle = 0.0
        self.total_tilt_actions.clear()
        self.antenna_design_tab.build_geometry(
            int(face_count),
            float(offset_m),
            float(heading_deg),
            int(level_count),
            float(spacing_m),
            bool(cogged),
        )
        self._sync_design_panel_count_from_array()
        self.refresh_tower_layout_preview()
        self._invalidate_calculation_outputs(
            "Tower geometry regenerated and applied to Array Data."
        )

    def _get_catalog_frequency_mhz(self):
        for value in (
            self.design_info_widget.channel_freq_input.text(),
            self.design_info_widget.design_freq_input.text(),
        ):
            parsed = _parse_float_text(value, None)
            if parsed is not None:
                return parsed
        return 539.0

    def refresh_predefined_panel_catalog(self):
        if self.original_adt_catalog is None:
            return

        try:
            frequency_mhz = self._get_catalog_frequency_mhz()
            polarization = self.design_info_widget.polarisation_combo.currentText()
            entries = self.original_adt_catalog.get_standard_panel_entries(
                frequency_mhz,
                polarization,
            )
            self.pattern_library_widget.set_predefined_panel_options(entries)
            if hasattr(self, "tower_layout_tab"):
                self.refresh_tower_layout_preview()
        except Exception as error:
            if hasattr(self, "message_list_widget"):
                import datetime

                time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
                self.message_list_widget.add_message(
                    time_str,
                    f"Catalog refresh failed: {error}",
                )

    def on_calculate_clicked(self):
        from app.project_service import build_project_from_ui, calculate_project_metrics
        
        try:
            project = build_project_from_ui(
                self.design_info_widget,
                self.site_details_widget,
                self.antenna_design_tab,
                self.pattern_library_widget,
            )
            metrics, mag_3d, az_angles, el_angles = calculate_project_metrics(project)

            self.last_project = project
            self.last_mag_3d = mag_3d
            self.last_az_angles = az_angles
            self.last_el_angles = el_angles
            self.last_metrics = metrics
            
            self.result_summary_widget.update_results(metrics)
            hrp_elevation = (
                self.selected_hrp_elevation_deg
                if self.lock_hrp_elevation and self.selected_hrp_elevation_deg is not None
                else metrics.get("_hrp_cut_elevation_deg")
            )
            vrp_azimuth = (
                self.selected_vrp_azimuth_deg
                if self.lock_vrp_azimuth and self.selected_vrp_azimuth_deg is not None
                else metrics.get("_vrp_cut_azimuth_deg")
            )
            self._refresh_displayed_pattern_cuts(hrp_elevation, vrp_azimuth)
            self.refresh_tower_layout_preview()
            self._add_message(
                "Calculated 3D pattern and refreshed HRP/VRP displays from the 3D field."
            )
        
        except Exception as e:
            self._add_message(f"Error calculating pattern: {str(e)}")

    def _animation_delay_ms(self, delay_index: int) -> int:
        return {
            0: 10,
            1: 20,
            2: 40,
            3: 60,
            4: 80,
        }.get(int(delay_index), 40)

    def _animation_frame_step(self, axis: str) -> float:
        return 1.0 if axis == "vrp" else 0.1

    def _open_pattern_animation_dialog(self, axis: str) -> PatternAnimationSettings | None:
        if axis == "vrp":
            defaults = PatternAnimationSettings(
                axis="vrp",
                start_angle=float(self.animation_vrp_start_angle),
                stop_angle=float(self.animation_vrp_stop_angle),
                delay_index=int(self.animation_delay_index),
                scan_peer=bool(self.scan_hrp_during_vrp_animation),
            )
        else:
            defaults = PatternAnimationSettings(
                axis="hrp",
                start_angle=float(self.animation_hrp_start_angle),
                stop_angle=float(self.animation_hrp_stop_angle),
                delay_index=int(self.animation_delay_index),
                scan_peer=bool(self.scan_vrp_during_hrp_animation),
            )

        dialog = PatternAnimationDialog(defaults, self)
        if dialog.exec():
            return dialog.get_settings()
        return None

    def _start_pattern_animation(
        self,
        axis: str,
        start_angle: float,
        stop_angle: float,
        delay_index: int = 2,
        scan_peer: bool = True,
        *,
        start_timer: bool = True,
    ):
        self._ensure_pattern_ready_for_export()
        axis = str(axis).lower()
        if axis not in {"vrp", "hrp"}:
            raise ValueError("Unknown animation axis")

        start_angle = float(start_angle)
        stop_angle = float(stop_angle)
        if stop_angle < start_angle:
            raise ValueError("Animation stop angle must be greater than or equal to the start angle.")

        self.animation_timer.stop()
        self.animation_state = {
            "axis": axis,
            "start_angle": start_angle,
            "stop_angle": stop_angle,
            "current_angle": start_angle,
            "step": self._animation_frame_step(axis),
            "delay_ms": self._animation_delay_ms(delay_index),
            "scan_peer": bool(scan_peer),
            "original_hrp_elevation_deg": float(self._current_displayed_elevation()),
            "original_vrp_azimuth_deg": float(self._current_displayed_azimuth()),
            "original_lock_hrp_elevation": bool(self.lock_hrp_elevation),
            "original_lock_vrp_azimuth": bool(self.lock_vrp_azimuth),
            "original_hrp_scan_line": bool(self.hrp_widget.show_selected_azimuth_line),
            "original_vrp_scan_line": bool(self.vrp_widget.show_selected_elevation_line),
        }

        if axis == "vrp":
            self.animation_vrp_start_angle = int(round(start_angle))
            self.animation_vrp_stop_angle = int(round(stop_angle))
            self.scan_hrp_during_vrp_animation = bool(scan_peer)
        else:
            self.animation_hrp_start_angle = start_angle
            self.animation_hrp_stop_angle = stop_angle
            self.scan_vrp_during_hrp_animation = bool(scan_peer)
        self.animation_delay_index = int(delay_index)

        if start_timer:
            self.animation_timer.start(self.animation_state["delay_ms"])

    def _apply_animation_frame(self, axis: str, angle_value: float, scan_peer: bool):
        if axis == "vrp":
            internal_azimuth_deg = display_to_internal_azimuth(angle_value)
            self.selected_vrp_azimuth_deg = float(internal_azimuth_deg)
            self.lock_vrp_azimuth = True
            self._refresh_vrp_plot(azimuth_deg=internal_azimuth_deg)
            self.hrp_widget.show_selected_azimuth_line = bool(scan_peer)
            self.hrp_widget.set_selected_azimuth(internal_azimuth_deg)
        else:
            self.selected_hrp_elevation_deg = float(angle_value)
            self.lock_hrp_elevation = True
            self._refresh_hrp_plot(elevation_deg=angle_value)
            self.vrp_widget.show_selected_elevation_line = bool(scan_peer)
            self.vrp_widget.set_selected_elevation(angle_value)

        self._update_point_info_from_current_cuts()

    def _finish_pattern_animation(self):
        if not self.animation_state:
            return

        state = self.animation_state
        axis = state["axis"]
        self.animation_timer.stop()
        self.hrp_widget.show_selected_azimuth_line = state["original_hrp_scan_line"]
        self.vrp_widget.show_selected_elevation_line = state["original_vrp_scan_line"]
        self.lock_hrp_elevation = bool(state["original_lock_hrp_elevation"])
        self.lock_vrp_azimuth = bool(state["original_lock_vrp_azimuth"])
        self.selected_hrp_elevation_deg = float(state["original_hrp_elevation_deg"])
        self.selected_vrp_azimuth_deg = float(state["original_vrp_azimuth_deg"])
        self.animation_state = None
        self._refresh_displayed_pattern_cuts(
            elevation_deg=self.selected_hrp_elevation_deg,
            azimuth_deg=self.selected_vrp_azimuth_deg,
        )
        self._add_message(f"{axis.upper()} animation completed.")

    def _advance_pattern_animation_frame(self):
        if not self.animation_state:
            return

        state = self.animation_state
        current_angle = float(state["current_angle"])
        stop_angle = float(state["stop_angle"])
        step = float(state["step"])
        if current_angle > stop_angle + (step / 2.0):
            self._finish_pattern_animation()
            return

        self._apply_animation_frame(
            state["axis"],
            current_angle,
            bool(state["scan_peer"]),
        )
        state["current_angle"] = round(current_angle + step, 1 if state["axis"] == "hrp" else 0)

    def on_action_animate_vrp(self):
        try:
            settings = self._open_pattern_animation_dialog("vrp")
            if settings is None:
                return
            self._start_pattern_animation(
                settings.axis,
                settings.start_angle,
                settings.stop_angle,
                delay_index=settings.delay_index,
                scan_peer=settings.scan_peer,
            )
            self._add_message("VRP animation started.")
        except Exception as exc:
            QMessageBox.warning(self, "Animate VRP", str(exc))
            self._add_message(f"Animate VRP: {exc}")

    def on_action_animate_hrp(self):
        try:
            settings = self._open_pattern_animation_dialog("hrp")
            if settings is None:
                return
            self._start_pattern_animation(
                settings.axis,
                settings.start_angle,
                settings.stop_angle,
                delay_index=settings.delay_index,
                scan_peer=settings.scan_peer,
            )
            self._add_message("HRP animation started.")
        except Exception as exc:
            QMessageBox.warning(self, "Animate HRP", str(exc))
            self._add_message(f"Animate HRP: {exc}")

    def on_not_implemented(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Not Implemented", "This mechanism is not yet fully ported from the original C# application to Python.\n(Phase 3 task)")

    def on_file_open(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from app.project_service import apply_project_to_ui
        from infra.project_store import load_project

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "ADT_PY Project Files (*.adpy.json *.json);;All Files (*)",
        )
        if path:
            try:
                project = load_project(path)
                apply_project_to_ui(
                    project,
                    self.design_info_widget,
                    self.site_details_widget,
                    self.antenna_design_tab,
                    self.pattern_library_widget,
                )
                self.refresh_predefined_panel_catalog()
                self.refresh_beam_shape_frequency()
                self._refresh_site_feeder_loss()
                self.total_rotation_angle = 0.0
                self.total_tilt_actions.clear()
                self._invalidate_calculation_outputs()
                self.last_project = project
                self._sync_design_panel_count_from_array()
                self.refresh_tower_layout_preview()
                QMessageBox.information(self, "Loaded", f"Loaded project: {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load project: {str(e)}")

    def on_file_save(self):
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from app.project_service import build_project_from_ui
        from infra.project_store import save_project

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "ADT_PY Project Files (*.adpy.json);;JSON Files (*.json);;All Files (*)",
        )
        if path:
            try:
                if Path(path).suffix.lower() != ".json" and not path.endswith(".adpy.json"):
                    path += ".adpy.json"
                project = build_project_from_ui(
                    self.design_info_widget,
                    self.site_details_widget,
                    self.antenna_design_tab,
                    self.pattern_library_widget,
                )
                save_project(path, project)
                self.last_project = project
                QMessageBox.information(self, "Saved", f"Saved project to: {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save project: {str(e)}")

    def on_util_dist(self):
        from widgets.dis_and_bear import DistanceBearingDialog
        dlg = DistanceBearingDialog(self)
        dlg.exec()

    def on_util_exposure(self):
        from widgets.field_strength import FieldStrengthExposureDialog

        tx_pow = _parse_float_text(
            (self.last_metrics or {}).get("Transmitter Power (kW)", 10.0),
            10.0,
        )
        erp = _parse_float_text(
            (self.last_metrics or {}).get("ERP (kW)", tx_pow),
            tx_pow,
        )
        freq = _parse_float_text(
            self.design_info_widget.channel_freq_input.text() or 539.0,
            539.0,
        )
        
        dlg = FieldStrengthExposureDialog(self, frequency=freq, tx_power=tx_pow, erp=erp,
                                          mag_3d=self.last_mag_3d, az_angles=self.last_az_angles, el_angles=self.last_el_angles)
        dlg.exec()

    def on_util_blackspot(self):
        from widgets.black_spot import BlackSpotViewer
        if self.last_mag_3d is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Pattern Data", "Please calculate a 3D pattern before opening the Blackspot Viewer.")
            return
             
        dlg = BlackSpotViewer(self, mag_3d=self.last_mag_3d)
        dlg.exec()

    def _build_export_context(self):
        from app.project_service import build_project_from_ui
        from exports.pattern_exporters import ExportContext

        try:
            project = build_project_from_ui(
                self.design_info_widget,
                self.site_details_widget,
                self.antenna_design_tab,
                self.pattern_library_widget,
            )
        except Exception:
            project = self.last_project

        hrp_elevation = (
            self.selected_hrp_elevation_deg
            if self.lock_hrp_elevation and self.selected_hrp_elevation_deg is not None
            else (self.last_metrics or {}).get("_hrp_cut_elevation_deg")
        )
        vrp_azimuth = (
            self.selected_vrp_azimuth_deg
            if self.lock_vrp_azimuth and self.selected_vrp_azimuth_deg is not None
            else (self.last_metrics or {}).get("_vrp_cut_azimuth_deg")
        )

        return ExportContext(
            project=project,
            metrics=self.last_metrics,
            mag_3d=self.last_mag_3d,
            az_angles=self.last_az_angles,
            el_angles=self.last_el_angles,
            hrp_elevation_deg=hrp_elevation,
            vrp_azimuth_deg=vrp_azimuth,
            normalised_vrp=False,
            design_info_widget=self.design_info_widget,
            antenna_design_widget=self.antenna_design_tab,
            pattern_library_widget=self.pattern_library_widget,
            result_summary_widget=self.result_summary_widget,
            hrp_widget=self.hrp_widget,
            vrp_widget=self.vrp_widget,
            tower_preview_widget=self.tower_layout_tab.preview_widget,
            logo_path=Path(__file__).resolve().with_name("logo.png"),
            rotation_angle_deg=float(self.total_rotation_angle),
        )

    def _add_message(self, description):
        self.message_list_widget.add_message(
            datetime.now().strftime("%H:%M:%S"),
            description,
        )

    def on_save_patterns_error(self, message):
        QMessageBox.warning(self, "Save Patterns", message)
        self._add_message(message)

    def _ensure_pattern_ready_for_export(self):
        if self.last_mag_3d is None or self.last_az_angles is None or self.last_el_angles is None:
            raise ValueError("Please calculate a 3D pattern first.")

    def _validate_export_base_path(self, base_path: str | Path) -> Path:
        candidate = Path(base_path)
        if str(candidate).strip() == "":
            raise ValueError("Invalid file name")
        if candidate.exists() and candidate.is_dir():
            raise ValueError("Invalid file name")
        base_name = self._export_base_name(candidate)
        if base_name.strip(" .") == "":
            raise ValueError("Invalid file name")
        return candidate

    def _export_base_name(self, candidate: Path) -> str:
        base_name = candidate.name
        while True:
            stem = Path(base_name).stem
            suffix = Path(base_name).suffix
            if not suffix:
                return base_name
            base_name = stem

    def _append_selection_formats(self, formats, selection, hrp_format=None, vrp_format=None, d3_format=None):
        if selection == "HRP" and hrp_format:
            formats.append(hrp_format)
        elif selection == "VRP" and vrp_format:
            formats.append(vrp_format)
        elif selection == "HRP & VRP":
            if hrp_format:
                formats.append(hrp_format)
            if vrp_format:
                formats.append(vrp_format)
        elif selection == "3D" and d3_format:
            formats.append(d3_format)

    def _save_patterns_formats(self, settings: SavePatternsSettings):
        formats = []
        if settings.save_jpg:
            self._append_selection_formats(formats, settings.jpg_target, "HRP JPEG", "VRP JPEG")
        if settings.save_tabdata:
            self._append_selection_formats(formats, settings.tabdata_target, "HRP PDF", "VRP PDF")
        if settings.save_pat:
            self._append_selection_formats(formats, settings.pat_target, "HRP PAT", "VRP PAT")
        if settings.save_txt:
            self._append_selection_formats(formats, settings.txt_target, "HRP Text", "VRP Text")
        if settings.save_csv:
            self._append_selection_formats(formats, settings.csv_target, "HRP CSV", "VRP CSV")
        if settings.save_vsoft:
            self._append_selection_formats(formats, settings.vsoft_target, "HRP V-Soft", "VRP V-Soft")
        if settings.save_atdi:
            self._append_selection_formats(formats, settings.atdi_target, "HRP ATDI", "VRP ATDI", "3D ATDI")
        if settings.save_3d_text:
            formats.append("3D Text")
        if settings.save_ngw3d:
            formats.append("NGW3D")
        if settings.save_prn:
            formats.append("PRN")
        if settings.save_edx:
            formats.append("EDX" if settings.edx_file_type == "Simple file-1 VRP" else "Complex EDX")
        return formats

    def _save_patterns_target_path(self, base_path: Path, format_name: str) -> Path:
        base_dir = base_path.parent
        base_name = self._export_base_name(base_path)
        file_names = {
            "HRP JPEG": f"{base_name}_HRP.jpg",
            "VRP JPEG": f"{base_name}_VRP.jpg",
            "HRP PDF": f"{base_name}_HRP.pdf",
            "VRP PDF": f"{base_name}_VRP.pdf",
            "HRP PAT": f"{base_name}_HRP.pat",
            "VRP PAT": f"{base_name}_VRP.pat",
            "HRP Text": f"{base_name}_HRP.txt",
            "VRP Text": f"{base_name}_VRP.txt",
            "HRP CSV": f"{base_name}_HRP.csv",
            "VRP CSV": f"{base_name}_VRP.csv",
            "HRP V-Soft": f"{base_name}_HRP.vep",
            "VRP V-Soft": f"{base_name}_VRP.vep",
            "HRP ATDI": f"{base_name}.H_DIA.DIA",
            "VRP ATDI": f"{base_name}.V_DIA.DIA",
            "3D ATDI": f"{base_name} ATDI_3d.csv",
            "3D Text": f"{base_name}.3dp",
            "NGW3D": f"{base_name}.ng3dant",
            "PRN": f"{base_name}.prn",
            "EDX": f"{base_name}.ProgiraEDX.pat",
            "Complex EDX": f"{base_name}.ProgiraEDX.pat",
        }
        return base_dir / file_names[format_name]

    def export_selected_patterns(self, base_path: str | Path, settings: SavePatternsSettings):
        from exports.pattern_exporters import export_to_format

        selected_formats = self._save_patterns_formats(settings)
        if not selected_formats:
            raise ValueError("Tick at least one pattern file format")
        self._ensure_pattern_ready_for_export()

        context = self._build_export_context()
        context.edx_peak_hrp = settings.edx_hrp_used == "Peak HRP"
        context.edx_start_deg = float(settings.edx_start_deg)
        context.edx_stop_deg = float(settings.edx_stop_deg)
        context.edx_increment_deg = float(settings.edx_increment_deg)
        context.export_image_scale = float(settings.image_resolution_scale)

        saved_paths = []
        base_path = self._validate_export_base_path(base_path)
        for format_name in selected_formats:
            target = self._save_patterns_target_path(base_path, format_name)
            export_to_format(format_name, target, context)
            saved_paths.append(target)
        return saved_paths

    def on_save_patterns_requested(self, settings: SavePatternsSettings):
        try:
            self._ensure_pattern_ready_for_export()
        except Exception as exc:
            self.on_save_patterns_error(str(exc))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Patterns Base Name",
            str(Path.home() / "pattern_export"),
            "Base Name (*)",
        )
        if not path:
            return

        try:
            saved_paths = self.export_selected_patterns(path, settings)
            self._add_message(f"Save patterns complete ({len(saved_paths)} files)")
            QMessageBox.information(
                self,
                "Save Patterns",
                f"Successfully exported {len(saved_paths)} file(s) to\n{Path(path).parent}",
            )
        except Exception as exc:
            self.on_save_patterns_error(str(exc))

    def on_export_file(self, format_name):
        from exports.pattern_exporters import export_to_format, get_export_definition

        definition = get_export_definition(format_name)
        if definition.requires_pattern:
            try:
                self._ensure_pattern_ready_for_export()
            except Exception as exc:
                QMessageBox.warning(self, "Error", str(exc))
                return
        path, _ = QFileDialog.getSaveFileName(
            self,
            definition.label,
            str(Path.home() / "pattern_export"),
            definition.file_filter,
        )
        if path:
            try:
                if definition.suffix and not path.lower().endswith(definition.suffix.lower()):
                    path += definition.suffix
                export_to_format(format_name, path, self._build_export_context())
                QMessageBox.information(self, "Exported", f"Successfully exported to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Apply a modern stylesheet here if needed
    # app.setStyleSheet(modern_style)
    
    window = ADTMainWindow()
    window.show()
    sys.exit(app.exec())
