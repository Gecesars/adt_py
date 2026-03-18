import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTabWidget, QDockWidget, QMenuBar, QMenu, QStatusBar,
                             QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QLabel)
from PyQt6.QtCore import Qt

# Import UI modular components
from ui.design_info import DesignInfoWidget
from ui.pattern_library import PatternLibraryWidget
from ui.antenna_design import AntennaDesignWidget
from ui.tower_layout import TowerLayoutWidget
from ui.compensation import CompensationWidget
from ui.radiation_plots import HrpPlotWidget, VrpPlotWidget
from ui.result_summary import ResultSummaryWidget
from ui.message_list import MessageListWidget
from ui.beam_shape import BeamShapeWidget


class ADTMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antenna Design Tool (ADT) - Python Version")
        self.resize(1400, 900)
        
        self.init_menu()
        self.init_ui()
        
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
        
        act_util_beam.triggered.connect(self.on_not_implemented)
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
        
        # Central Top Tabs
        self.central_tabs = QTabWidget()
        self.antenna_design_tab = AntennaDesignWidget()
        self.central_tabs.addTab(self.antenna_design_tab, "Antenna Design Details")
        self.tower_layout_tab = TowerLayoutWidget()
        self.central_tabs.addTab(self.tower_layout_tab, "Tower and Panel Layout")
        self.compensation_tab = CompensationWidget()
        self.central_tabs.addTab(self.compensation_tab, "Imp Compensation / Array Imp")
        central_layout.addWidget(self.central_tabs, stretch=2)
        
        # Central Bottom Plots (Horizontal Split)
        plots_widget = QWidget()
        plots_layout = QHBoxLayout(plots_widget)
        plots_layout.setContentsMargins(0, 0, 0, 0)
        
        self.hrp_widget = HrpPlotWidget()
        # Mocking a group box look for the plots to match ADT
        from PyQt6.QtWidgets import QGroupBox
        hrp_group = QGroupBox("Horizontal Radiation Pattern")
        hl1 = QVBoxLayout(hrp_group)
        hl1.addWidget(self.hrp_widget)
        plots_layout.addWidget(hrp_group)
        
        self.vrp_widget = VrpPlotWidget()
        vrp_group = QGroupBox("Vertical Radiation Pattern")
        hl2 = QVBoxLayout(vrp_group)
        hl2.addWidget(self.vrp_widget)
        plots_layout.addWidget(vrp_group)
        
        central_layout.addWidget(plots_widget, stretch=1)
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
        self.dock_pattern_lib.setWidget(PatternLibraryWidget())
        self.dock_pattern_lib.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_pattern_lib)
        
        self.splitDockWidget(self.dock_left_top, self.dock_pattern_lib, Qt.Orientation.Vertical)
        
        # --- RIGHT DOCKS (Top: Result Summary, Middle: Point Info/Find, Bottom: Message List Tabs) ---
        self.dock_result_summary = QDockWidget("Result Summary", self)
        self.dock_result_summary.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.dock_result_summary.setWidget(ResultSummaryWidget())
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

    def on_calculate_clicked(self):
        from core.antenna_models import calculate_system_metrics, ArrayDesign, AntennaPanel
        import datetime
        
        # Scrape data from UI docks
        try:
            freq_str = self.design_info_widget.design_freq_input.text()
            frequency = float(freq_str) if freq_str else 539.0
            
            pattern_configs = self.dock_pattern_lib.widget().get_pattern_configs()
            array_data = self.antenna_design_tab.get_array_data()
            
            # Build the backend models
            array_design = ArrayDesign()
            array_design.frequency = frequency
            
            for p_data in array_data:
                panel = AntennaPanel(p_data['panel_id'], "Standard")
                panel.y = p_data['y']
                panel.power = p_data['power']
                panel.phase = p_data['phase']
                panel.tilt = p_data['tilt']
                
                # Link valid paths from pattern library if matched
                pat_index = p_data['pat']
                if pat_index in pattern_configs:
                    panel.hrp_path = pattern_configs[pat_index].get('hrp_path', '')
                    panel.vrp_path = pattern_configs[pat_index].get('vrp_path', '')
                    
                array_design.add_panel(panel)
        
            # Read Loss Fields
            try:
                i_loss = float(self.design_info_widget.internal_loss_input.text())
                p_loss = float(self.design_info_widget.pol_loss_input.text())
                filt_loss = float(self.design_info_widget.filter_loss_input.text())
                feed_loss = float(self.design_info_widget.feeder_loss_input.text())
            except ValueError:
                i_loss, p_loss, filt_loss, feed_loss = 0.5, 3.0, 0.8, 1.2
        
            # Run backend physics synthesis based exclusively on the UI
            metrics, mag_3d, az_angles, el_angles = calculate_system_metrics(
                array_design, 
                internal_loss=i_loss, 
                pol_loss=p_loss, 
                filter_loss=filt_loss, 
                feeder_loss=feed_loss
            )
            
            # Cache results for Exporters
            self.last_mag_3d = mag_3d
            self.last_az_angles = az_angles
            self.last_el_angles = el_angles
            
            # Update result UI tabs
            self.dock_result_summary.widget().update_results(metrics)
            
            # Update plot widgets
            self.dock_hrp.widget().plot_data(az_angles, mag_3d[:, 900]) # Example indexing 90 degrees el
            self.dock_vrp.widget().plot_data(el_angles, mag_3d[0, :])
            
            # Update message log
            time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.dock_message_list.widget().add_message(time_str, "Calculated 3D Pattern properly dynamically using selected GUI .pat files.")
        
        except Exception as e:
            time_str = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.dock_message_list.widget().add_message(time_str, f"Error calculating pattern: {str(e)}")

    def on_not_implemented(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Not Implemented", "This mechanism is not yet fully ported from the original C# application to Python.\n(Phase 3 task)")

    def on_file_open(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.antr);;All Files (*)")
        if path:
            QMessageBox.information(self, "Loaded", f"Loaded project: {path}")

    def on_file_save(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.antr);;All Files (*)")
        if path:
            QMessageBox.information(self, "Saved", f"Saved project to: {path}")

    def on_util_dist(self):
        from ui.dis_and_bear import DistanceBearingDialog
        dlg = DistanceBearingDialog(self)
        dlg.exec()

    def on_util_exposure(self):
        from ui.field_strength import FieldStrengthExposureDialog
        # Pass cached 3D metrics to the Field Strength UI if available
        # It relies on Tx Power and ERP from the ResultSummary panel
        try:
            tx_pow = float(self.antenna_design_tab.design_info.input_tx_power.text() or 10.0)
            erp = float(self.antenna_design_tab.result_summary.val_erp_kw.text() or tx_pow)
        except ValueError:
            tx_pow = 10.0
            erp = 10.0
            
        freq = self.antenna_design_tab.design_info.channel_frequency
        
        dlg = FieldStrengthExposureDialog(self, frequency=freq, tx_power=tx_pow, erp=erp,
                                          mag_3d=self.last_mag_3d, az_angles=self.last_az_angles, el_angles=self.last_el_angles)
        dlg.exec()

    def on_util_blackspot(self):
        from ui.black_spot import BlackSpotViewer
        if self.last_mag_3d is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Pattern Data", "Please calculate a 3D pattern before opening the Blackspot Viewer.")
            return
            
        dlg = BlackSpotViewer(self, mag_3d=self.last_mag_3d)
        dlg.exec()

    def on_export_file(self, format_name, ext):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from core.exporters import export_to_format
        
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
