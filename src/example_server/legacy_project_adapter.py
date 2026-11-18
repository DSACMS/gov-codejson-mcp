"""Map cleaned legacy inventory records into project responses."""

from example_server.models import ProjectDetail
from example_server.project_reader import (
    format_date_field,
    parse_license_field,
    parse_list_field,
)


def prepare_legacy_project(
    record: dict,
    *,
    entry_id: str,
) -> ProjectDetail:
    """Map approved fields using an explicitly supplied unique entry ID."""
    if not entry_id.strip():
        raise ValueError("A nonblank inventory entry ID is required")

    return ProjectDetail(
        entry_id=entry_id,
        agency=record.get("agency"),
        organization=record.get("organization"),
        name=record.get("name"),
        description=record.get("description"),
        repositoryURL=record.get("repositoryURL"),
        usageType=record.get("permissions_usageType"),
        licenses=parse_license_field(record.get("permissions_licenses")),
        tags=parse_list_field(record.get("tags"), separator="|"),
        languages=parse_list_field(record.get("languages"), separator="|"),
        laborHours=record.get("laborHours"),
        dateCreated=format_date_field(record.get("date_created")),
        dateLastModified=format_date_field(record.get("date_lastModified")),
    )
