import json
import socket
import threading
import random
import secrets
import string
import sqlite3
import argparse
from confluent_kafka import Producer, Consumer, KafkaError

KAFKA_BROKER = "127.0.0.1:9092"
KAFKA_TOPIC = "drones"
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

def autenticar_dron(conn, db_cursor):
    msg = conn.recv(HEADER).decode(FORMAT)
    print(msg)
    
    # El mensaje enviado debe ser la ID de autenticación
    
    # Consultar la base de datos para verificar si la ID de autenticación es válida
    db_cursor.execute("SELECT Id FROM Dron WHERE Id=?", (msg,))
    resultado = db_cursor.fetchone()
    
    print(resultado)
    
    
    if resultado:
        # Autenticación correcta
        print("Autenticación correcta")
        conn.send("Autenticación correcta".encode(FORMAT))
        return True
        
    else:
        print("Incorrecto, expulsando dron")
        return False


def handle_client(conn, addr):
    print(f"[NUEVA CONEXIÓN] {addr} connected.")
    # Crear una conexión de base de datos SQLite para este hilo
    db_connection = sqlite3.connect('Registro.db')
    db_cursor = db_connection.cursor()
    
    # Autenticar al dron
    conn.send("Id de autenticacion: ".encode(FORMAT))
    conn.recv(2048).decode(FORMAT)
    conectado=autenticar_dron(conn, db_cursor)
    
    connected = True
    while connected:
        try:
            
            if not conectado:
                print(f"[CONEXIÓN CERRADA] {addr} se ha desconectado.")
                break
            
            msg2 = "Polla de negro"
            print(msg2)
            
            # Envía el mensaje al tópico de Kafka
            producer.produce(KAFKA_TOPIC, key=None, value=msg2)
            
            conn.send("Mensaje enviado a Kafka".encode(FORMAT))
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")
            break

    print(f"ADIOS. TE ESPERO EN OTRA OCASIÓN [{addr}]")
    try:
        conn.close()
    except Exception as e:
        print(f"Error al cerrar la conexión: {e}")

def consume_messages():
    consumer.subscribe([KAFKA_TOPIC])
    
    while True:
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Error al consumir mensaje: {msg.error()}")
        
        print(f"Mensaje recibido de Kafka: {msg.value()}")

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER} con puerto {PORT}")
    CONEX_ACTIVAS = threading.active_count() - 1
    print(CONEX_ACTIVAS)
    
    # Inicia el hilo para consumir mensajes de Kafka
    kafka_thread = threading.Thread(target=consume_messages)
    kafka_thread.daemon = True
    kafka_thread.start()
    
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
            try:
                conn.close()
            except Exception as e:
                print(f"Error al cerrar la conexión: {e}")

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()
