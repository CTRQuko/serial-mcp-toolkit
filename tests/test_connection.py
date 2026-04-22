import pytest
from unittest.mock import patch, MagicMock
from uart_mcp.connection import (
    SessionState,
    SessionStats,
    SessionConfig,
    Session,
    ConnectionManager,
)
from uart_mcp.errors import ConnectionError, SessionError, ValidationError


class TestSessionState:
    def test_values(self):
        assert SessionState.CREATING.value == "creating"
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.SUSPENDED.value == "suspended"
        assert SessionState.CLOSING.value == "closing"
        assert SessionState.CLOSED.value == "closed"
        assert SessionState.ERROR.value == "error"


class TestSessionStats:
    def test_initial(self):
        stats = SessionStats()
        assert stats.bytes_sent == 0
        assert stats.bytes_received == 0
        assert stats.messages_sent == 0
        assert stats.messages_received == 0
        assert stats.errors_count == 0
        assert stats.reconnections == 0

    def test_record_send(self):
        stats = SessionStats()
        stats.record_send(100)
        assert stats.bytes_sent == 100
        assert stats.messages_sent == 1
        assert stats.last_activity is not None

    def test_record_receive(self):
        stats = SessionStats()
        stats.record_receive(200)
        assert stats.bytes_received == 200
        assert stats.messages_received == 1

    def test_record_error(self):
        stats = SessionStats()
        stats.record_error()
        assert stats.errors_count == 1

    def test_to_dict(self):
        stats = SessionStats()
        stats.record_send(50)
        d = stats.to_dict()
        assert "bytes_sent" in d
        assert "bytes_received" in d
        assert d["bytes_sent"] == 50


class TestSessionConfig:
    def test_defaults(self):
        config = SessionConfig(port="COM1")
        assert config.baudrate == 115200
        assert config.data_bits == 8
        assert config.stop_bits == 1
        assert config.parity == "none"
        assert config.flow_control == "none"
        assert config.auto_reconnect is False
        assert config.max_reconnect_attempts == 3

    def test_from_params(self):
        config = SessionConfig.from_params(
            port="COM3", baudrate=9600, data_bits=7, stop_bits=2, parity="even"
        )
        assert config.port == "COM3"
        assert config.baudrate == 9600
        assert config.data_bits == 7
        assert config.stop_bits == 2
        assert config.parity == "even"

    def test_invalid_baud(self):
        with pytest.raises(ValidationError):
            SessionConfig.from_params(port="COM1", baudrate=99999)

    def test_config_string_8n1(self):
        config = SessionConfig(
            port="COM1", baudrate=115200, data_bits=8, parity="none", stop_bits=1
        )
        assert config.config_string() == "115200/8N1"

    def test_config_string_7e2(self):
        config = SessionConfig(
            port="COM1", baudrate=9600, data_bits=7, parity="even", stop_bits=2
        )
        assert config.config_string() == "9600/7E2"

    def test_parity_serial(self):
        config = SessionConfig(port="COM1", parity="even")
        assert config.parity_serial() == "E"
        config = SessionConfig(port="COM1", parity="odd")
        assert config.parity_serial() == "O"


class TestConnectionManager:
    def test_list_ports(self):
        ports = ConnectionManager.list_ports()
        assert isinstance(ports, list)

    def test_max_sessions(self):
        mgr = ConnectionManager()
        assert len(mgr._sessions) == 0

    @patch("uart_mcp.connection.serial.Serial")
    def test_connect_and_disconnect(self, mock_serial):
        mock_ser = MagicMock()
        mock_ser.is_open = True
        mock_serial.return_value = mock_ser

        mgr = ConnectionManager()
        config = SessionConfig.from_params(port="COM1", baudrate=115200)
        session = mgr.connect("test_session", "test_proj", "Test Device", config)
        assert session.state == SessionState.ACTIVE
        assert session.session_id == "test_session"

        result = mgr.disconnect("test_session")
        assert result == "test_session"
        assert session.state == SessionState.CLOSED

    def test_disconnect_nonexistent(self):
        mgr = ConnectionManager()
        with pytest.raises(SessionError, match="not found"):
            mgr.disconnect("nonexistent")

    def test_get_nonexistent(self):
        mgr = ConnectionManager()
        with pytest.raises(SessionError, match="not found"):
            mgr.get("nonexistent")

    def test_list_sessions_empty(self):
        mgr = ConnectionManager()
        assert mgr.list_sessions() == []

    @patch("uart_mcp.connection.serial.Serial")
    def test_list_sessions(self, mock_serial):
        mock_ser = MagicMock()
        mock_ser.is_open = True
        mock_serial.return_value = mock_ser

        mgr = ConnectionManager()
        config = SessionConfig.from_params(port="COM1")
        mgr.connect("s1", "p1", "dev1", config)
        sessions = mgr.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "s1"

    def test_cleanup_idle_no_sessions(self):
        mgr = ConnectionManager()
        result = mgr.cleanup_idle(60)
        assert result == []


class TestSession:
    @patch("uart_mcp.connection.serial.Serial")
    def test_session_touch(self, mock_serial):
        mock_ser = MagicMock()
        mock_ser.is_open = True
        config = SessionConfig(port="COM1")
        session = Session("test", "proj", "dev", config, mock_ser)
        old_access = session.last_accessed
        import time

        time.sleep(0.01)
        session.touch()
        assert session.last_accessed >= old_access

    def test_session_idle_seconds(self):
        config = SessionConfig(port="COM1")
        mock_ser = MagicMock()
        mock_ser.is_open = True
        session = Session("test", "proj", "dev", config, mock_ser)
        assert session.idle_seconds() >= 0

    def test_reconnect_delay_exponential(self):
        config = SessionConfig(port="COM1")
        config.auto_reconnect = True
        mock_ser = MagicMock()
        mock_ser.is_open = True
        session = Session("test", "proj", "dev", config, mock_ser)

        session._reconnect_attempts = 0
        assert session.reconnect_delay() == 1.0

        session._reconnect_attempts = 1
        assert session.reconnect_delay() == 2.0

        session._reconnect_attempts = 2
        assert session.reconnect_delay() == 4.0

        session._reconnect_attempts = 10
        assert session.reconnect_delay() == 30.0  # capped at RECONNECT_MAX_DELAY
