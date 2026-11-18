from datetime import datetime, timezone

import pytest

from example_server.legacy_project_adapter import prepare_legacy_project


def test_maps_legacy_fields_without_exposing_contacts():
    record = {
        "identifier": "example.org/shared-landing-page",
        "agency": "DOE",
        "organization": "Example Laboratory",
        "name": "Example Project",
        "repositoryURL": "https://example.org/shared-landing-page",
        "permissions_usageType": "exemptByLaw",
        "permissions_licenses": "BSD-3-Clause",
        "languages": "Python|Shell",
        "tags": " energy | research ",
        "laborHours": 1.5,
        "date_created": datetime(
            2024, 4, 2, 13, 30, tzinfo=timezone.utc
        ),
        "contact_email": "contact@example.org",
        "contact_name": "Example Contact",
    }

    project = prepare_legacy_project(record, entry_id="inventory-001")
    data = project.model_dump()

    assert project.entry_id == "inventory-001"
    assert project.usageType == "exemptByLaw"
    assert project.licenses[0].name == "BSD-3-Clause"
    assert project.languages == ["Python", "Shell"]
    assert project.tags == ["energy", "research"]
    assert project.laborHours == 1.5
    assert project.dateCreated == "2024-04-02T13:30:00+00:00"
    assert project.version is None
    assert project.dateMetadataLastUpdated is None
    assert project.source_identifier is None
    assert not any(key.startswith("contact") for key in data)
    assert "contact@example.org" not in project.model_dump_json()


def test_missing_fields_remain_null_and_zero_is_preserved():
    project = prepare_legacy_project(
        {"name": "Example Project", "laborHours": 0},
        entry_id="inventory-002",
    )

    assert project.laborHours == 0
    assert project.languages is None
    assert project.tags is None
    assert project.licenses is None
    assert project.dateCreated is None
    assert project.dateLastModified is None


def test_shared_identifier_does_not_replace_supplied_entry_ids():
    record = {
        "identifier": "example.org/shared-landing-page",
        "name": "Example Project",
    }

    first = prepare_legacy_project(record, entry_id="inventory-001")
    second = prepare_legacy_project(record, entry_id="inventory-002")

    assert first.entry_id == "inventory-001"
    assert second.entry_id == "inventory-002"


@pytest.mark.parametrize("entry_id", ["", " "])
def test_blank_entry_id_is_rejected(entry_id):
    with pytest.raises(ValueError, match="nonblank inventory entry ID"):
        prepare_legacy_project({}, entry_id=entry_id)
