"""Allow ``python -m kimss.mcp`` (delegates to :func:`kimss.mcp.server.main`)."""

from kimss.mcp.server import main

if __name__ == "__main__":
    main()
