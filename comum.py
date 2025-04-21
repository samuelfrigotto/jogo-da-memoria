from enum import Enum
import random

class Animal(Enum):
    CACHORRO = 1
    CAVALO = 2
    COBRA = 3
    CORUJA = 4
    ELEFANTE = 5
    GATO = 6
    GIRAFA = 7
    JACARE = 8
    LEAO = 9
    MACACO = 10
    PENGUIM = 11
    TIGRE = 12
    TUBARAO = 13
    URSO = 14
    ZEBRA = 15

class Jogador:
    def __init__(self, socket, id):
        self.socket = socket
        self.id = id
        self.pontos = 0

def gerar_tabuleiro():
    """Gera e embaralha 15 pares de animais (30 cartas)."""
    animais = list(Animal) * 2
    random.shuffle(animais)
    return animais  # lista com 30 elementos
