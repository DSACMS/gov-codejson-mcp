from unittest.mock import MagicMock

import pytest

from example_server import warehouse
from example_server.catalog_reader import get_catalog_info


@pytest.mark.parametrize(
    ("rows", "expected_total"),
    [
        (
            [
                ("HHS", "CMS", 2),
                ("HHS", "CDC", 1),
                ("VA", None, 4),
            ],
            7,
        ),
        ([(None, None, 2)], 2),
        ([], 0),
    ],
)
def test_catalog_counts_all_groups(monkeypatch, rows, expected_total):
    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.description = [
        ("agency",),
        ("organization",),
        ("project_count",),
    ]
    cursor.fetchall.return_value = rows
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    response = get_catalog_info(
        catalog="test_catalog",
        schema="test_schema",
        table="test_projects",
    )

    assert response.total_count == expected_total
    assert [
        (group.agency, group.organization, group.project_count)
        for group in response.groups
    ] == rows
    assert response.dataset_version is None
    assert response.dataset_updated_at is None

    connect_mock.assert_called_once_with()
    cursor.execute.assert_called_once()
    query = cursor.execute.call_args.args[0]
    assert "`test_catalog`.`test_schema`.`test_projects`" in query
    assert "COUNT(*) AS project_count" in query
    assert "GROUP BY agency, organization" in query
    assert "LIMIT" not in query.upper()
    assert "WHERE" not in query.upper()
    assert "contact" not in query.lower()
