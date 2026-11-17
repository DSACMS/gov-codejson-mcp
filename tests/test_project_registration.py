from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP

from example_server import warehouse
from example_server.config import Settings
from example_server.tools import register_tools


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_project_registration_follows_enable_setting(
    monkeypatch,
    enabled,
):
    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=enabled,
        govcode_project_catalog="test_catalog",
        govcode_project_schema="test_schema",
        govcode_project_table="test_projects",
    )
    connect_mock = MagicMock()
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    server = FastMCP("test")
    register_tools(server, config=config)

    async with Client(server) as client:
        tools = await client.list_tools()

    names = {tool.name for tool in tools}

    assert ("govcode_get_project" in names) == enabled
    assert "databricks_preview_table" in names
    assert "example_search_datasets" in names
    connect_mock.assert_not_called()
