import sys
import socket
from map import Map
import sqlite3
import argparse

ID = 0 #Por defecto
TOKEN = ""

HEADER = 64
PORTENGINE = 5051
PORTREG = 5050
PORTBOOT=9092
IPBOOT="127.0.0.1"

FORMAT = 'utf-8'

def send(msg, client_socket):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client_socket.send(send_length)
    client_socket.send(message)

# if len(sys.argv) != 7:
#     print("Oops!. Parece que algo falló. Necesito estos argumentos: <ServerIP> <Puerto>")
#     sys.exit()

def id_existe(id, db_cursor):
    # Comprueba si el ID ya existe en la base de datos
    db_cursor.execute("SELECT id FROM drone WHERE id=?", (id,))
    existe = db_cursor.fetchone()
    return existe is not None

def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor de drones con Kafka")
    parser.add_argument("--Engine", type=str, default="127.0.1.1", help="Puerto de escucha")
    parser.add_argument("--Id", type=str, help="Id del dron")
    parser.add_argument("--kafka", type=str,default="127.0.0.1", help="Dirección IP del servidor Kafka")
    parser.add_argument("--Registry", type=str, default="127.0.1.1", help="Puerto de escucha")

    return parser.parse_args()

args = parse_arguments()

SERVERENG = args.Engine
ADDRENG = (SERVERENG, PORTENGINE)
SERVERBOOT=args.kafka
ADDRBOOT=(SERVERBOOT,PORTBOOT)
SERVERREG=args.Registry
ADDREG=(SERVERREG,PORTREG)
ID= args.Id
#coor=sys.argv[5]

#=sys.argv[]
def gestionarMovimientos():
    print("jejeje")


    # Función para registrar un dron
def registrar_dron(opcion):
    print("Registrando un dron...")
    send(opcion,client)
    print(ID)
   
    send(str(ID), client)
    respuesta = client.recv(2048).decode(FORMAT)

    if respuesta:
        TOKEN = respuesta

        conexion = sqlite3.connect('drone.db')

        # Crear un cursor
        cursor = conexion.cursor()

        nuevo_token = TOKEN  # Reemplaza "tu_token" con el token que desees insertar

        # Insertar el nuevo registro en la tabla "drone"
        if id_existe(ID,cursor) == False:
            cursor.execute("INSERT INTO drone (id, token) VALUES (?, ?)", (ID, nuevo_token))

            # Guardar los cambios en la base de datos
            conexion.commit()

            # Cerrar la conexión
            conexion.close()
            print(f"Respuesta del servidor: {TOKEN}")
            print("Dron registrado con éxito!")

        else:
            print("Ya existe el ID")
            conexion.close()

    else:
        print("No se pudo registrar el dron.")

# Función para editar el perfil del dron
def editar_perfil(opcion,newID):
    print("Editando el perfil del dron...")
    # Aquí puedes agregar tu lógica para editar el perfil

    send(str(opcion),client)
    
    send(str(ID), client)
    send(str(newID), client)
    respuesta = client.recv(HEADER).decode(FORMAT)

    print(f"Respuesta del servidor: {respuesta}")
    print("Perfil editado con éxito!")

# Función para darse de baja
def darse_de_baja(opcion):
    print("Dándose de baja...")
    # Aquí puedes agregar tu lógica para darte de baja
    print("Registrando un dron...")
    send(str(opcion),client)
    send(str(ID), client)
    respuesta = client.recv(HEADER).decode(FORMAT)
    print(f"Respuesta del servidor: {respuesta}")
    print("Dado de baja con éxito!")

# Menú principal

#Aqui me tiene que pasar alberto algo para que el dron deje de funcionar por la temperatura
while True:

    print("Menú Principal:")
    print("1. Registrar dron")
    print("2. Unirse al espectáculo")
    print("3. Salir")
    opcion = input("Elija una opción: ")

    if opcion == "1":
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDREG)
        print(f"Establecida conexión en {ADDREG}")
        # Submenú para opciones relacionadas con el dron
        while True:
            print("\nSubmenú del Dron:")
            print("1. Darse de alta")
            print("2. Editar perfil")
            print("3. Darse de baja")
            print("4. Volver al menú principal")
            sub_opcion = input("Elija una opción: ")
            if sub_opcion == "1":
                print(f"UWU")
                
                registrar_dron(sub_opcion)
                break
            elif sub_opcion == "2":
                
                resp=input("Cual es el nuevo id que quieres?")
                editar_perfil(sub_opcion,resp)
            elif sub_opcion == "3":
                
                print(f"Establecida conexión en {ADDREG}")
                darse_de_baja(sub_opcion)
            elif sub_opcion=="4":
                break
            else:
                print("Opción no válida. Por favor, elija una opción válida.")

    elif opcion == "2":
        print("Unirse al espectáculo...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDRENG)

        opcion = input("Desea mostrar el mapa?(s/n)")
        if(opcion=="s" or opcion =="S"):
            print(f"mostrar el mapa")

        elif(opcion =="n" or opcion=="N"):
            print(f"no mostrar el mapa")

        else:
            print(f"opcion incorrecta")

        send(TOKEN,client)
        coor = client.recv(HEADER).decode(FORMAT)#recibo coor final

        #Si un dron falla o su aplicación se bloquea por cualquier causa es eliminado visualmente de la acción
                 

        #Autentificar el token
            #Envio token
            #ESpero respuesta
        #Quedo en espera de que el engine me mande instrucciones

        #hay que hacer un hilo
        
        



        print(f"Establecida conexión en {ADDRENG}")

    elif opcion == "3":
        print("Saliendo del programa. ¡Hasta luego!")
        print("SE ACABO LO QUE SE DABA")
        client.close()
        break

    else:
        print("Opción no válida. Por favor, elija una opción válida.")
    

client.close()
#elif (PORT==5051):
