import argparse
import os
import sys
from typing import Literal

__all__ = ["main"]


def main() -> None:
    """
    Main CLI entry point for the MCP server.
    Accepts --transport CLI argument (falls back to MCP_TRANSPORT env var, then stdio).

    Heavy dependencies (numpy, etc.) are imported lazily inside this
    function so that ``uv run`` can finish installing packages and Python
    can start before the 30-second MCP connection timeout fires.
    """
    from dotenv import load_dotenv

    # Load environment variables from .env file if it exists
    load_dotenv()

    parser = argparse.ArgumentParser(description="Massive MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help="Transport protocol (default: stdio). Overrides MCP_TRANSPORT env var.",
    )
    args = parser.parse_args()

    # CLI arg takes precedence over env var; default to stdio
    if args.transport is not None:
        transport: Literal["stdio", "sse", "streamable-http"] = args.transport
    else:
        supported_transports: dict[str, Literal["stdio", "sse", "streamable-http"]] = {
            "stdio": "stdio",
            "sse": "sse",
            "streamable-http": "streamable-http",
        }
        mcp_transport_str = os.environ.get("MCP_TRANSPORT", "stdio")
        transport = supported_transports.get(mcp_transport_str, "stdio")

    # Check API key and print startup message
    massive_api_key = os.environ.get("MASSIVE_API_KEY", "")
    polygon_api_key = os.environ.get("POLYGON_API_KEY", "")

    # Startup messages go to stderr — stdout is the MCP protocol channel
    # for stdio transport; non-JSON data there corrupts the handshake.
    if massive_api_key:
        print("Starting Massive MCP server with API key configured.", file=sys.stderr)
    elif polygon_api_key:
        print(
            "Warning: POLYGON_API_KEY is deprecated. Please migrate to MASSIVE_API_KEY.",
            file=sys.stderr,
        )
        print(
            "Starting Massive MCP server with API key configured (using deprecated POLYGON_API_KEY).",
            file=sys.stderr,
        )
        massive_api_key = polygon_api_key
    else:
        print("Warning: MASSIVE_API_KEY environment variable not set.", file=sys.stderr)

    base_url = os.environ.get("MASSIVE_API_BASE_URL", "https://api.massive.com").rstrip(
        "/"
    )
    llms_txt_url = os.environ.get("MASSIVE_LLMS_TXT_URL")

    max_tables: int | None = None
    max_rows: int | None = None
    if os.environ.get("MASSIVE_MAX_TABLES"):
        max_tables = int(os.environ["MASSIVE_MAX_TABLES"])
    if os.environ.get("MASSIVE_MAX_ROWS"):
        max_rows = int(os.environ["MASSIVE_MAX_ROWS"])

    # Defer importing server until after env vars are read
    from .server import configure_credentials, mass_mcp
    import uvicorn

    configure_credentials(
        massive_api_key,
        base_url,
        llms_txt_url=llms_txt_url,
        max_tables=max_tables,
        max_rows=max_rows,
    )

    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
    import uvicorn

    from importlib.metadata import version
        print("MCP VERSION:", version("mcp"), file=sys.stderr)
    
    mcp_app = mass_mcp.streamable_http_app()

    async def health(request):
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/", health),
            Route("/health", health),
            Mount("/mcp", app=mcp_app),
        ]
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )

if __name__ == "__main__":
    main()
