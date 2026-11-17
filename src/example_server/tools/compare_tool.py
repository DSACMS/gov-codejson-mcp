"""Compare inventory entries using an explicitly supplied function."""

from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from example_server.errors import InvalidComparisonRequest
from example_server.models import ProjectComparisonResponse


def register(
    mcp: FastMCP,
    *,
    project_comparer: Callable[[list[str]], ProjectComparisonResponse],
) -> None:
    """Register comparison using the supplied inventory function."""

    @mcp.tool(
        name="govcode_compare_projects",
        annotations={
            "title": "Compare Government Software Projects",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def compare_projects(
        entry_ids: Annotated[
            list[str],
            Field(
                min_length=2,
                max_length=5,
                description="Two to five distinct inventory entry IDs.",
            ),
        ],
    ) -> ProjectComparisonResponse:
        """
        Retrieve inventory evidence for comparing selected projects.

        Preserve requested order and report missing IDs separately.
        Unknown values remain null. Entries sharing a repository stay separate.
        This tool supplies metadata, not readiness scores or a comparison winner.
        Entries are read separately and may reflect concurrent inventory updates.
        """
        try:
            return project_comparer(entry_ids)
        except InvalidComparisonRequest as error:
            raise ToolError(str(error)) from None
        except Exception:
            raise ToolError(
                "Project comparison failed. Please try again later."
            ) from None
