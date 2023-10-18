import sqlite3
import socket 
import threading
import random
import sys

HEADER = 64
PORT = 5052
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 2

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


def temperatura():
    
    conexion = sqlite3.connect('Clima.db') 

    cursor = conexion.cursor()
    
    consulta = "SELECT * FROM clima "
    

    cursor.execute(consulta)
    resultado = cursor.fetchone()

    if resultado:
        temperatura = resultado[0]
    else:
        temperatura = None

    conexion.close()
    return temperatura
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
            conn.send(temperatura(msg).encode(FORMAT))
    
    print(f"ADIOS. TE ESPERO EN OTRA OCASION [{addr}]")
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count()-1
    print(CONEX_ACTIVAS)
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        print (f"Establecida conexión en [{ADDR}]")
       
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
            
        

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()


