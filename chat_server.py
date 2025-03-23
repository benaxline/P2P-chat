import socket
import select
import sys
import threading
from _thread import *
from math import expm1
from typing import List, Tuple

# local host
HOST: str = '127.0.0.1'
PORT: int = 5050

clients: List[socket.socket] = []

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
    Hnadles communication with a single client

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
                clients.remove(client_socket)
                client_socket.close()
                break
            broadcast_message(message, client_socket)
        except ConnectionResetError:
            print(f'[-] Client {address} closed connection.')
            clients.remove(client_socket)
            client_socket.close()
            break
        except Exception as e:
            print(f'[!] Error handling client {address}: {e}')
            clients.remove(client_socket)
            client_socket.close()
            break


def start_server() -> None:
    """
    create server socket, listen for connections, and create new threads for each client

    :return: None
    """
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'Server listening on {HOST}:{PORT}')

    try:
        while True:
            client_socket, address = server_socket.accept()
            clients.append(client_socket)

            # create a new thread
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.start()
    except KeyboardInterrupt:
        print(f'\n[!] Server shutting down.')
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()



