import socket
import threading
import tkinter as tk

class ChatClient(tk.Frame):
    def __init__(self, master, host, port, nickname):
        super().__init__(master)
        self.master = master
        self.host = host
        self.port = port
        self.create_widgets()
        self.socket = None
        self.nickname = nickname

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
            try:
                data = self.socket.recv(1024)
                if not data:
                    self.display_message("[!] Connection closed by server.")
                    break
                self.display_message(data.decode('utf-8'))
            except Exception as e:
                self.display_message(f"[!] Error receiving message: {e}")
                break

    def display_message(self, message):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, message + '\n')
        self.text_area.config(state='disabled')
        self.text_area.see(tk.END)

    def send_message(self, event):
        message = self.entry.get()
        if not message:
            return
        formatted_message = f'{self.nickname}: {message}'
        self.display_message(formatted_message)
        self.entry.delete(0, tk.END)
        try:
            self.socket.sendall(formatted_message.encode('utf-8'))
        except Exception as e:
            self.display_message(f'[!] Error sending message: {e}')

def main():
    nickname = input("Enter your nickname: ")
    root = tk.Tk()
    root.title("Chat Client")
    client = ChatClient(root, "127.0.0.1", 5050, nickname)
    client.connect_to_server()
    root.mainloop()

if __name__ == "__main__":
    main()