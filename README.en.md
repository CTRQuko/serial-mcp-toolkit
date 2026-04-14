# UART MCP

Universal MCP for serial port/UART device control.

## Features

- **Universal**: Works with any device with serial console (Raspberry Pi, routers, switches, GPON sticks, etc.)
- **Multi-platform**: Windows, Linux, macOS
- **Multi-LLM**: Compatible with any MCP client (Claude Desktop, Cursor, etc.)
- **Per-project memory**: Documents working commands for each device
- **Obsidian documentation**: Markdown compatible with Obsidian
- **Separate logs**: Logs in `data/logs/`

## Structure

```
uart-mcp/
├── src/uart_mcp/      # MCP server
│   └── server.py
├── data/
│   ├── devices.json   # Device memory
│   └── logs/          # Session logs
├── docs/
│   ├── session.md     # Project index
│   └── [proyecto]/   # Per-project documentation
├── utils/
│   ├── config.example.ini  # Example configuration
│   └── REFERENCIAS.md      # How to get paths
└── LICENSE
```

## Installation

```bash
cd uart-mcp
uv sync
```

## MCP Configuration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["--directory", "PATH_TO_UART_MCP", "run", "src/uart_mcp/server.py"]
    }
  }
}
```

### Cursor

Add to `cursor_settings.json` or workspace settings:

```json
{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["--directory", "PATH_TO_UART_MCP", "run", "src/uart_mcp/server.py"]
    }
  }
}
```

## PuTTY Configuration

1. Copy `utils/config.example.ini` to `utils/config.ini`
2. Edit paths according to your system (see `utils/REFERENCIAS.md`)

## Available Tools

| Tool | Description |
|------|-------------|
| `uart_configurar()` | Configure environment (scan, copy, download, skip) |
| `uart_descargar_putty()` | Download and install PuTTY automatically |
| `uart_puertos()` | List available serial ports |
| `uart_conectar(proyecto, puerto, dispositivo)` | Connect to existing project or create new one |
| `uart_desconectar()` | Close serial connection |
| `uart_estado()` | Show connection status |
| `uart_comando(cmd)` | Send command to device |
| `uart_ver()` | Read pending data on port |
| `uart_enviar(datos)` | Send raw data |
| `uart_break()` | Send BREAK signal |
| `uart_info()` | Active project information |
| `uart_dispositivos()` | List known devices |
| `uart_proyecto()` | View active project document |
| `uart_indice()` | View all projects index |
| `uart_proyectos()` | List all projects |
| `uart_putty_abrir()` | Open PuTTY for interactive session |

## Usage

### First time with a project

1. User proposes a project name
2. LLM asks: "What COM port?" and "What device?"
3. User responds (e.g., COM4, Raspberry Pi)
4. LLM connects: `uart_conectar(proyecto="my_rpi", puerto="COM4", dispositivo="Raspberry Pi")`

### Subsequent sessions

1. User mentions project name
2. LLM connects automatically: `uart_conectar(proyecto="my_rpi")`
3. Server reads port and device from saved document

### Send commands

```python
uart_comando("ls -la")
uart_comando("ip route show")
uart_comando("cat /etc/config/network")
```

### View project documentation

```python
uart_proyecto()  # Active project document
uart_indice()    # All projects index
uart_proyectos() # Project list
```

## Helper Scripts

```bash
# List serial ports
python utils/scripts/list_ports.py

# Backup memory
python utils/scripts/backup.py

# Open PuTTY
python utils/scripts/open_putty.py COM4 115200
```

## Security

- **DO NOT push to git**: `utils/config.ini` contains local paths (already in .gitignore)
- **Logs**: Logs contain sensitive information, keep locally
- **Passwords**: Do not store passwords in project documents

## License

MIT License - see [LICENSE](./LICENSE) file