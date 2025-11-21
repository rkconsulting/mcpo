# Header Forwarding in MCPO

MCPO supports forwarding HTTP headers from incoming requests to MCP servers. This enables SSO token validation, capability authorization and user context passing to your MCP servers. 

## Configuration

Add header forwarding configuration to your MCP server config:

```json
{
  "mcpServers": {
    "some-mcp": {
      "command": "uvx",
      "args": ["some-mcp"],
      "client_header_forwarding": {
        "enabled": true,
        "whitelist": ["Authorization", "X-User-*"],
        "blacklist": ["Host", "Content-Length"],
        "debug_headers": false
      }
    }
  }
}
```

## Configuration Options

- `enabled`: Enable/disable header forwarding for this server
- `whitelist`: List of header patterns to forward (supports wildcards with `*`)
- `blacklist`: List of header patterns to block (takes precedence over whitelist)
- `debug_headers`: Enable debug logging for header processing

## How It Works

1. **Request Processing**: When a request comes to mcpo with headers like `Authorization: Bearer <token>`
2. **Header Filtering**: Headers are filtered based on whitelist/blacklist rules
3. **MCP Forwarding**: Headers are passed to the MCP server via the `_meta.headers` field in JSON-RPC tool calls

## Transport Support

Header forwarding works with **all MCP transport types**:

- **stdio**: Headers are passed via `_meta.headers` field in JSON-RPC calls over stdin/stdout
- **SSE**: Headers are passed via `_meta.headers` field in JSON-RPC calls over HTTP+SSE
- **Streamable HTTP**: Headers are passed via `_meta.headers` field in JSON-RPC calls over HTTP

The MCP server receives headers in the `_meta` metadata field of the JSON-RPC request, regardless of the transport mechanism used. This approach is transport-agnostic and follows the MCP specification's support for custom metadata in request parameters.

## Security Considerations

- **Whitelist Headers**: Only forward necessary headers to minimize attack surface
- **Blacklist Sensitive Headers**: Block headers like `Host`, `Content-Length`, etc.
- **Debug Mode**: Only enable `debug_headers` in development environments

## MCP Server Integration

Your MCP server can access forwarded headers through the `_meta` field in tool call requests. The exact implementation depends on your MCP SDK:

### Python (FastMCP/MCP SDK)

```python
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolRequest

mcp = FastMCP(name="Example Server")

@mcp.tool()
async def protected_tool(data: str) -> str:
    # Access the current request context
    # The _meta field contains forwarded headers
    # Implementation varies by SDK - check your SDK's documentation
    # for how to access request metadata
    
    # Example structure that would be received:
    # {
    #   "jsonrpc": "2.0",
    #   "method": "tools/call",
    #   "params": {
    #     "name": "protected_tool",
    #     "arguments": {"data": "some value"},
    #     "_meta": {
    #       "headers": {
    #         "Authorization": "Bearer token123",
    #         "X-User-ID": "user456"
    #       }
    #     }
    #   }
    # }
    
    return f"Processed: {data}"
```

### TypeScript/JavaScript (MCP TypeScript SDK)

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Access forwarded headers from _meta
  const headers = request.params._meta?.headers || {};
  const authHeader = headers['Authorization'] || '';
  const userId = headers['X-User-ID'] || 'unknown';
  
  // Your tool logic here
  return {
    content: [{
      type: "text",
      text: `Processed for user ${userId}`
    }]
  };
});
```

## Example Use Cases

1. **Authentication**: Forward `Authorization` header for JWT validation
2. **User Context**: Forward `X-User-*` headers for user identification and permissions
3. **Tenant Isolation**: Forward tenant identifiers for multi-tenant applications
4. **Audit Logging**: Forward user/session information for compliance tracking
