"""Abrir PuTTY si está disponible."""

import sys
import subprocess
from pathlib import Path


def open_putty(port: str = None, baudrate: int = 115200):
    """Abrir PuTTY para conexión serie."""
    base_dir = Path(__file__).parent.parent
    putty_dir = base_dir / "portable" / "putty"
    putty_exe = putty_dir / "putty.exe"

    if not putty_exe.exists():
        print("ERROR: PuTTY no encontrado en utils/portable/putty/")
        print("Descarga PuTTY desde: https://www.putty.org/")
        return False

    if port:
        cmd = [str(putty_exe), "-serial", port, "-sercfg", f"{baudrate},8,n,1"]
    else:
        cmd = [str(putty_exe)]

    try:
        subprocess.Popen(cmd)
        print(f"✓ PuTTY abierto en {port or 'modo interactivo'}")
        return True
    except Exception as e:
        print(f"ERROR al abrir PuTTY: {e}")
        return False


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else None
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    open_putty(port, baudrate)
