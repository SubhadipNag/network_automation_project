# ============================================================
# MODULE: napalm_module.py
# Covers: NAPALM (#27), Functions (#11), Exception Handling (#13),
#         Dictionary (#7), Lists (#8), Conditional (#12),
#         Strings (#1), For-loops (#2)
# ============================================================

try:
    from napalm import get_network_driver                    # NAPALM (#27)
    NAPALM_AVAILABLE = True
except ImportError:
    NAPALM_AVAILABLE = False
    print("  [NAPALM] napalm not installed — module in stub mode")

from typing import Dict, Any, List


def napalm_get_facts(device: dict) -> Dict[str, Any]:
    """
    Use NAPALM to fetch device facts.
    Covers: NAPALM (#27), Dictionary (#7), Exception Handling (#13)
    """
    if not NAPALM_AVAILABLE:                                 # Conditional (#12)
        return {"error": "napalm not installed"}

    driver = get_network_driver(device["platform"])          # NAPALM (#27)

    optional_args = {                                        # Dictionary (#7)
        "transport": "telnet",
        "port": device["telnet_port"],
    }

    try:
        with driver(
            hostname     = device["host"],
            username     = device["username"],
            password     = device["password"],
            optional_args= optional_args,
        ) as conn:                                           # NAPALM (#27)

            facts         = conn.get_facts()
            interfaces    = conn.get_interfaces()
            bgp_neighbors = conn.get_bgp_neighbors()

            # Combine into one result dict
            result: Dict[str, Any] = {                       # Dictionary (#7)
                "facts":          facts,
                "interfaces":     interfaces,
                "bgp_neighbors":  bgp_neighbors,
            }

            print(f"    [NAPALM] ✓ Facts retrieved from {device['name']}")
            return result

    except Exception as e:                                   # Exception Handling (#13)
        print(f"    [NAPALM] ✗ Error on {device['name']}: {e}")
        return {"error": str(e)}


def napalm_get_all_devices(devices: List[dict]) -> Dict[str, Any]:
    """
    Collect NAPALM facts from all devices.
    Covers: For-loops (#2), Functions (#11), Dictionary (#7)
    """
    all_facts: Dict[str, Any] = {}                           # Dictionary (#7)

    for device in devices:                                   # For-loops (#2)
        name = device["name"]
        print(f"\n  [NAPALM] Fetching facts for {name}...")
        all_facts[name] = napalm_get_facts(device)

    return all_facts


def format_napalm_facts(facts_dict: Dict[str, Any]) -> str:
    """
    Format NAPALM facts as readable text.
    Covers: Strings (#1), For-loops (#2), Conditional (#12)
    """
    lines = []                                               # Lists (#8)
    lines.append("=" * 60)
    lines.append("  NAPALM DEVICE FACTS")
    lines.append("=" * 60)

    for device_name, data in facts_dict.items():             # For-loops (#2)
        lines.append(f"\n  Device: {device_name}")
        lines.append("-" * 40)

        if "error" in data:                                  # Conditional (#12)
            lines.append(f"  ERROR: {data['error']}")
            continue

        facts = data.get("facts", {})
        for key, val in facts.items():                       # For-loops (#2)
            lines.append(f"  {key:25s}: {val}")             # Strings (#1)

        ifaces = data.get("interfaces", {})
        lines.append(f"\n  Interfaces ({len(ifaces)}):")
        for iname, idata in ifaces.items():                  # For-loops (#2)
            state = "UP" if idata.get("is_up") else "DOWN"   # Conditional (#12)
            lines.append(f"    {iname:25s}: {state}")

    return "\n".join(lines)                                  # Strings (#1)
