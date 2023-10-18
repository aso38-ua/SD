
import mysql.connector
import socket 
import threading
import random

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 2

def temperatura (ciudad):

    conexion1 = mysql.connector.connect(host="localhost", user="root", passwd="", database="bd1") #cambiar por lo que sea
    cursor1 = conexion1.cursor()
    
    consulta = "SELECT temperatura FROM clima WHERE ciudad = %s"
    ciudad_parametro = (ciudad,)
    
    cursor1.execute(consulta, ciudad_parametro)
    resultado = cursor1.fetchone()

    if resultado:
        temperatura = resultado[0]
    else:
        temperatura = None

    conexion1.close()
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
    #CONEX_ACTIVAS = threading.active_count()-1
    #print(CONEX_ACTIVAS)
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-CONEX_ACTIVAS)
        else:
            print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
            conn.send("OOppsss... DEMASIADAS CONEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
            conn.close()
            CONEX_ACTUALES = threading.active_count()-1

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()


