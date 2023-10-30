import sqlite3
import socket
import threading
import random
import time

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

# Función para actualizar valores aleatorios en la base de datos
def actualizar_valores_aleatorios():
    while True:
        nuevo_valor = random.randint(-10, 50)
        conexion = sqlite3.connect('clima.db')
        cursor = conexion.cursor()
        cursor.execute("UPDATE clima SET temperatura = ?", (nuevo_valor,))
        conexion.commit()
        conexion.close()
        print(f"Valor actualizado en la base de datos: {nuevo_valor}")
        time.sleep(60)  # Actualiza cada 60 segundos

# Inicia el hilo para la actualización de valores aleatorios
update_thread = threading.Thread(target=actualizar_valores_aleatorios)
update_thread.daemon = True
update_thread.start()


# Función para manejar al cliente y enviar la temperatura cuando cambia
def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] {addr} connected.")

    connected = True
    temp_anterior = None  # Almacena la temperatura anterior

    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if not msg_length:
            print(f"[CONEXIÓN CERRADA] {addr} se ha desconectado.")
            break

        temp_actual = temperatura()
        
        if temp_actual != temp_anterior:
            # Si la temperatura cambió, envía la nueva temperatura al cliente
            conn.send(str(temp_actual).encode(FORMAT))
            temp_anterior = temp_actual

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
