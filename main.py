import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTabWidget, QDockWidget, QMenuBar, QMenu, QStatusBar,
                             QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QLabel, QSplitter)
from PyQt6.QtCore import Qt, QLocale

from catalogs import OriginalAdtCatalog
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
from widgets.antenna_design import AntennaDesignWidget
from widgets.tower_layout import TowerLayoutWidget
from widgets.compensation import CompensationWidget
from widgets.radiation_plots import (
    HrpPlotWidget,
    VrpPlotWidget,
    display_to_internal_azimuth,
)
from widgets.result_summary import ResultSummaryWidget
from widgets.message_list import MessageListWidget
from widgets.beam_shape import BeamShapeWidget


def _parse_float_text(value, default):
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


class ADTMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        QLocale.setDefault(QLocale.c())
        self.setWindowTitle("Antenna Design Tool (ADT) - Python Version")
        self.resize(1400, 900)
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
        try:
            self.original_adt_catalog = OriginalAdtCatalog()
        except Exception:
            self.original_adt_catalog = None
        
        self.init_menu()
        self.init_ui()
        self.init_catalog_bindings()
        self.refresh_predefined_panel_catalog()
        self.refresh_beam_shape_frequency()
        self._sync_design_panel_count_from_array()
        self.refresh_tower_layout_preview()
        
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
        
        act_save_rfs_pat = QAction("Save Displayed Pattern as RFS PAT Format", self)
        act_save_txt = QAction("Save Displayed Pattern as Text Format", self)
        act_save_csv = QAction("Save Displayed Pattern as CSV Format", self)
        act_save_vsoft = QAction("Save Displayed Pattern as V-Soft Format", self)
        act_save_atdi = QAction("Save Pattern as ATDI Format", self)
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
        file_menu.addAction(act_save_rfs_pat)
        file_menu.addAction(act_save_txt)
        file_menu.addAction(act_save_csv)
        file_menu.addAction(act_save_vsoft)
        file_menu.addAction(act_save_atdi)
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
        
        # Wire View actions to lambda functions targeting the tabs/docks
        # Note: the lambda uses a trick passing `self` to avoid late-binding issues, though not strictly necessary here
        act_view_design_info.triggered.connect(lambda: self._focus_tab(self.left_tabs, 0))
        act_view_site_details.triggered.connect(lambda: self._focus_tab(self.left_tabs, 1))
        act_view_save_patterns.triggered.connect(lambda: self._focus_tab(self.left_tabs, 2))
        
        act_view_antenna_details.triggered.connect(lambda: self._focus_tab(self.central_tabs, 0))
        act_view_tower_layout.triggered.connect(lambda: self._focus_tab(self.central_tabs, 1))
        act_view_imp_comp.triggered.connect(lambda: self._focus_tab(self.central_tabs, 2))
        
        act_view_result_summary.triggered.connect(lambda: self.dock_result_summary.show())
        
        act_view_memory_trace.triggered.connect(lambda: self._focus_tab(self.right_bottom_tabs, 2))
        
        # --- PLOT MENU ---
        act_plot_save_hrp_jpg = QAction("Save Displayed HRP to File (jpg)", self)
        act_plot_save_vrp_jpg = QAction("Save Displayed VRP to File (jpg)", self)
        act_plot_save_layout_jpg = QAction("Save Layout to File (jpg)", self)
        act_plot_save_summary_pdf = QAction("Save Result Summary to File (pdf)", self)
        act_plot_save_panel_pdf = QAction("Save Panel Positions and Electrical Data to File (pdf)", self)
        act_plot_save_all_pdf = QAction("Save All to File (pdf)", self)
        
        plot_save_pattern_menu = plot_menu.addMenu("Save Displayed Pattern to File (jpg)")
        plot_save_pattern_menu.addAction(act_plot_save_hrp_jpg)
        plot_save_pattern_menu.addAction(act_plot_save_vrp_jpg)
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
        act_action_hpat = QAction("Launch HPAT", self)
        act_action_vpat = QAction("Launch VPAT", self)
        action_menu.addAction(act_action_calc_3d)
        action_menu.addAction(act_action_anim_vrp)
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
        
        act_save_rfs_pat.triggered.connect(lambda: self.on_export_file("RFS PAT", "pat"))
        act_save_txt.triggered.connect(lambda: self.on_export_file("Text", "txt"))
        act_save_csv.triggered.connect(lambda: self.on_export_file("CSV", "csv"))
        act_save_vsoft.triggered.connect(lambda: self.on_export_file("V-Soft", "pat"))
        act_save_atdi.triggered.connect(lambda: self.on_export_file("ATDI", "txt"))
        act_save_3d_txt.triggered.connect(lambda: self.on_export_file("3D Text", "txt"))
        act_save_3d_ngw.triggered.connect(lambda: self.on_export_file("NGW3D", "txt"))
        act_save_3d_prn.triggered.connect(lambda: self.on_export_file("PRN", "prn"))
        act_save_edx.triggered.connect(lambda: self.on_export_file("EDX", "pat"))
        act_save_complex_edx.triggered.connect(lambda: self.on_export_file("Complex EDX", "pat"))
        act_save_directivity.triggered.connect(lambda: self.on_export_file("Directivity", "txt"))
        act_save_anim_video.triggered.connect(lambda: self.on_export_file("Video", "avi"))
        
        act_plot_save_hrp_jpg.triggered.connect(lambda: self.on_export_file("HRP JPEG", "jpg"))
        act_plot_save_vrp_jpg.triggered.connect(lambda: self.on_export_file("VRP JPEG", "jpg"))
        act_plot_save_layout_jpg.triggered.connect(lambda: self.on_export_file("Layout JPEG", "jpg"))
        act_plot_save_summary_pdf.triggered.connect(lambda: self.on_export_file("Summary PDF", "pdf"))
        act_plot_save_panel_pdf.triggered.connect(lambda: self.on_export_file("Panel PDF", "pdf"))
        act_plot_save_all_pdf.triggered.connect(lambda: self.on_export_file("All PDF", "pdf"))
        
        act_setup_coords_polar.triggered.connect(self.on_not_implemented)
        act_setup_coords_cart.triggered.connect(self.on_not_implemented)
        act_setup_feed.triggered.connect(self.on_not_implemented)
        
        act_action_anim_vrp.triggered.connect(self.on_not_implemented)
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
        """Helper to safely focus and show a tab."""
        if hasattr(self, 'dock_left_top') and tab_widget == self.left_tabs:
            self.dock_left_top.show()
        if hasattr(self, 'dock_messages') and tab_widget == self.right_bottom_tabs:
            self.dock_messages.show()
        tab_widget.setCurrentIndex(index)

    def init_ui(self):
        # --- CENTRAL WIDGET (Top: Tabs for Design/Layout, Bottom: Radiation Plots) ---
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        central_splitter = QSplitter(Qt.Orientation.Vertical)
        central_splitter.setChildrenCollapsible(False)
        central_splitter.setHandleWidth(5)

        # Central Top Tabs
        self.central_tabs = QTabWidget()
        self.antenna_design_tab = AntennaDesignWidget()
        self.central_tabs.addTab(self.antenna_design_tab, "Antenna Design Details")
        self.tower_layout_tab = TowerLayoutWidget()
        self.central_tabs.addTab(self.tower_layout_tab, "Tower and Panel Layout")
        self.compensation_tab = CompensationWidget()
        self.central_tabs.addTab(self.compensation_tab, "Imp Compensation / Array Imp")
        central_splitter.addWidget(self.central_tabs)

        # Central Bottom Plots (Horizontal Split)
        plots_splitter = QSplitter(Qt.Orientation.Horizontal)
        plots_splitter.setChildrenCollapsible(False)
        plots_splitter.setHandleWidth(5)

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
        central_splitter.addWidget(plots_splitter)
        central_splitter.setSizes([560, 340])

        central_layout.addWidget(central_splitter)
        self.setCentralWidget(central_widget)
        
        # --- LEFT DOCKS (Top: Design Info Tabs, Bottom: Pattern Library) ---
        self.dock_left_top = QDockWidget("Design Information", self)
        # Wrap Design Info in a TabWidget to match the reference "Design Information | Site Details | Save Patterns"
        self.left_tabs = QTabWidget()
        self.design_info_widget = DesignInfoWidget()
        self.left_tabs.addTab(self.design_info_widget, "Design Information")
        self.left_tabs.addTab(QWidget(), "Site Details")
        self.left_tabs.addTab(QWidget(), "Save Patterns")
        self.dock_left_top.setWidget(self.left_tabs)
        self.dock_left_top.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_left_top)
        
        self.dock_pattern_lib = QDockWidget("Pattern Library", self)
        self.pattern_library_widget = PatternLibraryWidget()
        self.dock_pattern_lib.setWidget(self.pattern_library_widget)
        self.dock_pattern_lib.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_pattern_lib)
        
        self.splitDockWidget(self.dock_left_top, self.dock_pattern_lib, Qt.Orientation.Vertical)
        
        # --- RIGHT DOCKS (Top: Result Summary, Middle: Point Info/Find, Bottom: Message List Tabs) ---
        self.dock_result_summary = QDockWidget("Result Summary", self)
        self.dock_result_summary.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.result_summary_widget = ResultSummaryWidget()
        self.dock_result_summary.setWidget(self.result_summary_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_result_summary)
        
        # Point Info (Azimuth, Elevation, Relative Field, Power from Peak) + Find Button
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel
        self.dock_point_info = QDockWidget("Point Info", self)
        self.dock_point_info.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        point_widget = QWidget()
        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 0, 0, 0)
        
        point_table = QTableWidget(1, 4)
        point_table.setHorizontalHeaderLabels(["Azimuth\nAngle", "Elevation\nAngle", "Relative Field\n(E/Emax)", "Power from\nPeak (dB)"])
        point_table.verticalHeader().setVisible(False)
        point_table.setItem(0, 0, QTableWidgetItem("359"))
        point_table.setItem(0, 1, QTableWidgetItem("0.0"))
        point_table.setItem(0, 2, QTableWidgetItem("1.0000"))
        point_table.setItem(0, 3, QTableWidgetItem("0.00"))
        point_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        point_layout.addWidget(point_table)
        
        find_layout = QHBoxLayout()
        find_layout.addStretch()
        find_btn = QPushButton("Find")
        find_btn.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold; width: 80px;")
        find_layout.addWidget(find_btn)
        point_layout.addLayout(find_layout)
        
        self.dock_point_info.setWidget(point_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_point_info)
        
        self.dock_messages = QDockWidget("Messages", self)
        self.dock_messages.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.right_bottom_tabs = QTabWidget()
        self.message_list_widget = MessageListWidget()
        self.beam_shape_widget = BeamShapeWidget()
        self.right_bottom_tabs.addTab(self.message_list_widget, "Result Su...")
        self.right_bottom_tabs.addTab(self.beam_shape_widget, "Beam Sh...")
        self.right_bottom_tabs.addTab(QWidget(), "Memory...")
        self.right_bottom_tabs.addTab(QWidget(), "Distance...")
        self.dock_messages.setWidget(self.right_bottom_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_messages)
        
        self.splitDockWidget(self.dock_result_summary, self.dock_point_info, Qt.Orientation.Vertical)
        self.splitDockWidget(self.dock_point_info, self.dock_messages, Qt.Orientation.Vertical)

        # Wiring logic
        # DesignInfo is now inside a QTabWidget which is inside self.dock_left_top
        self.design_info_widget.calc_btn.clicked.connect(self.on_calculate_clicked)
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

    def init_catalog_bindings(self):
        self.design_info_widget.design_freq_input.editingFinished.connect(
            self._on_design_frequency_changed
        )
        self.design_info_widget.channel_freq_input.editingFinished.connect(
            self.refresh_predefined_panel_catalog
        )
        self.design_info_widget.polarisation_combo.currentTextChanged.connect(
            lambda _text: self.refresh_predefined_panel_catalog()
        )

    def _on_design_frequency_changed(self):
        self.refresh_predefined_panel_catalog()
        self.refresh_beam_shape_frequency()

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
        self.tower_layout_tab.update_preview(
            self.antenna_design_tab.get_array_data(),
            self.pattern_library_widget.get_pattern_configs(),
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

    def on_hrp_elevation_changed(self, elevation_deg):
        self.selected_hrp_elevation_deg = float(elevation_deg)
        self.lock_hrp_elevation = True
        self._refresh_hrp_plot(elevation_deg=elevation_deg)

    def on_vrp_azimuth_changed(self, azimuth_deg):
        internal_azimuth_deg = display_to_internal_azimuth(azimuth_deg)
        self.selected_vrp_azimuth_deg = float(internal_azimuth_deg)
        self.lock_vrp_azimuth = True
        self.hrp_widget.set_selected_azimuth(internal_azimuth_deg)
        self._refresh_vrp_plot(
            azimuth_deg=internal_azimuth_deg
        )

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
            self._refresh_hrp_plot(hrp_elevation)
            self._refresh_vrp_plot(vrp_azimuth)
            self.refresh_tower_layout_preview()
            self._add_message(
                "Calculated 3D pattern and refreshed HRP/VRP displays from the 3D field."
            )
        
        except Exception as e:
            self._add_message(f"Error calculating pattern: {str(e)}")

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
                    self.antenna_design_tab,
                    self.pattern_library_widget,
                )
                self.refresh_predefined_panel_catalog()
                self.refresh_beam_shape_frequency()
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

    def on_export_file(self, format_name, ext):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from exports.pattern_exporters import export_to_format
        
        path, _ = QFileDialog.getSaveFileName(self, f"Export as {format_name}", "", f"{format_name} Files (*.{ext});;All Files (*)")
        if path:
            try:
                mag = getattr(self, 'last_mag_3d', None)
                az = getattr(self, 'last_az_angles', None)
                el = getattr(self, 'last_el_angles', None)
                export_to_format(format_name, path, mag, az, el)
                QMessageBox.information(self, "Exported", f"Successfully exported to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export: {str(e)}\n\nMake sure to run 'Calculate 3D Pattern' first.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Apply a modern stylesheet here if needed
    # app.setStyleSheet(modern_style)
    
    window = ADTMainWindow()
    window.show()
    sys.exit(app.exec())
