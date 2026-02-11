# Docker Network Setup Guide

This guide shows you how to run ddmcp as a **centralized Docker container** that all your Claude clients can connect to over HTTP.

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │─┐
└─────────────────┘ │
                    │
┌─────────────────┐ │    HTTP (port 8000)
│  Claude Code    │─┼──────────────────────┐
└─────────────────┘ │                      │
                    │                      ▼
┌─────────────────┐ │              ┌──────────────┐
│  Other Clients  │─┘              │    Docker    │
└─────────────────┘                │ ddmcp Server │
                                   └──────────────┘
```

**Benefits:**
- ✅ Single server instance (saves resources)
- ✅ All clients connect to the same server
- ✅ Easy updates (restart one container)
- ✅ Centralized logging
- ✅ Works across your local network

---

## Step 1: Configure Credentials

Create a `.env` file with your Datadog credentials:

```bash
cd /Users/danielhostetler/src/ddmcp

# Create .env file
cat > .env << 'EOF'
DD_API_KEY=989494cf6e61d776c8d3611f8d13e2d4
DD_APP_KEY=a6d6b84d78f84b61a6fb76b0bf5e09cb4b0f4c01
DD_SITE=us5
EOF

# Secure the file
chmod 600 .env
```

**⚠️ Security:** Never commit `.env` to version control!

---

## Step 2: Start the Docker Container

```bash
# Build and start
docker-compose up -d

# Verify it's running
docker-compose ps

# Check logs
docker-compose logs -f ddmcp
```

You should see output indicating the server started on `http://0.0.0.0:8000`

---

## Step 3: Verify Server is Working

Test the HTTP endpoint:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check MCP endpoint
curl http://localhost:8000/

# Or open in browser
open http://localhost:8000
```

---

## Step 4: Configure Claude Code (CLI)

Copy the HTTP client config:

```bash
cp client-configs/claude-code-http.json ~/.claude/mcp.json
```

**Or manually edit** `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "ddmcp": {
      "url": "http://localhost:8000",
      "transport": "http"
    }
  }
}
```

**Restart Claude Code** for changes to take effect.

---

## Step 5: Configure Claude Desktop

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

**Or manually edit** the config file:

```json
{
  "mcpServers": {
    "ddmcp": {
      "url": "http://localhost:8000",
      "transport": "http"
    }
  }
}
```

**Restart Claude Desktop** for changes to take effect.

---

## Step 6: Test the Connection

In **Claude Code** or **Claude Desktop**, try:

```
"List the available MCP tools"
```

You should see 7 ddmcp tools:
- apm_search_spans
- apm_get_slow_endpoints
- apm_aggregate_spans
- apm_get_span_by_id
- apm_list_services
- apm_get_service
- apm_get_service_stats

Or test directly:

```
"Show me the top 10 endpoints in the analyst service"
```

---

## Managing the Server

### Start/Stop

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f
```

### Update Server

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check Status

```bash
# Container status
docker-compose ps

# Health check
curl http://localhost:8000/health

# View logs
docker-compose logs --tail=50 ddmcp
```

---

## Network Access from Other Machines

To allow connections from other machines on your network:

### 1. Find your local IP

```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
```

Example: `192.168.1.100`

### 2. Update docker-compose.yml

Change the ports section:

```yaml
ports:
  - "0.0.0.0:8000:8000"  # Allow external connections
```

### 3. Configure firewall

**macOS:**
```bash
# Allow incoming connections on port 8000
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/docker
```

**Linux (ufw):**
```bash
sudo ufw allow 8000/tcp
```

**Windows:**
```powershell
netsh advfirewall firewall add rule name="DDMCP" dir=in action=allow protocol=TCP localport=8000
```

### 4. Connect from other machines

Update client configs to use your IP:

```json
{
  "mcpServers": {
    "ddmcp": {
      "url": "http://192.168.1.100:8000",
      "transport": "http"
    }
  }
}
```

---

## Troubleshooting

### Server won't start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs ddmcp

# Verify credentials
docker-compose exec ddmcp env | grep DD_
```

### Can't connect from clients

```bash
# Test server is accessible
curl http://localhost:8000/health

# Check port is open
netstat -an | grep 8000

# Check firewall
# macOS: System Preferences > Security & Privacy > Firewall
# Windows: Windows Defender Firewall
# Linux: sudo ufw status
```

### Tools not showing up in Claude

1. Verify server is running: `docker-compose ps`
2. Check client config path is correct
3. Restart Claude Desktop/Code
4. Check logs: `docker-compose logs -f`

### Port 8000 already in use

Change the port in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use port 8001 externally
```

Then update client configs:

```json
{
  "mcpServers": {
    "ddmcp": {
      "url": "http://localhost:8001",
      "transport": "http"
    }
  }
}
```

---

## Security Considerations

### For local-only use:

✅ Current setup is fine - only accessible from localhost

### For network access:

⚠️ **Important security measures:**

1. **Use HTTPS** (set up reverse proxy with TLS)
2. **Add authentication** (API key, OAuth, etc.)
3. **Firewall rules** (restrict to specific IPs)
4. **VPN** (access only through VPN)

**Example with nginx reverse proxy:**

```nginx
server {
    listen 443 ssl;
    server_name ddmcp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring

### View real-time logs

```bash
docker-compose logs -f ddmcp
```

### Check resource usage

```bash
docker stats ddmcp-server
```

### Set up log rotation

Add to `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Performance Tuning

### Increase workers (for high load)

Modify `src/ddmcp/http_server.py`:

```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # Add multiple workers
    log_level="info",
)
```

### Limit memory usage

Add to `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

---

## Next Steps

1. ✅ Start the Docker container
2. ✅ Configure your Claude clients
3. ✅ Test the connection
4. 🎯 Start using Datadog queries in Claude!

For more deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md)
