import socket, time

HOST = "0.0.0.0"
PORT = 5001
REPLY_AT_END = False  # set True to only reply after a burst

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"TCP server listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        buf = b""
        count = 0
        while True:
            data = conn.recv(4096)
            if not data: break
            buf += data
            while b"\n" in buf:
                msg, buf = buf.split(b"\n", 1)
                count += 1
                if REPLY_AT_END:
                    if msg == b"END":
                        conn.sendall(b"BACK\n")
                else:
                    conn.sendall(b"BACK\n")
