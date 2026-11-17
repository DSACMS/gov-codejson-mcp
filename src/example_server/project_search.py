"""Search filters shared by project count and result queries."""
from example_server import warehouse
from example_server.models import (
    PaginationParams,
    ProjectDetail,
    ProjectSearchFilters,
    ProjectSearchResponse,
)
from example_server.project_reader import prepare_project


def build_search_filters(
    *,
    query: str | None = None,
    agency: str | None = None,
    organization: str | None = None,
) -> tuple[ProjectSearchFilters, str, list[str]]:
    """Return normalized filters, a WHERE clause, and bound values."""
    filters = ProjectSearchFilters(
        query=query.strip() or None if query is not None else None,
        agency=agency.strip() or None if agency is not None else None,
        organization=(
            organization.strip() or None if organization is not None else None
        ),
    )
    clauses = []
    parameters = []

    if filters.query is not None:
        clauses.append(
            "(contains(lower(coalesce(name, '')), lower(?)) "
            "OR contains(lower(coalesce(description, '')), lower(?)))"
        )
        parameters.extend([filters.query, filters.query])

    if filters.agency is not None:
        clauses.append("agency = ?")
        parameters.append(filters.agency)

    if filters.organization is not None:
        clauses.append("organization = ?")
        parameters.append(filters.organization)

    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    return filters, where_clause, parameters


def search_projects(
    *,
    catalog: str,
    schema: str,
    table: str,
    query: str | None = None,
    agency: str | None = None,
    organization: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> ProjectSearchResponse:
    """Count all matching entries and return one ordered result page."""
    pagination = PaginationParams(limit=limit, offset=offset)
    filters, where_clause, parameters = build_search_filters(
        query=query,
        agency=agency,
        organization=organization,
    )
    table_name = ".".join(
        "`" + identifier.replace("`", "``") + "`"
        for identifier in (catalog, schema, table)
    )

    with warehouse.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name}{where_clause}",
                parameters=parameters,
            )
            total_count = cursor.fetchone()[0]

            cursor.execute(
                f"""SELECT
                    CAST(id AS STRING) AS entry_id,
                    agency,
                    organization,
                    name,
                    description,
                    repositoryURL,
                    version,
                    usageType,
                    licenses,
                    tags,
                    languages,
                    laborHours,
                    dateCreated,
                    dateLastModified,
                    dateMetadataLastUpdated
                FROM {table_name}{where_clause}
                ORDER BY name ASC NULLS LAST, entry_id ASC
                LIMIT ? OFFSET ?""",
                parameters=[
                    *parameters,
                    pagination.limit,
                    pagination.offset,
                ],
            )
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

    results = [
        ProjectDetail.model_validate(
            prepare_project(dict(zip(columns, row, strict=True)))
        )
        for row in rows
    ]

    return ProjectSearchResponse(
        results=results,
        total_count=total_count,
        applied_filters=filters,
        limit=pagination.limit,
        offset=pagination.offset,
        has_more=pagination.offset + len(results) < total_count,
    )
