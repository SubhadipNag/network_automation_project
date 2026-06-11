# ============================================================
# MODULE: sniff_module.py
# Covers: Netmiko Network Packet Sniffing (#28),
#         Multithreading (#18), Functions (#11),
#         Exception Handling (#13), Lists (#8),
#         Variables (#5), Conditional (#12), While Loop (#6)
# ============================================================

import threading                                             # Multithreading (#18)
import time
from typing import List, Dict, Optional

# Scapy for packet sniffing — graceful fallback
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP         # Packet Sniffing (#28)
    from scapy.layers.inet import Ether
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("  [SNIFF] scapy not installed — sniff module in stub mode")


# ── Shared state for captured packets
captured_packets: List[dict] = []                            # Lists (#8)
sniff_lock        = threading.Lock()                         # Multithreading (#18)
sniff_active      = threading.Event()                        # Multithreading (#18)


def packet_callback(packet) -> None:
    """
    Callback for each captured packet.
    Covers: Functions (#11), Conditional (#12), Strings (#1)
    """
    global captured_packets

    try:
        pkt_info: Dict = {}                                  # Dictionary (#7)

        if IP in packet:                                     # Conditional (#12)
            pkt_info["src_ip"] = packet[IP].src             # Strings (#1)
            pkt_info["dst_ip"] = packet[IP].dst
            pkt_info["proto"]  = packet[IP].proto

        if TCP in packet:                                     # Conditional (#12)
            pkt_info["sport"]  = packet[TCP].sport           # Numbers (#3)
            pkt_info["dport"]  = packet[TCP].dport
            pkt_info["type"]   = "TCP"

        elif UDP in packet:
            pkt_info["sport"]  = packet[UDP].sport
            pkt_info["dport"]  = packet[UDP].dport
            pkt_info["type"]   = "UDP"

        elif ICMP in packet:
            pkt_info["type"]   = "ICMP"

        if pkt_info:                                         # Conditional (#12)
            with sniff_lock:                                 # Multithreading (#18)
                captured_packets.append(pkt_info)

    except Exception:                                        # Exception Handling (#13)
        pass


def sniff_thread_worker(interface: str, count: int, timeout: int) -> None:
    """
    Runs in a separate thread to sniff packets.
    Covers: Multithreading (#18), Packet Sniffing (#28)
    """
    if not SCAPY_AVAILABLE:                                  # Conditional (#12)
        print("  [SNIFF] Scapy not available — simulating sniff")
        time.sleep(2)
        return

    try:
        sniff(
            iface   = interface,
            prn     = packet_callback,                       # Packet Sniffing (#28)
            count   = count,
            timeout = timeout,
            store   = False,
        )
    except Exception as e:                                   # Exception Handling (#13)
        print(f"  [SNIFF] Error: {e}")
    finally:
        sniff_active.clear()


def start_packet_sniff(interface: str = "eth0",
                       count: int = 20,
                       timeout: int = 10) -> threading.Thread:
    """
    Start packet sniffing in a background thread.
    Covers: Multithreading (#18), Functions (#11)
    """
    global captured_packets
    captured_packets = []                                    # Reset
    sniff_active.set()

    t = threading.Thread(                                    # Multithreading (#18)
        target = sniff_thread_worker,
        args   = (interface, count, timeout),
        daemon = True,
        name   = "PacketSnifferThread",
    )
    t.start()
    print(f"  [SNIFF] Packet sniffing started on {interface} "
          f"(count={count}, timeout={timeout}s)")
    return t


def wait_for_sniff(thread: threading.Thread,
                   poll_interval: float = 1.0) -> List[dict]:
    """
    Wait for sniff thread to finish; use while loop for polling.
    Covers: While Loop (#6), Multithreading (#18), Variables (#5)
    """
    elapsed = 0.0                                            # Variables (#5), Numbers (#3)
    max_wait = 15.0                                          # Numbers (#3)

    while thread.is_alive() and elapsed < max_wait:         # While Loop (#6)
        time.sleep(poll_interval)
        elapsed += poll_interval                             # Operators (#4)

    thread.join(timeout=2)

    with sniff_lock:                                         # Multithreading (#18)
        results = list(captured_packets)

    print(f"  [SNIFF] Captured {len(results)} packets")
    return results


def run_multithreaded_commands(device_list: list,
                               command_fn,
                               **kwargs) -> Dict[str, str]:
    """
    Run a command function across multiple devices concurrently.
    Covers: Multithreading (#18), For-loops (#2),
            Lambda (#15), Functions (#11)
    """
    results:  Dict[str, str] = {}                            # Dictionary (#7)
    threads:  List[threading.Thread] = []                    # Lists (#8)
    lock      = threading.Lock()                             # Multithreading (#18)

    def worker(device: dict) -> None:
        """Thread worker — runs command_fn for one device."""
        name = device["name"]
        try:
            out = command_fn(device, **kwargs)
            with lock:                                       # Multithreading (#18)
                results[name] = out
        except Exception as e:                               # Exception Handling (#13)
            with lock:
                results[name] = f"ERROR: {e}"

    # Create a thread per device
    for device in device_list:                               # For-loops (#2)
        t = threading.Thread(                                # Multithreading (#18)
            target = worker,
            args   = (device,),
            name   = f"Thread-{device['name']}",
        )
        threads.append(t)
        t.start()
        print(f"  [MT] Started thread for {device['name']}")

    # Wait for all threads to complete
    for t in threads:                                        # For-loops (#2)
        t.join(timeout=30)
        print(f"  [MT] Thread {t.name} completed")

    return results
