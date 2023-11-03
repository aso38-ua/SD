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
        self.matriz = np.zeros((20, 20), dtype=int)
        self.screen = screen
        self.drones = {}

    def display_map(self):
        square_size = 40  # Tamaño de los cuadrados

        for i in range(self.tam):
            for j in range(self.tam):
                # Verifica si hay un dron en esta posición
                if (i, j) in self.drones:
                    fill_color = (0, 255, 0)  # Verde para el dron
                    drone_id = self.drones[(i, j)]  # Obtén el ID del dron
                else:
                    fill_color = (255, 255, 255)  # Blanco para celdas vacías

                # Definir colores
                border_color = (128, 128, 128)  # Gris para el borde
                pygame.draw.rect(self.screen, border_color, (j * square_size, i * square_size, square_size, square_size))
                pygame.draw.rect(self.screen, fill_color, (j * square_size + 1, i * square_size + 1, square_size - 2, square_size - 2))
                
                # Dibuja el ID del dron en la casilla
                if (i, j) in self.drones:
                    font = pygame.font.Font(None, 18)  # Tamaño de fuente
                    text = font.render(drone_id, True, (0, 0, 0))  # Texto negro
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
        for position, drone_id in drone_data:
            x, y = position
            if 0 <= x < self.tam and 0 <= y < self.tam:
                self.matriz[x, y] = 1
                self.drones[position] = drone_id

        # Compara el mapa actual con el mapa anterior para detectar cambios
        changes = np.where(self.matriz != previous_map)

        # Vuelve a dibujar solo las celdas que han cambiado
        for x, y in zip(*changes):
            # Dibuja el fondo limpio (puedes ajustar el color del fondo)
            fill_color = (0, 0, 0)  # Fondo negro en este ejemplo
            pygame.draw.rect(self.screen, fill_color, (y * 40 + 1, x * 40 + 1, 38, 38))

            # Dibuja el ID del dron en la casilla
            font = pygame.font.Font(None, 18)
            drone_id = self.drones.get((x, y), "")  # Usamos get para obtener el ID o una cadena vacía si no hay dron
            text = font.render(drone_id, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = (y * 40 + 20, x * 40 + 20)
            self.screen.blit(text, text_rect)

        pygame.display.update()




    def clear_drones(self):
        # Borra las posiciones de los drones en el diccionario
        self.drones = {}

if __name__ == "__main__":
    pygame.init()
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    my_map = Map(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Ejemplo de cómo actualizar las posiciones de los drones
        drone_positions = [((1, 1), "Dron1"), ((3, 3), "Dron2"), ((5, 5), "Dron3")]
        my_map.clear_drones()  # Borra las posiciones anteriores
        my_map.update_drones(drone_positions)  # Actualiza las nuevas posiciones
        my_map.display_map()
        pygame.display.flip()

    pygame.quit()
