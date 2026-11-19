"""Evaluate discovery through local MCP using the live legacy inventory."""

import asyncio
import json
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from fastmcp import Client, FastMCP

from example_server.config import Settings
from example_server.models import (
    CatalogInfoResponse,
    ProjectComparisonResponse,
    ProjectDetail,
    ProjectSearchResponse,
)
from example_server.tools import register_tools


@contextmanager
def evaluated_case(report: dict, name: str):
    """Record a case outcome and elapsed time without swallowing failures."""
    case = {"name": name, "status": "RUNNING"}
    report["cases"].append(case)
    started = perf_counter()

    try:
        yield
    except AssertionError:
        case["status"] = "FAIL"
        case["error_type"] = "AssertionError"
        raise
    except Exception as error:
        case["status"] = "ERROR"
        case["error_type"] = type(error).__name__
        raise
    else:
        case["status"] = "PASS"
    finally:
        case["elapsed_seconds"] = round(perf_counter() - started, 3)


async def main(report: dict) -> None:
    """Run a read-only discovery workflow using local authentication."""
    load_dotenv(dotenv_path=".env")
    os.environ["DATABRICKS_READER_AUTH_MODE"] = "local"

    config = Settings(
        _env_file=None,
        govcode_project_lookup_enabled=True,
        govcode_project_search_enabled=True,
        govcode_catalog_info_enabled=True,
        govcode_project_compare_enabled=True,
        govcode_project_catalog="users",
        govcode_project_schema="natalia_luzuriaga1",
        govcode_project_table="legacy_gov_code",
        govcode_project_dataset_format="legacy",
    )
    server = FastMCP("Local discovery evaluation")
    register_tools(server, config=config)

    async with Client(server) as client:
        with evaluated_case(report, "tool_discovery"):
            tools = await client.list_tools()
            names = {tool.name for tool in tools}
            required = {
                "govcode_catalog_info",
                "govcode_search_projects",
                "govcode_get_project",
                "govcode_compare_projects",
            }
            assert required <= names, "Required discovery tools are missing"
            print("Tool discovery: PASS")

        with evaluated_case(report, "catalog_response"):
            result = await client.call_tool("govcode_catalog_info", {})
            assert result.structured_content is not None
            catalog = CatalogInfoResponse.model_validate(
                result.structured_content
            )
            assert catalog.total_count > 0, "Expected a populated legacy inventory"
            assert catalog.total_count == sum(
                group.project_count for group in catalog.groups
            )
            print("Catalog response consistency: PASS")
            print("Inventory entries:", catalog.total_count)

        with evaluated_case(report, "search_to_detail"):
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

        with evaluated_case(report, "search_to_comparison"):
            assert len(search.results) == 2, "Expected two search results"

            # Reverse the search results to check requested ordering.
            expected_projects = list(reversed(search.results))
            known_ids = [project.entry_id for project in expected_projects]
            assert len(set(known_ids)) == 2, "Expected distinct entry IDs"

            missing_id = "__govcode_missing_entry_839271__"
            requested_ids = [known_ids[0], missing_id, known_ids[1]]

            result = await client.call_tool(
                "govcode_compare_projects",
                {"entry_ids": requested_ids},
            )
            assert result.structured_content is not None
            comparison = ProjectComparisonResponse.model_validate(
                result.structured_content
            )

            assert comparison.requested_entry_ids == requested_ids
            assert comparison.missing_entry_ids == [missing_id]
            assert [
                project.entry_id for project in comparison.projects
            ] == known_ids

            for actual, expected in zip(
                comparison.projects,
                expected_projects,
                strict=True,
            ):
                assert actual.model_dump() == expected.model_dump(), (
                    f"Comparison differs from search for {expected.entry_id}"
                )

            assert not any(
                key.startswith("contact")
                for project in result.structured_content["projects"]
                for key in project
            )
            print("Search-to-comparison consistency: PASS")
            print("Compared entry IDs:", known_ids)
            print("Missing entry IDs:", comparison.missing_entry_ids)

        with evaluated_case(report, "no_match_search"):
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

        with evaluated_case(report, "unknown_project"):
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

        with evaluated_case(report, "invalid_pagination"):
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


def run_with_report() -> None:
    """Save an overall run summary, including unsuccessful runs."""
    output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc)
    started = perf_counter()
    report = {
        "evaluation_type": "functional_workflow",
        "execution_mode": "local_in_process_mcp",
        "warehouse_identity": "local_user",
        "dataset": "users.natalia_luzuriaga1.legacy_gov_code",
        "dataset_format": "legacy",
        "dataset_snapshot": None,
        "started_at": started_at.isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip(),
        "tracked_worktree_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
            ).strip()
        ),
        "status": "RUNNING",
        "llm_evaluated": False,
        "deployed_app_evaluated": False,
        "cases": [],
    }

    try:
        asyncio.run(main(report))
    except AssertionError:
        report["status"] = "FAIL"
        report["error_type"] = "AssertionError"
        raise
    except Exception as error:
        report["status"] = "ERROR"
        report["error_type"] = type(error).__name__
        raise
    else:
        report["status"] = "PASS"
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(perf_counter() - started, 3)
        report_path = output_dir / (
            started_at.strftime("%Y%m%dT%H%M%S%fZ") + "-discovery.json"
        )
        report_path.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        print("Evaluation report:", report_path)


if __name__ == "__main__":
    run_with_report()
