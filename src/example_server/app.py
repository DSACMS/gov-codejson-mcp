"""MCP server entry point.

Keep this file THIN. It only:
  1. creates the FastMCP instance,
  2. registers tools / prompts / resources / routes from the submodules, and
  3. decides which transport to run (stdio locally vs. HTTP when deployed).

All real logic lives in the submodules:
  - tools/      one file per tool (each exposes `register(mcp)`)
  - prompts/    reusable conversation starters
  - resources/  static/semi-static data the client can read directly
  - routes.py   HTTP-only infrastructure (health check, etc.)
  - config.py   settings loaded from env vars / .env
  - models.py   Pydantic models & enums for tool parameters
  - utils.py    shared helpers (HTTP client, formatting, pagination)
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from example_server.config import settings
from example_server.prompts import register_prompts
from example_server.resources import register_resources
from example_server.routes import register_routes
from example_server.tools import register_tools

# MCP clients display this name and receive these server instructions.
mcp = FastMCP(
    name="Federal Source Code Inventory",
    instructions=(
        "Discover federal software inventory entries using the enabled tools. "
        "Use catalog information to describe the configured inventory's coverage. "
        "Search matches literal text in project names or descriptions; "
        "agency and organization filters use exact values. "
        "Use entry_id values returned by search for lookup and comparison. "
        "Keep separate inventory entries distinct even when they share a repository. "
        "Describe missing values as unknown. "
        "Listed technologies may include operating systems and platforms. "
        "Inventory metadata and usage classifications do not establish security, "
        "active maintenance, suitability, or legal permission to reuse software. "
        "Software modification dates are not dataset refresh dates. "
        "Do not invent missing records, licenses, scores, or comparison winners."
    ),
)

# Wire up everything the server exposes. Each aggregator lives in its submodule.
register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)
register_routes(mcp)


def main() -> None:
    """Start the server, choosing a transport based on the environment.

    Precedence:
      1. A platform-injected port (Databricks `DATABRICKS_APP_PORT` or a generic
         `PORT`) → run HTTP on that port. Cloud hosts set this for you.
      2. `MCP_TRANSPORT=streamable-http` in the environment → run HTTP on
         `MCP_HOST`:`MCP_PORT` (see config.py / .env).
      3. Otherwise → stdio, which is how local clients (Claude Desktop, Claude
         Code, Zed) launch the server as a subprocess.
    """
    platform_port = os.getenv("DATABRICKS_APP_PORT") or os.getenv("PORT")

    if platform_port:
        mcp.run(transport="http", host="0.0.0.0", port=int(platform_port))
    elif settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
