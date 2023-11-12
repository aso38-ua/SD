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
import uuid
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("dron-89c7a-firebase-adminsdk-u7k4s-1bb27db4d6.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://dron-89c7a-default-rtdb.europe-west1.firebasedatabase.app'
})


def generate_unique_member_id():
    unique_id = str(uuid.uuid4())  # Genera un UUID único
    return f"dron_{unique_id}"

clock = pygame.time.Clock()

global drones_coordinates
drones_coordinates=[]
dron_id = generate_unique_member_id()
global ID
TOKEN = ""
KAFKA_TOPIC = "drones-positions"
KAFKA_TOPIC_SEC = "drones-coordinate"
KAFKA_TOPIC_ORDERS= "dron-back"
KAFKA_TOPIC_ALL="drones-all-positions"
KAFKA_TOPIC_FIGURES="figures"
KAFKA_BROKER = "192.168.1.129:9092"

CONSUMER_CONFIG = {
    'bootstrap.servers': '192.168.1.129:9092',
    'group.id': dron_id,
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

total_figuras = []
total_drones_por_figura = []
nombres_figuras = []

def leer_variables_desde_kafka():
    global total_figuras, total_drones_por_figura, nombres_figuras

    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC_FIGURES])

    should_exit = False

    try:
        while not should_exit:
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
            
            # Procesa el mensaje de texto
            try:
                # Divide la cadena en partes utilizando la coma como separador
                parts = payload.split(', ')

                # Extrae el total de figuras
                total_figuras = int(parts[0].split(': ')[1])

                # Extrae datos de cada figura
                nombres_figuras = []
                total_drones_por_figura = []
                for figura_data in parts[1:]:
                    nombre, drones = figura_data.rsplit(':', 1)
                    nombres_figuras.append(nombre)
                    total_drones_por_figura.append(int(drones))

                print("Datos de figuras actualizados:")
                print(f"Total de figuras: {total_figuras}")
                for nombre, drones in zip(nombres_figuras, total_drones_por_figura):
                    print(f"{nombre}: {drones} drones")

                should_exit = True
                
            except Exception as e:
                print(f"Error al procesar el mensaje: {e}")

    finally:
        consumer.close()
        print("OK")


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
            if len(parts) == 4:
                id, x, y, nombre_figura = parts
                if id == dron_id:
                    # Convierte las coordenadas a enteros si es necesario
                    try:
                        x = int(x)
                        y = int(y)
                    except ValueError:
                        pass  # En caso de que no se pueda convertir a entero
                    # Aquí puedes trabajar con los valores de id, x e y

                    pos_info = ((x, y), nombre_figura)
                    if pos_info not in drone_positions.get(id, []):
                        drone_positions.setdefault(id, []).append(pos_info)
                        print(f"Mensaje:{dron_id} en {pos_info}")
                    
                else:
                    print(f"Mensaje ignorado para ID {id}: {payload}")
            else:
                print("Mensaje no válido:", payload)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()



def id_existe(id):
    # Comprueba si el ID ya existe en la base de datos
    ref = db.reference('/Dron')
    return ref.child(id).get() is not None

def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor de drones con Kafka")
    parser.add_argument("--Engine", type=str, default="192.168.1.129", help="Puerto de escucha")
    parser.add_argument("--Id", type=str, help="Id del dron")
    parser.add_argument("--kafka", type=str,default="192.168.1.129", help="Dirección IP del servidor Kafka")
    parser.add_argument("--Registry", type=str, default="192.168.23.124", help="Direccion IP del servidor registro")

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

# Define un semáforo
movimiento_semaphore = threading.Semaphore()
orden_semaphore = threading.Semaphore()

def esperar_ordenes():
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC_ORDERS])

    while True:

        message = consumer.poll(1.0)  # Espera a recibir un mensaje por un segundo
        if message is None:
            continue
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                print('No se encontraron más mensajes')
            else:
                print(f'Error al recibir mensaje: {message.error()}')
        else:
            payload = message.value().decode('utf-8')
            if payload == 'Regresar a casa':
                movimiento_semaphore.acquire()
                mover_drones_a_casa()
                movimiento_semaphore.release()
            elif payload == 'Todo OK':
                continue

def mover_drones_a_casa():
    global drones_coordinates

    producer = Producer(PRODUCER_CONFIG)

    x_destino, y_destino = 0, 0  # Posición de destino (casa)
    velocidad = 1  # Velocidad de movimiento

    for i, (coordenadas, drone_id, estado) in enumerate(drones_coordinates):
        x_actual, y_actual = coordenadas  # Obtiene la posición actual del dron

        estado = "moviendo"
        while (x_actual, y_actual) != (x_destino, y_destino):
            # Calcula el desplazamiento en x e y hacia el destino
            distancia_x = x_destino - x_actual
            distancia_y = y_destino - y_actual

            if abs(distancia_x) > abs(distancia_y):
                if distancia_x > 0:
                    x_actual += velocidad
                else:
                    x_actual -= velocidad
            else:
                if distancia_y > 0:
                    y_actual += velocidad
                else:
                    y_actual -= velocidad

            # Actualiza la posición del dron en la lista
            drones_coordinates[i] = ((x_actual, y_actual), drone_id, estado)
            print(f"ID: {drone_id}, X: {x_actual}, Y: {y_actual}, Estado: {estado}")

            # Envía la nueva posición y estado a Kafka
            mensaje_kafka = f"{x_actual},{y_actual},{drone_id},{estado}"
            producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
            producer.flush()  # Asegura que el mensaje se envíe a Kafka

            time.sleep(4)  # Espera antes de la siguiente actualización de posición

        estado = "en reposo"  # El dron llegó a casa y se encuentra en reposo
        drones_coordinates = [((x_destino, y_destino), drone_id, estado)]
        print(f"Dron {drone_id} ha llegado a casa en (0, 0), Estado: {estado}")

        # Envía la última posición al estado de reposo a Kafka
        mensaje_kafka = f"0,0,{drone_id},{estado}"
        producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
        producer.flush()  # Asegura que el mensaje se envíe a Kafka

def mover_dron_a_casa(drone_id):
    global drones_coordinates
    x_destino, y_destino = 0, 0
    x_actual, y_actual = drones_coordinates[0][0]  # Obtiene la posición actual del dron
    velocidad = 1  # Velocidad de movimiento
    

    producer = Producer(PRODUCER_CONFIG)

    estado = "moviendo"

    while (x_actual, y_actual) != (x_destino, y_destino):
        # Calcula el desplazamiento en x e y hacia el destino
        distancia_x = x_destino - x_actual
        distancia_y = y_destino - y_actual

        if abs(distancia_x) > abs(distancia_y):
            if distancia_x > 0:
                x_actual += velocidad
            else:
                x_actual -= velocidad
        else:
            if distancia_y > 0:
                y_actual += velocidad
            else:
                y_actual -= velocidad

        # Actualiza la posición del dron en el diccionario
        drones_coordinates = [((x_actual, y_actual), drone_id, estado)]
        print(f"ID: {drone_id}, X: {x_actual}, Y: {y_actual}, Estado: {estado}")

        # Envía la nueva posición y estado a Kafka
        mensaje_kafka = f"{x_actual},{y_actual},{drone_id},{estado}"
        producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
        producer.flush()  # Asegura que el mensaje se envíe a Kafka

        time.sleep(4)  # Espera antes de la siguiente actualización de posición

    estado = "en reposo"  # El dron llegó a casa y se encuentra en reposo
    drones_coordinates = [((x_destino, y_destino), drone_id, estado)]
    print(f"Dron {drone_id} ha llegado a casa en (0, 0), Estado: {estado}")

    # Envía la última posición al estado de reposo a Kafka
    mensaje_kafka = f"0,0,{drone_id},{estado}"
    producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
    producer.flush()  # Asegura que el mensaje se envíe a Kafka

global drones_en_destino
drones_en_destino=0
# Función para mover el dron hacia la posición final
def mover_dron_hacia_destino(drone_id, x_destino, y_destino):
    
        try:

            x_actual, y_actual = 0, 0  # Coordenadas iniciales del dron
            global drones_coordinates,drones_en_destino

            # Define la velocidad a la que se mueve el dron (de una casilla en una)
            velocidad = 1

            producer = Producer(PRODUCER_CONFIG)

            estado = "moviendo"  # Estado inicial: moviendo

            # Adquiere el semáforo para bloquear otras llamadas a esta función
            with movimiento_semaphore:
                while (x_actual, y_actual) != (x_destino, y_destino):
                    # Calcula el desplazamiento en x e y para avanzar hacia el destino
                    distancia_x = x_destino - x_actual
                    distancia_y = y_destino - y_actual

                    if abs(distancia_x) > abs(distancia_y):
                        if distancia_x > 0:
                            x_actual += velocidad
                        else:
                            x_actual -= velocidad
                    else:
                        if distancia_y > 0:
                            y_actual += velocidad
                        else:
                            y_actual -= velocidad

                    time.sleep(4)
                    # Actualiza la posición del dron en el diccionario
                    drone_positions[drone_id] = (x_actual, y_actual)

                    drones_coordinates = [((x_actual, y_actual), drone_id, estado)]
                    print(f"ID: {drone_id}, X: {x_actual}, Y: {y_actual}, Estado: {estado}")

                    # Envía la nueva posición y estado a Kafka
                    mensaje_kafka = f"{x_actual},{y_actual},{drone_id},{estado}"
                    producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
                    producer.flush()  # Asegura que el mensaje se envíe a Kafka

                estado = "parado"  # Estado: parado después de llegar al destino
                drones_coordinates = [((x_destino, y_destino), drone_id, estado)]
                print(f"Dron {drone_id} ha llegado a su destino en ({x_destino}, {y_destino}), Estado: {estado}")
                

                mensaje_kafka = f"{x_destino},{y_destino},{drone_id},{estado}"
                producer.produce(KAFKA_TOPIC_SEC, key=drone_id, value=mensaje_kafka)
                producer.flush()  # Asegura que el mensaje se envíe a Kafka

                #drones_en_destino+=1
                #mensaje_drones_en_destino = f"Drones en destino: {drones_en_destino}"
                #producer.produce(KAFKA_TOPIC_SEC, key=None, value=mensaje_drones_en_destino)
                #producer.flush()
        finally:
            # Libera el semáforo después de completar el movimiento
            movimiento_semaphore.release()

###########DESCONEXIÓN DRONES###################

def send_disconnection_notification_to_engine(client,drone_id):
    try:
        # Envia una notificación de desconexión al engine
        message = f"DISCONNECTED:{drone_id}"
        client.send(message.encode(FORMAT))
    except Exception as e:
        print(f"Error al enviar notificación de desconexión: {e}")
        client.close()
    finally:
        # Cierra la conexión con el engine
        client.close()


def consume_drone_positions():
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC_ALL])

    # Diccionario para almacenar el último mensaje de cada dron
    last_messages = {}

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

            # Procesa el mensaje y actualiza el último mensaje de cada dron
            dron_id, x, y, estado = payload.split(',')
            last_message = f"ID del dron: {dron_id}, Posición: ({x}, {y}), Estado: {estado}"
            last_messages[dron_id] = last_message

            # Muestra solo el último mensaje de cada dron
            for dron_id in last_messages:
                print(last_messages[dron_id])
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

################################################

##################FUNCIONES REGISTRO##################

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
        if id_existe(ID) == False:
            ref = db.reference(f'/Dron/{ID}')
            ref.set({'id': ID, 'token': TOKEN})

            print(f"Respuesta del servidor: {TOKEN}")
            print("Dron registrado con éxito!")
            client.close()
            

        else:
            print("Ya existe el ID")
            conexion.close()
            client.close()
            

    else:
        print("No se pudo registrar el dron.")

    client.close()

# Función para editar el perfil del dron
def editar_perfil(opcion):
    print("Editando el perfil del dron...")
    global ID

    # Combina la opción y el ID con una coma como separador

    mensaje = f"{opcion},{ID}"
    client.send(mensaje.encode(FORMAT))

    newID = input("¿Cuál es el nuevo ID que quieres?: ")
    client.send(newID.encode(FORMAT))

    try:
        ref = db.reference(f'/Dron/{ID}')
        ref.update({"id": newID})
        print("Dron actualizado con éxito!")
        ID = newID
    except Exception as e:
        print(f"Error al actualizar el valor en la base de datos de Firebase: {e}")
    finally:
        client.close()

# Función para darse de baja
def darse_de_baja(opcion):
    print("Dándose de baja...")
    global ID
    
    mensaje = f"{opcion},{ID}"

    client.send(mensaje.encode(FORMAT))

    respuesta = client.recv(HEADER).decode(FORMAT)
    print(f"Respuesta del servidor: {respuesta}")
    
    if respuesta:

        conexion = sqlite3.connect('drone.db')

        # Crear un cursor
        cursor = conexion.cursor()

        # Insertar el nuevo registro en la tabla "drone"
        if id_existe(ID) == False:
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

############################################################################

####################Menú principal########################################

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

##############################################################################

#Aqui me tiene que pasar alberto algo para que el dron deje de funcionar por la temperatura

while True:
    try:
        drone_conectado=False
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
                    
                    registrar_dron(sub_opcion)
                    break
                elif sub_opcion == "2":
                    
                    
                    editar_perfil(sub_opcion)
                    break
                elif sub_opcion == "3":
                    
                    print(f"Establecida conexión en {ADDREG}")
                    darse_de_baja(sub_opcion)
                elif sub_opcion=="4":
                    client.close()
                    break
                else:
                    print("Opción no válida. Por favor, elija una opción válida.")

        elif opcion == "2":
            if not drone_conectado:  # Verifica si el dron ya está conectado
                print("Unirse al espectáculo...")
                conexion = sqlite3.connect('drone.db')

                # Crear un cursor
                cursor = conexion.cursor()
                db_cursor = conexion.cursor()
                if id_existe(ID):
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
                    if (opcion == "s" or opcion == "S"):
                        print(f"mostrar el mapa")
                        pygame.init()
                        screen_width = 800
                        screen_height = 800
                        screen = pygame.display.set_mode((screen_width, screen_height))
                        my_map = Map(screen)

                        # Inicia el hilo para el bucle del mapa
                        game_thread = threading.Thread(target=game_loop_thread)
                        game_thread.daemon = True
                        game_thread.start()

                    elif (opcion == "n" or opcion == "N"):
                        print(f"no mostrar el mapa")

                    else:
                        print(f"Opcion incorrecta")

                    client.send(ID.encode(FORMAT))

                    kafka_thread = threading.Thread(target=consume_messages, args=(ID,))
                    kafka_thread.daemon = True
                    kafka_thread.start()

                    kafka_thread = threading.Thread(target=esperar_ordenes)
                    kafka_thread.daemon = True
                    kafka_thread.start()

                    consume_thread = threading.Thread(target=consume_drone_positions)
                    consume_thread.daemon = True
                    consume_thread.start()

                    print(f"Establecida conexión en {ADDRENG}")

                    while not drone_positions:
                        time.sleep(1)  # Espera 1 segundo antes de verificar nuevamente

                    total_figuras = []

                    print("Contenido de drone_positions:")
                    for dron_id, positions in drone_positions.items():
                        print(f"ID: {dron_id}")
                        for position, nombre_figura in positions:
                            x, y = position
                            print(f"Figura: {nombre_figura}, X: {x}, Y: {y}")

                    position_info = drone_positions.get(ID, [])
                    for position, nombre_figura in position_info:
                        x, y = position
                        print(f"Posición destino del dron {ID} para la figura {nombre_figura}: X: {x}, Y: {y}")

                    leer_variables_desde_kafka()

                    time.sleep(3)
                    mover_dron_hacia_destino(ID, x, y)

                    drone_conectado = True  # Marcar el dron como conectado
                else:
                    print(f"No estás registrado {ID}")
            else:
                print("El dron ya está conectado.")

        elif opcion == "3":
            print("Saliendo del programa. ¡Hasta luego!")
            print("SE ACABO LO QUE SE DABA")
            client.close()
            break

        else:
            print("Opción no válida. Por favor, elija una opción válida.")
    


    except KeyboardInterrupt:
            # Manejo de Ctrl+C (Interrupción del usuario)
            print("Se ha presionado Ctrl+C. Saliendo...")
            send_disconnection_notification_to_engine(client,ID)  # Envía una notificación de desconexión al motor
            client.close()
            sys.exit(0)  # Sale del programa
    #elif (PORT==5051):
