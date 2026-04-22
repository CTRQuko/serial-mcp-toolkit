import pytest
from uart_mcp.security import (
    has_shell_metacharacters,
    is_read_only,
    is_dangerous,
    is_allowed_with_project,
    validate_command,
)


class TestMetacharacters:
    @pytest.mark.parametrize(
        "cmd", ["; rm", "& cmd", "| cat", "`cmd`", "$(cmd)", "> file"]
    )
    def test_dangerous_chars(self, cmd):
        result = has_shell_metacharacters(cmd)
        assert result is not None

    @pytest.mark.parametrize("cmd", ["ls -la", "cat /etc/config", "ping 8.8.8.8"])
    def test_clean_commands(self, cmd):
        result = has_shell_metacharacters(cmd)
        assert result is None

    def test_newline(self):
        result = has_shell_metacharacters("cmd\nrm")
        assert result is not None

    def test_carriage_return(self):
        result = has_shell_metacharacters("cmd\rrm")
        assert result is not None

    def test_chaining_and(self):
        result = has_shell_metacharacters("cmd1 && cmd2")
        assert result is not None

    def test_chaining_or(self):
        result = has_shell_metacharacters("cmd1 || cmd2")
        assert result is not None

    def test_semicolons(self):
        result = has_shell_metacharacters("cmd1;; cmd2")
        assert result is not None


class TestReadOnly:
    @pytest.mark.parametrize(
        "cmd", ["ls", "ls -la", "cat /etc/config", "ping 8.8.8.8", "dmesg"]
    )
    def test_read_only_commands(self, cmd):
        assert is_read_only(cmd) is True

    @pytest.mark.parametrize("cmd", ["reboot", "rm -rf /", "uci set test=1"])
    def test_non_read_only(self, cmd):
        assert is_read_only(cmd) is False


class TestDangerous:
    @pytest.mark.parametrize(
        "cmd", ["reboot", "rm -rf /", "poweroff", "mkfs.ext4 /dev/sda"]
    )
    def test_dangerous_commands(self, cmd):
        assert is_dangerous(cmd) is True

    @pytest.mark.parametrize("cmd", ["ls", "cat /etc/config", "ping 8.8.8.8"])
    def test_safe_commands(self, cmd):
        assert is_dangerous(cmd) is False


class TestAllowedWithProject:
    def test_uci_show(self):
        assert is_allowed_with_project("uci show network") is True

    def test_opkg_install(self):
        assert is_allowed_with_project("opkg install vim") is True

    def test_ifup(self):
        assert is_allowed_with_project("ifup wan") is True

    def test_unknown(self):
        assert is_allowed_with_project("unknown_command") is False


class TestValidateCommand:
    def test_clean_command(self):
        allowed, reason = validate_command("ls -la", "test_project")
        assert allowed is True

    def test_dangerous_command(self):
        allowed, reason = validate_command("reboot", "test_project")
        assert allowed is False

    def test_injection(self):
        allowed, reason = validate_command("; rm -rf /", "test_project")
        assert allowed is False

    def test_uci_with_project(self):
        allowed, reason = validate_command("uci show network", "test_project")
        assert allowed is True

    def test_uci_without_project_allowed(self):
        allowed, reason = validate_command("uci set test=1", "")
        assert allowed is True
