import configparser
import json
import os
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
SERVER_DIR = MODULE_DIR.parent
ROOT_DIR = SERVER_DIR.parent

_USER_DATA_DIR = os.environ.get("UART_DATA_DIR")
_USER_DOCS_DIR = os.environ.get("UART_DOCS_DIR")

DATA_DIR = Path(_USER_DATA_DIR) if _USER_DATA_DIR else (ROOT_DIR / "data")
DOCS_DIR = Path(_USER_DOCS_DIR) if _USER_DOCS_DIR else (ROOT_DIR / "docs")
LOGS_DIR = DATA_DIR / "logs"
CONFIG_FILE = ROOT_DIR / "utils" / "config.ini"
PUTTY_PATH_DEFAULT = "C:\\Program Files\\PuTTY\\putty.exe"

VALID_BAUD_RATES = [
    300,
    600,
    1200,
    2400,
    4800,
    9600,
    14400,
    19200,
    28800,
    38400,
    57600,
    115200,
    230400,
    460800,
    921600,
]

DEFAULT_BAUD = 115200
DEFAULT_DATA_BITS = 8
DEFAULT_STOP_BITS = 1
DEFAULT_PARITY = "none"
DEFAULT_FLOW_CONTROL = "none"
DEFAULT_TIMEOUT = 30
COMMAND_TIMEOUT = 120
MAX_SESSIONS = 10
IDLE_TIMEOUT_SECONDS = 3600
RECONNECT_BASE_DELAY = 1.0
RECONNECT_MAX_DELAY = 30.0
RECONNECT_MAX_ATTEMPTS = 3

READ_ONLY_COMMANDS = [
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
    "time",
    "df",
    "du",
    "free",
    "ps",
    "uname",
    "uptime",
    "id",
    "date",
    "mount",
    "dmesg",
    "hexdump",
    "file",
    "env",
    "expr",
    "wc",
    "sort",
    "uniq",
    "dirname",
    "basename",
    "printf",
    "clear",
    "logread",
    "ubus",
    "iw",
    "iwinfo",
    "/etc/init.d/network status",
    "/etc/init.d/firewall status",
    "/etc/init.d/dropbear status",
    "/etc/init.d/dnsmasq status",
]

DANGEROUS_PATTERNS = [
    "rm ",
    "rm -",
    "rmdir",
    "opkg remove",
    "opkg delete",
    "opkg uninstall",
    "uci delete",
    "uci revert",
    "reboot",
    "poweroff",
    "halt",
    "shutdown",
    "firstboot",
    "factory",
    "dd",
    "mkfs",
    "mkfs.ext4",
    "mkfs.ext3",
    "mkfs.vfat",
    "fdisk",
    "parted",
    "mount --bind",
    "mount -o remount,rw",
    "/etc/init.d/network stop",
    "/etc/init.d/network disable",
    "/etc/init.d/firewall stop",
    "/etc/init.d/firewall disable",
]

ALLOWED_WITH_PROJECT = [
    "uci show",
    "uci get",
    "uci set",
    "uci commit",
    "uci changes",
    "uci add",
    "uci import",
    "uci export",
    "opkg update",
    "opkg list",
    "opkg list-installed",
    "opkg info",
    "opkg install",
    "opkg download",
    "wifi",
    "wifi reload",
    "wifi up",
    "wifi down",
    "ifup",
    "ifdown",
    "/etc/init.d/network reload",
    "/etc/init.d/network restart",
    "/etc/init.d/network enable",
    "/etc/init.d/network disable",
    "/etc/init.d/firewall reload",
    "/etc/init.d/firewall restart",
    "/etc/init.d/firewall enable",
    "/etc/init.d/dropbear reload",
    "/etc/init.d/dropbear restart",
    "/etc/init.d/dropbear enable",
    "/etc/init.d/dnsmasq reload",
    "/etc/init.d/dnsmasq restart",
    "/etc/init.d/dnsmasq enable",
    "/etc/init.d/system reload",
    "/etc/init.d/system restart",
    "/etc/init.d/* start",
    "/etc/init.d/* restart",
    "/etc.d/* enable",
    "/etc/init.d/* disable",
    "iw dev",
    "iw list",
    "iw scan",
]

for d in [DATA_DIR, LOGS_DIR, DOCS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
    return config


def get_putty_path() -> str:
    config = load_config()
    if config.has_option("putty", "path"):
        return config.get("putty", "path")
    return PUTTY_PATH_DEFAULT


def load_devices() -> dict:
    devices_file = DATA_DIR / "devices.json"
    if devices_file.exists():
        return json.loads(devices_file.read_text())
    return {"devices": {}}


def save_devices(data: dict):
    (DATA_DIR / "devices.json").write_text(json.dumps(data, indent=2))
