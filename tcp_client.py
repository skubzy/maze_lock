import socket, time, statistics

HOST = "127.0.0.1"   # change to server IP for cross-machine test
PORT = 5001

def rtt_once():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        t0 = time.perf_counter_ns()
        c.sendall(b"hello\n")
        _ = c.recv(4096)
        t1 = time.perf_counter_ns()
    return (t1 - t0) / 1e6  # ms

def rtt_burst(n=1000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        t0 = time.perf_counter_ns()
        for _ in range(n-1):
            c.sendall(b"hello\n")
        c.sendall(b"END\n")
        _ = c.recv(4096)  # single reply
        t1 = time.perf_counter_ns()
    return (t1 - t0) / 1e3  # µs, total burst time

print(f"TCP one-shot RTT: {rtt_once():.3f} ms")
print(f"TCP 1000-burst total: {rtt_burst():.0f} µs")
