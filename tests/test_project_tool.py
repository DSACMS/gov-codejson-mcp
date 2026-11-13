import json
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.tools import project_tool

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "projects.json"


@pytest.mark.asyncio
async def test_get_project_returns_converted_fields():
    server = FastMCP("test")
    project_tool.register(server, fixture_path=FIXTURE_PATH)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "mock-001"},
        )

    assert result.structured_content["entry_id"] == "mock-001"
    assert result.structured_content["tags"] == ["documents", "accessibility"]
    assert result.structured_content["languages"] == ["Python", "JavaScript"]
    assert result.structured_content["licenses"] == [{"name": "MIT", "url": None}]
    assert result.structured_content["laborHours"] == 0
    assert result.structured_content["dateCreated"] == "2024-03-01"
    assert (
        result.structured_content["dateMetadataLastUpdated"]
        == "2025-06-15T14:30:00Z"
    )


@pytest.mark.asyncio
async def test_get_project_preserves_nulls():
    server = FastMCP("test")
    project_tool.register(server, fixture_path=FIXTURE_PATH)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "mock-002"},
        )

    assert result.structured_content["description"] is None
    assert result.structured_content["tags"] is None
    assert result.structured_content["languages"] is None
    assert result.structured_content["licenses"] is None
    assert result.structured_content["laborHours"] is None


@pytest.mark.asyncio
async def test_get_project_unknown_id_returns_error():
    server = FastMCP("test")
    project_tool.register(server, fixture_path=FIXTURE_PATH)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="Project entry not found"):
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "unknown"},
            )


@pytest.mark.asyncio
async def test_get_project_excludes_contact_fields(tmp_path):
    fixture_path = tmp_path / "projects.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "entry_id": "mock-contact",
                    "name": "Example Project",
                    "contactName": "Example Contact",
                    "contactEmail": "contact@example.org",
                    "contactPhone": "example-phone",
                    "contactURL": "https://example.org/contact",
                }
            ]
        ),
        encoding="utf-8",
    )

    server = FastMCP("test")
    project_tool.register(server, fixture_path=fixture_path)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "mock-contact"},
        )

    assert result.structured_content["entry_id"] == "mock-contact"
    assert not any(key.startswith("contact") for key in result.structured_content)
    assert "contact@example.org" not in json.dumps(result.structured_content)

    for block in result.content:
        if block.type == "text":
            assert "contact@example.org" not in block.text