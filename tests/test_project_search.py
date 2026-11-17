from unittest.mock import MagicMock

import pytest

from example_server import warehouse
from example_server.project_search import (
    build_search_filters,
    search_projects,
)


def test_no_filters_searches_entire_inventory():
    filters, where_clause, parameters = build_search_filters()

    assert filters.model_dump() == {
        "query": None,
        "agency": None,
        "organization": None,
    }
    assert where_clause == ""
    assert parameters == []


def test_filters_preserve_values_and_bind_them_separately():
    filters, where_clause, parameters = build_search_filters(
        query=" documents ",
        agency=" HHS ",
        organization=" CMS ",
    )

    assert filters.query == "documents"
    assert filters.agency == "HHS"
    assert filters.organization == "CMS"
    assert parameters == ["documents", "documents", "HHS", "CMS"]
    assert "OR contains" in where_clause
    assert "AND agency = ?" in where_clause
    assert "AND organization = ?" in where_clause
    assert "documents" not in where_clause
    assert "HHS" not in where_clause


def test_blank_filters_become_no_restriction():
    filters, where_clause, parameters = build_search_filters(
        query=" ",
        agency="",
        organization="\t",
    )

    assert filters.query is None
    assert filters.agency is None
    assert filters.organization is None
    assert where_clause == ""
    assert parameters == []


def test_special_characters_remain_parameter_values():
    query = "100%_coverage' OR 1=1 --"

    filters, where_clause, parameters = build_search_filters(query=query)

    assert filters.query == query
    assert parameters == [query, query]
    assert query not in where_clause
    assert "LIKE" not in where_clause.upper()


def test_search_counts_all_matches_and_returns_one_page(monkeypatch):
    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (25,)
    cursor.description = [
        ("entry_id",),
        ("name",),
        ("languages",),
    ]
    cursor.fetchall.return_value = [
        ("1006", "Example Project", "Python; JavaScript"),
    ]
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    response = search_projects(
        catalog="test_catalog",
        schema="test_schema",
        table="test_projects",
        query="documents",
        agency="VA",
        limit=1,
        offset=2,
    )

    assert response.total_count == 25
    assert len(response.results) == 1
    assert response.results[0].entry_id == "1006"
    assert response.results[0].languages == ["Python", "JavaScript"]
    assert response.applied_filters.query == "documents"
    assert response.applied_filters.agency == "VA"
    assert response.has_more is True
    assert response.offset == 2

    assert cursor.execute.call_count == 2
    count_call, page_call = cursor.execute.call_args_list
    assert "COUNT(*)" in count_call.args[0]
    assert "LIMIT" not in count_call.args[0]
    assert count_call.kwargs["parameters"] == [
        "documents", "documents", "VA",
    ]
    assert page_call.kwargs["parameters"] == [
        "documents", "documents", "VA", 1, 2,
    ]

    _, where_clause, _ = build_search_filters(
        query="documents",
        agency="VA",
    )
    assert where_clause in count_call.args[0]
    assert where_clause in page_call.args[0]

@pytest.mark.parametrize(
    ("total_count", "offset", "rows"),
    [
        (0, 0, []),
        (3, 2, [("last-entry",)]),
        (3, 3, []),
        (3, 5, []),
    ],
)
def test_search_handles_page_boundaries(
    monkeypatch,
    total_count,
    offset,
    rows,
):
    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (total_count,)
    cursor.description = [("entry_id",)]
    cursor.fetchall.return_value = rows
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    response = search_projects(
        catalog="test_catalog",
        schema="test_schema",
        table="test_projects",
        limit=2,
        offset=offset,
    )

    assert response.total_count == total_count
    assert len(response.results) == len(rows)
    assert response.offset == offset
    assert response.has_more is False


@pytest.mark.parametrize(
    "pagination",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_invalid_pagination_does_not_connect(monkeypatch, pagination):
    connect_mock = MagicMock()
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    with pytest.raises(ValueError):
        search_projects(
            catalog="test_catalog",
            schema="test_schema",
            table="test_projects",
            **pagination,
        )

    connect_mock.assert_not_called()
