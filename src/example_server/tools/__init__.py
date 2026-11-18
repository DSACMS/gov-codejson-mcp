"""Tools submodule — one tool per file.

Each tool module (e.g. `example_tool.py`) exposes a `register(mcp)` function
that attaches its `@mcp.tool`-decorated function to the server. This file
aggregates them into a single `register_tools(mcp)` that `app.py` calls.

To add a tool:
  1. Create `tools/<your_tool>.py` with a `register(mcp)` function.
  2. Import it below and call `<your_tool>.register(mcp)` inside register_tools.
"""

from __future__ import annotations

from functools import partial

from example_server.catalog_reader import get_catalog_info
from example_server.config import Settings, settings
from example_server.project_comparison import compare_projects
from example_server.project_search import search_projects
from example_server.tools import (
    catalog_tool,
    compare_tool,
    example_tool,
    project_tool,
    read_tool,
    search_tool,
)
from example_server.warehouse_project_reader import get_project_from_warehouse


def register_tools(mcp, *, config: Settings | None = None) -> None:
    """Register tools, including project lookup when explicitly enabled."""
    active_settings = settings if config is None else config

    example_tool.register(mcp)
    read_tool.register(mcp)

    if active_settings.govcode_project_lookup_enabled:
        project_tool.register(
            mcp,
            project_loader=partial(
                get_project_from_warehouse,
                dataset_format=active_settings.govcode_project_dataset_format,
                catalog=active_settings.govcode_project_catalog,
                schema=active_settings.govcode_project_schema,
                table=active_settings.govcode_project_table,
            ),
        )

    if active_settings.govcode_project_search_enabled:
        search_tool.register(
            mcp,
            project_searcher=partial(
                search_projects,
                dataset_format=active_settings.govcode_project_dataset_format,
                catalog=active_settings.govcode_project_catalog,
                schema=active_settings.govcode_project_schema,
                table=active_settings.govcode_project_table,
            ),
        )

    if active_settings.govcode_catalog_info_enabled:
        catalog_tool.register(
            mcp,
            catalog_loader=partial(
                get_catalog_info,
                catalog=active_settings.govcode_project_catalog,
                schema=active_settings.govcode_project_schema,
                table=active_settings.govcode_project_table,
            ),
        )

    if active_settings.govcode_project_compare_enabled:
        compare_tool.register(
            mcp,
            project_comparer=partial(
                compare_projects,
                project_loader=partial(
                    get_project_from_warehouse,
                    dataset_format=active_settings.govcode_project_dataset_format,
                    catalog=active_settings.govcode_project_catalog,
                    schema=active_settings.govcode_project_schema,
                    table=active_settings.govcode_project_table,
                ),
            ),
        )


__all__ = ["register_tools"]
