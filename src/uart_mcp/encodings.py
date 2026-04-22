import base64
from .errors import EncodingError


class DataConverter:
    @staticmethod
    def encode(data: bytes, encoding: str = "utf8") -> str:
        encoding = encoding.lower().replace("-", "")
        if encoding in ("utf8", "text", "string"):
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1", errors="replace")
        elif encoding == "hex":
            return " ".join(f"{b:02x}" for b in data)
        elif encoding == "base64":
            return base64.b64encode(data).decode("ascii")
        elif encoding in ("binary", "raw", "bin"):
            return repr(data)
        else:
            raise EncodingError(
                encoding, f"Unsupported encoding. Use: utf8, hex, base64, binary"
            )

    @staticmethod
    def decode(data: str, encoding: str = "utf8") -> bytes:
        encoding = encoding.lower().replace("-", "")
        if encoding in ("utf8", "text", "string"):
            return data.encode("utf-8")
        elif encoding == "hex":
            clean = data.replace(" ", "").replace("0x", "").replace(",", "")
            if len(clean) % 2 != 0:
                raise EncodingError("hex", "Hex string must have even length")
            try:
                return bytes.fromhex(clean)
            except ValueError as e:
                raise EncodingError("hex", f"Invalid hex characters: {e}")
        elif encoding == "base64":
            try:
                return base64.b64decode(data.strip())
            except Exception as e:
                raise EncodingError("base64", f"Invalid base64: {e}")
        elif encoding in ("binary", "raw", "bin"):
            raise EncodingError(
                "binary", "Binary decoding not supported from string input"
            )
        else:
            raise EncodingError(
                encoding, f"Unsupported encoding. Use: utf8, hex, base64"
            )

    @staticmethod
    def escape_display(data: bytes | str) -> str:
        if isinstance(data, bytes):
            chars = data
        else:
            chars = data
        result = []
        for c in chars:
            code = c if isinstance(c, int) else ord(c)
            ch = chr(code) if code < 256 else c
            if code == 10:
                result.append("\\n")
            elif code == 13:
                result.append("\\r")
            elif code == 9:
                result.append("\\t")
            elif code == 0:
                result.append("\\0")
            elif code == 92:
                result.append("\\\\")
            elif code < 32 and code not in (10, 13, 9):
                result.append(f"\\x{code:02x}")
            elif code > 126:
                result.append(f"\\x{code:02x}")
            else:
                result.append(ch)
        return "".join(result)

    @staticmethod
    def format_bytes(data: bytes) -> str:
        if not data:
            return "(0 bytes)"
        if len(data) <= 64:
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return DataConverter.encode(data, "hex")
        try:
            text = data.decode("utf-8")
            if len(text) > 200:
                return text[:200] + f"... ({len(text)} chars total)"
            return text
        except UnicodeDecodeError:
            hex_str = DataConverter.encode(data, "hex")
            if len(hex_str) > 200:
                return hex_str[:200] + f"... ({len(data)} bytes total)"
            return hex_str
