"""Read project details from the cleaned warehouse table."""

from example_server import warehouse
from example_server.errors import DuplicateProjectError
from example_server.inventory_layout import get_inventory_layout


def get_project_from_warehouse(
    entry_id: str,
    *,
    catalog: str,
    schema: str,
    table: str,
    dataset_format: str = "mock",
) -> dict | None:
    """Return one project, or None when its entry ID is not found."""
    layout = get_inventory_layout(dataset_format)

    table_name = ".".join(
        "`" + identifier.replace("`", "``") + "`"
        for identifier in (catalog, schema, table)
    )

    with warehouse.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT {layout.select_columns}
                FROM {table_name}
                WHERE {layout.id_expression} = ?
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
    return layout.prepare_record(project)
