from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PatternLibraryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pattern_count = 4
        self.section_widgets = {}
        self.predefined_entries_by_pattern = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 112)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(22)

        for index in range(1, self.pattern_count + 1):
            self.add_pattern_group(index)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_pattern_group(self, index):
        self.section_widgets[index] = {}
        self.predefined_entries_by_pattern[index] = []

        row = self.table.rowCount()
        self.table.insertRow(row)

        item_title = QTableWidgetItem(f"Pattern {index}")
        item_title.setBackground(Qt.GlobalColor.lightGray)

        combo_standard = QComboBox()
        combo_standard.addItems(["Standard", "Custom", "Imported"])
        combo_standard.currentTextChanged.connect(
            lambda _text, pattern_index=index: self._on_mode_changed(pattern_index)
        )

        self.table.setItem(row, 0, item_title)
        self.table.setCellWidget(row, 1, combo_standard)
        self.section_widgets[index]["mode"] = combo_standard

        props = [
            ("Panel Type", ""),
            ("Elevation Spacing (m)", "1.15"),
            ("Width (m)", "0.5"),
            ("Height (m)", "1.09"),
            ("Depth (m)", "0.22"),
            ("HRP File", ""),
            ("VRP File", ""),
        ]

        for property_name, default_value in props:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(property_name))

            key = self._property_key(property_name)
            if property_name == "Panel Type":
                panel_combo = QComboBox()
                panel_combo.setEditable(True)
                panel_combo.setCurrentText(default_value)
                panel_combo.currentTextChanged.connect(
                    lambda text, pattern_index=index: self._on_panel_type_changed(
                        pattern_index, text
                    )
                )
                self.table.setCellWidget(row, 1, panel_combo)
                self.section_widgets[index][key] = panel_combo
            elif "File" in property_name:
                file_widget = QWidget()
                layout = QHBoxLayout(file_widget)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)

                path_input = QLineEdit(default_value)
                path_input.setReadOnly(True)
                path_input.setStyleSheet("border: 1px solid #ccc;")

                browse_button = QPushButton("...")
                browse_button.setMaximumWidth(30)
                browse_button.clicked.connect(
                    lambda _checked, target=path_input: self.browse_file(target)
                )

                layout.addWidget(path_input)
                layout.addWidget(browse_button)
                self.table.setCellWidget(row, 1, file_widget)
                self.section_widgets[index][key] = path_input
                self.section_widgets[index][f"{key}_button"] = browse_button
            else:
                value_input = QLineEdit(default_value)
                value_input.setStyleSheet("border: none; background: transparent;")
                self.table.setCellWidget(row, 1, value_input)
                self.section_widgets[index][key] = value_input

        self._on_mode_changed(index)

    def browse_file(self, line_edit):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pattern File",
            "",
            "Pattern Files (*.pat *.hup *.vup);;All Files (*)",
        )
        if file_name:
            line_edit.setText(file_name)

    def _property_key(self, property_name):
        return {
            "Panel Type": "panel_type",
            "Elevation Spacing (m)": "elevation_spacing_m",
            "Width (m)": "width_m",
            "Height (m)": "height_m",
            "Depth (m)": "depth_m",
            "HRP File": "hrp_path",
            "VRP File": "vrp_path",
        }[property_name]

    def _is_standard_mode(self, pattern_index):
        mode_widget = self.section_widgets[pattern_index]["mode"]
        return mode_widget.currentText() == "Standard"

    def _lookup_predefined_entry(self, pattern_index, panel_type_text):
        panel_type_text = (panel_type_text or "").strip()
        for entry in self.predefined_entries_by_pattern.get(pattern_index, []):
            if entry.display_name == panel_type_text or entry.panel_type == panel_type_text:
                return entry
        return None

    def _preferred_default_panel_name(self, entries):
        preferred_names = [
            "Panel Array_PHP4S",
            "Panel Array_PCP-600_Hpol",
            "MTV",
        ]
        available_names = {entry.display_name for entry in entries}
        for preferred_name in preferred_names:
            if preferred_name in available_names:
                return preferred_name
        return entries[0].display_name if entries else ""

    def _apply_predefined_entry(self, pattern_index, panel_type_text):
        if not self._is_standard_mode(pattern_index):
            return

        entry = self._lookup_predefined_entry(pattern_index, panel_type_text)
        if entry is None:
            return

        self.section_widgets[pattern_index]["elevation_spacing_m"].setText(
            f"{entry.elevation_spacing_m:g}"
        )
        self.section_widgets[pattern_index]["width_m"].setText(f"{entry.width_m:g}")
        self.section_widgets[pattern_index]["height_m"].setText(f"{entry.height_m:g}")
        self.section_widgets[pattern_index]["depth_m"].setText(f"{entry.depth_m:g}")
        self.section_widgets[pattern_index]["hrp_path"].setText(entry.hrp_path)
        self.section_widgets[pattern_index]["vrp_path"].setText(entry.vrp_path)

    def _on_panel_type_changed(self, pattern_index, panel_type_text):
        if self._is_standard_mode(pattern_index):
            self._apply_predefined_entry(pattern_index, panel_type_text)

    def _on_mode_changed(self, pattern_index):
        widgets = self.section_widgets[pattern_index]
        is_standard = self._is_standard_mode(pattern_index)

        panel_widget = widgets["panel_type"]
        panel_widget.setEditable(not is_standard)

        for key in ("elevation_spacing_m", "width_m", "height_m", "depth_m"):
            widgets[key].setReadOnly(is_standard)

        widgets["hrp_path_button"].setEnabled(not is_standard)
        widgets["vrp_path_button"].setEnabled(not is_standard)

        if is_standard:
            current_text = widgets["panel_type"].currentText().strip()
            if not current_text and widgets["panel_type"].count() > 0:
                widgets["panel_type"].setCurrentIndex(0)
                current_text = widgets["panel_type"].currentText().strip()
            self._apply_predefined_entry(pattern_index, current_text)

    def set_predefined_panel_options(self, entries, pattern_indices=None):
        if pattern_indices is None:
            pattern_indices = list(self.section_widgets.keys())

        for pattern_index in pattern_indices:
            panel_widget = self.section_widgets[pattern_index]["panel_type"]
            current_text = panel_widget.currentText().strip()
            self.predefined_entries_by_pattern[pattern_index] = list(entries)

            blocker = QSignalBlocker(panel_widget)
            panel_widget.clear()
            for entry in entries:
                panel_widget.addItem(entry.display_name)

            if current_text:
                match_index = panel_widget.findText(current_text)
                if match_index >= 0:
                    panel_widget.setCurrentIndex(match_index)
                elif panel_widget.isEditable():
                    panel_widget.setCurrentText(current_text)
            elif panel_widget.count() > 0:
                preferred_name = self._preferred_default_panel_name(entries)
                match_index = panel_widget.findText(preferred_name)
                panel_widget.setCurrentIndex(match_index if match_index >= 0 else 0)
            del blocker

            self._on_mode_changed(pattern_index)

    def select_standard_panel(self, panel_name, pattern_indices=None):
        if pattern_indices is None:
            pattern_indices = [1]

        for pattern_index in pattern_indices:
            widgets = self.section_widgets.get(pattern_index)
            if not widgets:
                continue
            mode_widget = widgets["mode"]
            panel_widget = widgets["panel_type"]

            mode_blocker = QSignalBlocker(mode_widget)
            if mode_widget.currentText() != "Standard":
                mode_widget.setCurrentText("Standard")
            del mode_blocker

            panel_blocker = QSignalBlocker(panel_widget)
            index = panel_widget.findText(panel_name)
            if index >= 0:
                panel_widget.setCurrentIndex(index)
            elif panel_widget.isEditable():
                panel_widget.setCurrentText(panel_name)
            del panel_blocker

            self._on_mode_changed(pattern_index)

    def _find_pattern_sections(self):
        sections = {}
        current_pattern = None

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            if not key_item:
                continue

            key_text = key_item.text()
            if key_text.startswith("Pattern "):
                current_pattern = int(key_text.split(" ")[1])
                sections[current_pattern] = {"header": row}
            elif current_pattern is not None:
                sections[current_pattern][key_text] = row

        return sections

    def _read_value(self, row):
        if row is None:
            return ""

        widget = self.table.cellWidget(row, 1)
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if widget is not None:
            path_input = widget.findChild(QLineEdit)
            if path_input is not None:
                return path_input.text()

        item = self.table.item(row, 1)
        return item.text() if item else ""

    def _write_value(self, row, value):
        if row is None or value is None:
            return

        text = str(value)
        widget = self.table.cellWidget(row, 1)
        if isinstance(widget, QLineEdit):
            widget.setText(text)
            return
        if isinstance(widget, QComboBox):
            blocker = QSignalBlocker(widget)
            index = widget.findText(text)
            if index >= 0:
                widget.setCurrentIndex(index)
            elif widget.isEditable():
                widget.setCurrentText(text)
            else:
                widget.addItem(text)
                widget.setCurrentText(text)
            del blocker
            return
        if widget is not None:
            path_input = widget.findChild(QLineEdit)
            if path_input is not None:
                path_input.setText(text)
                return

        item = self.table.item(row, 1)
        if item is None:
            item = QTableWidgetItem(text)
            self.table.setItem(row, 1, item)
        else:
            item.setText(text)

    def get_pattern_configs(self):
        configs = {}
        sections = self._find_pattern_sections()

        for current_pattern, rows in sections.items():
            header_widget = self.table.cellWidget(rows["header"], 1)
            mode = (
                header_widget.currentText()
                if isinstance(header_widget, QComboBox)
                else "Standard"
            )
            configs[current_pattern] = {
                "mode": mode,
                "panel_type": self._read_value(rows.get("Panel Type")),
                "elevation_spacing_m": self._read_value(
                    rows.get("Elevation Spacing (m)")
                ),
                "width_m": self._read_value(rows.get("Width (m)")),
                "height_m": self._read_value(rows.get("Height (m)")),
                "depth_m": self._read_value(rows.get("Depth (m)")),
                "hrp_path": self._read_value(rows.get("HRP File")),
                "vrp_path": self._read_value(rows.get("VRP File")),
            }

        return configs

    def set_pattern_configs(self, configs):
        sections = self._find_pattern_sections()
        for pattern_index, config in configs.items():
            rows = sections.get(pattern_index)
            if not rows:
                continue

            header_widget = self.table.cellWidget(rows["header"], 1)
            if isinstance(header_widget, QComboBox):
                index = header_widget.findText(config.get("mode", "Standard"))
                if index >= 0:
                    header_widget.setCurrentIndex(index)

            self._write_value(rows.get("Panel Type"), config.get("panel_type"))
            self._write_value(
                rows.get("Elevation Spacing (m)"),
                config.get("elevation_spacing_m"),
            )
            self._write_value(rows.get("Width (m)"), config.get("width_m"))
            self._write_value(rows.get("Height (m)"), config.get("height_m"))
            self._write_value(rows.get("Depth (m)"), config.get("depth_m"))
            self._write_value(rows.get("HRP File"), config.get("hrp_path"))
            self._write_value(rows.get("VRP File"), config.get("vrp_path"))

            self._on_mode_changed(pattern_index)
