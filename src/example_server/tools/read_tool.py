import os
from typing import Annotated

from databricks import sql
from fastmcp import FastMCP


def quote_identifier(identifier: str) -> str:
    """Escape and quote one SQL identifier."""
    escaped_identifier = identifier.replace("`", "``")
    return "`" + escaped_identifier + "`"

def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="databricks_preview_table",
        annotations={
            "title": "Preview Databricks Table",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    def preview_table(
        limit: Annotated[int, "The maximum number of rows to return."] = 10,
        agency: Annotated[str, "The agency abbreviation, such as GSA or HHS."] = "GSA",
    ) -> dict:
        """
        This tool reads GSA projects from a configured Databricks table.
        It returns agency, name, description, repository URL, and languages.
        Results are ordered by project name.
        The limit accepts 1–100 and defaults to 10.
        The agency parameter filters results by the specified agency.
        """
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        allowed_agencies = {
            "DHS", "DoD", "DoE", "EPA", "FEC", "GSA",
            "HHS", "NSF", "SSA", "TREASURY", "USDA", "VA",
        }
        if agency not in allowed_agencies:
            raise ValueError("agency must match a supported agency abbreviation")

        agency_column = quote_identifier(agency)
        table_name = ".".join(
            quote_identifier(os.environ[key])
            for key in (
                "DATABRICKS_CATALOG",
                "DATABRICKS_SCHEMA",
                "DATABRICKS_TABLE"
                )
        )
        with sql.connect(
            server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            auth_type="databricks-oauth"
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""SELECT
                        raw.{agency_column}.agency AS agency,
                        projects.project.name AS name,
                        projects.project.description AS description,
                        projects.project.repositoryURL AS repository_url,
                        projects.project.languages AS languages
                    FROM {table_name} AS raw,
                    LATERAL explode(raw.{agency_column}.releases) AS projects(project)
                    ORDER BY name
                    LIMIT {limit}"""
                )

                result = {
                    "columns": [column[0] for column in cursor.description],
                    "rows": [list(row) for row in cursor.fetchall()],
                }

        return result
