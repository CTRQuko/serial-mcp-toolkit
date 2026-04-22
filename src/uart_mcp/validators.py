from .errors import ValidationError
from .config import VALID_BAUD_RATES


def validate_baud_rate(baud_rate: int) -> int:
    if baud_rate <= 0:
        raise ValidationError("baud_rate", baud_rate, "Must be positive")
    if baud_rate > 4_000_000:
        raise ValidationError("baud_rate", baud_rate, "Must be <= 4,000,000")
    if baud_rate not in VALID_BAUD_RATES:
        raise ValidationError(
            "baud_rate",
            baud_rate,
            f"Not a standard rate. Valid: {', '.join(str(r) for r in VALID_BAUD_RATES)}",
        )
    return baud_rate


def validate_data_bits(data_bits: int) -> int:
    if data_bits not in (5, 6, 7, 8):
        raise ValidationError("data_bits", data_bits, "Must be 5, 6, 7, or 8")
    return data_bits


def validate_stop_bits(stop_bits) -> float:
    valid = {1, 1.5, 2, "1", "1.5", "2", "one", "two"}
    sb = stop_bits
    if isinstance(sb, str):
        sb_lower = sb.lower()
        if sb_lower in ("1", "one"):
            return 1
        if sb_lower in ("2", "two"):
            return 2
        if sb_lower == "1.5":
            return 1.5
        raise ValidationError("stop_bits", stop_bits, "Must be 1, 1.5, or 2")
    if sb not in (1, 1.5, 2):
        raise ValidationError("stop_bits", stop_bits, "Must be 1, 1.5, or 2")
    return float(sb)


def validate_parity(parity: str) -> str:
    valid = {"none", "even", "odd", "mark", "space"}
    if parity.lower() not in valid:
        raise ValidationError(
            "parity", parity, f"Must be one of: {', '.join(sorted(valid))}"
        )
    return parity.lower()


def validate_flow_control(flow_control: str) -> str:
    valid = {"none", "software", "hardware"}
    if flow_control.lower() not in valid:
        raise ValidationError(
            "flow_control", flow_control, f"Must be one of: {', '.join(sorted(valid))}"
        )
    return flow_control.lower()


def validate_port_name(port: str) -> str:
    if not port or not port.strip():
        raise ValidationError("port", port, "Port name cannot be empty")
    if len(port) > 255:
        raise ValidationError("port", port, "Port name too long (max 255 chars)")
    return port.strip()
