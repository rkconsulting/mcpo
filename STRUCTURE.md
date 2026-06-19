# MCPO Project Structure

## Overview
mcpo is an MCP-to-OpenAPI proxy that exposes MCP server tools as RESTful HTTP endpoints with auto-generated OpenAPI schemas.

## Directory Structure

```
mcpo/
├── src/
│   └── mcpo/
│       ├── __init__.py          # CLI entry point (typer)
│       ├── main.py              # Core server logic, lifespan, config handling
│       ├── utils/
│       │   ├── auth.py          # API key middleware and verification
│       │   ├── config_watcher.py # Hot-reload config file watcher
│       │   ├── headers.py       # Client header forwarding
│       │   ├── main.py          # Tool handler, schema processing, model generation
│       │   └── oauth.py         # OAuth 2.1 provider creation
│       └── tests/
│           ├── test_main.py     # Unit tests for schema processing
│           └── test_hot_reload.py # Unit tests for config validation and hot reload
├── pyproject.toml               # Project metadata and dependencies
├── uv.lock                      # Locked dependency versions
├── Dockerfile                   # Container build instructions
├── README.md                    # Main documentation
├── OAUTH_GUIDE.md               # OAuth configuration guide
├── HEADER_FORWARDING.md         # Header forwarding documentation
├── CHANGELOG.md                 # Version history
├── STRUCTURE.md                 # This file
├── IMPLEMENT.md                 # Current implementation plan
└── TODO.md                      # Task tracking
```

## Key Components

### Config System
- Supports single-server mode (CLI args) and multi-server mode (config file)
- Config file follows Claude Desktop format with `mcpServers` key
- Hot-reload via `--hot-reload` flag watches config file for changes
- Per-server options: `disabledTools`, `hiddenTools`, `headers`, `oauth`, `client_header_forwarding`

### Tool Management
- `disabledTools`: Completely removes tools (not accessible, not in schema)
- `hiddenTools`: Keeps tools accessible but excludes from OpenAPI schema
- Tools are registered as POST endpoints on sub-apps mounted per server

### Authentication
- API key middleware for mcpo-level auth
- OAuth 2.1 for upstream MCP server authentication
- Supports dynamic client registration and static client metadata
