"""UART MCP Server - Main entry point.

Thin registration layer. All logic lives in the module files:
  - connection.py  → SessionManager, Session, ConnectionManager
  - security.py     → Command validation & metacharacter detection
  - encodings.py    → Hex/base64/text data conversion
  - checksums.py    → CRC-8, XOR, sum checksums
  - project.py      → Project documentation & logging
  - putty.py        → PuTTY detection, download, launch
  - validators.py   → Serial params validation (baud, parity, etc.)
  - config.py        → Paths, constants, config loading
  - errors.py       → Typed exceptions
"""

import asyncio
import uuid
from datetime import datetime

import serial
from mcp.server.fastmcp import FastMCP

from . import (
    __version__,
    DEFAULT_BAUD,
    DEFAULT_DATA_BITS,
    DEFAULT_STOP_BITS,
    DEFAULT_PARITY,
    DEFAULT_FLOW_CONTROL,
    IDLE_TIMEOUT_SECONDS,
    DataConverter,
    ConnectionManager,
    SessionConfig,
    has_shell_metacharacters,
    validate_command,
    detect_putty,
    copy_to_portable,
    download_putty,
    launch_putty,
    init_project_doc,
    update_session_index,
    load_session_index,
    get_project_doc,
    log_to_project,
    compute_checksum,
    verify_checksum,
    load_devices,
    UartError,
    ConnectionError,
    SessionError,
    SecurityError,
    ValidationError,
    EncodingError,
)

mcp = FastMCP(
    "UART MCP",
    instructions="""UART MCP - Universal serial port communication server.

Tools for connecting to embedded devices via UART/serial: routers, modems,
GPON sticks, Arduino, STM32, etc. Supports hex/base64 encoding, checksums,
project documentation, and PuTTY integration.""",
)

_manager = ConnectionManager()


def _active_session_id() -> str | None:
    sessions = _manager.list_sessions()
    active = [s for s in sessions if s["state"] == "active"]
    return active[0]["session_id"] if active else None


def _get_active():
    sid = _active_session_id()
    if not sid:
        return None
    return _manager.get(sid)


# ── Port Discovery ──────────────────────────────────────────────────────────


@mcp.tool()
def uart_puertos() -> str:
    """Lista los puertos serie disponibles en el sistema."""
    ports = ConnectionManager.list_ports()
    if not ports:
        return "No hay puertos serie disponibles."
    result = "Puertos serie disponibles:\n"
    for i, p in enumerate(ports, 1):
        result += f"{i}. {p['device']} - {p['description']}"
        if p.get("hwid"):
            result += f" ({p['hwid']})"
        result += "\n"
    return result


# ── Session Management ──────────────────────────────────────────────────────


@mcp.tool()
def uart_conectar(
    proyecto: str,
    puerto: str = None,
    dispositivo: str = None,
    baudrate: int = DEFAULT_BAUD,
    data_bits: int = DEFAULT_DATA_BITS,
    stop_bits=DEFAULT_STOP_BITS,
    parity: str = DEFAULT_PARITY,
    flow_control: str = DEFAULT_FLOW_CONTROL,
    auto_reconnect: bool = False,
) -> str:
    """Conectar a un proyecto existente o crear uno nuevo.

    - Si el proyecto ya existe en memoria → conectar automaticamente
    - Si es proyecto nuevo → PREGUNTAR puerto y dispositivo al usuario

    Parametros serie completos: baudrate, data_bits (5-8), stop_bits (1/1.5/2),
    parity (none/even/odd/mark/space), flow_control (none/software/hardware).
    auto_reconnect: Si True, reconecta automaticamente al perder conexion.

    IMPORTANTE: Si es la primera vez con este proyecto, DEBES preguntar al usuario:
    - ?Que puerto COM? - ?Que dispositivo? No asumas nada."""
    try:
        config = SessionConfig.from_params(
            port=puerto or "",
            baudrate=baudrate,
            data_bits=data_bits,
            stop_bits=stop_bits,
            parity=parity,
            flow_control=flow_control,
        )
        config.auto_reconnect = auto_reconnect
    except ValidationError as e:
        return f"[ERROR] Parametros invalidos: {e}"

    if not puerto or not dispositivo:
        existing = _manager.list_sessions()
        for s in existing:
            if s["project"] == proyecto.strip().lower().replace(" ", "_"):
                return f"[WARN] Proyecto '{proyecto}' ya tiene sesion activa ({s['session_id'][:12]}...). Usa uart_estado() para ver."

        return (
            f"[WARN] PRIMERA VEZ con proyecto '{proyecto}'. "
            f"Debes PREGUNTAR al usuario:\n"
            f"- ?Que puerto COM usar? (ej: COM4, COM5)\n"
            f"- ?Que dispositivo es? (ej: Raspberry Pi, Router OpenWrt, Stick GPON)\n\n"
            f"No asumas el puerto - espera respuesta del usuario."
        )

    session_id = f"uart_{uuid.uuid4().hex[:12]}"
    proyecto = proyecto.strip().lower().replace(" ", "_")

    try:
        session = _manager.connect(session_id, proyecto, dispositivo, config)
    except (ConnectionError, SessionError) as e:
        return f"[ERROR] {e}"

    init_project_doc(
        proyecto,
        puerto,
        dispositivo,
        baudrate,
        data_bits,
        stop_bits,
        parity,
        flow_control,
    )

    return (
        f"[OK] Conectado a {puerto}\n"
        f"[DEV] Dispositivo: {dispositivo}\n"
        f"[PRJ] Proyecto: {proyecto}\n"
        f"[CFG] {config.config_string()}\n"
        f"[SID] Sesion: {session_id}"
    )


@mcp.tool()
def uart_desconectar() -> str:
    """Cerrar la conexion serie activa."""
    session = _get_active()
    if not session:
        return "No hay conexion activa."

    proyecto = session.project
    try:
        _manager.disconnect(session.session_id)
    except SessionError:
        pass

    if proyecto:
        update_session_index(proyecto, "Cerrado")

    return "[OK] Desconectado."


@mcp.tool()
def uart_estado() -> str:
    """Ver el estado de la conexion serie activa."""
    session = _get_active()
    if not session:
        return "Sin conexion activa. Usa uart_conectar() primero."

    info = session.to_dict()
    return (
        f"Conectado: {info['port']} | "
        f"[DEV] {info['device']} | "
        f"[PRJ] {info['project']} | "
        f"[CFG] {info['config']} | "
        f"[SID] {info['session_id'][:12]}..."
    )


@mcp.tool()
def uart_sesiones() -> str:
    """Lista todas las sesiones UART (activas e inactivas)."""
    sessions = _manager.list_sessions()
    if not sessions:
        return "No hay sesiones registradas."

    lines = ["Sesiones UART:"]
    for s in sessions:
        status = "ACTIVA" if s["state"] == "active" else s["state"]
        lines.append(
            f"  [{status}] {s['session_id'][:12]}... | {s['port']} | {s['project']} | {s['config']}"
        )
    return "\n".join(lines)


# ── Data I/O ────────────────────────────────────────────────────────────────


@mcp.tool()
def uart_comando(cmd: str) -> str:
    """Enviar un comando al dispositivo. Ejemplo: uart_comando("ls -la")

    WARNING: Los comandos se validan contra una whitelist de seguridad.
    Metacaracteres como ;, &, |, $ estan prohibidos."""
    session = _get_active()
    if not session:
        return "ERROR: No hay conexion. Usa uart_conectar() primero."

    allowed, reason = validate_command(cmd, session.project)
    if not allowed:
        return reason

    ser = session.ser
    proyecto = session.project

    if not ser or not ser.is_open:
        if session.config.auto_reconnect:
            reconnected = session.try_reconnect()
            if not reconnected:
                return (
                    f"[ERROR]Conexion perdida, fallo al reconectar "
                    f"(intentos: {session._reconnect_attempts})."
                )
            ser = session.ser
        else:
            return "[ERROR] Conexion perdida. Reconecta con uart_conectar()."

    try:
        ser.reset_input_buffer()
        ser.write(f"{cmd}\n".encode())
        ser.flush()

        long_running = any(
            c in cmd.lower()
            for c in [
                "ping",
                "traceroute",
                "opkg update",
                "opkg install",
                "wget",
                "curl",
            ]
        )
        read_delay = 2 if long_running else 0.5
        timeout = 120 if long_running else 30

        response = ""
        start = datetime.now()
        last_data_time = start

        while (datetime.now() - start).seconds < timeout:
            if ser.in_waiting > 0:
                try:
                    data = ser.read(ser.in_waiting)
                    response += data.decode("utf-8", errors="replace")
                    last_data_time = datetime.now()
                except Exception:
                    response += data.decode("latin-1", errors="replace")
                    last_data_time = datetime.now()
            else:
                if (
                    datetime.now() - last_data_time
                ).seconds >= read_delay and response.strip():
                    break

        success = bool(response.strip())

        session.stats.record_send(len(cmd.encode()))
        session.stats.record_receive(len(response.encode()))

        if proyecto:
            log_to_project(proyecto, cmd, response[:2000], success)

        if not success:
            return (
                f"[WARN] El comando '{cmd}' no dio resultado.\n\n"
                f"Posibles causas:\n- Comando no disponible\n- Timeout\n"
                f"- Necesita interaccion manual\n\nPara sesion interactiva: usa uart_putty_abrir()"
            )

        return response if response else "[OK] Enviado."

    except serial.SerialException as e:
        session.stats.record_error()
        if session.config.auto_reconnect:
            reconnected = session.try_reconnect()
            if reconnected:
                return (
                    "[WARN] Conexion se perdio pero se reconecto. Reenvia el comando."
                )
        return f"ERROR: {e}"
    except Exception as e:
        session.stats.record_error()
        return f"ERROR: {e}"


@mcp.tool()
def uart_ver(encoding: str = "utf8") -> str:
    """Ver los datos pendientes en el puerto serie.

    Args:
        encoding: Formato de salida - utf8 (defecto), hex, base64"""
    session = _get_active()
    if not session:
        return "No hay conexion."

    if not session.ser or not session.ser.is_open:
        if session.config.auto_reconnect:
            reconnected = session.try_reconnect()
            if not reconnected:
                return "[ERROR] Conexion perdida, fallo al reconectar."
        else:
            return "[ERROR] Conexion perdida."

    if session.ser.in_waiting > 0:
        data = session.ser.read(session.ser.in_waiting)
        session.stats.record_receive(len(data))
        try:
            return DataConverter.encode(data, encoding)
        except EncodingError as e:
            return f"[ERROR] {e}"
    return "Sin datos pendientes."


@mcp.tool()
def uart_enviar(datos: str, encoding: str = "utf8") -> str:
    """Enviar datos crudos al dispositivo.

    Args:
        datos: Datos a enviar
        encoding: Formato de entrada - utf8 (defecto), hex, base64"""
    session = _get_active()
    if not session:
        return "No hay conexion."

    try:
        raw = DataConverter.decode(datos, encoding)
    except EncodingError as e:
        return f"[ERROR] {e}"

    if not session.ser or not session.ser.is_open:
        if session.config.auto_reconnect:
            reconnected = session.try_reconnect()
            if not reconnected:
                return "[ERROR] Conexion perdida, fallo al reconectar."
        else:
            return "[ERROR] Conexion perdida."

    try:
        session.ser.write(raw)
        session.ser.flush()
        session.stats.record_send(len(raw))
        return f"[OK] Enviados {len(raw)} bytes (encoding: {encoding})."
    except serial.SerialException as e:
        session.stats.record_error()
        if session.config.auto_reconnect:
            reconnected = session.try_reconnect()
            if reconnected:
                return "[WARN] Conexion perdida pero reconectada. Reenvia los datos."
        return f"ERROR: {e}"
    except Exception as e:
        session.stats.record_error()
        return f"ERROR: {e}"


@mcp.tool()
def uart_break() -> str:
    """Enviar senal BREAK para reiniciar."""
    session = _get_active()
    if not session:
        return "No hay conexion."

    if not session.ser or not session.ser.is_open:
        return "[ERROR] Conexion perdida."

    try:
        session.ser.send_break()
        return "[OK] Senal BREAK enviada."
    except Exception as e:
        session.stats.record_error()
        return f"ERROR: {e}"


# ── Info & Stats ───────────────────────────────────────────────────────────


@mcp.tool()
def uart_info() -> str:
    """Ver informacion completa de la sesion actual, incluyendo estadisticas."""
    session = _get_active()
    if not session:
        return "No hay proyecto activo."

    info = session.to_dict()
    stats = info["stats"]
    return (
        f"📡 {info['project']}\n"
        f"  Puerto: {info['port']}\n"
        f"  Dispositivo: {info['device']}\n"
        f"  Config: {info['config']}\n"
        f"  Sesion: {info['session_id'][:16]}...\n"
        f"  Estado: {info['state']}\n"
        f"  Creada: {info['created_at'][:19]}\n"
        f"  ─── Estadisticas ───\n"
        f"  Bytes enviados: {stats['bytes_sent']}\n"
        f"  Bytes recibidos: {stats['bytes_received']}\n"
        f"  Mensajes enviados: {stats['messages_sent']}\n"
        f"  Mensajes recibidos: {stats['messages_received']}\n"
        f"  Errores: {stats['errors_count']}\n"
        f"  Reconexiones: {stats['reconnections']}\n"
        f"  Ultima actividad: {stats['last_activity'][:19] if stats['last_activity'] else 'N/A'}"
    )


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
    session = _get_active()
    if not session:
        return "Ningun proyecto activo."

    doc = get_project_doc(session.project)
    if doc.exists():
        return doc.read_text()
    return f"No hay documento para {session.project}."


@mcp.tool()
def uart_indice() -> str:
    """Ver el indice de todos los proyectos."""
    return load_session_index()


@mcp.tool()
def uart_proyectos() -> str:
    """Lista todos los proyectos."""
    from .config import DOCS_DIR

    if not DOCS_DIR.exists():
        return "No hay proyectos."

    dirs = [d.name for d in DOCS_DIR.iterdir() if d.is_dir()]
    if not dirs:
        return "No hay proyectos."

    return "Proyectos:\n" + "\n".join(f"• {p}" for p in dirs)


# ── Configuration ───────────────────────────────────────────────────────────


@mcp.tool()
def uart_configurar(accion: str = None) -> str:
    """Configurar el entorno de UART MCP.

    Sin argumentos: Ejecuta scan y muestra menu interactivo.
    Con accion: Ejecuta la accion seleccionada.

    Acciones disponibles:
    - "scan": Buscar ejecutables en el sistema
    - "copiar": Copiar ejecutables encontrados a utils/portable/
    - "descargar": Descargar PuTTY automaticamente
    - "omitir": Usar solo conexion serie directa"""
    found = detect_putty()

    if accion is None:
        if found:
            return (
                f"Utilidades encontradas:\n"
                + "\n".join(f"- {k}: {v}" for k, v in found.items())
                + "\n\nQue deseas hacer?\n\n"
                "[S] Copiar a utils/portable/\n"
                "[N] Solo guardar rutas\n"
                "[D] Descargar PuTTY\n"
                "[X] Omitir - Usar solo serie directa\n\n"
                "Nota: Despues de copiar, reinicia el MCP."
            )
        else:
            return (
                "[WARN] No se encontraron utilidades.\n\n"
                "Opciones:\n\n"
                "[D] Descargar PuTTY automaticamente\n"
                "[M] Lo manejo manualmente (crear config.ini)\n"
                "[X] Omitir - Usar solo serie directa\n\n"
                "Para descargar PuTTY:\n"
                "- Windows: https://putty.org\n"
                "- Linux: sudo apt install putty\n"
                "- macOS: brew install putty"
            )

    accion = accion.strip().lower() if accion else ""

    if accion == "scan":
        if found:
            return (
                f"[OK] Encontrado: {', '.join(f'{k} en {v}' for k, v in found.items())}"
            )
        return "[WARN] No se encontraron ejecutables."

    elif accion == "copiar":
        if not found:
            return "[WARN] No hay ejecutables para copiar. Ejecuta uart_configurar() sin argumentos primero."
        return copy_to_portable(found)

    elif accion == "descargar":
        return download_putty()

    elif accion == "omitir":
        return "[OK] Entendido. Usaras solo conexion serie directa.\n\nUsa uart_conectar() para conectar a dispositivos."

    return (
        "[WARN] Accion no reconocida.\n\n"
        "Acciones validas:\n"
        "- uart_configurar('scan') - Buscar ejecutables\n"
        "- uart_configurar('copiar') - Copiar a utils/portable/\n"
        "- uart_configurar('descargar') - Descargar PuTTY\n"
        "- uart_configurar('omitir') - Usar solo serie directa"
    )


# ── Checksums ───────────────────────────────────────────────────────────────


@mcp.tool()
def uart_checksum(datos: str, algoritmo: str = "xor", encoding: str = "hex") -> str:
    """Calcular checksum de datos.

    Args:
        datos: Datos en hex, base64, o texto plano
        algoritmo: sum, xor, crc8, crc16
        encoding: Formato de entrada (hex, base64, utf8)"""
    try:
        raw = DataConverter.decode(datos, encoding)
    except EncodingError as e:
        return f"[ERROR] {e}"

    try:
        result = compute_checksum(raw, algoritmo)
    except ValueError as e:
        return f"[ERROR] {e}"

    return f"[OK] Checksum {algoritmo}: {result} (0x{result:02X})"


@mcp.tool()
def uart_verificar(
    datos: str, checksum_esperado: int, algoritmo: str = "xor", encoding: str = "hex"
) -> str:
    """Verificar checksum de datos.

    Args:
        datos: Datos a verificar
        checksum_esperado: Valor esperado del checksum
        algoritmo: sum, xor, crc8, crc16
        encoding: Formato de entrada"""
    try:
        raw = DataConverter.decode(datos, encoding)
    except EncodingError as e:
        return f"[ERROR] {e}"

    computed = compute_checksum(raw, algoritmo)
    match = computed == checksum_esperado

    status = (
        "[OK] Checksum correcto"
        if match
        else f"[FAIL] Checksum incorrecto (esperado {checksum_esperado}, calculado {computed})"
    )
    return f"{status}\nAlgoritmo: {algoritmo}\nCalculado: {computed} (0x{computed:02X})\nEsperado: {checksum_esperado} (0x{checksum_esperado:02X})"


# ── PuTTY ───────────────────────────────────────────────────────────────────


@mcp.tool()
def uart_putty_abrir() -> str:
    """Abrir PuTTY para sesion serie interactiva.

    Requiere que uart_configurar() se haya ejecutado antes."""
    session = _get_active()
    port = session.config.port if session else ""
    baud = session.config.baudrate if session else DEFAULT_BAUD
    return launch_putty(port, baud)


# ── Cleanup ────────────────────────────────────────────────────────────────


@mcp.tool()
def uart_limpiar_sesiones(max_idle_seconds: int = IDLE_TIMEOUT_SECONDS) -> str:
    """Limpiar sesiones inactivas que excedan el timeout de inactividad.

    Args:
        max_idle_seconds: Segundos de inactividad para considerar una sesion idle (default 3600)"""
    cleaned = _manager.cleanup_idle(max_idle_seconds)
    if not cleaned:
        return f"[OK] No hay sesiones inactivas para limpiar (timeout: {max_idle_seconds}s)."
    return f"[OK] Limpiadas {len(cleaned)} sesiones inactivas: {', '.join(cleaned)}"


def main():
    from .config import load_config

    load_config()
    mcp.run()


if __name__ == "__main__":
    main()
