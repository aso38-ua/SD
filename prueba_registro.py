import socket
import sys

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
SERVER = "127.0.1.1"

def send(msg, client_socket):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client_socket.send(send_length)
    client_socket.send(message)

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    
    print(f"Conectado al servidor {SERVER}:{PORT}")

    while True:
        print("\nMenú:")
        print("1. Comprobar registro del dron")
        print("q. Salir")
        opcion = input("Elija una opción: ")

        if opcion == "1":
            id_dron = input("Ingrese el ID del dron que desea comprobar: ")

            # Enviar la opción 1 al servidor para comprobar el registro
            send("1", client)

            # Enviar el ID del dron al servidor
            send(id_dron, client)

            respuesta = client.recv(HEADER).decode(FORMAT)
            if respuesta == "registrado":
                print(f"El dron con ID {id_dron} está registrado.")
            else:
                print(f"El dron con ID {id_dron} no está registrado.")

        elif opcion == "q":
            print("Saliendo del programa. ¡Hasta luego!")
            client.close()
            sys.exit()
        else:
            print("Opción no válida. Por favor, elija una opción válida.")

if __name__ == "__main__":
    main()

