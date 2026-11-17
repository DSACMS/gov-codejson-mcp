import pytest
from pydantic import ValidationError

from example_server.models import (
    ProjectSearchFilters,
    ProjectSearchResponse,
)


def test_search_response_separates_page_from_total_count():
    response = ProjectSearchResponse(
        results=[
            {"entry_id": "example-001", "name": "Example Project"},
        ],
        total_count=25,
        applied_filters=ProjectSearchFilters(query="documents"),
        limit=1,
        offset=0,
        has_more=True,
    )

    data = response.model_dump()

    assert len(data["results"]) == 1
    assert data["total_count"] == 25
    assert data["has_more"] is True
    assert data["applied_filters"] == {
        "query": "documents",
        "agency": None,
        "organization": None,
    }
    assert data["results"][0]["description"] is None


def test_empty_search_response_preserves_filters():
    response = ProjectSearchResponse(
        results=[],
        total_count=0,
        applied_filters=ProjectSearchFilters(
            query="documents",
            agency="HHS",
            organization="CMS",
        ),
        has_more=False,
    )

    assert response.results == []
    assert response.total_count == 0
    assert response.limit == 10
    assert response.offset == 0
    assert response.applied_filters.agency == "HHS"
    assert response.applied_filters.organization == "CMS"


@pytest.mark.parametrize("limit", [0, 101])
def test_search_response_rejects_out_of_range_limits(limit):
    with pytest.raises(ValidationError, match="limit"):
        ProjectSearchResponse(
            results=[],
            total_count=0,
            applied_filters=ProjectSearchFilters(),
            limit=limit,
            has_more=False,
        )

