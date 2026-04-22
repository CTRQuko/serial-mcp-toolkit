from uart_mcp.config import (
    VALID_BAUD_RATES,
    DEFAULT_BAUD,
    DEFAULT_DATA_BITS,
    DEFAULT_STOP_BITS,
    DEFAULT_PARITY,
    DEFAULT_FLOW_CONTROL,
    DEFAULT_TIMEOUT,
    MAX_SESSIONS,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
    RECONNECT_MAX_ATTEMPTS,
    IDLE_TIMEOUT_SECONDS,
    READ_ONLY_COMMANDS,
    DANGEROUS_PATTERNS,
    ALLOWED_WITH_PROJECT,
    DATA_DIR,
    DOCS_DIR,
)


class TestConstants:
    def test_baud_rates(self):
        assert 9600 in VALID_BAUD_RATES
        assert 115200 in VALID_BAUD_RATES
        assert 99999 not in VALID_BAUD_RATES

    def test_defaults(self):
        assert DEFAULT_BAUD == 115200
        assert DEFAULT_DATA_BITS == 8
        assert DEFAULT_STOP_BITS == 1
        assert DEFAULT_PARITY == "none"
        assert DEFAULT_FLOW_CONTROL == "none"
        assert DEFAULT_TIMEOUT == 30

    def test_limits(self):
        assert MAX_SESSIONS == 10
        assert IDLE_TIMEOUT_SECONDS == 3600

    def test_reconnect(self):
        assert RECONNECT_BASE_DELAY == 1.0
        assert RECONNECT_MAX_DELAY == 30.0
        assert RECONNECT_MAX_ATTEMPTS == 3

    def test_read_only_commands(self):
        assert "ls" in READ_ONLY_COMMANDS
        assert "cat" in READ_ONLY_COMMANDS
        assert "ping" in READ_ONLY_COMMANDS

    def test_dangerous_patterns(self):
        assert "reboot" in DANGEROUS_PATTERNS
        assert "rm " in DANGEROUS_PATTERNS

    def test_allowed_with_project(self):
        assert "uci show" in ALLOWED_WITH_PROJECT
        assert "opkg install" in ALLOWED_WITH_PROJECT

    def test_dirs_exist(self):
        assert DATA_DIR.exists()
        assert DOCS_DIR.exists()
