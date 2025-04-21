import socket
import threading
from comum import Jogador, gerar_tabuleiro
import time

PORTA = 50000
HOST = '127.0.0.1'
PARES_PARA_VENCER = 8

tabuleiro = gerar_tabuleiro()  # Lista com 30 animais
cartas_reveladas = [False] * 30  # Controle do que já foi acertado

# Clientes conectados
jogadores = []
lock = threading.Lock()

def enviar_tabuleiro(jogador):
    msg = bytearray()
    msg.append(1)  # opcode 1 - tabuleiro
    for i in range(30):
        if cartas_reveladas[i]:
            msg.append(tabuleiro[i].value)
        else:
            msg.append(0)
    jogador.socket.sendall(msg)

def enviar_placar():
    msg = bytearray([5, jogadores[0].pontos, jogadores[1].pontos])
    for j in jogadores:
        j.socket.sendall(msg)

def enviar_msg(socket, opcode, *args):
    msg = bytearray([opcode])
    for a in args:
        msg.append(a)
    socket.sendall(msg)

def jogo_da_memoria():
    turno = 0
    jogadas = []

    for j in jogadores:
        enviar_tabuleiro(j)

    while True:
        jogador = jogadores[turno]
        adversario = jogadores[(turno + 1) % 2]

        enviar_msg(jogador.socket, 2)  # Sua vez
        enviar_msg(adversario.socket, 10)  # Vez do adversário

        while len(jogadas) < 2:
            try:
                msg = jogador.socket.recv(2)
                if msg[0] == 3:
                    pos = msg[1]
                    if pos < 0 or pos >= 30 or cartas_reveladas[pos]:
                        erro = "Jogada inválida. Carta fora do limite ou já revelada."
                        enviar_msg(jogador.socket, 9, len(erro), *erro.encode())
                        continue
                    jogadas.append(pos)
                    enviar_msg(jogador.socket, 8, pos, tabuleiro[pos].value)
                    enviar_msg(adversario.socket, 8, pos, tabuleiro[pos].value)
            except:
                continue

        pos1, pos2 = jogadas
        id1 = tabuleiro[pos1].value
        id2 = tabuleiro[pos2].value
        acerto = id1 == id2

        time.sleep(1)  # pequeno delay antes da revelação

        enviar_msg(jogador.socket, 4, int(acerto), pos1, id1, pos2, id2)
        enviar_msg(adversario.socket, 7, pos1, pos2, id1, id2)

        if acerto:
            cartas_reveladas[pos1] = True
            cartas_reveladas[pos2] = True
            jogador.pontos += 1
            enviar_msg(adversario.socket, 10, 1)  # adversário acertou
        else:
            enviar_msg(adversario.socket, 10, 0)  # adversário errou

        enviar_placar()
        for j in jogadores:
            enviar_tabuleiro(j)

        if jogador.pontos >= PARES_PARA_VENCER:
            for j in jogadores:
                enviar_msg(j.socket, 6, jogador.id)
            break

        if not acerto:
            turno = (turno + 1) % 2

        jogadas.clear()

    





def aceitar_conexoes():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORTA))
    servidor.listen(2)
    print('Servidor esperando conexões...')

    while len(jogadores) < 2:
        conn, addr = servidor.accept()
        jogador = Jogador(conn, len(jogadores))
        jogadores.append(jogador)
        print(f'Jogador {jogador.id} conectado.')
        conn.sendall(bytearray([0, jogador.id]))

    jogo_da_memoria()

if __name__ == '__main__':
    aceitar_conexoes()