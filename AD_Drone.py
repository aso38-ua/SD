import sys
import socket
from map import Map
import sqlite3
import argparse
import time
import threading
import math
from confluent_kafka import Consumer, KafkaError, Producer
import re
import pygame

clock = pygame.time.Clock()

global drones_coordinates
drones_coordinates=[]

ID = 0 #Por defecto
TOKEN = ""
KAFKA_TOPIC = "drones-positions"
KAFKA_TOPIC_SEC = "drones-coordinate"
KAFKA_BROKER = "127.0.0.1:9092"

CONSUMER_CONFIG = {
    'bootstrap.servers': '127.0.0.1:9092',
    'group.id': 'drones-positions',
    'auto.offset.reset': 'earliest'
}

PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'python-producer'
}

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

id = None
x = None
y = None

drone_positions = {}

def consume_messages(dron_id):
    global drones_coordinates
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error al consumir mensaje: {msg.error()}")
                    break
            payload = msg.value().decode('utf-8')
            
            # Procesa el mensaje y separa los campos
            parts = payload.split(',')
            if len(parts) == 3:
                id, x, y = parts
                if id == dron_id:
                    # Convierte las coordenadas a enteros si es necesario
                    try:
                        x = int(x)
                        y = int(y)
                    except ValueError:
                        pass  # En caso de que no se pueda convertir a entero
                    # Aquí puedes trabajar con los valores de id, x e y
                    message = (x, y)
                    drone_positions[dron_id] = message
                    print(f"Mensaje:{dron_id} en {message}")
                    
                else:
                    print(f"Mensaje ignorado para ID {id}: {payload}")
            else:
                print("Mensaje no válido:", payload)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()



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

# Función para calcular la distancia euclidiana
def calcular_distancia(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Función para mover el dron hacia la posición final
def mover_dron_hacia_destino(drone_id, x_destino, y_destino):
    x_actual, y_actual = 0, 0  # Coordenadas iniciales del dron
    global drones_coordinates

    # Define la velocidad a la que se mueve el dron (puedes ajustarla)
    velocidad = 1

    producer = Producer(PRODUCER_CONFIG)

    while (x_actual, y_actual) != (x_destino, y_destino):
        # Calcula el desplazamiento en x e y para avanzar hacia el destino
        drones_coordinates=[((x_actual,y_actual),drone_id)]
        if x_actual < x_destino:
            x_actual += velocidad
        elif x_actual > x_destino:
            x_actual -= velocidad

        if y_actual < y_destino:
            y_actual += velocidad
        elif y_actual > y_destino:
            y_actual -= velocidad

        time.sleep(4)
        # Actualiza la posición del dron en el diccionario
        drone_positions[drone_id] = (x_actual, y_actual)
        
        drones_coordinates=[((x_actual,y_actual),drone_id)]
        print(f"ID: {drone_id}, X: {x_actual}, Y: {y_actual}")

        #drone_positions = [((1, 1), "Dron1")]

        # Llama a la función para actualizar los drones en el mapa
        #my_map.update_drones(drone_positions)

        # Envía la nueva posición a Kafka
        mensaje_kafka = f"{x_actual},{y_actual},{drone_id}"
        producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
        producer.flush()  # Asegura que el mensaje se envíe a Kafka

    print(f"Dron {drone_id} ha llegado a su destino en ({x_destino}, {y_destino})")


    # Función para registrar un dron
def registrar_dron(opcion):
    print("Registrando un dron...")

    # Combina la opción y el ID con una coma como separador
    mensaje = f"{opcion},{ID}"

    client.send(mensaje.encode(FORMAT))
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
            client.close()

        else:
            print("Ya existe el ID")
            conexion.close()
            client.close()

    else:
        print("No se pudo registrar el dron.")

# Función para editar el perfil del dron
def editar_perfil(opcion):
    print("Editando el perfil del dron...")
    # Aquí puedes agregar tu lógica para editar el perfil

    mensaje = f"{opcion},{ID}"

    client.send(mensaje.encode(FORMAT))

    newID=input("Cual es el nuevo id que quieres?: ")

    client.send(newID.encode(FORMAT))

    respuesta = client.recv(2048).decode(FORMAT)

    if respuesta:
        TOKEN = respuesta

        conexion = sqlite3.connect('drone.db')

        # Crear un cursor
        cursor = conexion.cursor()

        # Insertar el nuevo registro en la tabla "drone"
        if id_existe(newID,cursor) == False:
            cursor.execute("UPDATE drone SET id = ? WHERE id = ?;", (newID, ID))

            # Guardar los cambios en la base de datos
            conexion.commit()

            # Cerrar la conexión
            conexion.close()
            print(f"Respuesta del servidor: {TOKEN}")
            print("Dron actualizado con éxito!")
            ID=newID
            client.close()

        else:
            print("Ya existe el ID")
            conexion.close()
            client.close()

    else:
        print("No se pudo actualizar el dron.")
        client.close()


# Función para darse de baja
def darse_de_baja(opcion):
    print("Dándose de baja...")
    
    mensaje = f"{opcion},{ID}"

    client.send(mensaje.encode(FORMAT))

    respuesta = client.recv(HEADER).decode(FORMAT)
    print(f"Respuesta del servidor: {respuesta}")
    
    if respuesta:

        conexion = sqlite3.connect('drone.db')

        # Crear un cursor
        cursor = conexion.cursor()

        # Insertar el nuevo registro en la tabla "drone"
        if id_existe(ID,cursor) == False:
            cursor.execute("DELETE FROM drone WHERE id = ?;",  (ID))

            # Guardar los cambios en la base de datos
            conexion.commit()

            # Cerrar la conexión
            conexion.close()
            print(f"Respuesta del servidor: {respuesta}")
            print("Dron eliminado con éxito!")
            client.close()

        else:
            print("Ya existe el ID")
            conexion.close()
            client.close()

    else:
        print("No se pudo actualizar el dron.")
        client.close()

    print("Dado de baja con éxito!")

# Menú principal

def main_game_loop():
    global drones_coordinates

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            my_map.display_map()


        # Actualiza el mapa con las posiciones de los drones
        my_map.update_drones(drones_coordinates)

        # Actualiza la pantalla
        pygame.display.flip()

        clock.tick(60)

# Función para ejecutar el bucle del mapa en un hilo separado
def game_loop_thread():
    while True:
        main_game_loop()

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
                
                
                editar_perfil(sub_opcion)
                break
            elif sub_opcion == "3":
                
                print(f"Establecida conexión en {ADDREG}")
                darse_de_baja(sub_opcion)
            elif sub_opcion=="4":
                break
            else:
                print("Opción no válida. Por favor, elija una opción válida.")

    elif opcion == "2":
        print("Unirse al espectáculo...")
        conexion = sqlite3.connect('drone.db')

        # Crear un cursor
        cursor = conexion.cursor()
        db_cursor = conexion.cursor()
        if id_existe(ID,cursor):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDRENG)

            print(ID)
            db_cursor.execute("SELECT token FROM drone WHERE id=?", (ID,))
            resultado = db_cursor.fetchone()
            
            if resultado:
                # Obtiene el token de la consulta
                token = resultado[0]
                
                # Envía el token al servidor a través del socket
                client.send(token.encode(FORMAT))

            

            opcion = input("Desea mostrar el mapa?(s/n)")
            if(opcion=="s" or opcion =="S"):
                print(f"mostrar el mapa")
                pygame.init()
                screen_width = 800
                screen_height = 600
                screen = pygame.display.set_mode((screen_width, screen_height))
                my_map = Map(screen)
                
                # Inicia el hilo para el bucle del mapa
                game_thread = threading.Thread(target=game_loop_thread)
                game_thread.daemon = True
                game_thread.start()

            elif(opcion =="n" or opcion=="N"):
                print(f"no mostrar el mapa")

            else:
                print(f"opcion incorrecta")

            client.send(ID.encode(FORMAT))

            kafka_thread = threading.Thread(target=consume_messages, args=(ID,))
            kafka_thread.daemon = True
            kafka_thread.start()
            
            print(f"Establecida conexión en {ADDRENG}")
            
            while not drone_positions:
                time.sleep(1)  # Espera 1 segundo antes de verificar nuevamente
            

            print("Contenido de drone_positions:")
            for dron_id, position in drone_positions.items():
                x, y = position
                print(f"ID: {dron_id}, X: {x}, Y: {y}")

            position_info = drone_positions[ID]
            x, y = position_info  # Desempaqueta la tupla de posición
            print(f"Posición destino del dron {ID}: X: {x}, Y: {y}")


            time.sleep(3)

            mover_dron_hacia_destino(ID, x, y)

        else:
            print(f"No estás registrado {ID}")

    elif opcion == "3":
        print("Saliendo del programa. ¡Hasta luego!")
        print("SE ACABO LO QUE SE DABA")
        client.close()
        break

    else:
        print("Opción no válida. Por favor, elija una opción válida.")
    

client.close()
#elif (PORT==5051):
