import json
import re
from datetime import datetime
from pathlib import Path

from .config import DOCS_DIR, DATA_DIR, LOGS_DIR


def get_project_doc(project: str) -> Path:
    project_dir = DOCS_DIR / project
    project_dir.mkdir(exist_ok=True)
    return project_dir / f"{project}.md"


def init_project_doc(
    project: str,
    port: str,
    device: str = "",
    baudrate: int = 115200,
    data_bits: int = 8,
    stop_bits: float = 1,
    parity: str = "none",
    flow_control: str = "none",
) -> Path:
    doc_file = get_project_doc(project)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    if not doc_file.exists():
        content = f"""---
title: Sesion {project}
created: {date_str}
modified: {date_str}
port: {port}
device: {device or "Desconocido"}
baudrate: {baudrate}
data_bits: {data_bits}
stop_bits: {stop_bits}
parity: {parity}
flow_control: {flow_control}
---

# Sesion {project}

## Proyecto: {project}

### Sesion 1 - {now.strftime("%d %B %Y")}

#### Conexion
- Puerto: {port}
- Dispositivo: {device or "No identificado"}
- Baudrate: {baudrate}
- Config: {data_bits}{parity[0].upper() if parity != "none" else "N"}{int(stop_bits)}
- Resultado: [OK] Conectado

#### Comandos Probados

| Comando | Resultado | Notas |
|---------|----------|-------|

#### Comandos Funcionales

"""
        doc_file.write_text(content)

    update_session_index(project, "Activo")
    return doc_file


def log_to_project(project: str, command: str, result: str, success: bool):
    doc = get_project_doc(project)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    if not doc.exists():
        return

    content = doc.read_text()

    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = "---".join([""] + parts[2:])
        frontmatter = re.sub(
            r"modified:\s*\S+",
            f"modified: {date_str}",
            frontmatter,
            count=1,
        )
        content = f"---{frontmatter}---{body}"

    result_emoji = "[OK]" if success else "[ERR]"
    content += f"""

### {now.strftime("%H:%M")} - `{command}`
```
{result[:2000]}
```

| Comando | Resultado |
|---------|----------|
| {command} | {result_emoji} |

"""

    doc.write_text(content)

    log_file = LOGS_DIR / f"{project}.log"
    with open(log_file, "a") as f:
        f.write(
            f"[{date_str} {now.strftime('%H:%M:%S')}] {command}: {'OK' if success else 'FAIL'}\n"
        )


def load_session_index() -> str:
    session_file = DOCS_DIR / "session.md"
    if session_file.exists():
        return session_file.read_text()
    return ""


def save_session_index(content: str):
    (DOCS_DIR / "session.md").write_text(content)


def update_session_index(project: str, status: str = "Activo"):
    session_file = DOCS_DIR / "session.md"
    now = datetime.now().strftime("%d %B %Y")
    content = load_session_index()

    if f"### {project}" in content:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"### {project}"):
                new_lines.append(line)
                new_lines.append(f"- Estado: [[{project}/{project}.md|{status}]]")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        header = (
            "---\ntitle: Sesiones UART\n---\n\n# Sesiones UART\n\n"
            f"## Proyecto Activo\n- **Proyecto:** {project}\n"
            f"- **Ultima sesion:** {now}\n- **Estado:** {status}\n\n"
            "## Historial de Proyectos\n\n"
        )
        if not content:
            content = header
        content += (
            f"### {project}\n- Inicio: {now}\n- Puerto:\n"
            f"- Dispositivo:\n- Estado: [[{project}/{project}.md|{status}]]\n\n"
        )

    save_session_index(content)
