# ddmcp Docker Quick Start

## ✅ Your Server is Running!

The ddmcp MCP server is now running in Docker on **port 8888**.

```
🐳 Container: ddmcp-server
📡 Endpoint: http://localhost:8888/mcp/sse
✅ Status: Running
```

---

## Connect Your Clients

### Claude Code (CLI)

```bash
# Copy the config
cp client-configs/claude-code-http.json ~/.claude/mcp.json

# Restart Claude Code
# (exit and start a new session)
```

### Claude Desktop

**macOS:**
```bash
cp client-configs/claude-desktop-http.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```powershell
Copy-Item client-configs\claude-desktop-http.json "$env:APPDATA\Claude\claude_desktop_config.json"
```

**Linux:**
```bash
cp client-configs/claude-desktop-http.json ~/.config/Claude/claude_desktop_config.json
```

Then **restart Claude Desktop**.

---

## Test It Works

In Claude Code or Claude Desktop, try:

```
"List available MCP tools"
```

or

```
"Show me top endpoints in the analyst service"
```

You should see 7 ddmcp tools available!

---

## Manage the Container

```bash
# View logs
docker-compose logs -f ddmcp

# Restart
docker-compose restart ddmcp

# Stop
docker-compose down

# Start again
docker-compose up -d

# Check status
docker-compose ps
```

---

## What's Running

- **Docker Container:** `ddmcp-server`
- **Internal Port:** 8000 (inside container)
- **External Port:** 8888 (on your machine)
- **Endpoint:** `/mcp/sse` (SSE transport)
- **Network:** `ddmcp-network` (bridge)

---

## Next Steps

1. ✅ Server is running
2. 🔧 Configure your Claude clients
3. 🧪 Test the connection
4. 🚀 Start querying Datadog!

For detailed setup including network access from other machines, see [DOCKER-NETWORK-SETUP.md](DOCKER-NETWORK-SETUP.md)
