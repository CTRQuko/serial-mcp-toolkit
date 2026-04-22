"""Regression tests for server.py — ensures all symbols used in tool
implementations are properly imported, preventing NameError at runtime."""

from uart_mcp import server


class TestServerImports:
    def test_load_devices_accessible(self):
        assert hasattr(server, "load_devices")
        assert callable(server.load_devices)

    def test_encoding_error_accessible(self):
        assert hasattr(server, "EncodingError")
        assert issubclass(server.EncodingError, Exception)


class TestUartDispositivos:
    def test_invocation_does_not_raise(self):
        fn = server.uart_dispositivos.fn if hasattr(server.uart_dispositivos, "fn") else server.uart_dispositivos
        result = fn()
        assert isinstance(result, str)
        assert len(result) > 0
