from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP

from example_server.models import CatalogInfoResponse
from example_server.tools import catalog_tool


@pytest.mark.asyncio
async def test_catalog_returns_coverage_and_unknown_provenance():
    loader = MagicMock(
        return_value=CatalogInfoResponse(
            total_count=3,
            groups=[
                {
                    "agency": "HHS",
                    "organization": "CMS",
                    "project_count": 2,
                },
                {
                    "agency": None,
                    "organization": None,
                    "project_count": 1,
                },
            ],
        )
    )
    server = FastMCP("test")
    catalog_tool.register(server, catalog_loader=loader)

    async with Client(server) as client:
        result = await client.call_tool("govcode_catalog_info", {})

    data = result.structured_content
    assert data is not None
    assert data["total_count"] == 3
    assert data["groups"][0] == {
        "agency": "HHS",
        "organization": "CMS",
        "project_count": 2,
    }
    assert data["groups"][1]["agency"] is None
    assert data["groups"][1]["organization"] is None
    assert data["dataset_version"] is None
    assert data["dataset_updated_at"] is None
    loader.assert_called_once_with()


@pytest.mark.asyncio
async def test_catalog_failure_returns_controlled_error():
    loader = MagicMock(side_effect=RuntimeError("internal-detail=fictional-secret"))
    server = FastMCP("test")
    catalog_tool.register(server, catalog_loader=loader)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_catalog_info",
            {},
            raise_on_error=False,
        )

    assert result.is_error
    messages = "\n".join(block.text for block in result.content if block.type == "text")
    assert "Catalog information could not be retrieved." in messages
    assert "fictional-secret" not in messages
    loader.assert_called_once_with()
