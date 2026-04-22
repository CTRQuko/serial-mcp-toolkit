import logging
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from .config import (
    DEFAULT_BAUD,
    DEFAULT_DATA_BITS,
    DEFAULT_STOP_BITS,
    DEFAULT_PARITY,
    DEFAULT_FLOW_CONTROL,
    DEFAULT_TIMEOUT,
    MAX_SESSIONS,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
)
from .validators import (
    validate_baud_rate,
    validate_data_bits,
    validate_stop_bits,
    validate_parity,
    validate_flow_control,
    validate_port_name,
)
from .errors import ConnectionError, SessionError, ValidationError

logger = logging.getLogger(__name__)


class SessionState(Enum):
    CREATING = "creating"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class SessionStats:
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    errors_count: int = 0
    reconnections: int = 0
    last_activity: Optional[datetime] = None

    def record_send(self, nbytes: int):
        self.bytes_sent += nbytes
        self.messages_sent += 1
        self.last_activity = datetime.now(timezone.utc)

    def record_receive(self, nbytes: int):
        self.bytes_received += nbytes
        self.messages_received += 1
        self.last_activity = datetime.now(timezone.utc)

    def record_error(self):
        self.errors_count += 1
        self.last_activity = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "errors_count": self.errors_count,
            "reconnections": self.reconnections,
            "last_activity": self.last_activity.isoformat()
            if self.last_activity
            else None,
        }


@dataclass
class SessionConfig:
    port: str = ""
    baudrate: int = DEFAULT_BAUD
    data_bits: int = DEFAULT_DATA_BITS
    stop_bits: float = DEFAULT_STOP_BITS
    parity: str = DEFAULT_PARITY
    flow_control: str = DEFAULT_FLOW_CONTROL
    timeout: float = DEFAULT_TIMEOUT
    auto_reconnect: bool = False
    max_reconnect_attempts: int = 3

    @classmethod
    def from_params(
        cls,
        port: str,
        baudrate: int = DEFAULT_BAUD,
        data_bits: int = DEFAULT_DATA_BITS,
        stop_bits=DEFAULT_STOP_BITS,
        parity: str = DEFAULT_PARITY,
        flow_control: str = DEFAULT_FLOW_CONTROL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> "SessionConfig":
        validate_port_name(port)
        validate_baud_rate(baudrate)
        validate_data_bits(data_bits)
        validate_stop_bits(stop_bits)
        validate_parity(parity)
        validate_flow_control(flow_control)

        return cls(
            port=port.strip(),
            baudrate=baudrate,
            data_bits=data_bits,
            stop_bits=stop_bits,
            parity=parity.lower(),
            flow_control=flow_control.lower(),
            timeout=timeout,
        )

    def parity_serial(self) -> str:
        mapping = {"none": "N", "even": "E", "odd": "O", "mark": "M", "space": "S"}
        return mapping.get(self.parity, "N")

    def config_string(self) -> str:
        p = self.parity_serial()
        s = int(self.stop_bits)
        return f"{self.baudrate}/{self.data_bits}{p}{s}"


class Session:
    def __init__(
        self,
        session_id: str,
        project: str,
        device: str,
        config: SessionConfig,
        ser: serial.Serial,
    ):
        self.session_id = session_id
        self.project = project
        self.device = device
        self.config = config
        self.ser = ser
        self.state = SessionState.ACTIVE
        self.created_at = datetime.now(timezone.utc)
        self.last_accessed = datetime.now(timezone.utc)
        self.stats = SessionStats()
        self._reconnect_attempts = 0
        self._reconnecting = False

    def touch(self):
        self.last_accessed = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        return self.state == SessionState.ACTIVE and self.ser and self.ser.is_open

    def idle_seconds(self) -> int:
        if self.last_accessed:
            return int(
                (datetime.now(timezone.utc) - self.last_accessed).total_seconds()
            )
        return 0

    def is_idle(self, max_idle: int = 3600) -> bool:
        return self.idle_seconds() > max_idle and not self.is_active()

    def close(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
        self.state = SessionState.CLOSED
        self.touch()

    def reconnect_delay(self) -> float:
        delay = RECONNECT_BASE_DELAY * (2**self._reconnect_attempts)
        return min(delay, RECONNECT_MAX_DELAY)

    def try_reconnect(self) -> bool:
        if self._reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.warning(
                "Session %s: max reconnect attempts reached (%d)",
                self.session_id[:12],
                self.config.max_reconnect_attempts,
            )
            self.state = SessionState.ERROR
            return False

        self._reconnecting = True
        self.state = SessionState.SUSPENDED
        delay = self.reconnect_delay()
        logger.info(
            "Session %s: reconnecting in %.1fs (attempt %d/%d)",
            self.session_id[:12],
            delay,
            self._reconnect_attempts + 1,
            self.config.max_reconnect_attempts,
        )
        time.sleep(delay)

        parity_map = {
            "none": serial.PARITY_NONE,
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD,
            "mark": serial.PARITY_MARK,
            "space": serial.PARITY_SPACE,
        }

        try:
            if self.ser and self.ser.is_open:
                self.ser.close()

            self.ser = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.data_bits,
                stopbits=self.config.stop_bits,
                parity=parity_map.get(self.config.parity, serial.PARITY_NONE),
                xonxoff=self.config.flow_control == "software",
                rtscts=self.config.flow_control == "hardware",
                timeout=self.config.timeout,
                write_timeout=self.config.timeout,
            )

            self._reconnect_attempts += 1
            self.stats.reconnections += 1
            self.state = SessionState.ACTIVE
            logger.info("Session %s: reconnected OK", self.session_id[:12])
            return True

        except serial.SerialException as e:
            self._reconnect_attempts += 1
            logger.error(
                "Session %s: reconnect failed (attempt %d): %s",
                self.session_id[:12],
                self._reconnect_attempts,
                e,
            )
            self.state = SessionState.ERROR
            self.stats.record_error()
            return False
        finally:
            self._reconnecting = False

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "project": self.project,
            "device": self.device,
            "port": self.config.port,
            "baudrate": self.config.baudrate,
            "config": self.config.config_string(),
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
            if self.last_accessed
            else None,
            "stats": self.stats.to_dict(),
        }


class ConnectionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def connect(
        self, session_id: str, project: str, device: str, config: SessionConfig
    ) -> Session:
        with self._lock:
            if len(self._sessions) >= MAX_SESSIONS:
                raise SessionError(
                    f"Max sessions reached ({MAX_SESSIONS}). Disconnect a session first."
                )

            for sid, sess in self._sessions.items():
                if sess.config.port == config.port and sess.is_active():
                    raise ConnectionError(
                        f"Port {config.port} already in use by session {sid}",
                        port=config.port,
                    )

        parity_map = {
            "none": serial.PARITY_NONE,
            "even": serial.PARITY_EVEN,
            "odd": serial.PARITY_ODD,
            "mark": serial.PARITY_MARK,
            "space": serial.PARITY_SPACE,
        }
        flow_map = {"none": False, "software": True, "hardware": True}

        try:
            ser = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.data_bits,
                stopbits=config.stop_bits,
                parity=parity_map.get(config.parity, serial.PARITY_NONE),
                xonxoff=flow_map.get(config.flow_control, False)
                if config.flow_control == "software"
                else False,
                rtscts=flow_map.get(config.flow_control, False)
                if config.flow_control == "hardware"
                else False,
                timeout=config.timeout,
                write_timeout=config.timeout,
            )
        except serial.SerialException as e:
            raise ConnectionError(str(e), port=config.port)

        session = Session(session_id, project, device, config, ser)

        with self._lock:
            self._sessions[session_id] = session

        return session

    def disconnect(self, session_id: str) -> str:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if not session:
            raise SessionError(f"Session {session_id} not found", session_id=session_id)
        session.close()
        return session_id

    def get(self, session_id: str) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if not session:
            raise SessionError(f"Session {session_id} not found", session_id=session_id)
        return session

    def get_active_session(self) -> Optional[Session]:
        with self._lock:
            for session in self._sessions.values():
                if session.is_active():
                    return session
        return None

    def list_sessions(self) -> list[dict]:
        with self._lock:
            return [s.to_dict() for s in self._sessions.values()]

    def cleanup_idle(self, max_idle: int = 3600) -> list[str]:
        cleaned = []
        with self._lock:
            to_remove = [
                sid for sid, s in self._sessions.items() if s.is_idle(max_idle)
            ]
        for sid in to_remove:
            try:
                self.disconnect(sid)
                cleaned.append(sid)
            except Exception:
                pass
        return cleaned

    @staticmethod
    def list_ports() -> list[dict]:
        ports = list(serial.tools.list_ports.comports())
        result = []
        for port in ports:
            result.append(
                {
                    "device": port.device,
                    "description": port.description,
                    "hwid": port.hwid if hasattr(port, "hwid") else "",
                }
            )
        return result
