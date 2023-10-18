import sys
import socket

ID = 0 #Por defecto
TOKEN = ""

HEADER = 64
PORTENGINE = 5050
PORTREG = 5051

FORMAT = 'utf-8'

def send(msg, client_socket):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client_socket.send(send_length)
    client_socket.send(message)

if len(sys.argv) != 5:
    print("Oops!. Parece que algo falló. Necesito estos argumentos: <ServerIP> <Puerto>")
    sys.exit()

SERVERENG = sys.argv[1]
ADDRENG = (SERVERENG, PORTENGINE)
SERVERBOOT=sys.argv[2]
ADDRBOOT=(SERVERBOOT,PORTBOOT)
ID= sys.argv[3]
#=sys.argv[]

if PORT == 5050:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    print(f"Establecida conexión en {ADDR}")

    while True:
        send(str(ID), client)
        respuesta = client.recv(HEADER).decode(FORMAT)
        TOKEN = respuesta

        print(f"Respuesta del servidor: {TOKEN}")

    print("SE ACABO LO QUE SE DABA")
    client.close()
#elif (PORT==5051):

