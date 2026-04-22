import pytest
from uart_mcp.encodings import DataConverter
from uart_mcp.errors import EncodingError


class TestEncodeUTF8:
    def test_hello(self):
        result = DataConverter.encode(b"Hello", "utf8")
        assert result == "Hello"

    def test_bytes(self):
        result = DataConverter.encode(b"\x01\x02\x03", "utf8")
        assert "\x01" in result

    def test_empty(self):
        result = DataConverter.encode(b"", "utf8")
        assert result == ""


class TestEncodeHex:
    def test_hello(self):
        result = DataConverter.encode(b"Hello", "hex")
        assert result == "48 65 6c 6c 6f"

    def test_empty(self):
        result = DataConverter.encode(b"", "hex")
        assert result == ""

    def test_single_byte(self):
        result = DataConverter.encode(b"\xff", "hex")
        assert result == "ff"


class TestEncodeBase64:
    def test_hello(self):
        result = DataConverter.encode(b"Hello, World!", "base64")
        assert result == "SGVsbG8sIFdvcmxkIQ=="

    def test_empty(self):
        result = DataConverter.encode(b"", "base64")
        assert result == ""


class TestDecodeHex:
    def test_hello(self):
        result = DataConverter.decode("48 65 6c 6c 6f", "hex")
        assert result == b"Hello"

    def test_no_spaces(self):
        result = DataConverter.decode("48656c6c6f", "hex")
        assert result == b"Hello"

    def test_mixed_case(self):
        result = DataConverter.decode("48656C6C6F", "hex")
        assert result == b"Hello"


class TestDecodeBase64:
    def test_hello(self):
        result = DataConverter.decode("SGVsbG8sIFdvcmxkIQ==", "base64")
        assert result == b"Hello, World!"


class TestDecodeUTF8:
    def test_hello(self):
        result = DataConverter.decode("Hello", "utf8")
        assert result == b"Hello"


class TestRoundtrip:
    @pytest.mark.parametrize("encoding", ["hex", "base64", "utf8"])
    def test_roundtrip(self, encoding):
        original = b"UART test data 123!"
        encoded = DataConverter.encode(original, encoding)
        decoded = DataConverter.decode(encoded, encoding)
        assert decoded == original

    def test_binary_roundtrip_hex(self):
        data = bytes(range(256))
        encoded = DataConverter.encode(data, "hex")
        decoded = DataConverter.decode(encoded, "hex")
        assert decoded == data


class TestInvalidEncoding:
    def test_unknown_encode(self):
        with pytest.raises(EncodingError, match="encoding"):
            DataConverter.encode(b"test", "unknown")

    def test_unknown_decode(self):
        with pytest.raises(EncodingError, match="encoding"):
            DataConverter.decode("test", "unknown")


class TestEscapeDisplay:
    def test_printable(self):
        result = DataConverter.escape_display(b"Hello")
        assert result == "Hello"

    def test_non_printable(self):
        result = DataConverter.escape_display(b"\x01\x02\x7f")
        assert "\\x01" in result

    def test_mixed(self):
        result = DataConverter.escape_display(b"Hi\x00World")
        assert "Hi" in result and "World" in result


class TestFormatBytes:
    def test_short(self):
        result = DataConverter.format_bytes(b"Hello")
        assert len(result) > 0

    def test_empty(self):
        result = DataConverter.format_bytes(b"")
        assert "0" in result
