import pygame
import numpy as np

class Coordinate:
    def __init__(self, row, column):
        self.row = row
        self.column = column

    def getRow(self):
        return self.row

    def getColumn(self):
        return self.column

    def setRow(self, row):
        self.row = row

    def setColumn(self, column):
        self.column = column

class Map:


    def __init__(self, screen):
        self.tam = 20
        self.matriz = np.zeros((self.tam, self.tam), dtype=int)
        self.screen = screen
        self.drones = {}
        self.previous_positions = {}
        self.drones_parados = {}

    def display_map(self):
        square_size = 40  # Tamaño de los cuadrados

        for i in range(self.tam):
            for j in range(self.tam):
                # Verifica si hay un dron en esta posición
                if (i, j) in self.drones:
                    drone_id = self.drones[(i, j)][0]  # Obtén el ID del dron
                    estado=self.drones[(i, j)][1]
                    fill_color = (255, 255, 255)  # Verde para el dron
                    if estado == "moviendo":
                        fill_color = (255, 0, 0)

                    else:
                        fill_color = (0, 255, 0)
                    
                else:
                    fill_color = (255, 255, 255)  # Blanco para celdas vacías

                # Definir colores
                border_color = (128, 128, 128)  # Gris para el borde
                pygame.draw.rect(self.screen, border_color, (j * square_size, i * square_size, square_size, square_size))
                pygame.draw.rect(self.screen, fill_color, (j * square_size + 1, i * square_size + 1, square_size - 2, square_size - 2))
                
                # Dibuja el ID del dron en la casilla
                if (i, j) in self.drones:
                    font = pygame.font.Font(None, 18)  # Tamaño de fuente
                    text = font.render(str(drone_id), True, (0, 0, 0))  # Texto negro
                    text_rect = text.get_rect()
                    text_rect.center = (j * square_size + square_size // 2, i * square_size + square_size // 2)  # Centra el texto
                    self.screen.blit(text, text_rect)



    def update_drones(self, drone_data):
        # Crea una copia de la matriz actual para mantener el estado anterior del mapa
        previous_map = np.copy(self.matriz)

        # Limpia el mapa anterior, eliminando todas las posiciones de drones
        self.matriz = np.zeros((self.tam, self.tam), dtype=int)
        self.drones = {}  # Limpiamos el diccionario de drones

        # Actualiza el mapa con las nuevas posiciones de los drones
        for data in drone_data:
            x, y = data[0]  # Posición
            drone_id = data[1]  # ID del dron
            estado = data[2] if len(data) == 3 else "en posicion"  # Estado, con valor predeterminado

            if 0 <= x < self.tam and 0 <= y < self.tam:
                self.matriz[x, y] = 1
                self.drones[(x, y)] = (drone_id, estado)

                # Verifica si el dron está "moviéndose" y tiene una posición anterior
                if estado == "moviendo" and drone_id in self.previous_positions:
                    prev_x, prev_y = self.previous_positions[drone_id]
                    self.matriz[prev_x, prev_y] = 0  # Borra la posición anterior

                if estado == "moviendo":
                    self.previous_positions[drone_id] = (x, y)  # Actualiza la posición anterior
                
                if estado == "parado":
                    self.drones_parados[(x, y)] = (drone_id, estado)
                else:
                    # Si el dron cambió de estado, elimínalo de los drones parados
                    self.drones_parados.pop((x, y), None)
            

        # Compara el mapa actual con el mapa anterior para detectar cambios
        changes = np.where(self.matriz != previous_map)

        # Restaura la información de drones previa
        for position, (drone_id, estado) in self.drones.items():
            x, y = position
            self.drones[(x, y)] = (drone_id, estado)

        # Vuelve a dibujar solo las celdas que han cambiado
        for x, y in zip(*changes):
            # Dibuja el fondo limpio (puedes ajustar el color del fondo)
            fill_color = (0, 0, 0)  # Fondo negro en este ejemplo
            pygame.draw.rect(self.screen, fill_color, (y * 40 + 1, x * 40 + 1, 38, 38))

            # Obtén el estado del dron (moviéndose o en posición)
            drone_info = self.drones.get((x, y), ("", ""))
            drone_id, estado = drone_info

            # Dibuja el dron en rojo si está "moviéndose" o en verde si está "en posición"
            if estado == "moviendo":
                drone_color = (255, 0, 0)  # Rojo
            elif estado == "parado":
                drone_color = (0, 255, 0)
            elif estado == "desconectado":
                drone_color = (0, 255, 0)
            else:
                drone_color = (255, 255, 255)  # Verde

            pygame.draw.rect(self.screen, drone_color, (y * 40 + 1, x * 40 + 1, 38, 38))

            # Dibuja el ID del dron en la casilla
            font = pygame.font.Font(None, 18)
            text = font.render(drone_id, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (y * 40 + 20, x * 40 + 20)
            self.screen.blit(text, text_rect)

        pygame.display.update()


    def draw_drones(self):
        # Dibuja todos los drones en el mapa, utilizando self.drones y self.drones_parados
        for (x, y), (drone_id, estado) in self.drones.items():
            if estado == "moviendo":
                drone_color = (255, 0, 0)  # Rojo
            elif estado == "parado":
                drone_color = (0, 255, 0)  # Verde
            elif estado == "desconectado":
                drone_color = (0, 255, 0)
            else:
                drone_color = (255, 255, 255)  # Otro color
            pygame.draw.rect(self.screen, drone_color, (y * 40 + 1, x * 40 + 1, 38, 38))

            # Dibuja el ID del dron
            font = pygame.font.Font(None, 18)  # Tamaño de fuente
            text = font.render(drone_id, True, (0, 0, 0))  # Texto negro
            text_rect = text.get_rect()
            text_rect.center = (y * 40 + 20, x * 40 + 20)  # Centra el texto
            self.screen.blit(text, text_rect)

        # Dibuja los drones parados en verde
        for (x, y), (drone_id, estado) in self.drones_parados.items():
            drone_color = (0, 255, 0)  # Verde
            pygame.draw.rect(self.screen, drone_color, (y * 40 + 1, x * 40 + 1, 38, 38))

            # Dibuja el ID del dron
            font = pygame.font.Font(None, 18)  # Tamaño de fuente
            text = font.render(drone_id, True, (0, 0, 0))  # Texto negro
            text_rect = text.get_rect()
            text_rect.center = (y * 40 + 20, x * 40 + 20)  # Centra el texto
            self.screen.blit(text, text_rect)

        pygame.display.update()



    def clear_drones(self):
        # Borra las posiciones de los drones en el diccionario
        self.drones = {}

if __name__ == "__main__":
    pygame.init()
    screen_width = 800
    screen_height = 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    my_map = Map(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Ejemplo de cómo actualizar las posiciones de los drones
        drone_positions = [((1, 1), "Dron1","moviendo")]
        my_map.clear_drones()  # Borra las posiciones anteriores
        my_map.update_drones(drone_positions)  # Actualiza las nuevas posiciones
        my_map.display_map()
        pygame.display.flip()

    pygame.quit()
