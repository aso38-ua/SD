# Usa una imagen base de Python
FROM python:latest

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app



COPY . .

RUN pip install -r requirements.txt

CMD ["bash"]


#sudo docker run -it dockerprueba:v1