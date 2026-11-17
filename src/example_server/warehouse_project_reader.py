"""Read project details from the cleaned warehouse table."""

from example_server import warehouse
from example_server.errors import DuplicateProjectError
from example_server.project_reader import prepare_project


def get_project_from_warehouse(
    entry_id: str,
    *,
    catalog: str,
    schema: str,
    table: str,
) -> dict | None:
    """Return one project, or None when its entry ID is not found."""
    table_name = ".".join(
        "`" + identifier.replace("`", "``") + "`"
        for identifier in (catalog, schema, table)
    )

    with warehouse.connect() as connection:
        with connection.cursor() as cursor:
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
                FROM {table_name}
                WHERE CAST(id AS STRING) = ?
                LIMIT 2""",
                parameters=[entry_id],
            )
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

    if not rows:
        return None

    if len(rows) > 1:
        raise DuplicateProjectError("Duplicate entry_id in warehouse")

    project = dict(zip(columns, rows[0], strict=True))
    return prepare_project(project)
