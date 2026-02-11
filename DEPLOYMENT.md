# ddmcp Deployment Guide

This guide covers different ways to run the ddmcp MCP server across all platforms.

---

## Option 1: Claude Desktop Integration (Recommended ⭐)

**Best for:** All users - Windows, macOS, and Linux

**Why:** MCP servers are designed to start automatically when Claude Desktop needs them. Zero maintenance!

### Configuration

**Windows:**
Edit `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux:**
Edit `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ddmcp": {
      "command": "uvx",
      "args": ["ddmcp"],
      "env": {
        "DD_API_KEY": "your-api-key-here",
        "DD_APP_KEY": "your-app-key-here",
        "DD_SITE": "us5"
      }
    }
  }
}
```

**Then:** Restart Claude Desktop

✅ That's it! The server will:
- Start automatically when you open conversations
- Stop when not in use (saves memory)
- Require no manual intervention

---

## Option 2: Docker Container (Universal 🐳)

**Best for:** All platforms - isolation, portability, remote servers

**Prerequisites:** Docker installed ([Get Docker](https://docs.docker.com/get-docker/))

### Setup

1. **Create `.env` file:**

   ```bash
   # Windows (PowerShell)
   @"
   DD_API_KEY=your-api-key-here
   DD_APP_KEY=your-app-key-here
   DD_SITE=us5
   "@ | Out-File -Encoding ASCII .env

   # Unix (macOS/Linux)
   cat > .env << 'EOF'
   DD_API_KEY=your-api-key-here
   DD_APP_KEY=your-app-key-here
   DD_SITE=us5
   EOF
   ```

2. **Run with docker-compose (easiest):**

   ```bash
   docker-compose up -d
   ```

   Or **using docker directly:**

   ```bash
   # Build
   docker build -t ddmcp .

   # Run
   docker run -d \
     --name ddmcp-server \
     --restart unless-stopped \
     -e DD_API_KEY=your-api-key \
     -e DD_APP_KEY=your-app-key \
     -e DD_SITE=us5 \
     -p 8000:8000 \
     ddmcp
   ```

3. **Manage the container:**

   ```bash
   # View logs
   docker-compose logs -f ddmcp

   # Restart
   docker-compose restart ddmcp

   # Stop
   docker-compose down

   # Status
   docker-compose ps
   ```

**Pros:**
- ✅ Works identically on Windows, macOS, Linux
- ✅ Complete isolation
- ✅ Easy updates (`docker-compose pull && docker-compose up -d`)
- ✅ Health checks included

**Cons:**
- ⚠️ Requires Docker (1-2 GB overhead)
- ⚠️ Slightly more complex setup

---

## Option 3: System Service (Platform-Specific)

**Best for:** Running as a background service without Docker

### Linux (systemd)

1. **Edit `ddmcp.service`:**

   Replace credentials in the service file.

2. **Install:**

   ```bash
   sudo cp ddmcp.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable ddmcp
   sudo systemctl start ddmcp
   ```

3. **Manage:**

   ```bash
   # Status
   sudo systemctl status ddmcp

   # Logs
   sudo journalctl -u ddmcp -f

   # Restart
   sudo systemctl restart ddmcp

   # Stop
   sudo systemctl stop ddmcp
   ```

### macOS (launchd)

1. **Edit `com.ddmcp.server.plist`:**

   Replace credentials in the plist file.

2. **Install:**

   ```bash
   cp com.ddmcp.server.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.ddmcp.server.plist
   launchctl start com.ddmcp.server
   ```

3. **Manage:**

   ```bash
   # View logs
   tail -f /tmp/ddmcp.out.log

   # Stop
   launchctl stop com.ddmcp.server
   launchctl unload ~/Library/LaunchAgents/com.ddmcp.server.plist
   ```

### Windows (NSSM - Non-Sucking Service Manager)

1. **Install NSSM:**

   Download from [nssm.cc](https://nssm.cc/download)

2. **Install service:**

   ```powershell
   # Install service
   nssm install ddmcp "C:\path\to\uv.exe" "run python -m ddmcp.server"

   # Set working directory
   nssm set ddmcp AppDirectory "C:\path\to\ddmcp"

   # Set environment variables
   nssm set ddmcp AppEnvironmentExtra DD_API_KEY=your-key DD_APP_KEY=your-key DD_SITE=us5

   # Start service
   nssm start ddmcp
   ```

3. **Manage:**

   ```powershell
   # Status
   nssm status ddmcp

   # View logs (in Event Viewer)
   # Computer > Windows Logs > Application

   # Stop
   nssm stop ddmcp

   # Uninstall
   nssm remove ddmcp confirm
   ```

---

## Option 4: Process Manager (Cross-Platform)

**Best for:** Development/testing with easy restarts

### Using PM2 (Node.js process manager)

```bash
# Install PM2 (requires Node.js)
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'ddmcp',
    script: 'uv',
    args: 'run python -m ddmcp.server',
    cwd: '/path/to/ddmcp',
    env: {
      DD_API_KEY: 'your-api-key',
      DD_APP_KEY: 'your-app-key',
      DD_SITE: 'us5'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M'
  }]
}
EOF

# Start
pm2 start ecosystem.config.js

# Manage
pm2 list           # List all processes
pm2 logs ddmcp     # View logs
pm2 restart ddmcp  # Restart
pm2 stop ddmcp     # Stop
pm2 delete ddmcp   # Remove

# Auto-start on boot
pm2 startup
pm2 save
```

---

## Quick Comparison

| Option | Complexity | Cross-Platform | Auto-Start | Resource Usage |
|--------|-----------|----------------|------------|----------------|
| **Claude Desktop** | 🟢 Very Easy | ✅ Yes | ✅ Yes | 🟢 Low (on-demand) |
| **Docker** | 🟡 Medium | ✅ Yes | ✅ Yes | 🟡 Medium |
| **System Service** | 🟡 Medium | ⚠️ Platform-specific | ✅ Yes | 🟢 Low |
| **PM2** | 🟢 Easy | ✅ Yes | ✅ Yes | 🟢 Low |

---

## Recommendations

| Use Case | Recommended Option |
|----------|-------------------|
| **Normal Usage** | Claude Desktop Integration |
| **Local Testing** | Docker or PM2 |
| **Production Server** | Docker |
| **Windows Desktop** | Claude Desktop or NSSM |
| **macOS Desktop** | Claude Desktop or launchd |
| **Linux Server** | Docker or systemd |

---

## Security Best Practices

⚠️ **Never commit API keys to version control!**

**For development:**
```bash
# Create .env file (add to .gitignore!)
echo ".env" >> .gitignore

# Store secrets in .env
cat > .env << 'EOF'
DD_API_KEY=your-key
DD_APP_KEY=your-key
DD_SITE=us5
EOF
```

**For production:**
- Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
- Use environment variables from secure sources
- Rotate keys regularly
- Use least-privilege API keys

---

## Troubleshooting

### Server won't start

```bash
# Check credentials
echo $DD_API_KEY
echo $DD_APP_KEY

# Test manually
DD_SITE=us5 uv run python -m ddmcp.server
```

### Can't connect from Claude Desktop

1. Check the server is running
2. Verify config path is correct for your OS
3. Restart Claude Desktop
4. Check logs for errors

### Docker issues

```bash
# Check container logs
docker logs ddmcp-server

# Check environment variables
docker exec ddmcp-server env | grep DD_

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Permission errors

**Linux/macOS:**
```bash
# Make sure uv is executable
which uv

# Check Python path
which python3
```

**Windows:**
```powershell
# Check paths
where uv
where python
```

---

## Next Steps

1. Choose your deployment method
2. Configure credentials
3. Test the server
4. Set up monitoring (optional)

For questions or issues, see the [main README](README.md) or open an issue on GitHub.
