from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.tools import project_tool


@pytest.mark.asyncio
async def test_missing_project_returns_not_found():
    loader = MagicMock(return_value=None)
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="Project entry not found"):
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "missing"},
            )

    loader.assert_called_once_with("missing")


@pytest.mark.asyncio
async def test_duplicate_project_returns_error():
    loader = MagicMock(
        side_effect=ValueError("Duplicate entry_id in warehouse")
    )
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="Duplicate entry_id"):
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "duplicate"},
            )

    loader.assert_called_once_with("duplicate")


@pytest.mark.asyncio
async def test_warehouse_failure_is_not_reported_as_missing():
    loader = MagicMock(
        side_effect=RuntimeError("Warehouse temporarily unavailable")
    )
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        with pytest.raises(ToolError) as error:
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "1006"},
            )

    assert "Project entry not found" not in str(error.value)
    loader.assert_called_once_with("1006")
