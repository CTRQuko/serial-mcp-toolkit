"""Listar puertos serie disponibles."""

import serial.tools.list_ports


def list_ports():
    """Lista todos los puertos serie disponibles."""
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No se encontraron puertos serie disponibles.")
        return

    print("Puertos disponibles:")
    for port in ports:
        print(f"  {port.device}: {port.description or 'Sin descripción'}")
        if port.hwid:
            print(f"    HWID: {port.hwid}")


if __name__ == "__main__":
    list_ports()
