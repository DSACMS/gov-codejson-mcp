"""Search government software using an explicitly supplied reader."""

from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from example_server.models import ProjectSearchResponse


def register(
    mcp: FastMCP,
    *,
    project_searcher: Callable[..., ProjectSearchResponse],
) -> None:
    """Register search using the supplied inventory reader."""

    @mcp.tool(
        name="govcode_search_projects",
        annotations={
            "title": "Search Government Software Projects",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def search_projects(
        query: Annotated[
            str | None,
            "Literal phrase to match within name or description, ignoring case.",
        ] = None,
        agency: Annotated[
            str | None,
            "Exact agency value. Omit to include all agencies.",
        ] = None,
        organization: Annotated[
            str | None,
            "Exact organization value. Omit to include all organizations.",
        ] = None,
        limit: Annotated[
            int,
            Field(ge=1, le=100, description="Maximum entries in this page."),
        ] = 10,
        offset: Annotated[
            int,
            Field(ge=0, description="Number of matching entries to skip."),
        ] = 0,
    ) -> ProjectSearchResponse:
        """
        Search inventory metadata and return one page plus the total count.

        With no filters, browse all entries. Order by name, then entry ID.
        Matches describe inventory metadata and do not establish suitability
        for reuse. Counts and pages may change when the inventory is updated.
        """
        try:
            return project_searcher(
                query=query,
                agency=agency,
                organization=organization,
                limit=limit,
                offset=offset,
            )
        except Exception:
            raise ToolError("Project search failed. Please try again later.") from None
