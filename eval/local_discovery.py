"""Evaluate discovery through local MCP using the live mock warehouse."""

import asyncio
import os
from time import perf_counter

from dotenv import load_dotenv
from fastmcp import Client, FastMCP

from example_server.config import Settings
from example_server.models import (
    CatalogInfoResponse,
    ProjectDetail,
    ProjectSearchResponse,
)
from example_server.tools import register_tools


async def main() -> None:
    """Run a read-only discovery workflow using local authentication."""
    load_dotenv(dotenv_path=".env")
    os.environ["DATABRICKS_READER_AUTH_MODE"] = "local"

    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=True,
        govcode_project_search_enabled=True,
        govcode_catalog_info_enabled=True,
        govcode_project_catalog="users",
        govcode_project_schema="natalia_luzuriaga1",
        govcode_project_table="mock_dataset",
    )
    server = FastMCP("Local discovery evaluation")
    register_tools(server, config=config)

    async with Client(server) as client:
        started = perf_counter()
        tools = await client.list_tools()
        names = {tool.name for tool in tools}
        required = {
            "govcode_catalog_info",
            "govcode_search_projects",
            "govcode_get_project",
        }
        assert required <= names, "Required discovery tools are missing"
        print("Tool discovery: PASS")
        print(f"Elapsed seconds: {perf_counter() - started:.3f}")

        started = perf_counter()
        result = await client.call_tool("govcode_catalog_info", {})
        assert result.structured_content is not None
        catalog = CatalogInfoResponse.model_validate(
            result.structured_content
        )
        assert catalog.total_count > 0, "Expected a populated mock inventory"
        assert catalog.total_count == sum(
            group.project_count for group in catalog.groups
        )
        print("Catalog response consistency: PASS")
        print("Inventory entries:", catalog.total_count)
        print(f"Elapsed seconds: {perf_counter() - started:.3f}")

        started = perf_counter()
        result = await client.call_tool(
            "govcode_search_projects",
            {"query": "data", "agency": "VA", "limit": 2},
        )
        assert result.structured_content is not None
        search = ProjectSearchResponse.model_validate(
            result.structured_content
        )
        assert search.results, "Expected VA matches for 'data'"
        assert search.total_count >= len(search.results)
        assert len(search.results) <= 2
        assert search.applied_filters.query == "data"
        assert search.applied_filters.agency == "VA"
        assert all(project.agency == "VA" for project in search.results)

        selected = search.results[0]
        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": selected.entry_id},
        )
        assert result.structured_content is not None
        detail = ProjectDetail.model_validate(result.structured_content)

        assert detail.entry_id == selected.entry_id
        assert detail.name == selected.name
        assert detail.agency == selected.agency
        assert detail.repositoryURL == selected.repositoryURL
        assert not any(
            key.startswith("contact") for key in result.structured_content
        )
        print("Search-to-detail consistency: PASS")
        print("Matching entries:", search.total_count)
        print("Selected entry ID:", detail.entry_id)
        print(f"Elapsed seconds: {perf_counter() - started:.3f}")

        started = perf_counter()
        result = await client.call_tool(
            "govcode_search_projects",
            {
                "query": "__govcode_no_match_839271__",
                "limit": 2,
            },
        )
        assert result.structured_content is not None
        empty = ProjectSearchResponse.model_validate(
            result.structured_content
        )
        assert empty.total_count == 0
        assert empty.results == []
        assert empty.has_more is False
        print("No-match search: PASS")
        print(f"Elapsed seconds: {perf_counter() - started:.3f}")

        result = await client.call_tool(
            "govcode_get_project",
            {"entry_id": "__govcode_missing_entry_839271__"},
            raise_on_error=False,
        )
        assert result.is_error
        messages = "\n".join(
            block.text for block in result.content if block.type == "text"
        )
        assert "Project entry not found" in messages
        print("Unknown project handling: PASS")

        result = await client.call_tool(
            "govcode_search_projects",
            {"limit": 101},
            raise_on_error=False,
        )
        assert result.is_error
        print("Invalid pagination rejected: PASS")

    print("Functional workflow: PASS")
    print("Mode: local MCP with local-user warehouse authentication")
    print("LLM evaluation and deployed App access: NOT TESTED")


if __name__ == "__main__":
    asyncio.run(main())
