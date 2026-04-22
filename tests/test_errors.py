import pytest
from uart_mcp.errors import (
    UartError,
    ConnectionError,
    SessionError,
    SecurityError,
    ValidationError,
    EncodingError,
    ConfigError,
)


class TestErrorHierarchy:
    def test_base_error(self):
        err = UartError("test")
        assert str(err) == "test"
        assert isinstance(err, Exception)

    def test_connection_error(self):
        err = ConnectionError("port not found", port="COM1")
        assert "port not found" in str(err)
        assert "COM1" in str(err)
        assert err.port == "COM1"
        assert isinstance(err, UartError)

    def test_connection_error_no_port(self):
        err = ConnectionError("port not found")
        assert err.port == ""

    def test_session_error(self):
        err = SessionError("not found", session_id="abc")
        assert "not found" in str(err)
        assert err.session_id == "abc"
        assert isinstance(err, UartError)

    def test_session_error_no_id(self):
        err = SessionError("not found")
        assert err.session_id == ""

    def test_security_error(self):
        err = SecurityError("blocked", command="reboot")
        assert "blocked" in str(err)
        assert err.command == "reboot"
        assert isinstance(err, UartError)

    def test_security_error_no_command(self):
        err = SecurityError("blocked")
        assert err.command == ""

    def test_validation_error(self):
        err = ValidationError("baud_rate", 99999, "Not a standard rate")
        assert "baud_rate" in str(err)
        assert "99999" in str(err)
        assert err.field == "baud_rate"
        assert err.value == 99999
        assert isinstance(err, UartError)

    def test_validation_error_no_reason(self):
        err = ValidationError("port", "")
        assert err.reason == ""

    def test_encoding_error(self):
        err = EncodingError("hex", "Invalid hex characters")
        assert "hex" in str(err)
        assert err.encoding == "hex"
        assert isinstance(err, UartError)

    def test_config_error(self):
        err = ConfigError("file not found")
        assert "file not found" in str(err)
        assert isinstance(err, UartError)


class TestErrorInheritance:
    def test_all_inherit_from_uart_error(self):
        for exc_class in [
            ConnectionError,
            SessionError,
            SecurityError,
            ValidationError,
            EncodingError,
            ConfigError,
        ]:
            assert issubclass(exc_class, UartError)

    def test_uart_error_inherits_from_exception(self):
        assert issubclass(UartError, Exception)

    def test_catch_specific(self):
        with pytest.raises(ValidationError):
            raise ValidationError("baud_rate", 99999)

    def test_catch_base(self):
        with pytest.raises(UartError):
            raise ConnectionError("test", port="COM1")

    def test_catch_as_uart_error(self):
        try:
            raise EncodingError("hex", "bad input")
        except UartError as e:
            assert "hex" in str(e)
