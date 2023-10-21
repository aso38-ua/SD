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
                if (i, j) in self.drones and self.drones[(i, j)] == 1:
                    fill_color = (0, 255, 0)  # Verde para el dron
                else:
                    fill_color = (255, 255, 255)  # Blanco para celdas vacías

                # Definir colores
                border_color = (128, 128, 128)  # Gris para el borde
                pygame.draw.rect(self.screen, border_color, (j * square_size, i * square_size, square_size, square_size))
                pygame.draw.rect(self.screen, fill_color, (j * square_size + 1, i * square_size + 1, square_size - 2, square_size - 2))


    def update_drones(self, drone_positions):
        # Actualiza el diccionario de drones con las nuevas posiciones
        for position in drone_positions:
            self.drones[position] = 1  # Marca la posición del dron como ocupada

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
        drone_positions = [(1, 1), (3, 3), (5, 5)]
        my_map.clear_drones()  # Borra las posiciones anteriores
        my_map.update_drones(drone_positions)  # Actualiza las nuevas posiciones
        my_map.display_map()
        pygame.display.flip()

    pygame.quit()
