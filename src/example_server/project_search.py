"""Search filters shared by project count and result queries."""

from example_server.models import ProjectSearchFilters


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
