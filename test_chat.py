import unittest
import threading
import time
import socket
from idlelib.squeezer import count_lines_with_wrapping

from chat_server import start_server, HOST, PORT, stop_server_event

class TestChatIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        starts the server once
        """
        stop_server_event.clear()
        cls.server_thread = threading.Thread(target=start_server, daemon=True)
        cls.server_thread.start()
        time.sleep(1)

    @classmethod
    def closeClass(cls):
        """
        Close connected client sockets and stop server
        """
        stop_server_event.set()
        cls.server_thread.join(timeout=3)


    def test_single_client_connects_and_sends_essage(self):
        """
        make sure that a single client can connect and send a message
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        test_message = 'Hello!'
        client_socket.sendall(test_message.encode('utf-8'))

        time.sleep(0.5)
        client_socket.close()


    def test_broadcast_between_two_clients(self):
        """
        connect 2 clients. make sure it is received
        """
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect((HOST, PORT))
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect((HOST, PORT))

        test_message = "Broadcast testing!"
        client1.sendall(test_message.encode('utf-8'))

        data = client2.recv(1024)
        received_message = data.decode('utf-8')

        self.assertIn(test_message, received_message, 'Client2 did not receive the broadcast message from Client1')

        client1.close()
        client2.close()

if __name__ == '__main__':
    unittest.main()