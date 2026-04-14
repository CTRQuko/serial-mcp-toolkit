# UART MCP

> **English version:** [README.en.md](./README.en.md)

MCP universal para control de dispositivos por puerto serie/UART.

## Características

- **Universal**: Funciona con cualquier dispositivo con consola serie (Raspberry Pi, routers, switches, GPON sticks, etc.)
- **Multi-plataforma**: Windows, Linux, macOS
- **Multi-LLM**: Compatible con cualquier cliente MCP (Claude Desktop, Cursor, etc.)
- **Memoria por proyecto**: Documenta comandos funcionales para cada dispositivo
- **Documentación Obsidian**: Markdown compatible con Obsidian
- **Logs separados**: Logs en `data/logs/`

## Estructura

```
uart-mcp/
├── src/uart_mcp/      # Servidor MCP
│   └── server.py
├── data/
│   ├── devices.json   # Memoria de dispositivos
│   └── logs/          # Logs de sesiones
├── docs/
│   ├── session.md     # Índice de proyectos
│   └── [proyecto]/   # Documentación por proyecto
├── utils/
│   ├── config.example.ini  # Configuración ejemplo
│   └── REFERENCIAS.md      # Cómo obtener rutas
└── LICENSE
```

## Instalación

```bash
cd uart-mcp
uv sync
```

## Configuración MCP

### Claude Desktop

Agregar en `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["--directory", "RUTA_A_UART_MCP", "run", "src/uart_mcp/server.py"]
    }
  }
}
```

### Cursor

Agregar en `cursor_settings.json` o configuración del workspace:

```json
{
  "mcpServers": {
    "uart-mcp": {
      "command": "uv",
      "args": ["--directory", "RUTA_A_UART_MCP", "run", "src/uart_mcp/server.py"]
    }
  }
}
```

## Configuración de PuTTY

El MCP incluye un sistema de configuración automática:

### Primer uso

```python
# 1. Ejecutar configuración inicial
uart_configurar()

# 2. El LLM mostrará menú interactivo:
#    - [S] Copiar a utils/portable/
#    - [N] Solo guardar rutas
#    - [D] Descargar PuTTY
#    - [X] Omitir - Usar solo serie directa

# 3. Si seleccionas "copiar", reinicia el MCP

# 4. Ahora puedes usar:
uart_putty_abrir()
```

### Opciones de uart_configurar()

| Acción | Descripción |
|--------|-------------|
| sin argumentos | Muestra menú interactivo |
| `uart_configurar("scan")` | Buscar ejecutables |
| `uart_configurar("copiar")` | Copiar a utils/portable/ |
| `uart_configurar("descargar")` | Instrucciones de descarga |
| `uart_configurar("omitir")` | Usar solo conexión serie |

## Herramientas Disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `uart_configurar()` | Configura el entorno (scan, copiar, descargar, omitir) |
| `uart_descargar_putty()` | Descarga e instala PuTTY automáticamente |
| `uart_puertos()` | Lista puertos serie disponibles |
| `uart_conectar(proyecto, puerto, dispositivo)` | Conecta a un proyecto existente o crea uno nuevo |
| `uart_desconectar()` | Cierra la conexión serie |
| `uart_estado()` | Muestra estado de conexión |
| `uart_comando(cmd)` | Envía comando al dispositivo |
| `uart_ver()` | Ver datos pendientes en el puerto |
| `uart_enviar(datos)` | Enviar datos crudos |
| `uart_break()` | Enviar señal BREAK |
| `uart_info()` | Información del proyecto activo |
| `uart_dispositivos()` | Lista dispositivos conocidos |
| `uart_proyecto()` | Ver documento del proyecto |
| `uart_indice()` | Ver índice de todos los proyectos |
| `uart_proyectos()` | Listar todos los proyectos |
| `uart_putty_abrir()` | Abrir PuTTY para sesión interactiva |

## Uso

### Primera vez con un proyecto

1. El usuario propone un nombre de proyecto
2. El LLM pregunta: "¿Qué puerto COM?" y "¿Qué dispositivo?"
3. El usuario responde (ej: COM4, Raspberry Pi)
4. El LLM conecta: `uart_conectar(proyecto="mi_rpi", puerto="COM4", dispositivo="Raspberry Pi")`

### Sesiones siguientes

1. El usuario menciona el nombre del proyecto
2. El LLM conecta automáticamente: `uart_conectar(proyecto="mi_rpi")`
3. El servidor lee puerto y dispositivo del documento guardado

### Enviar comandos

```python
uart_comando("ls -la")
uart_comando("ip route show")
uart_comando("cat /etc/config/network")
```

### Ver documentación del proyecto

```python
uart_proyecto()  # Documento del proyecto activo
uart_indice()    # Índice de todos los proyectos
uart_proyectos() # Lista de proyectos
```

## Scripts Auxiliares

```bash
# Listar puertos serie
python utils/scripts/list_ports.py

# Backup de memoria
python utils/scripts/backup.py

# Abrir PuTTY
python utils/scripts/open_putty.py COM4 115200
```

## Seguridad

- **NO subir a git**: `utils/config.ini` contiene rutas locales (ya está en .gitignore)
- **Logs**: Los logs contienen información sensible, mantener en local
- **Contraseñas**: No almacenar contraseñas en los documentos del proyecto

## Licencia

MIT License - ver archivo [LICENSE](./LICENSE)