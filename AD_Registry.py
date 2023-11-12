import socket 
import threading
import random
import secrets
import string
import sqlite3
import netifaces
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

id_conectados=[]


cred = credentials.Certificate("sddd-8c96a-firebase-adminsdk-7sqg0-e7dc7ec49d.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sddd-8c96a-default-rtdb.europe-west1.firebasedatabase.app'
})

def get_first_non_local_interface():
    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
        
        for addr_info in addrs:
            ip = addr_info.get('addr')
            if ip and not (ip.startswith('127.') or ip.startswith('10.')):
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

def id_existe(id):
    # Comprueba si el ID ya existe en la base de datos
    ref = db.reference('/Dron')
    return ref.child(id).get() is not None

def esta_ocupado(id, conectados):
    print("UWU")
    for a in conectados:
        print("a :",a)
        print("id: ",id)
        if(a==id):
            print("TRUE")
            return True
    print("False")    
    return False

def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] {addr} connected.")

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
                if esta_ocupado(ID,id_conectados)==False:
                    id_conectados.append(ID)
                    print(id_conectados)
                    if opcion == "1":
                        # Opción 1: Registro de dron
                        if id_existe(ID):
                            respuesta = "El id ya existe"
                            conn.send(respuesta.encode(FORMAT))
                        else:
                            token = generar_token(longitud_token)
                            print("Token de acceso es: ", token)

                            # Insertar los datos en Firebase Realtime Database utilizando el ID del dron
                            ref = db.reference(f'/Dron/{ID}')
                            ref.set({'id': ID, 'token': token})

                            

                            # Envía el token al cliente
                            conn.send(token.encode(FORMAT))
                        break
                    elif opcion == "2":
                        try:
                            if id_existe(ID):
                                # Recibir el nuevo valor desde el cliente
                                nuevo_valor = conn.recv(2048).decode(FORMAT)
                                print("NUEVO: ", nuevo_valor)

                                # Actualizar el valor en Firebase
                                ref = db.reference('/Dron')
                                ref.update({'id': nuevo_valor})

                                respuesta = "Valor actualizado con éxito"
                                conn.send(respuesta.encode(FORMAT))
                            else:
                                respuesta = "No existe el usuario en la base de datos"
                                conn.send(respuesta.encode(FORMAT))
                            break
                        except Exception as e:
                            print(f"Error al actualizar el valor en Firebase: {e}")
                    elif opcion == "3":
                        try:
                            if id_existe(ID) == False:
                                respuesta = "El id no existe"
                                conn.send(respuesta.encode(FORMAT))
                            else:
                                # Eliminar el dron de Firebase
                                ref = db.reference('/Dron')
                                ref.child(ID).delete()

                                respuesta = "Dron borrado con éxito"
                                conn.send(respuesta.encode(FORMAT))
                            break
                        except Exception as e:
                            print(f"Error al borrar el dron en Firebase: {e}")
                    else:
                        # Opción desconocida
                        conn.send("Opción desconocida".encode(FORMAT))
                else:
                    conn.send("Nao nao amigao ya esta otro".encode(FORMAT))
                    print("EL DRON YA ESTA CONECTADO")
                    return

    except Exception as e:
        print(f"Error al procesar la conexión: {e}")
    finally:
        conn.close()
        if(esta_ocupado(ID,id_conectados)==True):
            id_conectados.remove(ID)

    print(f"ADIOS. TE ESPERO EN OTRA OCASIÓN [{addr}]")

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
