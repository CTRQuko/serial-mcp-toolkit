# Bug Report: mcp-uart-serial

**Fecha:** 2026-04-17  
**Auditor:** Claude (audit exhaustivo + comparativa)  
**Proyecto:** mcp-uart-serial v0.1.0  
**Archivo principal:** `src/uart_mcp/server.py` (928 líneas)

---

## P0 — Crash (Bloqueante)

### BUG-001: `BASE_DIR` no definido — `uart_configurar("copiar")` y `uart_descargar_putty()` crashean

| Campo | Valor |
|-------|-------|
| **Líneas** | 746, 807 |
| **Severidad** | P0 — Crash inmediato |
| **Descripción** | Se usa `BASE_DIR` pero solo están definidos `MODULE_DIR`, `SERVER_DIR`, `ROOT_DIR`. `BASE_DIR` nunca se define. |
| **Impacto** | `uart_configurar("copiar")` y `uart_descargar_putty()` lanzan `NameError` al ejecutarse. |
| **Fix** | Reemplazar `BASE_DIR` por `ROOT_DIR` en ambas líneas. |

```python
# L746: PORTABLE_DIR = BASE_DIR / "utils" / "portable"  ← NameError
# L807: PORTABLE_DIR = BASE_DIR / "utils" / "portable"  ← NameError
# Fix:  PORTABLE_DIR = ROOT_DIR / "utils" / "portable"
```

### BUG-002: Rutas hardcodeadas a ubicación vieja en `test_paths.py`

| Campo | Valor |
|-------|-------|
| **Archivo** | `test_paths.py` |
| **Línea** | 4 |
| **Severidad** | P0 — Test inservible |
| **Descripción** | `sys.path.insert(0, "C:/homelab/opencode/mcp-opencode/servers/mcp-uart-serial/src")` apunta a la ubicación anterior. |
| **Fix** | Usar `ROOT_DIR` o ruta relativa dinámica. |

---

## P1 — Fallos Funcionales

### BUG-003: Todas las herramientas MCP son síncronas — bloquean el event loop

| Campo | Valor |
|-------|-------|
| **Líneas** | 297-648 (todas las `@mcp.tool()`) |
| **Severidad** | P1 — Degradación de rendimiento |
| **Descripción** | Todas las funciones usan `serial.Serial` (bloqueante) y `time.sleep` implícito. FastMCP ejecuta tools async; las tools sync se ejecutan en thread pool, pero las esperas activas (`while (datetime.now() - start).seconds < timeout` en L485-519) bloquean el thread por hasta 120s. |
| **Impacto** | Un `uart_comando("ping 8.8.8.8")` puede congelar el MCP 120 segundos. |
| **Fix** | Migrar a `asyncio` + `pyserial-asyncio`, o al menos usar `await asyncio.sleep()` dentro de funciones async. |

### BUG-004: Frontmatter YAML corrupto por `log_to_project()`

| Campo | Valor |
|-------|-------|
| **Línea** | 867 |
| **Severidad** | P1 — Corrupción de datos |
| **Descripción** | `content.replace("modified:", f"modified: {date_str}")` reemplaza **todas** las ocurrencias de "modified:" incluyendo las del YAML dentro de bloques de código, y si hay tablas markdown con "modified:", también las corrompe. Además, si el frontmatter no tiene campo `modified:`, no hace nada. |
| **Fix** | Usar un parser YAML adecuado para el frontmatter, o al menos limitar el replace al primer bloque `---` del documento. |

### BUG-005: `uart_descargar_putty()` no descarga realmente

| Campo | Valor |
|-------|-------|
| **Líneas** | 793-854 |
| **Severidad** | P1 — Funcionalidad vacía |
| **Descripción** | La función importa `urllib.request`, `zipfile`, `io` pero **nunca ejecuta la descarga**. El bloque `try` solo muestra un mensaje diciendo "mejor descárgalo manualmente". El import y la lógica de descarga están completamente muertos. |
| **Impacto** | El usuario ve "📥 Descargando PuTTY..." pero nunca recibe nada. |
| **Fix** | Implementar la descarga real con `urllib.request.urlretrieve()` y extracción con `zipfile`, o eliminar la función y clarificar que solo es informativa. |

---

## P2 — Calidad / Mantenibilidad

### BUG-006: Arquitectura monolítica (928 líneas, 1 archivo)

| Campo | Valor |
|-------|-------|
| **Severidad** | P2 — Mantenibilidad |
| **Descripción** | Todo el servidor está en un único archivo `server.py`. Sin separación de responsabilidades. |
| **Referencia** | `serial-mcp-server` (Rust) usa 7+ archivos modulares. |
| **Fix** | Refactorizar en módulos: `connection.py`, `security.py`, `project.py`, `config.py`, `putty.py`. |

### BUG-007: Sin tests

| Campo | Valor |
|-------|-------|
| **Severidad** | P2 — Calidad |
| **Descripción** | `test_paths.py` tiene rutas hardcodeadas rotas. No hay tests unitarios reales. |
| **Referencia** | `serial-mcp-server` tiene tests con `mockall`. |

### BUG-008: Whitelist de comandos evadible por metacaracteres

| Campo | Valor |
|-------|-------|
| **Líneas** | 421-454 (validación), 457-532 (ejecución) |
| **Severidad** | P2 — Seguridad |
| **Descripción** | `_is_read_only()` detecta si `cmd_lower.startswith(pattern.lower() + " ")`, pero comandos como `cat /etc/passwd; rm -rf /` pasan porque `cat` está en la whitelist. No hay validación de metacaracteres como `;`, `&`, `|`, `||`, `&&`, `` ` ``, `$()`. Esto es un riesgo en dispositivos embebidos si el LLM envía comandos compuestos. |
| **Fix** | Añadir detección de metacaracteres: si el comando contiene `;`, `&`, `|`, `` ` ``, `$()`, rechazarlo. El proyecto `mcp-android-eng` ya tiene `_validate_shell_command()` en `shell.py` que hace exactamente esto. |

### BUG-009: Sesión global única sin re conexión

| Campo | Valor |
|-------|-------|
| **Línea** | 167 |
| **Severidad** | P2 — Funcionalidad |
| **Descripción** | `session_active` es un dict global plano. Solo soporta **una conexión** al mismo tiempo. Si se desconecta, no hay mecanismo de re conexión. |
| **Referencia** | `serial-mcp-server` usa `SessionManager` con UUIDs, multi-sesión, auto-reconnect, y cleanup de sesiones idle. |
| **Fix**** | Migrar a un patrón de conexión pool con IDs únicos y soporte multi-sesión. |

---

## Comparativa con adancurusul/serial-mcp-server

| Característica | **Nuestro (Python)** | **adancurusul (Rust)** | Veredicto |
|---|---|---|---|
| **Lenguaje** | Python (pyserial) | Rust (tokio-serial) | Rust = rendimiento |
| **Arquitectura** | 1 archivo (928 líneas) | 7+ módulos | **Rust superior** |
| **Multi-sesión** | 1 sesión global | Multi-sesión con UUIDs | **Rust superior** |
| **Async** | Bloqueante (pyserial) | Nativo async (tokio) | **Rust superior** |
| **Config serie** | Hardcoded 8N1 | Completo (data bits, stop, parity, flow) | **Rust superior** |
| **Encodings** | UTF-8 solo | UTF-8, Hex, Base64 | **Rust superior** |
| **Auto-reconnect** | No | Sí | **Rust superior** |
| **Error handling** | try/except genérico | thiserror tipado | **Rust superior** |
| **Tests** | 0 | Unit tests | **Rust superior** |
| **Config seguridad** | Whitelist de comandos | Allowlist/blocklist de puertos | Distintos modelos |
| **Limpieza sesiones** | No | Cleanup de idle | **Rust superior** |
| **Estadísticas** | Log en archivo MD | Bytes sent/recv, mensajes | **Rust superior** |
| **Comandos embebidos** | Sí (ls, cat, ping, etc.) | No (raw read/write) | **Nosotros superiores** |
| **Gestión proyectos** | Sí (Obsidian-style) | No | **Nosotros superiores** |
| **PuTTY integration** | Sí | No | **Nosotros superiores** |
| **Whitelist comandos** | Sí (con bug) | No | **Nosotros superiores** (concepto) |
| **Device database** | Sí (devices.json) | No | **Nosotros superiores** |

### Resumen comparativa

**adancurusul/serial-mcp-server** nos supera en: arquitectura, multi-sesión, async, configuración serie, encodings, auto-reconnect, manejo de errores, tests, y estadísticas.

**Nosotros** superamos en: seguridad de comandos (whitelist/blacklist), gestión de proyectos con documentación, integración PuTTY, base de datos de dispositivos, y detección de comandos peligrosos.

### Lecciones a aplicar

1. **Multi-sesión** → Adoptar patrón de pool con IDs únicos
2. **Config serie completa** → Soportar data_bits, stop_bits, parity, flow_control
3. **Encodings** → Añadir soporte hex y base64 para datos binarios
4. **Async** → Migrar a pyserial-asyncio o usar thread pool correctamente
5. **Estadísticas** → Trackear bytes enviados/recibidos por sesión
6. **Tests** → Crear suite de tests unitarios con mocking
7. **Auto-reconnect** → Implementar reconexión automática con backoff
8. **Modularización** → Separar server.py en módulos

---

## Plan de Acción (Prioridad)

1. ~~**FIX P0**: Reemplazar `BASE_DIR` → `ROOT_DIR` (L746, L807)~~ ✅ HECHO
2. ~~**FIX P0**: Corregir `test_paths.py` rutas~~ ✅ HECHO
3. ~~**FIX P1**: Implementar descarga real de PuTTY~~ ✅ HECHO
4. ~~**FIX P1**: Corregir `log_to_project()` frontmatter~~ ✅ HECHO
5. ~~**FIX P2**: Añadir validación de metacaracteres en comandos~~ ✅ HECHO
6. **FIX P2**: Refactorizar a módulos (fase 2)
7. **FIX P2**: Crear tests unitarios (fase 2)

### Fixes aplicados en mcp-android-eng

- ✅ `server.py:81,89` — `asyncio.get_event_loop()` → `asyncio.get_running_loop()` (deprecado en 3.10+)
- ✅ `tools/adb/shell.py` — Añadida validación de patrones de encadenamiento (`&&`, `||`, `;;`, `\n`, `\r`)
- ✅ BUG-001 y BUG-003 verificados — No eran bugs reales, el código funciona correctamente
- ⚠️ SEC-001 parcialmente mitigado — La whitelist ya existía, se añadió más defensa con patrones de encadenamiento