from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.errors import DuplicateProjectError
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
        side_effect=DuplicateProjectError("Duplicate entry_id in warehouse")
    )
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="inventory needs correction"):
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "duplicate"},
            )

    loader.assert_called_once_with("duplicate")


@pytest.mark.asyncio
async def test_warehouse_failure_is_not_reported_as_missing():
    loader = MagicMock(
        side_effect=RuntimeError(
            "Warehouse unavailable; internal-detail=fictional-secret"
        )
    )
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        with pytest.raises(ToolError) as error:
            await client.call_tool(
                "govcode_get_project",
                {"entry_id": "1006"},
            )

    message = str(error.value)
    assert "Project lookup failed. Please try again later." in message
    assert "Project entry not found" not in message
    assert "fictional-secret" not in message
    assert "internal-detail" not in message
    loader.assert_called_once_with("1006")


@pytest.mark.asyncio
async def test_invalid_project_returns_controlled_error():
    loader = MagicMock(
        return_value={
            "entry_id": "invalid-project",
            "languages": {"internal-detail": "fictional-secret"},
        }
    )
    server = FastMCP("test")
    project_tool.register(server, project_loader=loader)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "invalid-project"},
            raise_on_error=False,
        )

    assert result.is_error
    messages = "\n".join(
        block.text for block in result.content if block.type == "text"
    )
    assert "Project lookup failed. Please try again later." in messages
    assert "fictional-secret" not in messages
    assert "internal-detail" not in messages
    loader.assert_called_once_with("invalid-project")