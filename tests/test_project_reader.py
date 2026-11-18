import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from example_server.models import ProjectDetail
from example_server.project_reader import (
    get_project_from_fixture,
    parse_list_field,
    prepare_project,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "projects.json"


def test_returns_matching_project():
    project = get_project_from_fixture(
        "mock-001",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["entry_id"] == "mock-001"
    assert project["agency"] == "VA"
    assert project["laborHours"] == 0


def test_preserves_missing_values():
    project = get_project_from_fixture(
        "mock-002",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["agency"] == "USDA"
    assert project["source_identifier"] is None
    assert project["languages"] is None
    assert project["laborHours"] is None


def test_unknown_id_returns_none():
    project = get_project_from_fixture(
        "unknown",
        fixture_path=FIXTURE_PATH,
    )

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
        get_project_from_fixture(
            "duplicate",
            fixture_path=fixture_path,
        )


def test_converts_tags_and_languages():
    project = get_project_from_fixture(
        "mock-001",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["tags"] == ["documents", "accessibility"]
    assert project["languages"] == ["Python", "JavaScript"]


def test_missing_tags_and_languages_remain_null():
    project = get_project_from_fixture(
        "mock-002",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["tags"] is None
    assert project["languages"] is None


def test_converts_license_name():
    project = get_project_from_fixture(
        "mock-001",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["licenses"] == [{"name": "MIT", "url": None}]


def test_missing_license_remains_null():
    project = get_project_from_fixture(
        "mock-002",
        fixture_path=FIXTURE_PATH,
    )

    assert project is not None
    assert project["licenses"] is None


def test_response_excludes_contact_fields():
    source = {
        "entry_id": "mock-contact",
        "name": "Example Project",
        "contactName": "Example Contact",
        "contactEmail": "contact@example.org",
        "contactPhone": "example-phone",
        "contactURL": "https://example.org/contact",
    }

    result = ProjectDetail.model_validate(source).model_dump()

    assert result["entry_id"] == "mock-contact"
    assert result["name"] == "Example Project"
    assert result["description"] is None
    assert not any(key.startswith("contact") for key in result)


def test_converts_typed_dates_without_adding_precision():
    project = prepare_project(
        {
            "dateCreated": date(2024, 3, 1),
            "dateLastModified": datetime(
                2025, 6, 12, 14, 30, tzinfo=timezone.utc
            ),
            "dateMetadataLastUpdated": None,
        }
    )

    assert project["dateCreated"] == "2024-03-01"
    assert project["dateLastModified"] == "2025-06-12T14:30:00+00:00"
    assert project["dateMetadataLastUpdated"] is None


def test_preserves_existing_date_strings():
    project = prepare_project(
        {
            "dateCreated": "2024-03-01",
            "dateMetadataLastUpdated": "2025-06-15T14:30:00Z",
        }
    )

    assert project["dateCreated"] == "2024-03-01"
    assert project["dateMetadataLastUpdated"] == "2025-06-15T14:30:00Z"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Python|Shell", ["Python", "Shell"]),
        (" Python | | Shell ", ["Python", "Shell"]),
        ("Python", ["Python"]),
        ("", None),
        (None, None),
    ],
)
def test_parses_pipe_separated_languages(value, expected):
    assert parse_list_field(value, separator="|") == expected


def test_default_separator_preserves_existing_mock_behavior():
    assert parse_list_field("Python; JavaScript") == [
        "Python",
        "JavaScript",
    ]


def test_separator_is_explicit():
    assert parse_list_field("Python|Shell") == ["Python|Shell"]
