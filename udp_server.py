import socket

HOST = "0.0.0.0"
PORT = 5002
REPLY_AT_END = False  # set True to only reply after a burst

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    print(f"UDP server listening on {HOST}:{PORT}")
    count = 0
    client_addr = None
    while True:
        data, addr = s.recvfrom(4096)
        client_addr = addr
        count += 1
        if REPLY_AT_END:
            if data == b"END\n":
                s.sendto(b"BACK\n", client_addr)
        else:
            s.sendto(b"BACK\n", addr)
