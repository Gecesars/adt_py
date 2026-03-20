from __future__ import annotations

from pathlib import Path


APP_NAME = "EFTX Antenna Designer (EAD)"
APP_VERSION = "0.5.3"
APP_WINDOW_TITLE = f"{APP_NAME} Version {APP_VERSION}"
APP_DEVELOPER = "Geraldo César Simão"
APP_EMAIL = "gecesars@gmail.com"
APP_COPYRIGHT = "Copyright © EFTX 2026"
APP_SUPPORT_TEXT = (
    "For technical support, documentation questions, or project assistance,\n"
    f"please contact {APP_DEVELOPER}.\n\n"
    f"Email: {APP_EMAIL}"
)


def app_logo_path() -> Path:
    return Path(__file__).resolve().with_name("logo.png")
