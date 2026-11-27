"""MCP server stub using the official Python SDK.

TODO: wrap the same tool functions from
shopping_agent.agent.tools as MCP tools, so the assistant can be hosted as a
local MCP server (stdio). The job listing specifically mentions MCP.

Official docs (verified):
- Python SDK: https://py.sdk.modelcontextprotocol.io/
- Installation: https://py.sdk.modelcontextprotocol.io/get-started/installation/
- Running a server: https://py.sdk.modelcontextprotocol.io/run/
- Source: https://github.com/modelcontextprotocol/python-sdk

Install:  pip install 'harbour-basket-agent[mcp]'   or   pip install "mcp[cli]"

The SDK has had a v1 -> v2 API change. Check the docs for the version you
install. As of the v2 docs, a minimal server looks like:

    from mcp.server import MCPServer
    mcp = MCPServer("harbour-basket")

    @mcp.tool()
    def search_products(query: str, max_price: float | None = None) -> dict:
        # docstring: Search the Harbour Basket catalogue.
        return service.search_products(query=query, max_price=max_price)

    if __name__ == "__main__":
        mcp.run()   # stdio by default; use transport="streamable-http" to deploy

Older (v1) tutorials use `from mcp.server.fastmcp import FastMCP`. Either is
fine — follow the docs for the installed version, and note the choice in the
README.

Do not put secrets in this file. Construct ShoppingService.default() at
module import or inside a factory so tests can inject a fake.
"""

from __future__ import annotations

from shopping_agent.backend import ShoppingService


def build_server(service: ShoppingService | None = None):
    """TODO: construct and return an MCP server instance with tools registered."""
    _ = service or ShoppingService.default()
    raise NotImplementedError(
        "Implement build_server() in shopping_agent/mcp_server/server.py using "
        "the official MCP Python SDK. See the module docstring and "
        "https://py.sdk.modelcontextprotocol.io/"
    )


def main() -> None:
    """CLI entry point used by `make mcp` and the harbour-basket-mcp script."""
    server = build_server()
    # TODO: server.run()  (or mcp.run()) once build_server returns a live server.
    _ = server


if __name__ == "__main__":
    main()
