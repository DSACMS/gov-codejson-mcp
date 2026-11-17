"""Project detail lookup using an explicitly supplied local fixture."""

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP

from example_server.models import ProjectDetail
from example_server.project_reader import get_project_from_fixture


def register(mcp: FastMCP, *, fixture_path: Path) -> None:
    """Register project lookup against a local development fixture."""

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
        project = get_project_from_fixture(fixture_path, entry_id)

        if project is None:
            raise ValueError("Project entry not found")

        return ProjectDetail.model_validate(project)