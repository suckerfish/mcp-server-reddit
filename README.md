# MCP Server Reddit (Fork)

A Model Context Protocol server providing access to Reddit's public API for LLMs. Forked from [Hawstein/mcp-server-reddit](https://github.com/Hawstein/mcp-server-reddit).

This server uses [redditwarp](https://github.com/Pyprohly/redditwarp) to interact with Reddit's public API and exposes the functionality through the MCP protocol.

## Fork Enhancements

This fork adds the following over the original:

- **Streamable HTTP transport** — Supports `--transport streamable-http` in addition to stdio, allowing deployment as a standalone HTTP service instead of requiring a stdio process manager
- **CLI flags** — `--transport`, `--host`, `--port` arguments for flexible deployment
- **FastMCP v3** — Migrated from low-level `mcp.server.Server` to `FastMCP` decorator-based API
- **Docker container** — Production-ready Dockerfile with multi-arch (amd64/arm64) support
- **GHCR publishing** — GitHub Actions workflow auto-builds and pushes to `ghcr.io/suckerfish/mcp-server-reddit:latest` on every push to main
- **redditwarp fix** — Monkey-patches the `active_user_count` KeyError crash in redditwarp 1.3.0 caused by Reddit removing the field from their API

## Available Tools

- `get_frontpage_posts` - Get hot posts from Reddit frontpage
  - Optional: `limit` (integer, default: 10, range: 1-100)

- `get_subreddit_info` - Get information about a subreddit
  - Required: `subreddit_name` (string)

- `get_subreddit_hot_posts` - Get hot posts from a specific subreddit
  - Required: `subreddit_name` (string)
  - Optional: `limit` (integer, default: 10, range: 1-100)

- `get_subreddit_new_posts` - Get new posts from a specific subreddit
  - Required: `subreddit_name` (string)
  - Optional: `limit` (integer, default: 10, range: 1-100)

- `get_subreddit_top_posts` - Get top posts from a specific subreddit
  - Required: `subreddit_name` (string)
  - Optional: `limit` (integer, default: 10, range: 1-100), `time` (string: hour, day, week, month, year, all)

- `get_subreddit_rising_posts` - Get rising posts from a specific subreddit
  - Required: `subreddit_name` (string)
  - Optional: `limit` (integer, default: 10, range: 1-100)

- `get_post_content` - Get detailed content of a specific post including comments
  - Required: `post_id` (string)
  - Optional: `comment_limit` (integer, default: 10), `comment_depth` (integer, default: 3)

- `get_post_comments` - Get comments from a post
  - Required: `post_id` (string)
  - Optional: `limit` (integer, default: 10, range: 1-100)

## Usage

### Docker (recommended for deployment)

```bash
docker run -p 8080:8080 ghcr.io/suckerfish/mcp-server-reddit:latest
```

The container runs streamable HTTP transport on port 8080 by default. MCP endpoint is at `/mcp`.

### Streamable HTTP (standalone)

```bash
uv run mcp-server-reddit --transport streamable-http --host 0.0.0.0 --port 8080
```

### Stdio (original behavior)

```bash
uv run mcp-server-reddit
```

Or in your MCP client config:

```json
"mcpServers": {
  "reddit": {
    "command": "uvx",
    "args": ["mcp-server-reddit"]
  }
}
```

## License

MIT License. See the LICENSE file for details.
