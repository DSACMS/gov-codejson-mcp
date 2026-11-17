from datetime import date
from unittest.mock import MagicMock

import pytest

from example_server import warehouse
from example_server.warehouse_project_reader import get_project_from_warehouse

TABLE_SETTINGS = {
    "catalog": "test_catalog",
    "schema": "test_schema",
    "table": "test_projects",
}


@pytest.fixture
def cursor_mock(monkeypatch):
    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.description = [
        ("entry_id",),
        ("tags",),
        ("languages",),
        ("licenses",),
        ("dateCreated",),
    ]
    monkeypatch.setattr(warehouse, "connect", connect_mock)
    return cursor


def test_returns_converted_project(cursor_mock):
    cursor_mock.fetchall.return_value = [
        (
            "1006",
            "documents; accessibility",
            "Python; JavaScript",
            "MIT",
            date(2024, 3, 1),
        )
    ]

    project = get_project_from_warehouse("1006", **TABLE_SETTINGS)

    assert project is not None
    assert project["entry_id"] == "1006"
    assert project["tags"] == ["documents", "accessibility"]
    assert project["languages"] == ["Python", "JavaScript"]
    assert project["licenses"] == [{"name": "MIT", "url": None}]
    assert project["dateCreated"] == "2024-03-01"

    cursor_mock.execute.assert_called_once()
    arguments = cursor_mock.execute.call_args
    query = arguments.args[0]
    assert "`test_catalog`.`test_schema`.`test_projects`" in query
    assert "WHERE CAST(id AS STRING) = ?" in query
    assert arguments.kwargs["parameters"] == ["1006"]
    assert "contact" not in query.lower()
    assert "SELECT *" not in query.upper()


def test_unknown_id_returns_none(cursor_mock):
    cursor_mock.fetchall.return_value = []

    project = get_project_from_warehouse("unknown", **TABLE_SETTINGS)

    assert project is None


def test_duplicate_id_raises_error(cursor_mock):
    row = ("1006", None, None, None, None)
    cursor_mock.fetchall.return_value = [row, row]

    with pytest.raises(ValueError, match="Duplicate entry_id in warehouse"):
        get_project_from_warehouse("1006", **TABLE_SETTINGS)


def test_entry_id_is_passed_as_a_parameter(cursor_mock):
    cursor_mock.fetchall.return_value = []
    entry_id = "1006' OR 1=1 --"

    get_project_from_warehouse(entry_id, **TABLE_SETTINGS)

    arguments = cursor_mock.execute.call_args
    assert entry_id not in arguments.args[0]
    assert arguments.kwargs["parameters"] == [entry_id]
