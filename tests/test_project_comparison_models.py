import pytest
from pydantic import ValidationError

from example_server.models import ProjectComparisonResponse


def test_comparison_preserves_entries_sharing_a_repository():
    response = ProjectComparisonResponse(
        requested_entry_ids=["entry-001", "entry-002"],
        projects=[
            {
                "entry_id": "entry-001",
                "name": "First Inventory Entry",
                "repositoryURL": "https://example.org/shared-repository",
                "laborHours": 0,
            },
            {
                "entry_id": "entry-002",
                "name": "Second Inventory Entry",
                "repositoryURL": "https://example.org/shared-repository",
                "laborHours": None,
            },
        ],
        missing_entry_ids=[],
    )

    assert len(response.projects) == 2
    assert response.projects[0].entry_id != response.projects[1].entry_id
    assert response.projects[0].laborHours == 0
    assert response.projects[1].laborHours is None


def test_comparison_identifies_missing_entries():
    response = ProjectComparisonResponse(
        requested_entry_ids=["entry-001", "missing"],
        projects=[{"entry_id": "entry-001"}],
        missing_entry_ids=["missing"],
    )

    assert response.requested_entry_ids == ["entry-001", "missing"]
    assert response.missing_entry_ids == ["missing"]
    assert len(response.projects) == 1


@pytest.mark.parametrize(
    "entry_ids",
    [
        ["only-one"],
        ["one", "two", "three", "four", "five", "six"],
    ],
)
def test_comparison_requires_two_to_five_requested_entries(entry_ids):
    with pytest.raises(ValidationError, match="requested_entry_ids"):
        ProjectComparisonResponse(
            requested_entry_ids=entry_ids,
            projects=[],
            missing_entry_ids=entry_ids,
        )
