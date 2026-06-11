# ============================================================
# MODULE: device_model.py
# Covers: Pydantic (#38), Classes (#25), Strings (#1),
#         Variables (#5), Conditional (#12), Functions (#11)
# ============================================================

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class DeviceModel(BaseModel):
    """
    Pydantic model for a network device.
    Validates all fields before any connection attempt.
    """
    name: str
    host: str
    telnet_port: int
    ssh_port: int
    username: str
    password: str
    enable_password: str
    platform: str
    interface: str
    ip_address: str
    subnet_mask: str
    loopback_ip: str
    loopback_mask: str
    bgp_as: int
    bgp_neighbor: str
    bgp_neighbor_as: int

    # ── Validator: name must be non-empty string
    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():                        # Strings (#1), Conditional (#12)
            raise ValueError("Device name cannot be empty")
        return v.upper()                         # Strings (#1)

    # ── Validator: port must be in valid range
    @field_validator("telnet_port", "ssh_port")
    @classmethod
    def port_range_check(cls, v: int) -> int:
        if not (1 <= v <= 65535):                # Numbers (#3), Operators (#4)
            raise ValueError(f"Port {v} is out of valid range 1-65535")
        return v

    # ── Validator: IP format check (basic)
    @field_validator("host", "ip_address", "loopback_ip", "bgp_neighbor")
    @classmethod
    def ip_format_check(cls, v: str) -> str:
        parts = v.split(".")                     # Strings (#1), Lists (#8)
        if len(parts) != 4:
            raise ValueError(f"Invalid IP address format: {v}")
        for part in parts:                       # For-loops (#2)
            if not part.isdigit():
                raise ValueError(f"Non-numeric octet in IP: {v}")
            if not (0 <= int(part) <= 255):      # Numbers (#3), Operators (#4)
                raise ValueError(f"Octet out of range in IP: {v}")
        return v

    def to_netmiko_dict(self) -> dict:
        """Return a dict compatible with Netmiko ConnectHandler."""
        return {                                  # Dictionary (#7)
            "device_type": self.platform,
            "host": self.host,
            "port": self.ssh_port,
            "username": self.username,
            "password": self.password,
            "secret": self.enable_password,
        }

    def to_telnet_tuple(self) -> tuple:
        """Return a tuple of (host, port) for Telnet."""
        return (self.host, self.telnet_port)     # Tuples (#9)

    def summary(self) -> str:
        """Return a human-readable device summary string."""
        return (                                  # Strings (#1), Variables (#5)
            f"[{self.name}] host={self.host} | "
            f"telnet={self.telnet_port} | ip={self.ip_address} | "
            f"loopback={self.loopback_ip} | bgp_as={self.bgp_as}"
        )


class GNS3ServerModel(BaseModel):
    """Pydantic model for the GNS3 REST API server."""
    host: str
    port: int
    username: str
    password: str

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}/v2"  # Strings (#1), Variables (#5)
