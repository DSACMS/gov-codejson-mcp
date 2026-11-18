import pytest

from example_server.inventory_layout import get_inventory_layout


def test_mock_layout_preserves_existing_conversion():
    layout = get_inventory_layout("mock")

    project = layout.prepare_record(
        {
            "entry_id": "mock-001",
            "languages": "Python; JavaScript",
            "licenses": "MIT",
        }
    )

    assert layout.id_expression == "CAST(id AS STRING)"
    assert project["languages"] == ["Python", "JavaScript"]
    assert project["licenses"] == [{"name": "MIT", "url": None}]


def test_legacy_layout_uses_entry_id_and_legacy_fields():
    layout = get_inventory_layout("legacy")

    project = layout.prepare_record(
        {
            "entry_id": "entry-001",
            "identifier": "example.org/shared-landing-page",
            "permissions_usageType": "openSource",
            "languages": "Python|Shell",
            "tags": "research|energy",
            "contact_email": "contact@example.org",
        }
    )

    assert layout.id_expression == "entry_id"
    assert project["entry_id"] == "entry-001"
    assert project["usageType"] == "openSource"
    assert project["languages"] == ["Python", "Shell"]
    assert project["tags"] == ["research", "energy"]
    assert project["version"] is None
    assert project["dateMetadataLastUpdated"] is None
    assert not any(key.startswith("contact") for key in project)
    assert "contact" not in layout.select_columns.lower()


def test_unknown_layout_is_rejected():
    with pytest.raises(ValueError, match="dataset_format"):
        get_inventory_layout("unsupported")
