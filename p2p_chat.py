import socket
import threading
import uuid


class Peer:
    def __init__(self, nickname, listen_port, known_peers):
        """
        :param nickname: nickname for yourself
        :param listen_port: port to listen for incoming connections
        :param known_peers: list of tuples [(ip, port), ... ] of peers to connect to
        """
        self.nickname = nickname
        self.listen_port = listen_port
        self.known_peers = known_peers
        self.server_socket = None
        self.connections = []
        self.lock = threading.Lock()
        self.seen_messages = set()

    def start(self):
        server_thread = threading.Thread(target=self.accept_connections, daemon=True)
        server_thread.start()

        for peer in self.known_peers:
            self.connect_to_peer(peer)

        self.input_loop()

    def accept_connections(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.listen_port))
        self.server_socket.listen(5)
        print(f'[INFO] Listening on port {self.listen_port}...')

        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f'[INFO] Incoming connection from {addr}')

                with self.lcok:
                    self.connections.append(client_socket)
                threading.Thread(target=self.receive_from_connection, args=(client_socket,), daemon=True).start()
            except Exception as e:
                print('[ERROR] accept_connections: ', e)
                break

    def connect_to_peer(self, peer):
        """

        :param peer:
        :return:
        """
        ip, port = peer
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            with self.lock:
                self.connections.append(s)
            print(f'[INFO] Connected to peer {ip}:{port}')
            threading.Thread(target=self.receive_from_connection, args=(s,), daemon=True).start()
        except Exception as e:
            print(f'[WARN] Could not connect to peer {ip}:{port}: {e}')

    def receive_from_connection(self, conn):
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break

                for line in data.decode('utf-8').splitlines():
                    self.handle_message(line, conn)
            except Exception as e:
                break
        with self.lock:
            if conn in self.connections:
                self.connections.remove(conn)
        conn.close()

    def handle_message(self, message, source_conn):
        """

        :param message:
        :param source_conn:
        :return:
        """
        parts = message.split("|", 3)
        if len(parts) != 4 or parts[0] != 'MSG':
            print('[WARN] Received malformed message: ', message)
            return

        msg_id = parts[1]
        sender = parts[2]
        text = parts[3]

        if msg_id in self.seen_messages:
            return
        self.seen_messages.add(msg_id)

        print(f'{sender}: {text}')

        self.foward_message(message, source_conn)

    def forward_message(self, message, source_conn):
        """

        :param message:
        :param source_conn:
        :return:
        """
        with self.lock:
            for conn in self.connections:
                if conn != source_conn:
                    try:
                        conn.sendall((message + '\n').encode('utf-8'))
                    except Exception as e:
                        pass

    def input_loop(self):
        """

        :return:
        """
        while True:
            try:
                text = input('')
                if text.lower() == "/quit":
                    print('[INFO] Exiting...')
                    break

                msg_id = str(uuid.uuid4())

                msg = f'MSQ|{msg_id}|{self.nickname}|{text}'

                self.seen_messages.add(msg_id)
                print(f'{self.nickname}: {text}')
                with self.lock:
                    for conn in self.connections:
                        try:
                            conn.sendall((msg + '\n').encode('utf-8'))
                        except Exception as e:
                            print('[WARN] Error sending to a connection: ', e)
            except KeyboardInterrupt:
                print("\n[INFO] Exiting...")
                break
        self.shutdown()

    def shutdown(self):
        """

        :return:
        """
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
        if self.server_socket:
            self.server_socket.close()

def main():
    nickname = input('Enter your nickname: ')
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
    peer = Peer(nickname, listen_port, known_peers)
    peer.start()


if __name__ == "__main__":
    main()