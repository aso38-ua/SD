import json
import socket
import threading
import random
import secrets
import string
import sqlite3
import argparse
import pygame
from confluent_kafka import Producer, Consumer, KafkaError
from map import Map
import time
from typing import List, Tuple

pygame.init()
screen_width = 800
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
my_map = Map(screen)

global global_drone_positions
global_drone_positions=[]
# Define un cerrojo para sincronizar el acceso a global_drone_positions
drone_positions_lock = threading.Lock()

KAFKA_BROKER = "127.0.0.1:9092"
KAFKA_TOPIC = "drones-positions"
KAFKA_TOPIC_SEC = "drones-coordinate"
PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'python-producer'
}

CONSUMER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'python-consumer',
    'auto.offset.reset': 'earliest'
}
producer = Producer(PRODUCER_CONFIG)
consumer = Consumer(CONSUMER_CONFIG)

# Ruta al archivo donde se almacenarán las figuras
archivo_figura = "figura.txt"

# Bandera para controlar si el motor debe esperar a las figuras
esperar_figura = False

def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor de drones con Kafka")
    parser.add_argument("--port", type=int, default=5051, help="Puerto de escucha")
    parser.add_argument("--max-drones", type=int, default=10, help="Número máximo de drones a admitir")

    return parser.parse_args()

args = parse_arguments()
PORT = args.port
MAX_CONEXIONES = args.max_drones

HEADER = 64
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"

# Configura la dirección y el puerto del servidor AD_Weather
AD_WEATHER_SERVER = "127.0.1.1"
AD_WEATHER_PORT = 5052




def send_message_to_kafka_from_figuras(topic, final_positions):
    producer = Producer(PRODUCER_CONFIG)
    for position, id_dron in final_positions:
        x_destino, y_destino = position
        message = f"{id_dron},{x_destino},{y_destino}"
        producer.produce(topic, key=None, value=message)
        print(f"Mensaje producido a Kafka: {message}")
    producer.flush()

def cargar_figura(figura):
    with open(archivo_figura, "w") as file:
        file.write(figura)

def ejecutar_figura(id_dron, x_destino, y_destino):
    # Aquí puedes implementar la lógica para mover el dron a las coordenadas de destino
    print(f"Ejecutando figura para dron {id_dron}: Moviendo a ({x_destino}, {y_destino})")
    # Simulación de movimiento
    time.sleep(2)

def procesar_figuras():
    try:
        with open(archivo_figura, "r") as file:
            figuras = file.read()
            if figuras:
                print(f"Se encontraron figuras para ejecutar:\n{figuras}")
                lineas = figuras.strip().split('\n')
                # Inicializa la lista de posiciones de los drones
                final_positions = []
                for linea in lineas[1:-1]:  # Ignorar la primera y última línea
                    campos = linea.split()
                    if len(campos) == 3:  # Verificar que hay cuatro campos
                        id_dron = campos[0]
                        x_destino = int(campos[1])
                        y_destino = int(campos[2])
                        # Agrega la posición del dron en el formato correcto
                        final_positions.append(((x_destino, y_destino), id_dron))
                        print(f"Figura procesada para dron {id_dron}: Moviendo a ({x_destino}, {y_destino})")
                send_message_to_kafka_from_figuras(KAFKA_TOPIC, final_positions)
                print("Figuras procesadas")
                return final_positions
            else:
                print("El archivo de figuras está vacío.")
                return []  # Retorna una lista vacía si no hay figuras en el archivo
    except FileNotFoundError:
        print("El archivo de figuras no se ha encontrado.")
        return []  # Retorna una lista vacía si el archivo no se encuentra
    except Exception as e:
        print(f"Error al procesar las figuras: {e}")
        return []  # Retorna una lista vacía en caso de error
    


# Cargar y procesar las figuras desde el archivo "figuras.txt"
final_positions = procesar_figuras()


drones_que_han_llegado = set()
total_drones_en_la_figura = 5

def verificar_figura_completada():
    return len(drones_que_han_llegado) == total_drones_en_la_figura

# Función para esperar hasta que todos los drones de la figura hayan llegado
def esperar_figura_completada():
    while not verificar_figura_completada():
        time.sleep(1)  # Espera 1 segundo antes de verificar nuevamente

# Función para enviar la orden a los drones para regresar a la posición (0, 0)
def enviar_orden_regreso_a_casa():
    # Aquí debes implementar la lógica para enviar la orden a los drones
    print("Enviando orden para que los drones regresen a la posición (0, 0)")


# Esta función se ejecutará en un hilo separado para obtener la temperatura desde AD_Weather
def get_temperature_from_ad_weather():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ad_weather_socket:
            try:
                ad_weather_socket.connect((AD_WEATHER_SERVER, AD_WEATHER_PORT))
                print("Conectado al servidor AD_Weather.")
                
                while True:
                    # Envía una solicitud de temperatura
                    ad_weather_socket.send(b"GET_TEMPERATURA")
                    
                    data = ad_weather_socket.recv(1024)
                    if not data:
                        pass

                    temperature = data.decode('utf-8')
                    print(f"Temperatura actual: {temperature}°C")
                    
                    # Espera un período antes de obtener una actualización
                    time.sleep(60)  # Espera 60 segundos antes de obtener la próxima actualización
                    
            except ConnectionRefusedError:
                print("No se pudo conectar al servidor AD_Weather. Intentando de nuevo en 30 segundos.")
                time.sleep(30)
            except Exception as e:
                print(f"Error al obtener la temperatura: {e}")

# Agrega un hilo para conectarse a AD_Weather y obtener la temperatura
ad_weather_thread = threading.Thread(target=get_temperature_from_ad_weather)
ad_weather_thread.daemon = True
ad_weather_thread.start()



def autenticar_dron(conn, db_cursor, token):
    global global_drone_positions

    # Consulta la base de datos para verificar si el token de autenticación es válido
    db_cursor.execute("SELECT Token FROM Dron WHERE Token=?", (token,))
    resultado = db_cursor.fetchone()

    if resultado:
        # Autenticación correcta
        print("Autenticación correcta")
        conn.send("Autenticación correcta".encode(FORMAT))
        return True
    else:
        print("Incorrecto, expulsando dron")
        conn.send("Autenticación incorrecta. Dron expulsado.".encode(FORMAT))
        return False

def handle_disconnection(drone_id, x_actual, y_actual):
    global global_drone_positions, my_map
    

    my_map.remove_drone(drone_id)
    
    with drone_positions_lock:
        # Elimina al dron de la lista utilizando pop()
        for i, drone_position in enumerate(global_drone_positions):
            if drone_position[1] == drone_id:
                global_drone_positions.pop(i)
                break

    print(f"Dron {drone_id} desconectado y movido a (0, 0).")

    # Aquí, puedes enviar una notificación o realizar otras acciones de limpieza.

    
def handle_client(conn, addr):
    global esperar_figura
    global global_drone_positions, my_map

    print(f"[NUEVA CONEXIÓN] {addr} connected.")
    # Crear una conexión de base de datos SQLite para este hilo
    db_connection = sqlite3.connect('Registro.db')
    db_cursor = db_connection.cursor()
    
    
    
    # Autenticar al dron
    token=conn.recv(2048).decode(FORMAT)
    conectado=autenticar_dron(conn, db_cursor,token)
    
    
    while True:
        try:
            # Inicia el hilo para consumir mensajes de Kafka
            kafka_thread = threading.Thread(target=consume_messages)
            kafka_thread.daemon = True
            kafka_thread.start()
            
            if conectado == False:
                print(f"[CONEXIÓN CERRADA] Fallo al autenticar, {addr} se ha desconectado.")
                enviar_estado_desconectado_a_kafka(ID)
                break
            
            ID=conn.recv(2048).decode(FORMAT)
            if not ID:
                break
            with drone_positions_lock:
                global_drone_positions.append(((0, 0), ID, "moviendo"))

            if esperar_figura:
                print("Esperando una figura para ejecutar...")
                # Aquí puedes implementar la lógica para leer una figura desde el archivo
                with open(archivo_figura, "r") as file:
                    figura = file.read()
                    if figura:
                        print(f"Se encontró una figura para ejecutar:\n{figura}")
                        # Procesa y ejecuta la figura
                        cargar_figura("")  # Borra la figura después de ejecutarla
                        esperar_figura = False  # Deja de esperar figuras


        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")
            break

    print(f"ADIOS. TE ESPERO EN OTRA OCASIÓN [{addr}]")
    try:
        
        found = False
        drone_position = None
        with drone_positions_lock:
            for position in global_drone_positions:
                if position[1] == ID:
                    found = True
                    drone_position = position
                    break

        if found:
            (x_actual, y_actual), _, _ = drone_position
            enviar_estado_desconectado_a_kafka(ID)
            handle_disconnection(ID, x_actual, y_actual)
        else:
            print(f"Dron con ID {ID} no encontrado en global_drone_positions.")
        
    except Exception as e:
        print(f"Error al cerrar la conexión: {e}")
    finally:
        conn.close()
    
def enviar_estado_desconectado_a_kafka(id_dron):
    estado_desconectado = "desconectado"
    message = f"{0},{0},{id_dron},{estado_desconectado}"
    producer.produce(KAFKA_TOPIC_SEC, key=None, value=message)
    producer.flush()
    print(f"Estado 'desconectado' enviado a Kafka para el dron {id_dron}")

def consume_messages():
    global global_drone_positions
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC_SEC])

    # Inicia el hilo para esperar la figura completada y enviar la orden de regreso
    esperar_figura_thread = threading.Thread(target=esperar_figura_completada)
    esperar_figura_thread.daemon = True
    esperar_figura_thread.start()

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
            
            # Parsea la posición y el estado del dron desde el mensaje
            try:
                x, y, drone_name, estado = payload.split(',')
                x, y = int(x), int(y)

                if drone_name != "DISCONNECTED":
                    with drone_positions_lock:
                        # Busca si el dron ya está en la lista por nombre
                        found = False
                        for i, drone_position in enumerate(global_drone_positions):
                            if drone_position[1] == drone_name:
                                if estado == "desconectado":
                                    # Detener el movimiento del dron si se desconecta
                                    global_drone_positions[i] = ((0, 0), drone_name, estado)
                                    handle_disconnection(drone_name, x, y)
                                else:
                                    global_drone_positions[i] = ((x, y), drone_name, estado)
                                found = True
                                break

                        if not found:
                            if estado != "desconectado":
                                # Si el dron no está en la lista, agrégalo
                                global_drone_positions.append(((x, y), drone_name, estado))
                                
                            else:
                                print(f"Dron {drone_name} se ha desconectado. Deteniendo movimiento.")
                                # Puedes enviar al dron a (0, 0) y luego eliminarlo de global_drone_positions
                                # Enviar al dron a (0, 0)...
                                # Eliminar al dron de global_drone_positions
                                global_drone_positions = [drone for drone in global_drone_positions if drone[1] != drone_name]

                    print(f"Posición de {drone_name}: ({x}, {y}), Estado: {estado}")

                if verificar_figura_completada():
                    print("Figura completada por todos los drones.")
                    # Espera un tiempo antes de enviar la orden de regreso
                    time.sleep(10)  # Espera 10 segundos antes de enviar la orden
                    enviar_orden_regreso_a_casa()
            except ValueError:
                print(f"Error al analizar la posición del dron: {payload}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()




def main_game_loop():
    global global_drone_positions, my_map

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            my_map.display_map()
            

        with drone_positions_lock:
            my_map.update_drones(global_drone_positions)
            my_map.draw_drones()
            # Actualiza la pantalla
            pygame.display.flip()


        # Actualiza la pantalla
        pygame.display.flip()

# Función para ejecutar el bucle del mapa en un hilo separado
def game_loop_thread():
    while True:
        main_game_loop()

def start():
    global global_drone_positions
    
    # Inicia el hilo para el bucle del mapa
    game_thread = threading.Thread(target=game_loop_thread)
    game_thread.daemon = True
    game_thread.start()
    

    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER} con puerto {PORT}")
    CONEX_ACTIVAS = threading.active_count() - 1
    print(CONEX_ACTIVAS)
    
    

        
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon=True
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES - CONEX_ACTIVAS)
        else:
            print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
            conn.send("OOppsss... DEMASIADAS CONEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
            try:
                conn.close()
            except Exception as e:
                print(f"Error al cerrar la conexión: {e}")

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()
