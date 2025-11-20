import socket, time, statistics
import threading, random

HOST = "127.0.0.1"
PORT = 5001
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        print("Connected to server")
        c.sendall(b"JOIN\n")

        pid = None

        while True:
            data = c.recv(4096)
            if not data:
                print("Server closed connection")
                return

            text = data.decode().strip()
            for line in text.split("\n"):
                if not line:
                    continue
                print("From server:", line)

                if line.startswith("WELCOME"):
                    _, pid = line.split()
                    print("My player id:", pid)
                elif line.startswith("POS"):
                    parts = line.split()
                    if len(parts) == 4:
                        _, pid_msg, x_str, y_str = parts
                        print(f"Player {pid_msg} at ({x_str}, {y_str})")


            cmd = input("Move (W A S D, or Q to quit): ").strip().upper()
            if cmd == "Q":
                break
            elif cmd == "W":
                c.sendall(b"MOVE UP\n")
            elif cmd == "S":
                c.sendall(b"MOVE DOWN\n")
            elif cmd == "A":
                c.sendall(b"MOVE LEFT\n")
            elif cmd == "D":
                c.sendall(b"MOVE RIGHT\n")

    print("Client closed")


if __name__ == "__main__":
    main()
