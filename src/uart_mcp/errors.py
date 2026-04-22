class UartError(Exception):
    pass


class ConnectionError(UartError):
    def __init__(self, message: str, port: str = ""):
        self.port = port
        super().__init__(f"{message}" + (f" (port: {port})" if port else ""))


class SessionError(UartError):
    def __init__(self, message: str, session_id: str = ""):
        self.session_id = session_id
        super().__init__(
            f"{message}" + (f" (session: {session_id})" if session_id else "")
        )


class SecurityError(UartError):
    def __init__(self, message: str, command: str = ""):
        self.command = command
        super().__init__(f"{message}" + (f" (command: {command})" if command else ""))


class ValidationError(UartError):
    def __init__(self, field: str, value, reason: str = ""):
        self.field = field
        self.value = value
        self.reason = reason
        msg = f"Invalid {field}: {value}"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)


class EncodingError(UartError):
    def __init__(self, encoding: str, message: str):
        self.encoding = encoding
        super().__init__(f"Encoding error ({encoding}): {message}")


class ConfigError(UartError):
    pass
