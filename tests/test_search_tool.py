from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.models import ProjectSearchFilters, ProjectSearchResponse
from example_server.tools import search_tool


@pytest.mark.asyncio
async def test_search_returns_page_and_forwards_filters():
    searcher = MagicMock(
        return_value=ProjectSearchResponse(
            results=[
                {
                    "entry_id": "example-001",
                    "agency": "HHS",
                    "organization": "CMS",
                    "name": "Example Project",
                }
            ],
            total_count=12,
            applied_filters=ProjectSearchFilters(
                query="documents",
                agency="HHS",
                organization="CMS",
            ),
            limit=1,
            offset=2,
            has_more=True,
        )
    )
    server = FastMCP("test")
    search_tool.register(server, project_searcher=searcher)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_search_projects",
            {
                "query": "documents",
                "agency": "HHS",
                "organization": "CMS",
                "limit": 1,
                "offset": 2,
            },
        )

    data = result.structured_content
    assert data is not None
    assert data["total_count"] == 12
    assert len(data["results"]) == 1
    assert data["results"][0]["entry_id"] == "example-001"
    assert data["results"][0]["description"] is None
    assert data["applied_filters"]["organization"] == "CMS"
    assert data["has_more"] is True
    searcher.assert_called_once_with(
        query="documents",
        agency="HHS",
        organization="CMS",
        limit=1,
        offset=2,
    )


@pytest.mark.asyncio
async def test_search_returns_controlled_failure():
    searcher = MagicMock(side_effect=RuntimeError("internal-detail=fictional-secret"))
    server = FastMCP("test")
    search_tool.register(server, project_searcher=searcher)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_search_projects",
            {"query": "documents"},
            raise_on_error=False,
        )

    assert result.is_error
    messages = "\n".join(block.text for block in result.content if block.type == "text")
    assert "Project search failed. Please try again later." in messages
    assert "fictional-secret" not in messages


@pytest.mark.asyncio
@pytest.mark.parametrize("arguments", [{"limit": 101}, {"offset": -1}])
async def test_invalid_pagination_does_not_call_searcher(arguments):
    searcher = MagicMock()
    server = FastMCP("test")
    search_tool.register(server, project_searcher=searcher)

    async with Client(server) as client:
        with pytest.raises(ToolError):
            await client.call_tool("govcode_search_projects", arguments)

    searcher.assert_not_called()
