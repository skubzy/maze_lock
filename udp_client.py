import socket, time

HOST = "127.0.0.1"   # change to server IP for cross-machine test
PORT = 5002

def rtt_once():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as c:
        c.settimeout(2)
        t0 = time.perf_counter_ns()
        c.sendto(b"hello\n", (HOST, PORT))
        _ = c.recvfrom(4096)
        t1 = time.perf_counter_ns()
    return (t1 - t0) / 1e6  # ms

def rtt_burst(n=1000):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as c:
        c.settimeout(2)
        t0 = time.perf_counter_ns()
        for _ in range(n-1):
            c.sendto(b"hello\n", (HOST, PORT))
        c.sendto(b"END\n", (HOST, PORT))
        _ = c.recvfrom(4096)  # single reply
        t1 = time.perf_counter_ns()
    return (t1 - t0) / 1e3  # µs

print(f"UDP one-shot RTT: {rtt_once():.3f} ms")
print(f"UDP 1000-burst total: {rtt_burst():.0f} µs")
