import socket
import threading

store = {}

def handle_client(conn):
    with conn:
        data = conn.recv(1024).decode().strip()
        if data == "PING":
            conn.sendall(b"PONG\n")
        elif data.startswith("SET "):
            _, key, value = data.split(" ", 2)
            store[key] = value
            conn.sendall(b"OK\n")
        elif data.startswith("GET "):
            _, key = data.split(" ", 1)
            value = store.get(key, "")
            conn.sendall(f"{value}\n".encode())
        else:
            conn.sendall(b"ERROR\n")

def start_server(port=4221):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port reuse
    s.bind(('localhost', port))
    s.listen()
    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()
