import socket
import random
import time

HEADER = 64
PORT = 5050
SERVER = "127.0.1.1"  # Cambia esta dirección IP por la del servidor
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

# Opción 1: Registro de dron
opcion = 1
client.send(str(opcion).encode(FORMAT))

# Espera un momento para la siguiente entrada (puedes ajustar esto)
time.sleep(8)

# ID del dron (puedes cambiarlo)
id_dron = "DRON123"
client.send(id_dron.encode(FORMAT))

# Espera la respuesta del servidor
response = client.recv(HEADER).decode(FORMAT)
print(response)

# Cierra la conexión
client.send(FIN.encode(FORMAT))
client.close()
