# ============================================================
# MODULE: log_parser.py
# Covers: Log Parsing (#31), Regex (#19), Functions (#11),
#         Strings (#1), Lists (#8), Dictionary (#7),
#         For-loops (#2), Conditional (#12),
#         Lambda (#15), List Comprehension (#16)
# ============================================================

import re                                                    # Regex (#19)
import os
from datetime import datetime
from typing import List, Dict, Optional


LOG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "logs", "automation.log"
)


# ── Regex patterns for Cisco IOS log lines (#19)
PATTERNS = {                                                 # Dictionary (#7)
    "bgp_neighbor_up":   re.compile(
        r"%BGP-5-ADJCHANGE:\s+neighbor\s+(\S+)\s+Up", re.I
    ),
    "bgp_neighbor_down": re.compile(
        r"%BGP-5-ADJCHANGE:\s+neighbor\s+(\S+)\s+Down", re.I
    ),
    "interface_up":      re.compile(
        r"%LINK-3-UPDOWN:\s+Interface\s+(\S+),\s+changed state to up", re.I
    ),
    "interface_down":    re.compile(
        r"%LINK-3-UPDOWN:\s+Interface\s+(\S+),\s+changed state to down", re.I
    ),
    "ospf_neighbor":     re.compile(
        r"%OSPF-5-ADJCHG:\s+Process\s+\d+,\s+Nbr\s+(\S+)", re.I
    ),
    "config_changed":    re.compile(
        r"%SYS-5-CONFIG_I:\s+Configured from (.+)", re.I
    ),
    "login":             re.compile(
        r"%SEC_LOGIN-5-LOGIN_SUCCESS:\s+Login Success.*from\s+(\S+)", re.I
    ),
}


def write_log(message: str, level: str = "INFO") -> None:
    """
    Append a log entry to the log file.
    Covers: Functions (#11), Strings (#1), Log Parsing (#31)
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Strings (#1)
    log_line  = f"[{timestamp}] [{level}] {message}\n"       # Strings (#1), Variables (#5)

    with open(LOG_FILE, "a") as f:
        f.write(log_line)


def parse_log_file(filepath: str = LOG_FILE) -> List[Dict[str, str]]:
    """
    Parse log file lines and classify each entry.
    Covers: Log Parsing (#31), Regex (#19), Lists (#8),
            Dictionary (#7), For-loops (#2), Conditional (#12)
    """
    events: List[Dict[str, str]] = []                        # Lists (#8)

    try:
        with open(filepath, "r") as f:
            lines = f.readlines()                            # Lists (#8)
    except FileNotFoundError:
        print(f"  [LOG] Log file not found: {filepath}")
        return events

    for line in lines:                                       # For-loops (#2)
        line = line.strip()
        if not line:                                         # Conditional (#12)
            continue

        # Try each regex pattern
        matched = False
        for event_type, pattern in PATTERNS.items():        # For-loops (#2)
            m = pattern.search(line)                        # Regex (#19)
            if m:                                            # Conditional (#12)
                events.append({                              # Dictionary (#7)
                    "raw":     line,
                    "event":   event_type,
                    "detail":  m.group(1) if m.lastindex else "",
                })
                matched = True
                break

        if not matched:
            events.append({
                "raw":   line,
                "event": "general",
                "detail": "",
            })

    return events


def parse_cisco_log_string(log_text: str) -> List[Dict[str, str]]:
    """
    Parse a raw Cisco IOS log string (from show logging).
    Covers: Regex (#19), List Comprehension (#16), Lambda (#15)
    """
    lines = log_text.split("\n")                             # Strings (#1)

    # Lambda: strip whitespace + filter blank lines
    clean_line = lambda l: l.strip()                         # Lambda (#15)
    non_empty  = list(filter(lambda l: len(l) > 5, map(clean_line, lines)))  # Lambda (#15)

    # List comprehension to extract lines containing %%
    cisco_syslogs = [                                        # List Comprehension (#16)
        line for line in non_empty
        if re.search(r"%[A-Z]+-\d+-\w+:", line)             # Regex (#19)
    ]

    results = []
    for line in cisco_syslogs:                               # For-loops (#2)
        event = {"raw": line, "event": "syslog", "detail": ""}

        # Extract severity level using regex
        sev_match = re.search(r"%\w+-(\d+)-\w+:", line)     # Regex (#19)
        if sev_match:                                        # Conditional (#12)
            sev = int(sev_match.group(1))
            event["severity"] = str(sev)
            # Severity 0-3 = critical, 4-5 = warning, 6-7 = info
            if sev <= 3:                                     # Numbers (#3), Operators (#4)
                event["level"] = "CRITICAL"
            elif sev <= 5:
                event["level"] = "WARNING"
            else:
                event["level"] = "INFO"

        results.append(event)

    return results


def get_log_summary(events: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Count events by type.
    Covers: Dictionary (#7), For-loops (#2), Numbers (#3)
    """
    summary: Dict[str, int] = {}                             # Dictionary (#7)

    for event in events:                                     # For-loops (#2)
        etype = event.get("event", "unknown")
        summary[etype] = summary.get(etype, 0) + 1          # Numbers (#3), Operators (#4)

    return summary


def extract_ip_addresses(text: str) -> List[str]:
    """
    Extract all IP addresses from a text block using Regex.
    Covers: Regex (#19), List Comprehension (#16), Sets (#10)
    """
    ip_pattern = re.compile(                                 # Regex (#19)
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )
    all_ips = ip_pattern.findall(text)                       # Regex (#19)

    # Remove duplicates using set, then return sorted list
    unique_ips = sorted(set(all_ips))                        # Sets (#10)
    return unique_ips


def extract_interface_names(text: str) -> List[str]:
    """
    Extract interface names from show output using Regex.
    Covers: Regex (#19), List Comprehension (#16)
    """
    pattern = re.compile(                                    # Regex (#19)
        r"(FastEthernet\d+/\d+|GigabitEthernet\d+/\d+|Loopback\d+|Serial\d+/\d+)",
        re.IGNORECASE
    )
    found = pattern.findall(text)                            # Regex (#19)

    # List comprehension — deduplicate, preserve order
    seen = set()                                             # Sets (#10)
    unique = [                                               # List Comprehension (#16)
        iface for iface in found
        if not (iface in seen or seen.add(iface))
    ]
    return unique
