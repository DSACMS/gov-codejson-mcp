"""Smoke tests for the Government Software Inventory MCP server."""

from __future__ import annotations

import pytest
from fastmcp import FastMCP

from example_server.app import mcp
from example_server.config import settings


def test_server_is_importable():
    assert mcp is not None


def test_server_has_name():
    assert mcp.name == "Government Software Inventory"


def test_default_transport_is_stdio():
    """Guard against accidentally shipping with a non-stdio default."""
    assert settings.mcp_transport == "stdio"


def test_tools_register_without_error():
    from example_server.tools import register_tools

    register_tools(FastMCP("test"))  # must not raise


@pytest.mark.asyncio
async def test_application_advertises_no_prompts():
    """Starter prompts should not appear in the application."""
    assert await mcp.list_prompts() == []


@pytest.mark.asyncio
async def test_application_advertises_no_resources():
    """Starter resources and templates should not appear."""
    assert await mcp.list_resources() == []
    assert await mcp.list_resource_templates() == []


def test_routes_register_without_error():
    from example_server.routes import register_routes

    register_routes(FastMCP("test"))  # must not raise


@pytest.mark.asyncio
async def test_starter_tools_are_not_discoverable():
    """The application should not advertise retired starter tools."""
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "example_search_datasets" not in tool_names
    assert "databricks_preview_table" not in tool_names
