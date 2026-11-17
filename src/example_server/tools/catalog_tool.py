"""Inventory coverage using an explicitly supplied catalog reader."""

from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from example_server.models import CatalogInfoResponse


def register(
    mcp: FastMCP,
    *,
    catalog_loader: Callable[[], CatalogInfoResponse],
) -> None:
    """Register inventory coverage using the supplied reader."""

    @mcp.tool(
        name="govcode_catalog_info",
        annotations={
            "title": "Government Software Inventory Coverage",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def catalog_info() -> CatalogInfoResponse:
        """
        Describe the configured inventory's current coverage.

        Count inventory entries, including separate entries sharing a repository.
        Group counts by supplied agency and organization values.
        Null agency or organization means that information was not provided.
        Dataset version and refresh date remain null when unavailable.

        Project search supports literal case-insensitive phrase matching within
        name or description, plus exact agency and organization filters.
        Search defaults to 10 results and permits at most 100 per page.
        Coverage describes this inventory, not all government software.
        """
        try:
            return catalog_loader()
        except Exception:
            raise ToolError(
                "Catalog information could not be retrieved. "
                "Please try again later."
            ) from None
