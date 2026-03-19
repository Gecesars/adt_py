from __future__ import annotations

import json
from pathlib import Path

from domain import Project


def save_project(path, project: Project):
    project_path = Path(path)
    project_path.write_text(
        json.dumps(project.to_dict(), indent=2),
        encoding="utf-8",
    )


def load_project(path) -> Project:
    project_path = Path(path)
    return Project.from_dict(json.loads(project_path.read_text(encoding="utf-8")))

