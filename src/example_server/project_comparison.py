"""Collect inventory evidence for project comparison."""

from collections.abc import Callable

from example_server.errors import InvalidComparisonRequest
from example_server.models import ProjectComparisonResponse, ProjectDetail


def compare_projects(
    entry_ids: list[str],
    *,
    project_loader: Callable[[str], dict | None],
) -> ProjectComparisonResponse:
    """Retrieve two to five distinct entries in the requested order."""
    if not 2 <= len(entry_ids) <= 5:
        raise InvalidComparisonRequest("Comparison requires between 2 and 5 entry IDs")

    if any(
        not isinstance(entry_id, str) or not entry_id.strip()
        for entry_id in entry_ids
    ):
        raise InvalidComparisonRequest("Entry IDs must be nonblank strings")

    if len(set(entry_ids)) != len(entry_ids):
        raise InvalidComparisonRequest("Comparison requires distinct entry IDs")

    projects = []
    missing_entry_ids = []

    for entry_id in entry_ids:
        project = project_loader(entry_id)

        if project is None:
            missing_entry_ids.append(entry_id)
            continue

        detail = ProjectDetail.model_validate(project)
        if detail.entry_id != entry_id:
            raise ValueError("Project reader returned an unexpected entry ID")

        projects.append(detail)

    return ProjectComparisonResponse(
        requested_entry_ids=entry_ids,
        projects=projects,
        missing_entry_ids=missing_entry_ids,
    )
