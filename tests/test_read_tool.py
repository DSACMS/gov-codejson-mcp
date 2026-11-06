from unittest.mock import MagicMock

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from example_server.tools import read_tool


@pytest.mark.asyncio
async def test_invalid_limit_does_not_connect(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")

    connect_mock = MagicMock()
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        with pytest.raises(ToolError, match="limit must be between 1 and 100"):
            await client.call_tool(
                "databricks_preview_table",
                {"limit": 0},
            )

    connect_mock.assert_not_called()

@pytest.mark.asyncio
async def test_preview_returns_project_rows(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")
    monkeypatch.setenv("DATABRICKS_READER_AUTH_MODE", "local")

    fetch_result = {
        "columns": ["agency", "name", "description", "repository_url", "languages"],
        "rows": [
            ["Agency1", "Project1", "Description1", "http://repo1", ["Python"]],
            ["Agency2", "Project2", "Description2", "http://repo2", ["Java"]],
        ],
    }

    connect_mock = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.description = [(col,) for col in fetch_result["columns"]]
    cursor_mock.fetchall.return_value = [tuple(row) for row in fetch_result["rows"]]
    connection_mock = connect_mock.return_value.__enter__.return_value
    cursor_context = connection_mock.cursor.return_value
    cursor_context.__enter__.return_value = cursor_mock
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)
    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        result = await client.call_tool(
            "databricks_preview_table",
            {"limit": 2},
        )

    assert result.data == fetch_result

    connect_mock.assert_called_once()
    connection_arguments = connect_mock.call_args.kwargs
    assert connection_arguments["auth_type"] == "databricks-oauth"
    assert "credentials_provider" not in connection_arguments

    cursor_mock.execute.assert_called_once()
    executed_sql = cursor_mock.execute.call_args.args[0]
    assert executed_sql.split()[-2:] == ["LIMIT", "2"]

@pytest.mark.asyncio
async def test_preview_returns_empty_rows(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")

    fetch_result = {
        "columns": ["agency", "name", "description", "repository_url", "languages"],
        "rows": [],
    }

    connect_mock = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.description = [(col,) for col in fetch_result["columns"]]
    cursor_mock.fetchall.return_value = []
    connection_mock = connect_mock.return_value.__enter__.return_value
    cursor_context = connection_mock.cursor.return_value
    cursor_context.__enter__.return_value = cursor_mock
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        result = await client.call_tool(
            "databricks_preview_table",
            {"limit": 2},
        )

    assert result.data == fetch_result

    cursor_mock.execute.assert_called_once()
    executed_sql = cursor_mock.execute.call_args.args[0]
    assert executed_sql.split()[-2:] == ["LIMIT", "2"]

@pytest.mark.asyncio
async def test_preview_selects_hhs(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")

    fetch_result = {
        "columns": ["agency", "name", "description", "repository_url", "languages"],
        "rows": [
            ["HHS", "ProjectHHS", "DescriptionHHS", "http://repoHHS", ["Python"]],
        ],
    }

    connect_mock = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.description = [(col,) for col in fetch_result["columns"]]
    cursor_mock.fetchall.return_value = [tuple(row) for row in fetch_result["rows"]]
    connection_mock = connect_mock.return_value.__enter__.return_value
    cursor_context = connection_mock.cursor.return_value
    cursor_context.__enter__.return_value = cursor_mock
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        result = await client.call_tool(
            "databricks_preview_table",
            {"limit": 2, "agency": "HHS"},
        )

    assert result.data == fetch_result

    cursor_mock.execute.assert_called_once()
    executed_sql = cursor_mock.execute.call_args.args[0]
    assert "raw.`HHS`.agency AS agency" in executed_sql
    assert "explode(raw.`HHS`.releases)" in executed_sql
    assert "raw.GSA" not in executed_sql
    assert "raw.`GSA`" not in executed_sql
    assert executed_sql.split()[-2:] == ["LIMIT", "2"]

@pytest.mark.asyncio
async def test_invalid_agency_does_not_connect(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")

    connect_mock = MagicMock()
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        with pytest.raises(
            ToolError,
            match="agency must match a supported agency abbreviation",
        ):
            await client.call_tool(
                "databricks_preview_table",
                {"limit": 2, "agency": "UNKNOWN"},
            )

    connect_mock.assert_not_called()

@pytest.mark.asyncio
async def test_preview_selects_ssa_without_languages(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")

    fetch_result = {
        "columns": ["agency", "name", "description", "repository_url", "languages"],
        "rows": [
            ["SSA", "ProjectSSA", "DescriptionSSA", "http://repoSSA", None],
        ],
    }

    connect_mock = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.description = [(col,) for col in fetch_result["columns"]]
    cursor_mock.fetchall.return_value = [tuple(row) for row in fetch_result["rows"]]
    connection_mock = connect_mock.return_value.__enter__.return_value
    cursor_context = connection_mock.cursor.return_value
    cursor_context.__enter__.return_value = cursor_mock
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        result = await client.call_tool(
            "databricks_preview_table",
            {"limit": 2, "agency": "SSA"},
        )

    assert result.data == fetch_result

    cursor_mock.execute.assert_called_once()
    executed_sql = cursor_mock.execute.call_args.args[0]
    assert "raw.`SSA`.agency AS agency" in executed_sql
    assert "explode(raw.`SSA`.releases)" in executed_sql
    assert "NULL AS languages" in executed_sql
    assert "projects.project.languages" not in executed_sql
    assert executed_sql.split()[-2:] == ["LIMIT", "2"]

@pytest.mark.asyncio
async def test_app_mode_uses_credentials_provider(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")
    monkeypatch.setenv("DATABRICKS_READER_AUTH_MODE", "app")

    provider_mock = MagicMock()
    monkeypatch.setattr(
        read_tool,
        "app_credentials_provider",
        provider_mock,
    )

    fetch_result = {
        "columns": ["agency", "name", "description", "repository_url", "languages"],
        "rows": [
            ["HHS", "ProjectHHS", "DescriptionHHS", "http://repoHHS", ["Python"]],
        ],
    }

    connect_mock = MagicMock()
    cursor_mock = MagicMock()
    cursor_mock.description = [(col,) for col in fetch_result["columns"]]
    cursor_mock.fetchall.return_value = [tuple(row) for row in fetch_result["rows"]]
    connection_mock = connect_mock.return_value.__enter__.return_value
    cursor_context = connection_mock.cursor.return_value
    cursor_context.__enter__.return_value = cursor_mock
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        result = await client.call_tool(
            "databricks_preview_table",
            {"limit": 2, "agency": "HHS"},
        )

    connect_mock.assert_called_once()
    connection_arguments = connect_mock.call_args.kwargs
    assert connection_arguments["credentials_provider"] is provider_mock
    assert "auth_type" not in connection_arguments

    assert result.data == fetch_result

    cursor_mock.execute.assert_called_once()
    executed_sql = cursor_mock.execute.call_args.args[0]
    assert "raw.`HHS`.agency AS agency" in executed_sql
    assert "explode(raw.`HHS`.releases)" in executed_sql
    assert "raw.GSA" not in executed_sql
    assert "raw.`GSA`" not in executed_sql
    assert executed_sql.split()[-2:] == ["LIMIT", "2"]

@pytest.mark.asyncio
async def test_invalid_auth_mode_does_not_connect(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/test")
    monkeypatch.setenv("DATABRICKS_CATALOG", "test_catalog")
    monkeypatch.setenv("DATABRICKS_SCHEMA", "test_schema")
    monkeypatch.setenv("DATABRICKS_TABLE", "test_table")
    monkeypatch.setenv("DATABRICKS_READER_AUTH_MODE", "unsupported")

    connect_mock = MagicMock()
    monkeypatch.setattr(read_tool.sql, "connect", connect_mock)

    server = FastMCP("test")
    read_tool.register(server)

    async with Client(server) as client:
        with pytest.raises(
            ToolError,
            match="DATABRICKS_READER_AUTH_MODE must be local or app"
        ):
            await client.call_tool(
                "databricks_preview_table",
                {"limit": 2, "agency": "GSA"},
            )

    connect_mock.assert_not_called()

def test_app_credentials_provider_uses_runtime_settings(monkeypatch):
    monkeypatch.setenv("DATABRICKS_SERVER_HOSTNAME", "example.invalid")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "fictional-client-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "fictional-client-secret")

    config_mock = MagicMock()
    config_factory = MagicMock(return_value=config_mock)
    oauth_factory = MagicMock()

    monkeypatch.setattr(read_tool, "Config", config_factory)
    monkeypatch.setattr(
        read_tool,
        "oauth_service_principal",
        oauth_factory,
    )

    provider = read_tool.app_credentials_provider()

    config_factory.assert_called_once_with(
        host="https://example.invalid",
        client_id="fictional-client-id",
        client_secret="fictional-client-secret",
    )
    oauth_factory.assert_called_once_with(config_mock)
    assert provider is oauth_factory.return_value
