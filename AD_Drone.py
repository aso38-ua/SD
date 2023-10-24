import sys
import socket

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

SERVERENG = sys.argv[1]
ADDRENG = (SERVERENG, PORTENGINE)
SERVERBOOT=sys.argv[2]
ADDRBOOT=(SERVERBOOT,PORTBOOT)
SERVERREG=sys.argv[3]
ADDREG=(SERVERREG,PORTREG)
ID= sys.argv[4]
#coor=sys.argv[5]

#=sys.argv[]
def gestionarMovimientos():
    rint("jejeje")


    # Función para registrar un dron
def registrar_dron(opcion):
    print("Registrando un dron...")
    send(str(opcion),client)
    respuestita=client.recv(HEADER).decode(FORMAT)#Era para saber si se habia enviado bn la opcion
    print(f"Esta es la respuesta: {respuestita}")
    # Aquí puedes agregar tu lógica para registrar un dron
    send(str(ID), client)
    respuesta = client.recv(HEADER).decode(FORMAT)
    TOKEN = respuesta
    print(f"Respuesta del servidor: {TOKEN}")
    print("Dron registrado con éxito!")

# Función para editar el perfil del dron
def editar_perfil():
    print("Editando el perfil del dron...")
    # Aquí puedes agregar tu lógica para editar el perfil
    print("Registrando un dron...")
    send(str(opcion),client)
    respuestita=client.recv(HEADER).decode(FORMAT)
    print(f"Esta es la respuesta: {respuestita}")
    # Aquí puedes agregar tu lógica para registrar un dron
    send(str(ID), client)
    respuesta = client.recv(HEADER).decode(FORMAT)
    TOKEN = respuesta
    print(f"Respuesta del servidor: {TOKEN}")
    print("Dron registrado con éxito!")

    print("Perfil editado con éxito!")

# Función para darse de baja
def darse_de_baja():
    print("Dándose de baja...")
    # Aquí puedes agregar tu lógica para darte de baja
    print("Registrando un dron...")
    send(str(opcion),client)
    respuestita=client.recv(HEADER).decode(FORMAT)
    print(f"Esta es la respuesta: {respuestita}")
    # Aquí puedes agregar tu lógica para registrar un dron
    send(str(ID), client)
    respuesta = client.recv(HEADER).decode(FORMAT)
    TOKEN = respuesta
    print(f"Respuesta del servidor: {TOKEN}")
    print("Dron registrado con éxito!")

    print("Dado de baja con éxito!")

# Menú principal
while True:
    print("Menú Principal:")
    print("1. Registrar dron")
    print("2. Unirse al espectáculo")
    print("3. Salir")
    opcion = input("Elija una opción: ")

    if opcion == "1":
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
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDREG)
                print(f"Establecida conexión en {ADDREG}")
                registrar_dron(sub_opcion)
                break
            elif sub_opcion == "2":
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDREG)
                print(f"Establecida conexión en {ADDREG}")
                editar_perfil(sub_opcion)
            elif sub_opcion == "3":
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDREG)
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
