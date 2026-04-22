import os
import platform
import shutil
import zipfile
import io
from pathlib import Path

from .config import ROOT_DIR, CONFIG_FILE, PUTTY_PATH_DEFAULT, DATA_DIR
from .config import load_config


def detect_putty() -> dict:
    found = {}
    os_name = platform.system()

    if os_name == "Windows":
        putty_paths = [
            "C:\\Program Files\\PuTTY\\putty.exe",
            "C:\\Program Files (x86)\\PuTTY\\putty.exe",
        ]
        for path in putty_paths:
            if os.path.exists(path):
                found["putty"] = path
                break
        moba_paths = [
            "C:\\Program Files (x86)\\Mobatek\\MobaXterm\\MobaXterm.exe",
        ]
        for path in moba_paths:
            if os.path.exists(path):
                found["mobaxterm"] = path
                break
    elif os_name == "Linux":
        putty_path = shutil.which("putty")
        if putty_path:
            found["putty"] = putty_path
    elif os_name == "Darwin":
        putty_path = shutil.which("putty")
        if putty_path:
            found["putty"] = putty_path

    return found


def copy_to_portable(found_paths: dict) -> str:
    portable_dir = ROOT_DIR / "utils" / "portable"
    portable_dir.mkdir(exist_ok=True)

    copied = []
    for name, src_path in found_paths.items():
        try:
            dst = portable_dir / Path(src_path).name
            shutil.copy2(src_path, dst)
            copied.append((name, str(dst)))
        except Exception as e:
            return f"[WARN] Error al copiar {name}: {e}"

    config_content = "# Configuracion generada automaticamente\n"
    for name, path in copied:
        config_content += f"\n[{name}]\npath = {path}\n"

    try:
        CONFIG_FILE.write_text(config_content)
        load_config()
        return f"[OK] Utilidades copiadas a utils/portable/:\n" + "\n".join(
            f"- {k}: {v}" for k, v in copied
        )
    except Exception as e:
        return f"[WARN] Error al guardar config: {e}"


def download_putty() -> str:
    os_name = platform.system()
    arch = platform.machine()

    portable_dir = ROOT_DIR / "utils" / "portable"
    portable_dir.mkdir(exist_ok=True)

    if os_name == "Windows":
        if arch in ["AMD64", "x86_64"]:
            url = "https://the.earth.li/~sgtatham/putty/latest/64-bit/putty-64bit.zip"
        else:
            url = "https://the.earth.li/~sgtatham/putty/latest/win32/putty.zip"
    elif os_name == "Linux":
        return (
            "[WARN] En Linux se recomienda instalar via package manager:\n\n"
            "sudo apt install putty        # Debian/Ubuntu\n"
            "sudo yum install putty        # RedHat/CentOS\n"
            "sudo dnf install putty        # Fedora\n\n"
            "Despues de instalar, ejecuta uart_configurar('scan') para detectar."
        )
    elif os_name == "Darwin":
        return (
            "[WARN] En macOS se recomienda instalar via Homebrew:\n\n"
            "brew install putty\n\n"
            "Despues de instalar, ejecuta uart_configurar('scan') para detectar."
        )
    else:
        return f"[WARN] Sistema operativo no soportado: {os_name}"

    try:
        import urllib.request

        resp = urllib.request.urlopen(url, timeout=60)
        data = resp.read()
        zip_buffer = io.BytesIO(data)

        with zipfile.ZipFile(zip_buffer) as zf:
            zf.extractall(portable_dir)

        putty_exe = None
        for f in portable_dir.iterdir():
            if f.name.lower() == "putty.exe":
                putty_exe = f
                break

        config_content = "# Configuracion generada automaticamente\n"
        if putty_exe:
            config_content += f"\n[putty]\npath = {putty_exe}\n"
        for f in portable_dir.iterdir():
            if f.suffix.lower() == ".exe" and f.name.lower() != "putty.exe":
                config_content += f"\n[{f.stem}]\npath = {f}\n"

        CONFIG_FILE.write_text(config_content)
        load_config()

        files_list = "\n".join(
            f"- {f.name}" for f in portable_dir.iterdir() if f.is_file()
        )
        return (
            f"[OK] PuTTY descargado e instalado en {portable_dir}\n\n"
            f"Archivos extraidos:\n{files_list}\n\n"
            "[WARN] **REINICIA el MCP** para aplicar los cambios.\n\n"
            "Despues del reinicio, usa uart_putty_abrir()"
        )
    except Exception as e:
        return (
            f"[ERROR] Fallo la descarga automatica: {e}\n\n"
            f"**Alternativa manual:**\n"
            f"1. Descarga desde: https://putty.org\n"
            f"2. Guarda putty.exe en: {portable_dir}\n"
            f"3. Ejecuta: uart_configurar('scan')"
        )


def launch_putty(port: str = "", baudrate: int = 115200) -> str:
    import subprocess

    putty_path = get_putty_path()
    if not putty_path:
        return "[WARN] PuTTY no configurado. Ejecuta uart_configurar() primero."

    try:
        if port:
            subprocess.Popen(
                [putty_path, "-serial", port, "-sercfg", f"{baudrate},8,n,1"]
            )
            return f"[OK] PuTTY abierto en {port}"
        else:
            subprocess.Popen([putty_path])
            return "[OK] PuTTY abierto."
    except Exception as e:
        return f"ERROR: {e}"


def get_putty_path() -> str:
    config = load_config()
    if config.has_option("putty", "path"):
        path = config.get("putty", "path")
        if os.path.exists(path):
            return path
    if os.path.exists(PUTTY_PATH_DEFAULT):
        return PUTTY_PATH_DEFAULT
    return ""
