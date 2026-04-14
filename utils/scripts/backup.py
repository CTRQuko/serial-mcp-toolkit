"""Backup de memoria de dispositivos."""

import json
import shutil
from datetime import datetime
from pathlib import Path


def backup_devices(backup_dir: str = None):
    """Hacer backup de devices.json."""
    base_dir = Path(__file__).parent.parent
    devices_file = base_dir / "data" / "devices.json"

    if not devices_file.exists():
        print("No hay archivo de dispositivos para respaldar.")
        return

    if backup_dir:
        dest = Path(backup_dir)
    else:
        backup_dir = base_dir / "data" / "backups"
        dest = backup_dir / f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(devices_file, dest)
    print(f"✓ Backup guardado en: {dest}")


def restore_devices(backup_file: str):
    """Restaurar desde backup."""
    base_dir = Path(__file__).parent.parent
    devices_file = base_dir / "data" / "devices.json"
    backup = Path(backup_file)

    if not backup.exists():
        print(f"ERROR: No existe el archivo: {backup}")
        return

    shutil.copy2(backup, devices_file)
    print(f"✓ Restaurado desde: {backup}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            if len(sys.argv) > 2:
                restore_devices(sys.argv[2])
            else:
                print("Uso: python backup.py restore <archivo_backup>")
        else:
            backup_devices(sys.argv[1])
    else:
        backup_devices()
