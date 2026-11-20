from datetime import date
from functools import partial
from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP

from example_server import warehouse
from example_server.tools import project_tool
from example_server.warehouse_project_reader import get_project_from_warehouse


@pytest.mark.asyncio
async def test_tool_returns_project_from_warehouse_reader(monkeypatch):
    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    cursor.description = [
        ("entry_id",),
        ("agency",),
        ("organization",),
        ("name",),
        ("description",),
        ("repositoryURL",),
        ("licenses",),
        ("tags",),
        ("languages",),
        ("laborHours",),
        ("dateCreated",),
        ("dateLastModified",),
        ("dateMetadataLastUpdated",),
    ]
    cursor.fetchall.return_value = [
        (
            "1006",
            "VA",
            "Example VA Office",
            "Example Document Toolkit",
            None,
            "https://example.org/document-toolkit",
            "MIT",
            "documents; accessibility",
            "Python; JavaScript",
            0,
            date(2024, 3, 1),
            None,
            date(2025, 6, 15),
        )
    ]

    monkeypatch.setattr(warehouse, "connect", connect_mock)

    server = FastMCP("test")
    project_tool.register(
        server,
        project_loader=partial(
            get_project_from_warehouse,
            catalog="test_catalog",
            schema="test_schema",
            table="test_projects",
        ),
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "1006"},
        )

    data = result.structured_content
    assert data is not None
    assert data["entry_id"] == "1006"
    assert data["agency"] == "VA"
    assert data["organization"] == "Example VA Office"
    assert data["name"] == "Example Document Toolkit"
    assert data["description"] is None
    assert data["tags"] == ["documents", "accessibility"]
    assert data["languages"] == ["Python", "JavaScript"]
    assert data["licenses"] == [{"name": "MIT", "url": None}]
    assert data["laborHours"] == 0
    assert data["dateCreated"] == "2024-03-01"
    assert data["dateLastModified"] is None
    assert data["dateMetadataLastUpdated"] == "2025-06-15"

    connect_mock.assert_called_once_with()
    cursor.execute.assert_called_once()
    arguments = cursor.execute.call_args
    assert arguments.kwargs["parameters"] == ["1006"]
    assert "`test_catalog`.`test_schema`.`test_projects`" in arguments.args[0]
