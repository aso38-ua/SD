import sqlite3
import socket
import threading

HEADER = 64
PORT = 5052
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 2

def temperatura():
    conexion = sqlite3.connect('clima.db')  # Conecta a la base de datos SQLite
    cursor = conexion.cursor()

    consulta = "SELECT temperatura FROM clima"
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


        temp = temperatura()

        conn.send(str(temp).encode(FORMAT))

    print(f"ADIOS. TE ESPERO EN OTRA OCASIÓN [{addr}]")
    conn.close()

def start():
    temper=temperatura()
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    
    print(f"La temperatura actual es: {temper}")
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES):
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES - CONEX_ACTIVAS)
        else:
            print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
            conn.send("OOppsss... DEMASIADAS CONEXEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
            conn.close()
            CONEX_ACTUALES = threading.active_count() - 1

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()
