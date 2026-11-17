"""Project detail lookup using an explicitly supplied reader."""

from collections.abc import Callable
from typing import Annotated

from fastmcp import FastMCP

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
        project = project_loader(entry_id)

        if project is None:
            raise ValueError("Project entry not found")

        return ProjectDetail.model_validate(project)
