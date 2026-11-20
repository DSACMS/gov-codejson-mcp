from functools import partial
from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.project_comparison import compare_projects
from example_server.tools import compare_tool


def build_server(loader):
    server = FastMCP("test")
    compare_tool.register(
        server,
        project_comparer=partial(compare_projects, project_loader=loader),
    )
    return server


@pytest.mark.asyncio
async def test_comparison_returns_evidence_and_missing_ids():
    loader = MagicMock(
        side_effect=[
            {"entry_id": "one", "laborHours": 0},
            None,
            {"entry_id": "two", "laborHours": None},
        ]
    )
    server = build_server(loader)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_compare_projects",
            {"entry_ids": ["one", "missing", "two"]},
        )

    data = result.structured_content
    assert data is not None
    assert data["requested_entry_ids"] == ["one", "missing", "two"]
    assert data["missing_entry_ids"] == ["missing"]
    assert [project["entry_id"] for project in data["projects"]] == [
        "one",
        "two",
    ]
    assert data["projects"][0]["laborHours"] == 0
    assert data["projects"][1]["laborHours"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entry_ids",
    [
        ["one"],
        ["one", "two", "three", "four", "five", "six"],
        ["one", "one"],
        ["one", " "],
    ],
)
async def test_invalid_comparison_does_not_call_reader(entry_ids):
    loader = MagicMock()
    server = build_server(loader)

    async with Client(server) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "govcode_compare_projects",
                {"entry_ids": entry_ids},
            )

    loader.assert_not_called()


@pytest.mark.asyncio
async def test_comparison_returns_controlled_reader_failure():
    loader = MagicMock(side_effect=RuntimeError("internal-detail=fictional-secret"))
    server = build_server(loader)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_compare_projects",
            {"entry_ids": ["one", "two"]},
            raise_on_error=False,
        )

    assert result.is_error
    messages = "\n".join(block.text for block in result.content if block.type == "text")
    assert "Project comparison failed. Please try again later." in messages
    assert "fictional-secret" not in messages
