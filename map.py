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
    def __init__(self):
        self.tam = 20
        self.matriz = np.empty((20, 20), dtype=int)

    def display_map(self):
        pygame.init()
        square_size = 40  # Tamaño de los cuadrados
        screen = pygame.display.set_mode((self.tam * square_size, self.tam * square_size))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            for i in range(self.tam):
                for j in range(self.tam):
                    cell_value = self.matriz[i, j]
                    # Definir colores
                    border_color = (128, 128, 128)  # Gris para el borde
                    fill_color = (255, 255, 255)  # Blanco para el relleno
                    pygame.draw.rect(screen, border_color, (j * square_size, i * square_size, square_size, square_size))
                    pygame.draw.rect(screen, fill_color, (j * square_size + 1, i * square_size + 1, square_size - 2, square_size - 2))

            pygame.display.flip()

if __name__ == "__main__":
    my_map = Map()
    my_map.display_map()
