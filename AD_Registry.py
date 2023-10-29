import socket 
import threading
import random
import secrets
import string
import sqlite3

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
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
    while connected:
        try:
            mensaje_completo = conn.recv(2048).decode(FORMAT)

            # Divide el mensaje utilizando la coma como separador
            opcion, ID = mensaje_completo.split(',')

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
            elif opcion == "2":
                try:
                    if id_existe(ID,db_cursor):
                        # Recibir el nuevo valor desde el cliente
                        nuevo_valor = conn.recv(2048).decode(FORMAT)

                        # Ejecutar una consulta SQL para actualizar el valor en la tabla
                        db_cursor.execute("UPDATE Dron SET id = ? WHERE id = ?", (nuevo_valor, ID))
                        db_connection.commit()

                        respuesta = "Valor actualizado con éxito"
                        conn.send(respuesta.encode(FORMAT))

                    else:
                        respuesta="No existe el usuario en la base de datos"
                        conn.send(respuesta.encode(FORMAT))

                except Exception as e:
                    print(f"Error al actualizar el valor en la base de datos: {e}")

            elif opcion == "3":
                try:
                    if id_existe(ID, db_cursor) == False:
                        respuesta = "El id no existe"
                        conn.send(respuesta.encode(FORMAT))
                    else:

                        db_cursor.execute("DELETE FROM Dron WHERE id = ?", (ID))
                        db_connection.commit()

                        respuesta="Dron borrado con éxito"
                        conn.send(respuesta.encode(FORMAT))

                except Exception as e:
                    print(f"Error al borrar el dron en la base de datos: {e}")


            else:
                # Opción desconocida
                conn.send("Opción desconocida".encode(FORMAT))
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")
            break

    print(f"ADIOS. TE ESPERO EN OTRA OCASION [{addr}]")
    conn.close()
    db_cursor.close()
    db_connection.close()

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count() - 1
    print(CONEX_ACTIVAS)
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
