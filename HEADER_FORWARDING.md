# Header Forwarding in MCPO

MCPO supports forwarding HTTP headers from incoming requests to MCP servers conforming to the (June 2025 MCP specification)[https://modelcontextprotocol.io/specification/2025-06-18]. This enables SSO token validation, capability authorization and user context passing to your MCP servers. 

## Configuration

Add header forwarding configuration to your MCP server config:

```json
{
  "mcpServers": {
    "some-mcp": {
      "command": "uvx",
      "args": ["some-mcp"],
      "header_forwarding": {
        "enabled": true,
        "whitelist": ["Authorization", "X-User-*"],
        "blacklist": ["Host", "Content-Length"],
        "debug_headers": false,
        "jwt_validation": {
          "enabled": true,
          "issuer": "https://keycloak.company.com/realms/main",
          "audience": "some-mcp",
          "algorithms": ["RS256"],
          "jwks_uri": "https://keycloak.company.com/realms/main/protocol/openid-connect/certs"
        }
      }
    }
  }
}
```

## Configuration Options

### Basic Settings
- `enabled`: Enable/disable header forwarding for this server
- `whitelist`: List of header patterns to forward (supports wildcards with `*`)
- `blacklist`: List of header patterns to block (takes precedence over whitelist)
- `debug_headers`: Enable debug logging for header processing

### JWT Validation
- `enabled`: Enable JWT token validation
- `issuer`: Expected JWT issuer
- `audience`: Expected JWT audience
- `algorithms`: Allowed JWT signing algorithms
- `jwks_uri`: URL to fetch JWT signing keys

## How It Works

1. **Request Processing**: When a request comes to mcpo with headers like `Authorization: Bearer <token>`
2. **Header Filtering**: Headers are filtered based on whitelist/blacklist rules
3. **JWT Validation**: If configured, JWT tokens are validated and user context is extracted
4. **MCP Forwarding**: Headers are passed to the MCP server via the `_meta.headers` field in tool calls

## Transport Support

Header forwarding works with all MCP transport types:
- **stdio**: Headers are passed via `_meta` field in JSON-RPC calls
- **SSE**: Headers are passed via `_meta` field in JSON-RPC calls  
- **HTTP**: Headers are passed via `_meta` field in JSON-RPC calls

The MCP server receives headers regardless of the transport mechanism used.

## Security Considerations

- **Whitelist Headers**: Only forward necessary headers to minimize attack surface
- **JWT Validation**: Always validate JWT tokens when using SSO
- **Blacklist Sensitive Headers**: Block headers like `Host`, `Content-Length`, etc.
- **Debug Mode**: Only enable `debug_headers` in development environments

## MCP Server Integration

Your MCP server can access forwarded headers through the `_meta` field in tool calls:

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

mcp = FastMCP(name="Example Server")

@mcp.tool()
async def protected_tool(data: str, ctx: Context[ServerSession, None]) -> str:
    # Access forwarded headers
    headers = getattr(ctx.request_meta, 'headers', {}) if hasattr(ctx, 'request_meta') else {}
    
    # Check authorization
    auth_header = headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise ValueError("Missing or invalid authorization")
    
    # Extract user context (if JWT validation is enabled, user info is in headers)
    user_id = headers.get('X-User-ID', 'unknown')
    user_email = headers.get('X-User-Email', 'unknown')
    
    return f"Protected data for user {user_id} ({user_email}): {data}"
```
