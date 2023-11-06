import socket 
import threading
import random
import secrets
import string
import sqlite3
import netifaces


def get_first_non_local_interface():
    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        
        for addr_info in addrs:
            ip = addr_info.get('addr')
            if ip and not ip.startswith('127.'):
                return ip
    
    return None

eth_interface = get_first_non_local_interface()

if eth_interface:
    SERVER = eth_interface
    print(f"La dirección IP de la interfaz de red no local es: {SERVER}")
else:
    print("No se pudo encontrar una interfaz de red no local.")
    SERVER = socket.gethostbyname(socket.gethostname())
    print(f"Usando la dirección IP del host: {SERVER}")


HEADER = 64
PORT = 5050
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 10
longitud_token = 32

# Crear un token de acceso aleatorio
def generar_token(longitud):
    caracteres = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return token

def id_existe(id, db_cursor):
    # Comprueba si el ID ya existe en la base de datos
    db_cursor.execute("SELECT id FROM Dron WHERE id=?", (id,))
    existe = db_cursor.fetchone()
    return existe is not None

def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] {addr} connected.")
    
    # Crear una conexión de base de datos SQLite para este hilo
    db_connection = sqlite3.connect('Registro.db')
    db_cursor = db_connection.cursor()
    
    connected = True
    try:
        while connected:
            mensaje_completo = conn.recv(2048).decode(FORMAT)

            mensaje_dividido = mensaje_completo.split(',')
        
            if len(mensaje_dividido) >= 2:
                opcion, ID = mensaje_dividido[0], mensaje_dividido[1]

                # Ahora tienes la opción y el ID por separado
                print("Opción:", opcion)
                print("ID:", ID)
                
                if opcion == "1":
                    # Opción 1: Registro de dron
                    if id_existe(ID, db_cursor):
                        respuesta = "El id ya existe"
                        conn.send(respuesta.encode(FORMAT))
                    else:
                        token = generar_token(longitud_token)
                        print("Token de acceso es: ", token)
                        
                        # Insertar los datos en la base de datos
                        db_cursor.execute("INSERT INTO Dron (token, id) VALUES (?, ?)", (token, ID))
                        db_connection.commit()
                        
                        conn.send(token.encode(FORMAT))
                    break
                elif opcion == "2":
                    try:
                        if id_existe(ID, db_cursor):
                            # Recibir el nuevo valor desde el cliente
                            nuevo_valor = conn.recv(2048).decode(FORMAT)

                            # Ejecutar una consulta SQL para actualizar el valor en la tabla
                            db_cursor.execute("UPDATE Dron SET id = ? WHERE id = ?", (nuevo_valor, ID))
                            db_connection.commit()

                            respuesta = "Valor actualizado con éxito"
                            conn.send(respuesta.encode(FORMAT))

                        else:
                            respuesta = "No existe el usuario en la base de datos"
                            conn.send(respuesta.encode(FORMAT))
                        break
                    except Exception as e:
                        print(f"Error al actualizar el valor en la base de datos: {e}")

                elif opcion == "3":
                    try:
                        if id_existe(ID, db_cursor) == False:
                            respuesta = "El id no existe"
                            conn.send(respuesta.encode(FORMAT))
                        else:
                            db_cursor.execute("DELETE FROM Dron WHERE id = ?", (ID,))
                            db_connection.commit()

                            respuesta = "Dron borrado con éxito"
                            conn.send(respuesta.encode(FORMAT))
                        break
                    except Exception as e:
                        print(f"Error al borrar el dron en la base de datos: {e}")

                else:
                    # Opción desconocida
                    conn.send("Opción desconocida".encode(FORMAT))
    except Exception as e:
        print(f"Error al procesar la conexión: {e}")
    finally:
        conn.close()


    print(f"ADIOS. TE ESPERO EN OTRA OCASION [{addr}]")
    db_cursor.close()
    db_connection.close()

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count() - 1
    print(CONEX_ACTIVAS)
    try:
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
    except KeyboardInterrupt:
        print("ADIOS. TE ESPERO EN OTRA OCASION")
        server.close()

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()
