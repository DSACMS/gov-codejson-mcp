"""Read project entries from a local development fixture."""
import json
from pathlib import Path


def parse_list_field(value: str | None) -> list[str] | None:
    """Convert semicolon-separated text into a list."""
    if value is None or not value.strip():
        return None

    return [item.strip() for item in value.split(";") if item.strip()]


def get_project_from_fixture(
    fixture_path: Path,
    entry_id: str,
) -> dict | None:
    """Return one entry by its exact ID, or None when not found."""
    with fixture_path.open(encoding="utf-8") as fixture_file:
        projects = json.load(fixture_file)

    matches = [
        project
        for project in projects
        if project["entry_id"] == entry_id
    ]

    if len(matches) > 1:
        raise ValueError(f"Duplicate entry_id in fixture: {entry_id}")

    if not matches:
        return None

    project = matches[0].copy()
    project["tags"] = parse_list_field(project.get("tags"))
    project["languages"] = parse_list_field(project.get("languages"))
    return project
