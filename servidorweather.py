import socket
import threading

HEADER = 64
PORT = 5053
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    print("[STARTING] Servidor inicializándose...")

    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {ADDR}")

    def handle_client(conn, addr):
        print(f"[NUEVA CONEXIÓN] {addr} connected.")
        
        connected = True
        while connected:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if not msg_length:
                print(f"[CONEXIÓN CERRADA] {addr} se ha desconectado.")
                break
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == FIN:
                connected = False
            else:
                # Procesa los datos recibidos desde otros servidores
                print(f"Datos recibidos: {msg}")

        print(f"ADIOS. TE ESPERO EN OTRA OCASION [{addr}]")
        conn.close()

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()

