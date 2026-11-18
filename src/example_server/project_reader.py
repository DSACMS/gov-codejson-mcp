"""Read project entries from a local development fixture."""
import json
from datetime import date, datetime
from pathlib import Path


def parse_list_field(
    value: str | None,
    *,
    separator: str = ";",
) -> list[str] | None:
    """Convert text using an explicitly supplied list separator."""
    if value is None or not value.strip():
        return None

    return [
        item.strip()
        for item in value.split(separator)
        if item.strip()
    ]


def parse_license_field(
    value: str | None,
) -> list[dict[str, str | None]] | None:
    """Represent a supplied license name without inferring a URL."""
    if value is None or not value.strip():
        return None

    return [{"name": value.strip(), "url": None}]


def get_project_from_fixture(
    entry_id: str,
    *,
    fixture_path: Path,
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
    project["licenses"] = parse_license_field(project.get("licenses"))

    return prepare_project(matches[0])


def format_date_field(value: date | datetime | str | None) -> str | None:
    """Preserve supplied date or timestamp precision as ISO text."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def prepare_project(project: dict) -> dict:
    """Convert inventory fields into project response values."""
    prepared = project.copy()
    prepared["tags"] = parse_list_field(project.get("tags"))
    prepared["languages"] = parse_list_field(project.get("languages"))
    prepared["licenses"] = parse_license_field(project.get("licenses"))

    for field in (
        "dateCreated",
        "dateLastModified",
        "dateMetadataLastUpdated",
    ):
        prepared[field] = format_date_field(project.get(field))

    return prepared
