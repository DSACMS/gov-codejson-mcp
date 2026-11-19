from datetime import datetime, timezone

import pytest

from example_server.complete_project_adapter import prepare_complete_project


def test_maps_complete_fields_without_exposing_contacts():
    timestamp = datetime(2026, 11, 19, 12, 30, tzinfo=timezone.utc)
    record = {
        "identifier": "github.com/example/project",
        "agency": "DHS",
        "organization": "Example Organization",
        "name": "Example Project",
        "description": "Inventory description",
        "repositoryURL": "https://github.com/example/project",
        "version": "1.2.0",
        "permissions_usageType": "openSource",
        "permissions_licenses": "MIT",
        "permissions_licenses_name": "MIT",
        "permissions_licenses_URL": "https://example.org/LICENSE",
        "languages": " Python | Shell ",
        "tags": " security | research ",
        "laborHours": 0,
        "date_created": timestamp,
        "date_lastModified": timestamp,
        "date_metadataLastUpdated": timestamp,
        "contact_email": "contact@example.org",
        "partners_email": "partner@example.org",
    }

    project = prepare_complete_project(record, entry_id="2026-DHS-1")

    assert project.entry_id == "2026-DHS-1"
    assert project.source_identifier == "github.com/example/project"
    assert project.agency == "DHS"
    assert project.organization == "Example Organization"
    assert project.name == "Example Project"
    assert project.description == "Inventory description"
    assert project.repositoryURL == "https://github.com/example/project"
    assert project.version == "1.2.0"
    assert project.usageType == "openSource"
    assert project.languages == ["Python", "Shell"]
    assert project.tags == ["security", "research"]
    assert project.laborHours == 0
    assert project.licenses[0].name == "MIT"
    assert project.licenses[0].url == "https://example.org/LICENSE"
    assert project.dateCreated == timestamp.isoformat()
    assert project.dateLastModified == timestamp.isoformat()
    assert project.dateMetadataLastUpdated == timestamp.isoformat()

    data = project.model_dump()
    assert not any(
        key.startswith(("contact", "partners")) for key in data
    )
    assert "contact@example.org" not in project.model_dump_json()
    assert "partner@example.org" not in project.model_dump_json()


def test_pairs_multiple_licenses_in_source_order():
    project = prepare_complete_project(
        {
            "permissions_licenses_name": " MIT | Apache-2.0 ",
            "permissions_licenses_URL": (
                " https://example.org/mit | https://example.org/apache "
            ),
        },
        entry_id="2026-DOE-1300",
    )

    assert [license.model_dump() for license in project.licenses] == [
        {"name": "MIT", "url": "https://example.org/mit"},
        {"name": "Apache-2.0", "url": "https://example.org/apache"},
    ]


def test_missing_url_position_does_not_shift_other_urls():
    project = prepare_complete_project(
        {
            "permissions_licenses_name": "MIT|BSD-3-Clause|Apache-2.0",
            "permissions_licenses_URL": (
                "https://example.org/mit||https://example.org/apache"
            ),
        },
        entry_id="2026-DOE-test",
    )

    assert [license.url for license in project.licenses] == [
        "https://example.org/mit",
        None,
        "https://example.org/apache",
    ]


def test_falls_back_to_license_text_without_inventing_urls():
    project = prepare_complete_project(
        {"permissions_licenses": "MIT|Apache-2.0"},
        entry_id="2026-DOD-test",
    )

    assert [license.name for license in project.licenses] == [
        "MIT",
        "Apache-2.0",
    ]
    assert all(license.url is None for license in project.licenses)


def test_missing_fields_remain_null():
    project = prepare_complete_project({}, entry_id="2026-test-1")

    assert all(
        value is None
        for key, value in project.model_dump().items()
        if key != "entry_id"
    )


def test_shared_source_identifier_does_not_replace_entry_ids():
    record = {"identifier": "example.org/shared-landing-page"}

    first = prepare_complete_project(record, entry_id="2026-test-1")
    second = prepare_complete_project(record, entry_id="2026-test-2")

    assert first.entry_id != second.entry_id
    assert first.source_identifier == second.source_identifier


@pytest.mark.parametrize("entry_id", ["", " "])
def test_blank_entry_id_is_rejected(entry_id):
    with pytest.raises(ValueError, match="nonblank inventory entry ID"):
        prepare_complete_project({}, entry_id=entry_id)


@pytest.mark.parametrize(
    ("record", "message"),
    [
        (
            {
                "permissions_licenses_name": "MIT|Apache-2.0",
                "permissions_licenses_URL": "https://example.org/mit",
            },
            "different lengths",
        ),
        (
            {"permissions_licenses_URL": "https://example.org/license"},
            "without license names",
        ),
        (
            {"permissions_licenses_name": "MIT||Apache-2.0"},
            "empty position",
        ),
    ],
)
def test_ambiguous_license_mapping_is_rejected(record, message):
    with pytest.raises(ValueError, match=message):
        prepare_complete_project(record, entry_id="2026-test-1")
