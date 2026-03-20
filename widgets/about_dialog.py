from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app_metadata import (
    APP_COPYRIGHT,
    APP_DEVELOPER,
    APP_EMAIL,
    APP_NAME,
    APP_SUPPORT_TEXT,
    APP_VERSION,
)


class AboutDialog(QDialog):
    def __init__(self, logo_path: str | Path | None = None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(640)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        logo_label = QLabel()
        logo_label.setFixedSize(88, 88)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if logo_path and Path(logo_path).exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaled(
                        88,
                        88,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        header_layout.addWidget(logo_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 17pt; font-weight: 700; color: #202020;")
        subtitle = QLabel("Broadcast Antenna Design and Analysis Platform")
        subtitle.setStyleSheet("font-size: 9.5pt; color: #404040;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch(1)
        header_layout.addLayout(title_layout, 1)
        root.addLayout(header_layout)

        info_box = QWidget()
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        for text in (
            f"Version {APP_VERSION}",
            APP_NAME,
            APP_COPYRIGHT,
            f"Developed by {APP_DEVELOPER}",
            f"Email: {APP_EMAIL}",
        ):
            label = QLabel(text)
            label.setStyleSheet("font-size: 10pt; color: #202020;")
            info_layout.addWidget(label)

        root.addWidget(info_box)

        support_frame = QFrame()
        support_frame.setFrameShape(QFrame.Shape.StyledPanel)
        support_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #c7c7c7; }"
            "QLabel { color: #202020; font-size: 10pt; }"
        )
        support_layout = QVBoxLayout(support_frame)
        support_layout.setContentsMargins(12, 12, 12, 12)
        support_layout.setSpacing(8)

        support_title = QLabel("Support")
        support_title.setStyleSheet("font-size: 10.5pt; font-weight: 600; color: #202020;")
        support_body = QLabel(APP_SUPPORT_TEXT)
        support_body.setWordWrap(True)

        support_layout.addWidget(support_title)
        support_layout.addWidget(support_body)
        root.addWidget(support_frame)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
