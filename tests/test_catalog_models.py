import pytest
from pydantic import ValidationError

from example_server.models import CatalogInfoResponse


def test_catalog_preserves_agency_organization_relationships():
    response = CatalogInfoResponse(
        total_count=3,
        groups=[
            {
                "agency": "HHS",
                "organization": "CMS",
                "project_count": 2,
            },
            {
                "agency": "HHS",
                "organization": "CDC",
                "project_count": 1,
            },
        ],
    )

    data = response.model_dump()

    assert data["total_count"] == 3
    assert data["groups"] == [
        {"agency": "HHS", "organization": "CMS", "project_count": 2},
        {"agency": "HHS", "organization": "CDC", "project_count": 1},
    ]
    assert data["dataset_version"] is None
    assert data["dataset_updated_at"] is None


def test_catalog_preserves_unknown_agency_and_organization():
    response = CatalogInfoResponse(
        total_count=1,
        groups=[
            {
                "agency": None,
                "organization": None,
                "project_count": 1,
            }
        ],
    )

    assert response.groups[0].agency is None
    assert response.groups[0].organization is None
    assert response.groups[0].project_count == 1


def test_empty_inventory_has_zero_entries_and_no_groups():
    response = CatalogInfoResponse(total_count=0, groups=[])

    assert response.total_count == 0
    assert response.groups == []


def test_catalog_rejects_negative_total_count():
    with pytest.raises(ValidationError, match="total_count"):
        CatalogInfoResponse(total_count=-1, groups=[])
