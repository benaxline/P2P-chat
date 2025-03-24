import socket
import threading

HOST: str = '127.0.0.1'
PORT: int = 5050

def receive_messages(client_socket:socket.socket) -> None:
    """
    listens continuously from the server and prints them out

    :param client_socket: the connected socket
    :return: None
    """
    while True:
        try:
            message: bytes = client_socket.recv(1024)
            if not message:
                print(f'[!] Connection closed by server.')
                client_socket.close()
                break
            print(message.decode('utf-8'))
        except Exception as e:
            print(f'[!] Error receiving message: {e}')
            client_socket.close()
            break


def start_client() -> None:
    """
    connect to server and start listening

    :return: None
    """
    client_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print(f'Connected to chat server at {HOST}:{PORT}')
    except Exception as e:
        print(f'[!] Unable to connect to server: {e}')
        return

    nickname = input("Enter your nickname: ")

    thread = threading.Thread(target=receive_messages, args=(client_socket,))
    thread.start()

    while True:
        message: str = input(f"{nickname}: ")
        if message.lower() == "/quit":
            print('[!] Quitting chat...')
            client_socket.close()
            break
        formatted_message = f'{nickname}: {message}'

        try:
            client_socket.sendall(formatted_message.encode('utf-8'))
        except Exception as e:
            print(f'[!] Error sending message: {e}')
            client_socket.close()
            break


if __name__ == "__main__":
    start_client()