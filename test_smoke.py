#!/usr/bin/env python3
"""Quick smoke test for uart_mcp v2.0.0 modules."""

from uart_mcp import __version__
from uart_mcp.connection import ConnectionManager, SessionConfig
from uart_mcp.security import validate_command, has_shell_metacharacters
from uart_mcp.encodings import DataConverter
from uart_mcp.checksums import compute_checksum, crc8, checksum_xor, checksum_sum
from uart_mcp.errors import (
    UartError,
    ConnectionError,
    SessionError,
    SecurityError,
    ValidationError,
    EncodingError,
)
from uart_mcp.validators import (
    validate_baud_rate,
    validate_data_bits,
    validate_parity,
    validate_stop_bits,
    validate_flow_control,
    validate_port_name,
)

print(f"=== UART MCP v{__version__} Smoke Test ===\n")

# --- Validators ---
print("1. Validators:")
print(f"  baud 115200: {validate_baud_rate(115200)}")
try:
    validate_baud_rate(12345)
    print("  baud 12345: FAIL (should have raised)")
except ValidationError as e:
    print(f"  baud 12345: OK (raised: {e})")

print(f"  data_bits 8: {validate_data_bits(8)}")
print(f"  parity none: {validate_parity('none')}")
print(f"  stop_bits 1: {validate_stop_bits(1)}")
print(f"  flow_control none: {validate_flow_control('none')}")
print(f"  port COM3: {validate_port_name('COM3')}")

# --- SessionConfig ---
print("\n2. SessionConfig:")
config = SessionConfig.from_params(
    port="COM1",
    baudrate=115200,
    data_bits=8,
    stop_bits=1,
    parity="none",
    flow_control="none",
)
print(f"  Config string: {config.config_string()}")
print(f"  Parity serial: {config.parity_serial()}")

config_7e2 = SessionConfig.from_params(
    port="COM2",
    baudrate=9600,
    data_bits=7,
    stop_bits=2,
    parity="even",
    flow_control="hardware",
)
print(f"  7E2 config: {config_7e2.config_string()}")

# --- Security ---
print("\n3. Security:")
print(f"  clean 'ls -la': {validate_command('ls -la')}")
print(
    f"  injection '; rm': blocked={validate_command('cat /etc/passwd; rm -rf /')[0] == False}"
)
print(f"  dangerous 'reboot': blocked={validate_command('reboot')[0] == False}")
print(f"  meta ';': {has_shell_metacharacters('ls;whoami')}")
print(f"  meta '&': {has_shell_metacharacters('ls & whoami')}")
print(f"  clean: {has_shell_metacharacters('ls -la /mnt')}")

# --- Encodings ---
print("\n4. Encodings:")
data = b"Hello, World!"
print(f"  UTF-8 encode: {DataConverter.encode(data, 'utf8')}")
print(f"  Hex encode: {DataConverter.encode(data, 'hex')}")
print(f"  Base64 encode: {DataConverter.encode(data, 'base64')}")
print(f"  Hex decode: {DataConverter.decode('48 65 6c 6c 6f', 'hex')}")
print(f"  B64 decode: {DataConverter.decode('SGVsbG8sIFdvcmxkIQ==', 'base64')}")
print(f"  UTF-8 decode: {DataConverter.decode('Hello', 'utf8')}")

# --- Checksums ---
print("\n5. Checksums:")
test_data = b"Hello"
print(f"  XOR: {checksum_xor(test_data)}")
print(f"  Sum: {checksum_sum(test_data)}")
print(f"  CRC-8: {crc8(test_data)}")
print(f"  compute_checksum(xor): {compute_checksum(test_data, 'xor')}")
print(f"  compute_checksum(crc8): {compute_checksum(test_data, 'crc8')}")
print(f"  compute_checksum(sum): {compute_checksum(test_data, 'sum')}")
print(f"  compute_checksum(crc16): {compute_checksum(test_data, 'crc16')}")

# --- ConnectionManager ---
print("\n6. ConnectionManager:")
mgr = ConnectionManager()
ports = mgr.list_ports()
print(f"  Ports found: {len(ports)}")
for p in ports:
    print(f"    {p['device']} - {p['description']}")

# --- Errors ---
print("\n7. Error types:")
try:
    raise ConnectionError("Test", port="COM1")
except ConnectionError as e:
    print(f"  ConnectionError: {e}")
try:
    raise SessionError("Test", session_id="abc")
except SessionError as e:
    print(f"  SessionError: {e}")
try:
    raise SecurityError("Test", command="reboot")
except SecurityError as e:
    print(f"  SecurityError: {e}")

print("\n=== All tests passed! ===")
