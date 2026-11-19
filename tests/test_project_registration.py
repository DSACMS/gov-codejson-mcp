from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP

from example_server import warehouse
from example_server.config import Settings
from example_server.models import ProjectDetail
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
    assert "databricks_preview_table" not in names
    assert "example_search_datasets" not in names
    connect_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_search_registration_is_independent_of_lookup(
    monkeypatch,
    enabled,
):
    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=False,
        govcode_project_search_enabled=enabled,
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
    assert ("govcode_search_projects" in names) == enabled
    assert "govcode_get_project" not in names
    connect_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_catalog_registration_is_independent(
    monkeypatch,
    enabled,
):
    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=False,
        govcode_project_search_enabled=False,
        govcode_catalog_info_enabled=enabled,
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
    assert ("govcode_catalog_info" in names) == enabled
    assert "govcode_get_project" not in names
    assert "govcode_search_projects" not in names
    connect_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_comparison_registration_is_independent(
    monkeypatch,
    enabled,
):
    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=False,
        govcode_project_search_enabled=False,
        govcode_catalog_info_enabled=False,
        govcode_project_compare_enabled=enabled,
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
    assert ("govcode_compare_projects" in names) == enabled
    assert "govcode_get_project" not in names
    assert "govcode_search_projects" not in names
    assert "govcode_catalog_info" not in names
    connect_mock.assert_not_called()


@pytest.mark.asyncio
async def test_registered_lookup_uses_legacy_layout(monkeypatch):
    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=True,
        govcode_project_search_enabled=False,
        govcode_catalog_info_enabled=False,
        govcode_project_compare_enabled=False,
        govcode_project_catalog="test_catalog",
        govcode_project_schema="test_schema",
        govcode_project_table="test_legacy",
        govcode_project_dataset_format="legacy",
    )

    connect_mock = MagicMock()
    connection = connect_mock.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.description = [
        ("entry_id",),
        ("name",),
        ("permissions_usageType",),
        ("languages",),
    ]
    cursor.fetchall.return_value = [
        ("entry-001", "Example Project", "openSource", "Python|Shell")
    ]
    monkeypatch.setattr(warehouse, "connect", connect_mock)

    server = FastMCP("test")
    register_tools(server, config=config)

    async with Client(server) as client:
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "entry-001"},
        )

    assert result.structured_content is not None
    detail = ProjectDetail.model_validate(result.structured_content)
    assert detail.entry_id == "entry-001"
    assert detail.usageType == "openSource"
    assert detail.languages == ["Python", "Shell"]

    arguments = cursor.execute.call_args
    assert "WHERE entry_id = ?" in arguments.args[0]
    assert "permissions_usageType" in arguments.args[0]
    assert arguments.kwargs["parameters"] == ["entry-001"]
