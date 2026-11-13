import json
from pathlib import Path

import pytest

from example_server.project_reader import get_project_from_fixture

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "projects.json"


def test_returns_matching_project():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-001")

    assert project is not None
    assert project["entry_id"] == "mock-001"
    assert project["agency"] == "VA"
    assert project["laborHours"] == 0


def test_preserves_missing_values():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-002")

    assert project is not None
    assert project["agency"] == "USDA"
    assert project["source_identifier"] is None
    assert project["languages"] is None
    assert project["laborHours"] is None


def test_unknown_id_returns_none():
    project = get_project_from_fixture(FIXTURE_PATH, "unknown")

    assert project is None


def test_duplicate_id_raises_error(tmp_path):
    fixture_path = tmp_path / "duplicate_projects.json"
    fixture_path.write_text(
        json.dumps(
            [
                {"entry_id": "duplicate"},
                {"entry_id": "duplicate"},
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate entry_id"):
        get_project_from_fixture(fixture_path, "duplicate")


def test_converts_tags_and_languages():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-001")

    assert project is not None
    assert project["tags"] == ["documents", "accessibility"]
    assert project["languages"] == ["Python", "JavaScript"]


def test_missing_tags_and_languages_remain_null():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-002")

    assert project is not None
    assert project["tags"] is None
    assert project["languages"] is None


def test_converts_license_name():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-001")

    assert project is not None
    assert project["licenses"] == [{"name": "MIT", "url": None}]


def test_missing_license_remains_null():
    project = get_project_from_fixture(FIXTURE_PATH, "mock-002")

    assert project is not None
    assert project["licenses"] is None