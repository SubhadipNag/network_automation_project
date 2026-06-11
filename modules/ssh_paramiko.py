# ============================================================
# MODULE: ssh_paramiko.py
# Covers: SSH Paramiko (#24), SSH Configuration (#17),
#         Functions (#11), Exception Handling (#13),
#         Strings (#1), Lambda (#15), Advanced Functions (#14)
# ============================================================

import paramiko                                              # SSH Paramiko (#24)
import time
from typing import List, Callable, Optional


# ── Advanced function: decorator for retry logic (#14)
def retry(max_attempts: int = 3, delay: float = 2.0):
    """
    Decorator factory — retries a function on exception.
    Covers: Advanced Functions (#14), Lambda (#15)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):       # For-loops (#2)
                try:
                    return func(*args, **kwargs)              # Exception Handling (#13)
                except Exception as e:
                    print(f"    [SSH] Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:                # Conditional (#12)
                        time.sleep(delay)
            raise RuntimeError(f"All {max_attempts} attempts failed.")
        return wrapper
    return decorator


class ParamikoSSH:
    """
    Paramiko-based SSH client for Cisco IOS devices.
    Covers: PyClasses (#25), SSH Paramiko (#24),
            SSH Configuration (#17), Functions (#11)
    """

    def __init__(self, host: str, port: int,
                 username: str, password: str):
        self.host     = host                                  # Variables (#5)
        self.port     = port
        self.username = username
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None     # SSH Paramiko (#24)
        self.shell  = None

    @retry(max_attempts=3, delay=2.0)                        # Advanced Functions (#14)
    def connect(self) -> None:
        """Open SSH connection using Paramiko."""
        self.client = paramiko.SSHClient()                   # SSH Paramiko (#24)
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )
        self.client.connect(
            hostname = self.host,
            port     = self.port,
            username = self.username,
            password = self.password,
            timeout  = 10,
            look_for_keys = False,
            allow_agent   = False,
        )
        self.shell = self.client.invoke_shell()
        time.sleep(1)
        self.shell.recv(4096)                                 # clear banner
        print(f"    [SSH] ✓ Paramiko connected to {self.host}:{self.port}")

    def send_command(self, command: str, wait: float = 1.0) -> str:
        """Send a single command and return output."""
        if self.shell is None:                               # Conditional (#12)
            raise RuntimeError("Not connected. Call connect() first.")
        self.shell.send(command + "\n")
        time.sleep(wait)
        output = b""
        while self.shell.recv_ready():                       # While Loop (#6)
            output += self.shell.recv(4096)
        return output.decode("utf-8", errors="ignore")       # Strings (#1)

    def send_config_commands(self, commands: List[str]) -> str:
        """
        Send a list of configuration commands.
        Covers: Lists (#8), For-loops (#2), Functions (#11)
        """
        outputs = []                                         # Lists (#8)
        self.send_command("conf t")
        for cmd in commands:                                 # For-loops (#2)
            out = self.send_command(cmd)
            outputs.append(out)
            print(f"      » {cmd}")
        self.send_command("end")
        self.send_command("write memory")
        return "\n".join(outputs)                            # Strings (#1)

    def get_interfaces(self) -> dict:
        """
        Get interfaces and parse to dict.
        Covers: Dictionary (#7), Lambda (#15), Strings (#1)
        """
        raw = self.send_command("show interfaces brief", wait=2.0)
        lines = raw.split("\n")                              # Strings (#1)

        # Lambda to clean a line
        clean = lambda line: line.strip()                    # Lambda (#15)
        lines = list(map(clean, lines))                      # Lambda (#15)

        result = {}                                          # Dictionary (#7)
        for line in lines:                                   # For-loops (#2)
            parts = line.split()
            if len(parts) >= 2 and "Fast" in parts[0]:      # Conditional (#12)
                result[parts[0]] = parts[1]                  # Dictionary (#7)
        return result

    def disconnect(self) -> None:
        """Close the Paramiko connection."""
        if self.client:                                      # Conditional (#12)
            self.client.close()
            print(f"    [SSH] Disconnected from {self.host}:{self.port}")


def paramiko_run_show_commands(device: dict, commands: List[str]) -> str:
    """
    Functional wrapper to run show commands via Paramiko.
    Covers: Functions (#11), SSH Paramiko (#24),
            Exception Handling (#13), Strings (#1)
    """
    ssh = ParamikoSSH(
        host     = device["host"],
        port     = device["ssh_port"],
        username = device["username"],
        password = device["password"],
    )
    output_parts = []                                        # Lists (#8)
    try:
        ssh.connect()
        for cmd in commands:                                 # For-loops (#2)
            out = ssh.send_command(cmd, wait=1.5)
            output_parts.append(f"\n--- {cmd} ---\n{out}")
    except Exception as e:                                   # Exception Handling (#13)
        output_parts.append(f"ERROR: {e}")
    finally:
        ssh.disconnect()

    return "\n".join(output_parts)                          # Strings (#1)
