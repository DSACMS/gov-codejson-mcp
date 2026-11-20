"""Read inventory coverage from the cleaned warehouse table."""

from example_server import warehouse
from example_server.models import CatalogInfoResponse, InventoryGroupCount


def get_catalog_info(
    *,
    catalog: str,
    schema: str,
    table: str,
) -> CatalogInfoResponse:
    """Count inventory entries grouped by agency and organization."""
    table_name = ".".join(
        "`" + identifier.replace("`", "``") + "`"
        for identifier in (catalog, schema, table)
    )

    with warehouse.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT
                    agency,
                    organization,
                    COUNT(*) AS project_count
                FROM {table_name}
                GROUP BY agency, organization
                ORDER BY agency ASC NULLS LAST,
                         organization ASC NULLS LAST"""
            )
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

    groups = [
        InventoryGroupCount.model_validate(dict(zip(columns, row, strict=True)))
        for row in rows
    ]

    return CatalogInfoResponse(
        total_count=sum(group.project_count for group in groups),
        groups=groups,
    )
