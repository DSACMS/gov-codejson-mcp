from unittest.mock import MagicMock, call

import pytest

from example_server.project_comparison import compare_projects


def test_comparison_preserves_order_and_identifies_missing_entries():
    loader = MagicMock(
        side_effect=[
            {"entry_id": "second", "name": "Second Project"},
            None,
            {"entry_id": "first", "name": "First Project"},
        ]
    )

    response = compare_projects(
        ["second", "missing", "first"],
        project_loader=loader,
    )

    assert response.requested_entry_ids == ["second", "missing", "first"]
    assert [project.entry_id for project in response.projects] == [
        "second",
        "first",
    ]
    assert response.missing_entry_ids == ["missing"]
    assert loader.call_args_list == [
        call("second"),
        call("missing"),
        call("first"),
    ]


def test_comparison_reports_when_all_entries_are_missing():
    loader = MagicMock(return_value=None)

    response = compare_projects(
        ["missing-one", "missing-two"],
        project_loader=loader,
    )

    assert response.projects == []
    assert response.missing_entry_ids == ["missing-one", "missing-two"]


@pytest.mark.parametrize(
    "entry_ids",
    [
        [],
        ["one"],
        ["one", "two", "three", "four", "five", "six"],
        ["one", "one"],
        ["one", " "],
    ],
)
def test_invalid_requests_do_not_call_reader(entry_ids):
    loader = MagicMock()

    with pytest.raises(ValueError):
        compare_projects(entry_ids, project_loader=loader)

    loader.assert_not_called()


def test_reader_failure_is_not_treated_as_a_missing_entry():
    loader = MagicMock(side_effect=RuntimeError("Warehouse unavailable"))

    with pytest.raises(RuntimeError, match="Warehouse unavailable"):
        compare_projects(["one", "two"], project_loader=loader)


def test_unexpected_returned_id_is_rejected():
    loader = MagicMock(return_value={"entry_id": "different-entry"})

    with pytest.raises(ValueError, match="unexpected entry ID"):
        compare_projects(["one", "two"], project_loader=loader)
