import socket
import threading
import tkinter as tk

class ChatClient(tk.Frame):
    def __init__(self, master, host, port):
        super().__init__(master)
        self.master = master
        self.host = host
        self.port = port
        self.create_widgets()
        self.socket = None

    def create_widgets(self):
        self.text_area = tk.Text(self, wrap='word', state='disabled')
        self.text_area.pack(expand=True, fill='both')

        self.entry = tk.Entry(self)
        self.entry.bind("<Return>", self.send_message)
        self.entry.pack(fill='x')

        self.pack(expand=True, fill='both')

    def connect_to_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            self.display_message(data.decode('utf-8'))

    def display_message(self, message):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message + '\n')
        self.text_area.config(state='disabled')
        self.text_area.see(tk.END)

    def send_message(self, event):
        message = self.entry.get()
        self.entry.delete(0, tk.END)
        self.socket.sendall(message.encode('utf-8'))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Chat Client")
    client = ChatClient(root, "127.0.0.1", 5050)
    client.connect_to_server()
    root.mainloop()