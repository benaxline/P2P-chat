import socket
import threading
from typing import List, Tuple

# local host
HOST: str = '127.0.0.1'
PORT: int = 5050

stop_server_event = threading.Event()
clients: List[socket.socket] = []

client_threads: List[threading.Thread] = []

def broadcast_message(message: bytes, source_socket: socket.socket) -> None:
    """
    sends a message to all clients except for the source_socket

    :param message: the message to be broadcast to clients
    :param source_socket: socket that we are sending the message
    :return: None
    """

    for client in clients:
        if client != source_socket:
            try:
                client.sendall(message)
            except Exception as e:
                print(f'Error sending message to a client: {e}')


def handle_client(client_socket: socket.socket, address: Tuple[str, int]) -> None:
    """
    Handles communication with a single client

    :param client_socket: the socket of the client
    :param address: contains the client IP and port
    :return: None
    """

    print(f'[+] New connection... Address: {address}')
    while True:
        try:
            message: bytes = client_socket.recv(1024)
            if not message:
                # disconnected
                print(f'[-] Client disconnected: {address}')
                break
            broadcast_message(message, client_socket)
        except ConnectionResetError:
            print(f'[-] Client {address} closed connection.')
            break
        except Exception as e:
            print(f'[!] Error handling client {address}: {e}')
            break

    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()


def start_server() -> None:
    """
    create server socket, listen for connections, and create new threads for each client

    :return: None
    """
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'Server listening on {HOST}:{PORT}')

    try:
        while not stop_server_event.is_set():
            server_socket.settimeout(1.0)
            try:
                client_socket, address = server_socket.accept()
            except socket.timeout:
                continue

            clients.append(client_socket)

            # create a new thread
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_threads.append(thread)
            thread.start()
    except KeyboardInterrupt:
        print(f'\n[!] Server shutting down.')
    finally:
        server_socket.close()
        for t in client_threads:
            t.join()
        print(f'[!] Server shutdown complete.')

if __name__ == "__main__":
    start_server()



