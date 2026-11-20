"""Map the final inventory table into approved project responses."""

from example_server.models import ProjectDetail
from example_server.project_reader import format_date_field, parse_list_field


def _parse_complete_licenses(
    record: dict,
) -> list[dict[str, str | None]] | None:
    """Pair supplied license names and URLs without dropping empty positions."""
    names_text = record.get("permissions_licenses_name")
    if names_text is None or not names_text.strip():
        names_text = record.get("permissions_licenses")

    urls_text = record.get("permissions_licenses_URL")

    if names_text is None or not names_text.strip():
        if urls_text is not None and urls_text.strip():
            raise ValueError("License URLs supplied without license names")
        return None

    names = [name.strip() for name in names_text.split("|")]
    if any(not name for name in names):
        raise ValueError("License names contain an empty position")

    if urls_text is None or not urls_text.strip():
        urls = [None] * len(names)
    else:
        urls = [url.strip() or None for url in urls_text.split("|")]
        if len(names) != len(urls):
            raise ValueError("License names and URLs have different lengths")

    return [
        {"name": name, "url": url}
        for name, url in zip(names, urls, strict=True)
    ]


def prepare_complete_project(
    record: dict,
    *,
    entry_id: str,
) -> ProjectDetail:
    """Map approved fields using the final inventory's stable record ID."""
    if not entry_id.strip():
        raise ValueError("A nonblank inventory entry ID is required")

    return ProjectDetail(
        entry_id=entry_id,
        source_identifier=record.get("identifier"),
        agency=record.get("agency"),
        organization=record.get("organization"),
        name=record.get("name"),
        description=record.get("description"),
        repositoryURL=record.get("repositoryURL"),
        version=record.get("version"),
        usageType=record.get("permissions_usageType"),
        licenses=_parse_complete_licenses(record),
        tags=parse_list_field(record.get("tags"), separator="|"),
        languages=parse_list_field(record.get("languages"), separator="|"),
        laborHours=record.get("laborHours"),
        dateCreated=format_date_field(record.get("date_created")),
        dateLastModified=format_date_field(record.get("date_lastModified")),
        dateMetadataLastUpdated=format_date_field(
            record.get("date_metadataLastUpdated")
        ),
    )
