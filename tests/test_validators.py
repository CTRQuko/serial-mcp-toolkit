import pytest
from uart_mcp.validators import (
    validate_baud_rate,
    validate_data_bits,
    validate_stop_bits,
    validate_parity,
    validate_flow_control,
    validate_port_name,
)
from uart_mcp.errors import ValidationError


class TestBaudRate:
    def test_valid_rates(self):
        for rate in [300, 9600, 115200, 921600]:
            assert validate_baud_rate(rate) == rate

    def test_invalid_rate(self):
        with pytest.raises(ValidationError, match="baud_rate"):
            validate_baud_rate(12345)

    def test_zero_rate(self):
        with pytest.raises(ValidationError):
            validate_baud_rate(0)

    def test_negative_rate(self):
        with pytest.raises(ValidationError):
            validate_baud_rate(-1)


class TestDataBits:
    def test_valid(self):
        for bits in [5, 6, 7, 8]:
            assert validate_data_bits(bits) == bits

    def test_invalid(self):
        with pytest.raises(ValidationError, match="data_bits"):
            validate_data_bits(9)

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_data_bits(0)


class TestStopBits:
    def test_valid(self):
        assert validate_stop_bits(1) == 1
        assert validate_stop_bits(1.5) == 1.5
        assert validate_stop_bits(2) == 2

    def test_invalid(self):
        with pytest.raises(ValidationError, match="stop_bits"):
            validate_stop_bits(3)

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_stop_bits(0)


class TestParity:
    def test_valid(self):
        for p in ["none", "even", "odd", "mark", "space"]:
            assert validate_parity(p) == p.lower()

    def test_case_insensitive(self):
        assert validate_parity("NONE") == "none"
        assert validate_parity("Even") == "even"

    def test_invalid(self):
        with pytest.raises(ValidationError, match="parity"):
            validate_parity("invalid")


class TestFlowControl:
    def test_valid(self):
        for f in ["none", "software", "hardware"]:
            assert validate_flow_control(f) == f.lower()

    def test_case_insensitive(self):
        assert validate_flow_control("NONE") == "none"

    def test_invalid(self):
        with pytest.raises(ValidationError, match="flow_control"):
            validate_flow_control("invalid")


class TestPortName:
    def test_valid_com(self):
        assert validate_port_name("COM1") == "COM1"
        assert validate_port_name("COM99") == "COM99"

    def test_valid_dev(self):
        assert validate_port_name("/dev/ttyUSB0") == "/dev/ttyUSB0"
        assert validate_port_name("/dev/ttyS0") == "/dev/ttyS0"

    def test_empty(self):
        with pytest.raises(ValidationError, match="port"):
            validate_port_name("")

    def test_whitespace_only(self):
        with pytest.raises(ValidationError, match="port"):
            validate_port_name("   ")
