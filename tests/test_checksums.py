import pytest
from uart_mcp.checksums import (
    checksum_sum,
    checksum_xor,
    crc8,
    checksum_crc16,
    compute_checksum,
    verify_checksum,
)


class TestSum:
    def test_basic(self):
        assert checksum_sum(b"\x01\x02\x03") == 6

    def test_empty(self):
        assert checksum_sum(b"") == 0

    def test_single_byte(self):
        assert checksum_sum(b"\xff") == 255


class TestXOR:
    def test_basic(self):
        assert checksum_xor(b"\x01\x02\x03") == 0

    def test_empty(self):
        assert checksum_xor(b"") == 0

    def test_same_bytes(self):
        assert checksum_xor(b"\xaa\xaa") == 0

    def test_single(self):
        assert checksum_xor(b"\x55") == 0x55


class TestCRC8:
    def test_known(self):
        data = bytes([1, 2, 3, 4, 5])
        result = crc8(data)
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_empty(self):
        assert crc8(b"") == 0

    def test_deterministic(self):
        data = b"UART"
        assert crc8(data) == crc8(data)


class TestCRC16:
    def test_known(self):
        data = bytes([1, 2, 3, 4, 5])
        result = checksum_crc16(data)
        assert isinstance(result, int)
        assert 0 <= result <= 65535

    def test_empty(self):
        result = checksum_crc16(b"")
        assert isinstance(result, int)

    def test_deterministic(self):
        assert checksum_crc16(b"test") == checksum_crc16(b"test")


class TestComputeChecksum:
    @pytest.mark.parametrize("algo", ["sum", "xor", "crc8", "crc16"])
    def test_all_algos(self, algo):
        result = compute_checksum(b"test", algo)
        assert isinstance(result, int)

    def test_aliases(self):
        assert compute_checksum(b"test", "CRC-8") == compute_checksum(b"test", "crc8")
        assert compute_checksum(b"test", "exor") == compute_checksum(b"test", "xor")
        assert compute_checksum(b"test", "additive") == compute_checksum(b"test", "sum")

    def test_unknown(self):
        with pytest.raises(ValueError, match="Unknown"):
            compute_checksum(b"test", "md5")


class TestVerifyChecksum:
    def test_correct(self):
        data = b"test"
        expected = compute_checksum(data, "xor")
        assert verify_checksum(data, "xor", expected) is True

    def test_incorrect(self):
        data = b"test"
        assert verify_checksum(data, "xor", 99999) is False

    def test_none_expected(self):
        assert verify_checksum(b"test", "xor", None) is True

    def test_crc8_verify(self):
        data = b"\x01\x02\x03"
        expected = crc8(data)
        assert verify_checksum(data, "crc8", expected) is True
