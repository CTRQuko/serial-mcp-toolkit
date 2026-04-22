from .config import READ_ONLY_COMMANDS, DANGEROUS_PATTERNS, ALLOWED_WITH_PROJECT
from .errors import SecurityError


def has_shell_metacharacters(cmd: str) -> str | None:
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "{", "}", "<", ">"]
    for char in dangerous_chars:
        if char in cmd:
            return char
    chaining_patterns = ["&&", "||", ";;", "\n", "\r"]
    for pattern in chaining_patterns:
        if pattern in cmd:
            return pattern
    return None


def is_read_only(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    for pattern in READ_ONLY_COMMANDS:
        if cmd_lower == pattern.lower() or cmd_lower.startswith(pattern.lower() + " "):
            return True
    return False


def is_dangerous(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        pattern_lower = pattern.lower()
        if pattern_lower.endswith(" "):
            if cmd_lower.startswith(pattern_lower):
                return True
        elif pattern_lower.startswith("/"):
            if cmd_lower.startswith(pattern_lower):
                return True
        elif "." in pattern_lower:
            if cmd_lower.startswith(pattern_lower.split()[0]):
                return True
        elif cmd_lower == pattern_lower or cmd_lower.startswith(pattern_lower + " "):
            return True
    return False


def is_allowed_with_project(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    for pattern in ALLOWED_WITH_PROJECT:
        pattern_lower = pattern.lower()
        if "*" in pattern_lower:
            base = pattern_lower.replace("*", "").strip()
            if cmd_lower.startswith(base):
                return True
        elif cmd_lower == pattern_lower or cmd_lower.startswith(pattern_lower + " "):
            return True
    return False


def validate_command(cmd: str, project: str = "") -> tuple[bool, str]:
    meta = has_shell_metacharacters(cmd)
    if meta:
        return False, (
            f"[SECURITY] Comando rechazado: contiene metacaracter '{meta}' "
            f"que permite inyeccion de comandos.\nComando original: {cmd}\n\n"
            f"Los caracteres ;, &, |, `, $, (), {{}}, <, > estan prohibidos.\n"
            f"Si necesitas encadenar operaciones, ejecutalas por separado.\n"
            f"Para sesiones interactivas, usa uart_putty_abrir()."
        )

    if is_dangerous(cmd):
        return False, (
            f"[DANGER] Comando peligroso detectado: '{cmd}'\n"
            f"Este tipo de comando requiere confirmacion manual en PuTTY.\n"
            f"Usa uart_putty_abrir() para sesion interactiva."
        )

    if project and not is_read_only(cmd) and not is_allowed_with_project(cmd):
        from .project import get_project_doc

        doc = get_project_doc(project)
        if doc.exists():
            content = doc.read_text()
            cmd_base = cmd.strip().split()[0] if cmd.strip() else ""
            if cmd_base not in content:
                return False, (
                    f"[WARN] '{cmd_base}' requiere confirmacion.\n"
                    f"Comando: {cmd}\nUsa uart_putty_abrir() para interactivo."
                )

    return True, ""
