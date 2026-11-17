"""Project detail lookup using an explicitly supplied reader."""

from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from example_server.errors import DuplicateProjectError
from example_server.models import ProjectDetail


def register(
    mcp: FastMCP,
    *,
    project_loader: Callable[[str], dict | None],
) -> None:
    """Register project lookup using the supplied reader."""

    @mcp.tool(
        name="govcode_get_project",
        annotations={
            "title": "Get Government Software Project",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def get_project(
        entry_id: Annotated[str, "The inventory entry ID to retrieve."],
    ) -> ProjectDetail:
        """Return one inventory entry, including unavailable fields as null."""
        try:
            project = project_loader(entry_id)

            if project is not None:
                detail = ProjectDetail.model_validate(project)
        except DuplicateProjectError:
            raise ToolError(
                "Project lookup found duplicate entries; "
                "the inventory needs correction."
            ) from None
        except Exception:
            raise ToolError(
                "Project lookup failed. Please try again later."
            ) from None

        if project is None:
            raise ToolError("Project entry not found")

        return detail
