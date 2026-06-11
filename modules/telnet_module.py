# ============================================================
# MODULE: telnet_module.py
# Covers: Telnet Script (#20), Telnet Library (#21),
#         Strings (#1), For-loops (#2), While Loop (#6),
#         Exception Handling (#13), Functions (#11),
#         Variables (#5), Conditional (#12)
# ============================================================

import telnetlib                                             # Telnet Library (#21)
import time
from typing import List


# ── Constants (Variables #5, Strings #1)
TELNET_TIMEOUT   = 10       # seconds
CMD_WAIT         = 0.5      # seconds between commands
ENCODING         = "utf-8"  # string encoding


def telnet_send(tn: telnetlib.Telnet, command: str, wait: float = CMD_WAIT) -> str:
    """
    Send a single command over Telnet and return output.
    Covers: Functions (#11), Strings (#1), Variables (#5)
    """
    tn.write(command.encode(ENCODING) + b"\n")               # Strings (#1)
    time.sleep(wait)
    output = tn.read_very_eager().decode(ENCODING, errors="ignore")
    return output


def telnet_connect(host: str, port: int,
                   username: str, password: str,
                   enable_pass: str) -> telnetlib.Telnet:
    """
    Connect to a Cisco device via Telnet.
    Returns an open Telnet session.
    Covers: Telnet Library (#21), Exception Handling (#13),
            Strings (#1), Conditional (#12)
    """
    try:
        print(f"    [TEL] Connecting to {host}:{port} via Telnet...")
        tn = telnetlib.Telnet(host, port, timeout=TELNET_TIMEOUT)  # Telnet Library

        # Wait for login prompt
        output = tn.read_until(b"Username:", timeout=TELNET_TIMEOUT)

        if b"Username:" in output:                           # Conditional (#12)
            tn.write(username.encode(ENCODING) + b"\n")
            time.sleep(0.3)

        tn.read_until(b"Password:", timeout=TELNET_TIMEOUT)
        tn.write(password.encode(ENCODING) + b"\n")
        time.sleep(0.5)

        # Enter enable mode
        tn.write(b"enable\n")
        time.sleep(0.3)

        result = tn.read_very_eager().decode(ENCODING, errors="ignore")

        if "Password" in result:                             # Conditional (#12)
            tn.write(enable_pass.encode(ENCODING) + b"\n")
            time.sleep(0.3)

        telnet_send(tn, "terminal length 0")                 # Disable paging
        print(f"    [TEL] ✓ Connected to {host}:{port}")
        return tn

    except Exception as e:                                   # Exception Handling (#13)
        raise ConnectionError(f"Telnet connect failed to {host}:{port} → {e}")


def telnet_configure_basic(host: str, port: int,
                            username: str, password: str,
                            enable_pass: str,
                            device_name: str,
                            interface: str,
                            ip_address: str,
                            subnet_mask: str) -> str:
    """
    Perform basic router configuration via Telnet.
    Covers: Telnet Script (#20), Lists (#8), For-loops (#2),
            Strings (#1), Exception Handling (#13)
    """
    collected_output = []                                    # Lists (#8)

    # Build config commands as a list
    commands: List[str] = [                                  # Lists (#8)
        "conf t",
        f"hostname {device_name}",
        f"interface {interface}",
        f"ip address {ip_address} {subnet_mask}",
        "no shutdown",
        "exit",
        "line con 0",
        "logging synchronous",
        "exit",
        "end",
        "write memory",
    ]

    try:
        tn = telnet_connect(host, port, username, password, enable_pass)

        # Send each command in a for-loop
        for cmd in commands:                                 # For-loops (#2)
            out = telnet_send(tn, cmd)
            collected_output.append(f"CMD: {cmd}\n{out}")   # Strings (#1)
            print(f"      » {cmd}")

        tn.close()
        print(f"    [TEL] ✓ Basic config applied on {device_name}")
        return "\n".join(collected_output)                   # Strings (#1)

    except Exception as e:                                   # Exception Handling (#13)
        print(f"    [TEL] ✗ Error: {e}")
        return str(e)


def telnet_run_commands(host: str, port: int,
                        username: str, password: str,
                        enable_pass: str,
                        commands: List[str]) -> str:
    """
    Run a list of show/exec commands via Telnet and return output.
    Covers: Telnet Script (#20), Lists (#8), For-loops (#2),
            While Loop (#6), Exception Handling (#13)
    """
    output_lines = []                                        # Lists (#8)

    try:
        tn = telnet_connect(host, port, username, password, enable_pass)

        # While loop: keep retrying prompt detection up to 3 times
        attempts = 0                                         # Numbers (#3)
        while attempts < 3:                                  # While Loop (#6)
            probe = telnet_send(tn, "")
            if "#" in probe or ">" in probe:                 # Conditional (#12)
                break
            attempts += 1                                    # Numbers (#3), Operators (#4)
            time.sleep(0.5)

        # For-loop over commands
        for cmd in commands:                                 # For-loops (#2)
            out = telnet_send(tn, cmd, wait=1.0)
            output_lines.append(f"\n{'='*40}\n$ {cmd}\n{out}")

        tn.close()
        return "\n".join(output_lines)                       # Strings (#1)

    except Exception as e:                                   # Exception Handling (#13)
        return f"ERROR: {e}"


def telnet_configure_ssh(host: str, port: int,
                         username: str, password: str,
                         enable_pass: str) -> str:
    """
    Enable SSH on the router via Telnet.
    Covers: SSH Configuration (#17), Telnet (#20/#21)
    """
    ssh_commands: List[str] = [                              # Lists (#8)
        "conf t",
        "ip domain-name lab.local",
        "crypto key generate rsa modulus 1024",
        "ip ssh version 2",
        f"username {username} privilege 15 secret {password}",
        "line vty 0 4",
        "transport input ssh telnet",
        "login local",
        "exit",
        "end",
        "write memory",
    ]

    try:
        tn = telnet_connect(host, port, username, password, enable_pass)
        output = []

        for cmd in ssh_commands:                             # For-loops (#2)
            out = telnet_send(tn, cmd, wait=1.5)
            output.append(out)
            print(f"      » {cmd}")

        tn.close()
        print(f"    [TEL] ✓ SSH enabled on {host}:{port}")
        return "\n".join(output)

    except Exception as e:                                   # Exception Handling (#13)
        print(f"    [TEL] ✗ SSH config error: {e}")
        return str(e)
