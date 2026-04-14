"""UART MCP - Servidor MCP Universal para comunicación serie."""

from mcp.server.fastmcp import FastMCP
import serial
import serial.tools.list_ports
import os
import json
import configparser
from datetime import datetime
from pathlib import Path

mcp = FastMCP("UART MCP")

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = DATA_DIR / "logs"
CONFIG_FILE = BASE_DIR / "utils" / "config.ini"
PUTTY_PATH_DEFAULT = "C:\\Program Files\\PuTTY\\putty.exe"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 10

BASIC_COMMANDS = [
    "ls",
    "cat",
    "pwd",
    "cd",
    "grep",
    "find",
    "head",
    "tail",
    "ip",
    "ifconfig",
    "route",
    "netstat",
    "arp",
    "ping",
    "df",
    "du",
    "free",
    "top",
    "ps",
    "whoami",
    "uname",
    "uptime",
    "hostname",
    "id",
    "date",
    "mount",
    "lsmod",
    "lspci",
    "lsusb",
    "dmesg",
    "strings",
    "hexdump",
    "file",
]

session_active = {"port": None, "ser": None, "proyecto": None, "dispositivo": None}

PUTTY_PATH = None  # Se carga desde config o usa默认值


def load_config():
    """Cargar configuración de utils/config.ini"""
    global PUTTY_PATH
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
        if config.has_option("putty", "path"):
            PUTTY_PATH = config.get("putty", "path")
        return config
    PUTTY_PATH = PUTTY_PATH_DEFAULT
    return {}


def load_devices():
    devices_file = DATA_DIR / "devices.json"
    if devices_file.exists():
        return json.loads(devices_file.read_text())
    return {"devices": {}}


def save_devices(data):
    (DATA_DIR / "devices.json").write_text(json.dumps(data, indent=2))


def load_session_index():
    session_file = DOCS_DIR / "session.md"
    if session_file.exists():
        return session_file.read_text()
    return ""


def save_session_index(content):
    (DOCS_DIR / "session.md").write_text(content)


def get_project_doc(project: str) -> Path:
    project_dir = DOCS_DIR / project
    project_dir.mkdir(exist_ok=True)
    return project_dir / f"{project}.md"


def init_project_doc(proyecto: str, puerto: str, dispositivo: str = ""):
    doc_file = get_project_doc(proyecto)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    if not doc_file.exists():
        content = f"""---
title: Sesión {proyecto}
created: {date_str}
modified: {date_str}
port: {puerto}
dispositivo: {dispositivo or "Desconocido"}
---

# Sesión {proyecto}

## Proyecto: {proyecto}

### Sesión 1 - {now.strftime("%d %B %Y")}

#### Conexión
- Puerto: {puerto}
- Dispositivo: {dispositivo or "No identificado"}
- Resultado: ✓ Conectado

#### Comandos Probados

| Comando | Resultado | Notas |
|---------|----------|-------|

#### Comandos Funcionales

"""
        doc_file.write_text(content)

    update_session_index(proyecto, "Activo")
    return doc_file


def update_session_index(proyecto: str, status: str = "Activo"):
    session_file = DOCS_DIR / "session.md"
    now = datetime.now().strftime("%d %B %Y")
    content = load_session_index()

    if f"### {proyecto}" in content:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"### {proyecto}"):
                new_lines.append(line)
                new_lines.append(f"- Estado: [[{proyecto}/{proyecto}.md|{status}]]")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        header = (
            """---
title: Sesiones UART
---

# Sesiones UART

## Proyecto Activo
- **Proyecto:** """
            + proyecto
            + """
- **Última sesión:** """
            + now
            + """
- **Estado:** """
            + status
            + """

## Historial de Proyectos

"""
        )
        if not content:
            content = header
        content += f"### {proyecto}\n- Inicio: {now}\n- Puerto:\n- Dispositivo:\n- Estado: [[{proyecto}/{proyecto}.md|{status}]]\n\n"

    save_session_index(content)


@mcp.tool()
def uart_puertos() -> str:
    """Lista los puertos serie disponibles en el sistema."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return "No hay puertos serie disponibles."

    result = "Puertos serie disponibles:\n"
    for i, port in enumerate(ports, 1):
        result += f"{i}. {port.device}"
        if port.description:
            result += f" - {port.description}"
        result += "\n"
    return result


@mcp.tool()
def uart_conectar(proyecto: str, puerto: str = None, dispositivo: str = None) -> str:
    """Conectar a un proyecto existente o crear uno nuevo.

    - Si el proyecto ya existe en memoria → conectar automáticamente (no necesita puerto/dispositivo)
    - Si es proyecto nuevo → PREGUNTAR puerto y dispositivo al usuario

    Ejemplo proyecto existente: uart_conectar(proyecto="rpi2_casa")
    Ejemplo proyecto nuevo: uart_conectar(proyecto="mi_nuevo_proyecto", puerto="COM4", dispositivo="Raspberry Pi")

    IMPORTANTE: Si es la primera vez con este proyecto, DEBES preguntar al usuario:
    - ¿Qué puerto COM?
    - ¿Qué dispositivo?
    No asumas nada."""
    global session_active

    if session_active.get("ser") and session_active["ser"].is_open:
        return f"Ya hay conexión activa en {session_active['port']}. Usa uart_desconectar() primero."

    proyecto = proyecto.strip().lower().replace(" ", "_")

    doc = get_project_doc(proyecto)

    if doc.exists():
        content = doc.read_text()
        if "puerto:" in content.lower():
            for line in content.split("\n"):
                if line.lower().startswith("port:") or line.lower().startswith(
                    "- puerto:"
                ):
                    puerto_guardado = (
                        line.split(":")[1].strip() if ":" in line else None
                    )
                    if puerto_guardado:
                        puerto = puerto_guardado
                        break

        for line in content.split("\n"):
            if line.lower().startswith("dispositivo:") or line.lower().startswith(
                "- dispositivo:"
            ):
                disp = line.split(":")[1].strip() if ":" in line else None
                if disp and disp != "No identificado":
                    dispositivo = disp
                    break

    if not puerto or not dispositivo:
        return f"⚠️ PRIMERA VEZ con proyecto '{proyecto}'. Debes PREGUNTAR al usuario:\n- ¿Qué puerto COM usar? (ej: COM4, COM5)\n- ¿Qué dispositivo es? (ej: Raspberry Pi, Router OpenWrt, Stick GPON)\n\nNo asumas el puerto - espera respuesta del usuario."

    try:
        ser = serial.Serial(
            port=puerto,
            baudrate=DEFAULT_BAUD,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=DEFAULT_TIMEOUT,
            write_timeout=DEFAULT_TIMEOUT,
        )
        session_active = {
            "port": puerto,
            "ser": ser,
            "proyecto": proyecto,
            "dispositivo": dispositivo,
            "baudrate": DEFAULT_BAUD,
        }

        init_project_doc(proyecto, puerto, dispositivo)

        return f"✓ Conectado a {puerto}\n📱 Dispositivo: {dispositivo}\n📁 Proyecto: {proyecto}"

    except Exception as e:
        return f"Error al conectar: {e}"


@mcp.tool()
def uart_desconectar() -> str:
    """Cerrar la conexión serie activa."""
    global session_active

    if not session_active.get("ser") or not session_active["ser"].is_open:
        session_active = {"port": None, "ser": None, "proyecto": None}
        return "No hay conexión activa."

    try:
        session_active["ser"].close()
        proyecto = session_active.get("proyecto")
        session_active = {"port": None, "ser": None, "proyecto": None}

        if proyecto:
            update_session_index(proyecto, "Cerrado")

        return "✓ Desconectado."

    except Exception as e:
        return f"Error al desconectar: {e}"


@mcp.tool()
def uart_estado() -> str:
    """Ver el estado de la conexión serie."""
    if not session_active.get("ser") or not session_active["ser"].is_open:
        return "Sin conexión activa. Usa uart_conectar() primero."

    info = session_active
    return f"Conectado: {info['port']} | 📱 {info.get('dispositivo', 'N/A')} | 📁 {info.get('proyecto', 'N/A')}"


@mcp.tool()
def uart_comando(cmd: str) -> str:
    """Enviar un comando al dispositivo. Ejemplo: uart_comando("ls -la")"""
    global session_active

    ser = session_active.get("ser")
    proyecto = session_active.get("proyecto")

    if not ser or not ser.is_open:
        return "ERROR: No hay conexion. Usa uart_conectar(puerto='COM4', proyecto='nombre')"

    cmd_base = cmd.strip().split()[0] if cmd.strip() else ""

    if proyecto and cmd_base not in BASIC_COMMANDS:
        doc = get_project_doc(proyecto)
        if doc.exists():
            content = doc.read_text()
            if cmd_base not in content:
                return f"⚠️ '{cmd_base}' no está en comandos básicos. ¿Confirmas ejecución de '{cmd}'?"

    try:
        ser.reset_input_buffer()
        ser.write(f"{cmd}\n".encode())
        ser.flush()

        response = ""
        start = datetime.now()

        while (datetime.now() - start).seconds < DEFAULT_TIMEOUT:
            if ser.in_waiting > 0:
                try:
                    data = ser.read(ser.in_waiting)
                    response += data.decode("utf-8", errors="replace")
                except:
                    response += data.decode("latin-1", errors="replace")
            else:
                if response.strip():
                    break

        success = bool(response.strip())

        if proyecto:
            log_to_project(proyecto, cmd, response, success)

        if not success:
            return f"⚠️ El comando '{cmd}' no dio resultado.\n\nPosibles causas:\n- Comando no disponible\n- Timeout\n- Necesita interacción manual\n\nPara sesión interactiva: usa uart_putty_abrir()"

        return response if response else "✓ Enviado."

    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def uart_ver() -> str:
    """Ver los datos pendientes en el puerto serie."""
    global session_active

    ser = session_active.get("ser")
    if not ser or not ser.is_open:
        return "No hay conexión."

    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        return data.decode("utf-8", errors="replace")
    return "Sin datos pendientes."


@mcp.tool()
def uart_enviar(datos: str) -> str:
    """Enviar datos crudos al dispositivo."""
    global session_active

    ser = session_active.get("ser")
    if not ser or not ser.is_open:
        return "No hay conexión."

    try:
        ser.write(datos.encode())
        ser.flush()
        return f"✓ Enviados {len(datos)} bytes."
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def uart_break() -> str:
    """Enviar señal BREAK para reiniciar."""
    global session_active

    ser = session_active.get("ser")
    if not ser or not ser.is_open:
        return "No hay conexión."

    try:
        ser.send_break()
        return "✓ Señal BREAK enviada."
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def uart_info() -> str:
    """Ver información del dispositivo conectado."""
    proyecto = session_active.get("proyecto")

    if not proyecto:
        return "No hay proyecto activo."

    dispositivo = session_active.get("dispositivo", "Desconocido")
    port = session_active.get("port", "N/A")

    return f"""📡 {proyecto}
- Puerto: {port}
- Dispositivo: {dispositivo}
- Usa uart_comando("ls") para listar"""


@mcp.tool()
def uart_dispositivos() -> str:
    """Lista todos los dispositivos conocidos."""
    devices = load_devices()
    all_dev = devices.get("devices", {})

    if not all_dev:
        return "No hay dispositivos registrados."

    result = "Dispositivos:\n"
    for name, info in all_dev.items():
        result += f"• {name}: {info.get('port', 'N/A')}\n"
    return result


@mcp.tool()
def uart_proyecto() -> str:
    """Ver el documento del proyecto actual."""
    proyecto = session_active.get("proyecto")

    if not proyecto:
        return "Ningún proyecto activo."

    doc = get_project_doc(proyecto)

    if doc.exists():
        return doc.read_text()

    return f"No hay documento para {proyecto}."


@mcp.tool()
def uart_indice() -> str:
    """Ver el índice de todos los proyectos."""
    return load_session_index()


@mcp.tool()
def uart_proyectos() -> str:
    """Lista todos los proyectos."""
    if not DOCS_DIR.exists():
        return "No hay proyectos."

    dirs = [d.name for d in DOCS_DIR.iterdir() if d.is_dir()]

    if not dirs:
        return "No hay proyectos."

    return "Proyectos:\n" + "\n".join(f"• {p}" for p in dirs)


@mcp.tool()
def uart_configurar(accion: str = None) -> str:
    """Configurar el entorno de UART MCP.

    Sin argumentos: Ejecuta scan y muestra menú interactivo.
    Con accion: Ejecuta la acción seleccionada.

    Acciones disponibles:
    - "scan": Buscar ejecutables en el sistema
    - "copiar": Copiar ejecutables encontrados a utils/portable/
    - "descargar": Descargar PuTTY automáticamente
    - "omitir": Usar solo conexión serie directa

    El LLM debe guiar al usuario seleccionar una opción."""
    import platform
    import shutil

    os_name = platform.system()
    found_paths = {}

    # Buscar ejecutables según SO
    if os_name == "Windows":
        putty_paths = [
            "C:\\Program Files\\PuTTY\\putty.exe",
            "C:\\Program Files (x86)\\PuTTY\\putty.exe",
        ]
        for path in putty_paths:
            if os.path.exists(path):
                found_paths["putty"] = path
                break

        moba_paths = [
            "C:\\Program Files (x86)\\Mobatek\\MobaXterm\\MobaXterm.exe",
        ]
        for path in moba_paths:
            if os.path.exists(path):
                found_paths["mobaxterm"] = path
                break

    elif os_name == "Linux":
        putty_path = shutil.which("putty")
        if putty_path:
            found_paths["putty"] = putty_path

    elif os_name == "Darwin":
        putty_path = shutil.which("putty")
        if putty_path:
            found_paths["putty"] = putty_path

    # Menu interactivo
    if accion is None:
        if found_paths:
            return f"""🔍 **UTILIDADES ENCONTRADAS** ({os_name})

Encontré las siguientes herramientas:
{chr(10).join(f"- {k}: {v}" for k, v in found_paths.items())}

**¿Qué deseas hacer?**

[S] Copiar a utils/portable/ (incluye ejecutables en el proyecto)
[N] Solo guardar rutas (usa herramientas del sistema)
[D] Descargar/reinstalar otra versión
[X] Omitir - Usar solo conexión serie directa

**Nota:** Después de copiar, reinicia el MCP para aplicar cambios."""

        else:
            return f"""⚠️ **NO SE ENCONTRARON UTILIDADES** ({os_name})

No encontré PuTTY ni MobaXterm en este sistema.

**Opciones disponibles:**

[D] Descargar PuTTY automáticamente
[M] Lo manejo manualmente (crear config.ini)
[X] Omitir - Usar solo conexión serie directa

**Para descargar PuTTY:**
- Windows: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
- Linux: `sudo apt install putty` o `sudo yum install putty`
- macOS: `brew install putty`"""

    # Procesar acciones
    accion = accion.strip().lower() if accion else ""

    if accion == "scan":
        if found_paths:
            return f"✓ Encontrado: {', '.join(f'{k} en {v}' for k, v in found_paths.items())}"
        else:
            return f"⚠️ No se encontraron ejecutables en {os_name}"

    elif accion == "copiar":
        if not found_paths:
            return "⚠️ No hay ejecutables para copiar. Ejecuta uart_configurar() sin argumentos primero."

        PORTABLE_DIR = BASE_DIR / "utils" / "portable"
        PORTABLE_DIR.mkdir(exist_ok=True)

        copied = []
        for name, src_path in found_paths.items():
            try:
                import shutil as sh

                dst = PORTABLE_DIR / src_path.split("\\")[-1].split("/")[-1]
                sh.copy2(src_path, dst)
                copied.append((name, str(dst)))
            except Exception as e:
                return f"⚠️ Error al copiar {name}: {e}"

        config_content = "# Configuración generada automáticamente\n"
        for name, path in copied:
            config_content += f"\n[{name}]\npath = {path}\n"

        try:
            CONFIG_FILE.write_text(config_content)
            load_config()
            return f"""✓ Utilidades copiadas a utils/portable/:

{chr(10).join(f"- {k}: {v}" for k, v in copied)}

⚠️ **REINICIA el MCP** para aplicar los cambios.

Después del reinicio, usa uart_putty_abrir()"""
        except Exception as e:
            return f"⚠️ Error al guardar config: {e}"

    elif accion == "descargar":
        return uart_descargar_putty()

    elif accion == "omitir":
        return "✓ Entendido. Usarás solo conexión serie directa.\n\nUsa uart_conectar() para conectar a dispositivos."

    else:
        return """⚠️ Acción no reconocida.

Acciones válidas:
- uart_configurar("scan") - Buscar ejecutables
- uart_configurar("copiar") - Copiar a utils/portable/
- uart_configurar("descargar") - Descargar PuTTY
- uart_configurar("omitir") - Usar solo serie directa"""


@mcp.tool()
def uart_descargar_putty() -> str:
    """Descargar e instalar PuTTY automáticamente.

    Detecta el sistema operativo y descarga la versión appropriate.
    Guarda los archivos en utils/portable/ y configura automáticamente."""
    import platform
    import urllib.request
    import zipfile
    import io

    os_name = platform.system()
    arch = platform.machine()

    PORTABLE_DIR = BASE_DIR / "utils" / "portable"
    PORTABLE_DIR.mkdir(exist_ok=True)

    # URLs de descarga según SO
    if os_name == "Windows":
        if arch in ["AMD64", "x86_64"]:
            url = "https://the.earth.li/~sgtatham/putty/latest/64-bit/putty-64bit.zip"
        else:
            url = "https://the.earth.li/~sgtatham/putty/latest/win32/putty.zip"
    elif os_name == "Linux":
        return """⚠️ En Linux se recomienda instalar via package manager:

sudo apt install putty        # Debian/Ubuntu
sudo yum install putty        # RedHat/CentOS
sudo dnf install putty        # Fedora

Después de instalar, ejecuta uart_configurar("scan") para detectar."""
    elif os_name == "Darwin":
        return """⚠️ En macOS se recomienda instalar via Homebrew:

brew install putty

Después de instalar, ejecuta uart_configurar("scan") para detectar."""
    else:
        return f"⚠️ Sistema operativo no soportado: {os_name}"

    try:
        return f"""📥 Descargando PuTTY para {os_name} ({arch})...

URL: {url}

Pero espera - la descarga directa tiene limitaciones:
1. Require verificar SSL/certificados
2. Grandes archivos pueden fallar
3. Sin progreso de descarga visible

**Mejor alternativa:**
1. Descarga manualmente desde: https://putty.org
2. Guarda el archivo .exe en: {PORTABLE_DIR}
3. Ejecuta: uart_configurar("scan")

**O usa el gestor de paquetes de tu sistema:**
- Windows:winget install PuTTY.PuTTY
- Linux: sudo apt install putty
- macOS: brew install putty"""

    except Exception as e:
        return f"⚠️ Error al preparar descarga: {e}"


def log_to_project(proyecto: str, command: str, result: str, success: bool):
    doc = get_project_doc(proyecto)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    if not doc.exists():
        return

    content = doc.read_text()

    content = content.replace("modified:", f"modified: {date_str}")

    result_emoji = "✓" if success else "✗"

    content += f"""

### {now.strftime("%H:%M")} - `{command}`
```
{result}
```

| Comando | Resultado |
|---------|----------|
| {command} | {result_emoji} |

"""

    doc.write_text(content)

    log_file = LOGS_DIR / f"{proyecto}.log"
    with open(log_file, "a") as f:
        f.write(
            f"[{date_str} {now.strftime('%H:%M:%S')}] {command}: {'OK' if success else 'FAIL'}\n"
        )


def main():
    load_config()
    mcp.run()


@mcp.tool()
def uart_putty_abrir() -> str:
    """Abrir PuTTY para sesión serie interactiva.

    Requiere que uart_configurar() se haya ejecutado antes para detectar PuTTY.
    Si no hay configuración, retorna instrucciones para configurar."""
    import subprocess

    global PUTTY_PATH
    load_config()  # Cargar config actualizada

    if not PUTTY_PATH:
        return "⚠️ PuTTY no configurado. Ejecuta uart_configurar() primero."

    putty_path = PUTTY_PATH

    try:
        if session_active.get("ser") and session_active["ser"].is_open:
            port = session_active["port"]
            baud = session_active.get("baudrate", DEFAULT_BAUD)
            subprocess.Popen([putty_path, "-serial", port, "-sercfg", f"{baud},8,n,1"])
            return f"✓ PuTTY abierto en {port}"
        else:
            subprocess.Popen([putty_path])
            return "✓ PuTTY abierto."
    except Exception as e:
        return f"ERROR: {e}"


if __name__ == "__main__":
    main()
