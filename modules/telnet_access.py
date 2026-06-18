import telnetlib

tn = telnetlib.Telnet("192.168.80.129", 5003)

tn.write(b"\n")

output = tn.read_until(b"#", timeout=5)

print(output.decode())
