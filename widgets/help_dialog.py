from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout

from app_metadata import APP_NAME, APP_VERSION


HELP_HTML = f"""
<h1>{APP_NAME}</h1>
<p><b>Version:</b> {APP_VERSION}</p>

<h2>Overview</h2>
<p>
{APP_NAME} is a professional desktop tool for antenna pattern design, array composition,
site configuration, project management, and engineering exports. The application follows
the ADT workflow while extending it with Python-based maintainability and automation.
</p>

<h2>Typical Workflow</h2>
<ol>
  <li>Fill in <b>Design Information</b> and <b>Site Details</b>.</li>
  <li>Select an antenna model in <b>Pattern Library</b>.</li>
  <li>Configure the array in <b>Antenna Design Details</b>.</li>
  <li>Adjust geometry in <b>Tower and Panel Layout</b>.</li>
  <li>Run <b>Calculate 3D Pattern</b>.</li>
  <li>Inspect HRP, VRP, summary tables, and engineering outputs.</li>
  <li>Export the final design in the required technical formats.</li>
</ol>

<h2>Design Information</h2>
<p>
Use this section for customer, site, model, frequency, channel, losses, and project notes.
These values feed both the engineering calculations and the final reports.
</p>

<h2>Site Details</h2>
<p>
This tab defines tower type, tower face width or diameter, heading, feeder type, feeder length,
transmitter power, HAAT, and branch feeder length. Feeder loss is automatically calculated from
the selected cable database and current channel frequency.
</p>

<h2>Pattern Library</h2>
<p>
Choose standard antennas from the imported ADT catalog or custom antennas created with
<b>File &gt; New Antenna...</b>. Custom antennas are stored locally and appear at the top of
the antenna list.
</p>

<h2>Antenna Design Details</h2>
<p>
This area controls horizontal groups, vertical groups, and array data. The calculated HRP and VRP
are fully coupled to these tables. Changing azimuth or elevation cut values updates the
corresponding plot in real time.
</p>

<h2>Tower and Panel Layout</h2>
<p>
Use this tab to define rotation, mechanical tilt, number of faces, number of levels, offsets,
vertical spacing, and top-view geometry. The preview respects tower dimensions, tower shape,
panel width, and radial offset.
</p>

<h2>Beam Shape</h2>
<p>
Beam Shape calculates vertical phasing according to the selected bay count, spacing, required tilt,
and null-fill settings. The generated phases can be transferred directly to the vertical group table.
</p>

<h2>Plots</h2>
<p>
The horizontal plot is controlled by <b>El Angle</b>. The vertical plot is controlled by
<b>Az Angle</b>. Red reference lines track the active cross-cut, and point information is updated
from the true 3D field matrix.
</p>

<h2>Exports</h2>
<p>
The application supports the legacy engineering exports from ADT, including PAT, TXT, CSV, V-Soft,
ATDI, 3DP, NGW3D, PRN, EDX, directivity, image, PDF, and batch export through <b>Save Patterns</b>.
</p>

<h2>Keyboard Shortcuts</h2>
<ul>
  <li><b>F1</b>: Open this help</li>
  <li><b>F6</b>: Calculate 3D Pattern</li>
  <li><b>F7</b>: Animate VRP</li>
  <li><b>F8</b>: Animate HRP</li>
</ul>

<h2>Notes</h2>
<p>
For reliable exports, calculate the 3D pattern before saving files. For custom antennas, import
the cleanest available HRP and VRP source data so the normalised internal files remain stable.
</p>
"""


class HelpDialog(QDialog):
    def __init__(self, logo_path: str | Path | None = None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"{APP_NAME} Help")
        self.resize(860, 700)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            "QTextBrowser { background: white; color: #202020; border: 1px solid #bcbcbc; }"
        )
        browser.setHtml(HELP_HTML)
        root.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
