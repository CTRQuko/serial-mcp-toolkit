"""UART MCP - Servidor MCP Universal para comunicacion serie."""

__version__ = "2.0.0"

from .config import (
    MODULE_DIR,
    SERVER_DIR,
    ROOT_DIR,
    DATA_DIR,
    DOCS_DIR,
    LOGS_DIR,
    CONFIG_FILE,
    PUTTY_PATH_DEFAULT,
    DEFAULT_BAUD,
    DEFAULT_TIMEOUT,
    COMMAND_TIMEOUT,
    READ_ONLY_COMMANDS,
    DANGEROUS_PATTERNS,
    ALLOWED_WITH_PROJECT,
    VALID_BAUD_RATES,
    MAX_SESSIONS,
    DEFAULT_DATA_BITS,
    DEFAULT_STOP_BITS,
    DEFAULT_PARITY,
    DEFAULT_FLOW_CONTROL,
    IDLE_TIMEOUT_SECONDS,
    load_config,
    get_putty_path,
    load_devices,
    save_devices,
)
from .errors import (
    UartError,
    ConnectionError,
    SessionError,
    SecurityError,
    ValidationError,
    EncodingError,
    ConfigError,
)
from .connection import (
    SessionState,
    SessionStats,
    SessionConfig,
    Session,
    ConnectionManager,
)
from .security import (
    has_shell_metacharacters,
    is_read_only,
    is_dangerous,
    is_allowed_with_project,
    validate_command,
)
from .encodings import DataConverter
from .checksums import (
    checksum_sum,
    checksum_xor,
    crc8,
    compute_checksum,
    verify_checksum,
)
from .project import (
    get_project_doc,
    init_project_doc,
    log_to_project,
    load_session_index,
    save_session_index,
    update_session_index,
)
from .putty import (
    detect_putty,
    copy_to_portable,
    download_putty,
    launch_putty,
    get_putty_path,
)
from .validators import (
    validate_baud_rate,
    validate_data_bits,
    validate_stop_bits,
    validate_parity,
    validate_flow_control,
    validate_port_name,
)
