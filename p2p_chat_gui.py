import tkinter as tk
import socket
import threading
import uuid
from datetime import datetime
from database import init_db, store_message, load_messages  # from your database.py


class P2PChatGUI(tk.Frame):
    def __init__(self, master, nickname, listen_port, known_peers):
        super().__init__(master)
        self.master = master
        self.nickname = nickname
        self.listen_port = listen_port
        self.known_peers = known_peers  # List of (ip, port) tuples.
        self.connections = []  # Active socket connections.
        self.seen_messages = set()  # To avoid processing duplicates.
        self.lock = threading.Lock()

        # Initialize the database connection.
        self.db_conn = init_db()

        self.create_widgets()
        self.load_history()

        # Start listening for incoming peer connections.
        threading.Thread(target=self.accept_connections, daemon=True).start()

        # Connect to any known peers.
        for peer in self.known_peers:
            threading.Thread(target=self.connect_to_peer, args=(peer,), daemon=True).start()

    def create_widgets(self):
        self.text_area = tk.Text(self, wrap='word', state='disabled', font=("Helvetica", 12))
        self.text_area.pack(expand=True, fill='both', padx=5, pady=5)

        self.entry = tk.Entry(self, font=("Helvetica", 12))
        self.entry.bind("<Return>", self.send_message)
        self.entry.pack(fill='x', padx=5, pady=(0, 5))

        self.pack(expand=True, fill='both')

    def load_history(self):
        messages = load_messages(self.db_conn)
        for msg in messages:
            # Each msg is (id, sender, timestamp, message)
            formatted = f"[{msg[2]}] {msg[1]}: {msg[3]}"
            self.display_message(formatted)

    def accept_connections(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.listen_port))
        self.server_socket.listen(5)
        self.display_message(f"[INFO] Listening on port {self.listen_port}...")
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                self.display_message(f"[INFO] Connection from {addr}")
                with self.lock:
                    self.connections.append(client_socket)
                threading.Thread(target=self.receive_from_connection, args=(client_socket,), daemon=True).start()
            except Exception as e:
                self.display_message(f"[ERROR] accept_connections: {e}")
                break

    def connect_to_peer(self, peer):
        ip, port = peer
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            with self.lock:
                self.connections.append(s)
            self.display_message(f"[INFO] Connected to peer {ip}:{port}")
            threading.Thread(target=self.receive_from_connection, args=(s,), daemon=True).start()
        except Exception as e:
            self.display_message(f"[WARN] Could not connect to peer {ip}:{port}: {e}")

    def receive_from_connection(self, conn):
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                # Assume messages are newline-delimited.
                for line in data.decode('utf-8').splitlines():
                    self.handle_message(line, conn)
            except Exception as e:
                break
        with self.lock:
            if conn in self.connections:
                self.connections.remove(conn)
        conn.close()

    def handle_message(self, message, source_conn):
        # Expected format: MSG|<msg_id>|<nickname>|<text>
        parts = message.split("|", 3)
        if len(parts) != 4 or parts[0] != "MSG":
            self.display_message(f"[WARN] Malformed message: {message}")
            return
        msg_id = parts[1]
        sender = parts[2]
        text = parts[3]
        if msg_id in self.seen_messages:
            return
        self.seen_messages.add(msg_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {sender}: {text}"
        self.display_message(formatted)
        # Store the message in the database.
        store_message(self.db_conn, sender, text.encode('utf-8'))
        self.forward_message(message, source_conn)

    def forward_message(self, message, source_conn):
        with self.lock:
            for conn in self.connections:
                if conn != source_conn:
                    try:
                        conn.sendall((message + "\n").encode('utf-8'))
                    except Exception as e:
                        pass

    def send_message(self, event):
        text = self.entry.get().strip()
        if not text:
            return
        msg_id = str(uuid.uuid4())
        # Build the message in our protocol.
        message = f"MSG|{msg_id}|{self.nickname}|{text}"
        self.seen_messages.add(msg_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {self.nickname}: {text}"
        self.display_message(formatted)
        # Store the outgoing message.
        store_message(self.db_conn, self.nickname, text.encode('utf-8'))
        self.entry.delete(0, tk.END)
        with self.lock:
            for conn in self.connections:
                try:
                    conn.sendall((message + "\n").encode('utf-8'))
                except Exception as e:
                    self.display_message(f"[WARN] Error sending message: {e}")

    def display_message(self, message):
        # Schedule the update on the main GUI thread.
        self.master.after(0, lambda: self._append_message(message))

    def _append_message(self, message):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.config(state='disabled')
        self.text_area.see(tk.END)

    def shutdown(self):
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
        if hasattr(self, 'server_socket') and self.server_socket:
            self.server_socket.close()
        if self.db_conn:
            self.db_conn.close()
        self.master.destroy()


def main():
    nickname = input("Enter your nickname: ")
    port_str = input("Enter your listening port: ")
    try:
        listen_port = int(port_str)
    except:
        print("Invalid port.")
        return
    known = input("Enter known peers (format ip:port, comma separated) or leave blank: ")
    known_peers = []
    if known.strip():
        for peer_str in known.split(","):
            peer_str = peer_str.strip()
            if not peer_str:
                continue
            try:
                ip, p_str = peer_str.split(":")
                peer_port = int(p_str)
                known_peers.append((ip, peer_port))
            except:
                print(f"Invalid peer format: {peer_str}")
    root = tk.Tk()
    root.title("P2P Chat")
    app = P2PChatGUI(root, nickname, listen_port, known_peers)
    root.protocol("WM_DELETE_WINDOW", app.shutdown)
    root.mainloop()


if __name__ == "__main__":
    main()
