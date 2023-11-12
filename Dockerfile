# Usa una imagen base de Python
FROM ubuntu:latest

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app



COPY . .



# Abre una terminal interactiva dentro del contenedor
CMD ["python"]


#sudo docker run -it dockerprueba:v1