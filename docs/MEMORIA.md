# Serial MCP Toolkit

## Resumen

MCP universal para control de dispositivos por puerto serie/UART. Desarrollado como herramienta para conectar a dispositivos serie (Raspberry Pi, routers, switches, GPON sticks, etc.) desde cualquier cliente MCP.

## Características

- **Universal**: Funciona con cualquier dispositivo con consola serie
- **Multi-plataforma**: Windows, Linux, macOS
- **Multi-LLM**: Compatible con cualquier cliente MCP
- **Memoria por proyecto**: Documenta comandos funcionales
- **Configuración automática**: Detecta PuTTY y utilerías

## Estructura

```
C:/homelab/laboratorio/serial-mcp-toolkit/
├── src/uart_mcp/server.py    # Servidor MCP (17 funciones)
├── data/                    # Memoria de dispositivos
├── docs/                    # Documentación por proyecto
├── utils/
│   ├── config.example.ini  # Template de configuración
│   └── REFERENCIAS.md       # Guía de rutas
└── .venv/                   # Entorno virtual con uart-mcp.exe
```

## Herramientas MCP

| Herramienta | Descripción |
|-------------|-------------|
| `uart_configurar()` | Configura el entorno (scan/copiar/descargar/omitir) |
| `uart_descargar_putty()` | Guía de descarga de PuTTY |
| `uart_puertos()` | Lista puertos serie disponibles |
| `uart_conectar(proyecto, puerto, dispositivo)` | Conecta a proyecto |
| `uart_desconectar()` | Cierra conexión |
| `uart_estado()` | Muestra estado de conexión |
| `uart_comando(cmd)` | Envía comando al dispositivo |
| `uart_ver()` | Ver datos pendientes |
| `uart_enviar(datos)` | Enviar datos crudos |
| `uart_break()` | Señal BREAK |
| `uart_info()` | Info del proyecto activo |
| `uart_dispositivos()` | Lista dispositivos conocidos |
| `uart_proyecto()` | Ver documento del proyecto |
| `uart_indice()` | Ver índice de proyectos |
| `uart_proyectos()` | Listar proyectos |
| `uart_putty_abrir()` | Abrir PuTTY para sesión interactiva |

## Integración OpenCode

- **Ubicación**: `C:\homelab\laboratorio\serial-mcp-toolkit\.venv\Scripts\uart-mcp.exe`
- **Configuración**: `C:\homelab\.mcp.json` (serial-mcp)
- **GitHub**: https://github.com/CTRQuko/serial-mcp-toolkit

## Uso Típico

```python
# 1. Configurar entorno
uart_configurar()

# 2. Conectar (primera vez)
uart_conectar(proyecto="mi_rpi", puerto="COM4", dispositivo="Raspberry Pi")

# 3. Enviar comandos
uart_comando("ls -la")
uart_comando("ip route show")

# 4. Ver documentación
uart_proyecto()
uart_indice()

# 5. Desconectar
uart_desconectar()
```

## Notas

-Primera vez: El LLM pregunta puerto y dispositivo al usuario
- Sesiones siguientes: Conecta automáticamente desde la memoria
- PuTTY es opcional: Funciona con conexión serie directa
- Datos locales excluidos de git (config.ini, devices.json, logs/)