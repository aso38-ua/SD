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
import netifaces
from collections import defaultdict
import signal
import sys
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from firebase_admin import db


cred = credentials.Certificate("sddd-8c96a-firebase-adminsdk-7sqg0-e7dc7ec49d.json")
firebase_admin.initialize_app(cred)
db = firestore.client()



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

def consume_all_messages():
    # Configuración del consumidor de Kafka
    consumer = Consumer(CONSUMER_CONFIG)
    consumer.subscribe([KAFKA_TOPIC,KAFKA_TOPIC_ALL,KAFKA_TOPIC_ORDERS,KAFKA_TOPIC_SEC])

    try:
        while True:
            # Intenta consumir mensajes con un límite de tiempo
            msg = consumer.poll(5.0)

            if msg is None:
                # Si no se reciben mensajes en 5 segundos, sal del bucle
                print("No se recibieron mensajes en 5 segundos. Saliendo...")
                break

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error al consumir mensaje: {msg.error()}")
                    break

            # Procesa el mensaje, por ejemplo, imprímelo
            print(f"Mensaje borrado: {msg.value().decode('utf-8')}")

    except KeyboardInterrupt:
        pass
    finally:
        # Cierra el consumidor de Kafka al finalizar
        consumer.close()




def cleanup_before_exit():
    # Limpia el mapa y la lista de posiciones de los drones
    my_map.clear_map()  # Reemplaza 'clear_map' con el método que tengas para limpiar el mapa
    global global_drone_positions
    global_drone_positions = []

def handle_interrupt_signal(sig, frame):
    print("Se recibió una señal de interrupción (Ctrl+C). Consumiendo mensajes y cerrando el servidor...")
    consume_all_messages()
    cleanup_before_exit()
    sys.exit(0)

# Registrar la función de manejo de señal
signal.signal(signal.SIGINT, handle_interrupt_signal)


last_sent_messages = defaultdict(str)
pygame.init()
screen_width = 800
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
my_map = Map(screen)

global global_drone_positions,temperature
global_drone_positions=[]
# Define un cerrojo para sincronizar el acceso a global_drone_positions
drone_positions_lock = threading.Lock()

drones_conectados = set()

KAFKA_BROKER = "192.168.1.129:9092"
KAFKA_TOPIC = "drones-positions"
KAFKA_TOPIC_SEC = "drones-coordinate"
KAFKA_TOPIC_ORDERS= "dron-back"
KAFKA_TOPIC_ALL="drones-all-positions"
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
archivo_figura = "AwD_figuras_CorreccionGrupo6.json"

# Bandera para controlar si el motor debe esperar a las figuras
esperar_figura = False

def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor de drones con Kafka")
    parser.add_argument("--port", type=int, default=5051, help="Puerto de escucha")
    parser.add_argument("--max-drones", type=int, default=90, help="Número máximo de drones a admitir")
    parser.add_argument("--WIp",type=str,default="192.168.1.129",help="Ip de clima")

    return parser.parse_args()

args = parse_arguments()
PORT = args.port
MAX_CONEXIONES = args.max_drones

HEADER = 64
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
FIN = "FIN"

# Configura la dirección y el puerto del servidor AD_Weather
AD_WEATHER_SERVER = args.WIp
AD_WEATHER_PORT = 5052

connected_drones = {}


def send_message_to_kafka_from_figuras(topic, final_positions):
    producer = Producer(PRODUCER_CONFIG)

    for nombre_figura, posiciones in final_positions.items():
        for position, id_dron in posiciones:
            x_destino, y_destino = position
            message = f"{id_dron},{x_destino},{y_destino},{nombre_figura}"
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

total_drones_figura=[]
total_figuras=[]

def procesar_figuras():
    try:
        with open(archivo_figura, "r") as file:
            data = json.load(file)
            figuras = data.get("figuras", [])
            if not figuras:
                print("No se encontraron figuras en el archivo.")
                return []

            final_positions = {}
            
            

            for figura in figuras:
                total_drones = 0
                nombre_figura = figura.get("Nombre")
                drones = figura.get("Drones", [])
                total_figuras.append(nombre_figura)
                
                for dron in drones:
                    id_dron = dron.get("ID")
                    pos = dron.get("POS")
                    x_destino, y_destino = map(int, pos.split(','))

                    if nombre_figura not in final_positions:
                        final_positions[nombre_figura] = []
                    final_positions[nombre_figura].append(((x_destino, y_destino), id_dron))

                    total_drones += 1
                    print(f"Figura procesada para dron {id_dron} ({nombre_figura}): Posición destino en ({x_destino}, {y_destino})")
                total_drones_figura.append(total_drones)
                print(f"Figura {nombre_figura} registrada")
                print(f"Hay {total_drones} drones en esta figura")

            send_message_to_kafka_from_figuras(KAFKA_TOPIC, final_positions)
            print("Figuras procesadas")
            return final_positions
    except FileNotFoundError:
        print("El archivo de figuras no se ha encontrado.")
        return []
    except Exception as e:
        print(f"Error al procesar las figuras: {e}")
        return []

    


final_positions_por_figura = procesar_figuras()



global drones_que_han_llegado
drones_que_han_llegado = 0


def verificar_figura_completada():

    return #drones_que_han_llegado == total_drones_en_la_figura

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
    global temperature
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

                    temperature = float(data.decode('utf-8'))
                    print(f"Temperatura actual: {temperature}°C")

                    if temperature<=0:
                        print("Mandando los drones a casa...")
                        mensaje = "Regresar a casa"
                        producer = Producer(PRODUCER_CONFIG)
                        producer.produce(KAFKA_TOPIC_ORDERS, key=None, value=mensaje)
                        producer.flush()

                    else:
                        mensaje = "Todo OK"
                        producer = Producer(PRODUCER_CONFIG)
                        producer.produce(KAFKA_TOPIC_ORDERS, key=None, value=mensaje)
                        producer.flush()
                    
                    # Espera un período antes de obtener una actualización
                    time.sleep(60)  # Espera 60 segundos antes de obtener la próxima actualización
                    
            except ConnectionRefusedError:
                print("No se pudo conectar al servidor AD_Weather. Intentando de nuevo en 30 segundos.")
                mensaje = "Todo OK"
                producer = Producer(PRODUCER_CONFIG)
                producer.produce(KAFKA_TOPIC_ORDERS, key=None, value=mensaje)
                producer.flush()
                time.sleep(30)
            except Exception as e:
                print(f"Error al obtener la temperatura: {e}")

# Agrega un hilo para conectarse a AD_Weather y obtener la temperatura
ad_weather_thread = threading.Thread(target=get_temperature_from_ad_weather)
ad_weather_thread.daemon = True
ad_weather_thread.start()



def autenticar_dron(conn, token):
    global drones_conectados

    # Consulta la base de datos de Firebase para verificar si el token de autenticación es válido
    dron_ref = db.collection('Dron').where('Token', '==', token)
    resultado = dron_ref.stream()

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
    global global_drone_positions, my_map, drones_que_han_llegado

    my_map.remove_drone(drone_id)

    with drone_positions_lock:
        try:
            # Busca al dron en la lista y elimínalo si lo encuentras
            drone_position = next(d for d in global_drone_positions if d[1] == drone_id)
            global_drone_positions.remove(drone_position)
            print(f"Dron {drone_id} desconectado y movido a (0, 0).")

            # Si el dron desconectado estaba en estado "parado," reduce la cuenta de drones en destino
            if drone_position[2] == "parado":
                drones_que_han_llegado -= 1

        except StopIteration:
            print(f"Dron {drone_id} no encontrado en la lista.")

last_sent_messages = {}

def send_drone_positions_to_all():
    # Crea un productor de Kafka
    producer = Producer(PRODUCER_CONFIG)

    # Itera a través de las posiciones de los drones y envía las posiciones a cada uno
    for position in global_drone_positions:
        (x, y), dron_id, estado = position
        message = f"{dron_id},{x},{y},{estado}"
        
        # Verifica si ya se ha enviado un mensaje para este dron
        if dron_id in last_sent_messages:
            last_message = last_sent_messages[dron_id]
            if message == last_message:
                continue  # Salta el mensaje si es igual al último enviado

        # Envía la posición a través de Kafka al dron actual
        producer.produce(KAFKA_TOPIC_ALL, key=None, value=message)
        producer.flush()  # Asegúrate de que todos los mensajes se envíen

        # Actualiza el último mensaje enviado para el dron
        last_sent_messages[dron_id] = message

def handle_client(conn, addr):
    global esperar_figura
    global global_drone_positions, my_map
    global drones_conectados

    print(f"[NUEVA CONEXIÓN] {addr} connected.")
    # Crear una conexión de base de datos SQLite para este hilo
    
    
    
    # Autenticar al dron
    token=conn.recv(2048).decode(FORMAT)
    conectado=autenticar_dron(conn,token)
    
    if conectado:
        kafka_thread = threading.Thread(target=consume_messages)
        kafka_thread.daemon = True
        kafka_thread.start()
    
    while conectado:
        try:
            
            
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
    global global_drone_positions,drones_que_han_llegado
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
                                if estado == "parado":
                                    drones_que_han_llegado += 1
                                
                            else:
                                print(f"Dron {drone_name} se ha desconectado. Deteniendo movimiento.")
                                # Puedes enviar al dron a (0, 0) y luego eliminarlo de global_drone_positions
                                # Enviar al dron a (0, 0)...
                                # Eliminar al dron de global_drone_positions
                                global_drone_positions = [drone for drone in global_drone_positions if drone[1] != drone_name]
                    send_drone_positions_to_all()
                    print(f"Posición de {drone_name}: ({x}, {y}), Estado: {estado}")

                if verificar_figura_completada():
                    print("Figura completada por todos los drones.")
                    # Espera un tiempo antes de enviar la orden de regreso
                    esperar_figura = False
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
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    print("[STARTING] Servidor inicializándose...")

    start()
except KeyboardInterrupt:
    pass
finally:
    cleanup_before_exit()
