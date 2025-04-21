import socket
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  # novo import
from comum import Animal


HOST = '127.0.0.1'
PORTA = 50000

class JogoMemoriaCliente:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 Jogo da Memória")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORTA))

        self.id_jogador = self.socket.recv(2)[1]
        self.vez_de_jogar = False
        self.tabuleiro = [0] * 30
        self.botoes = []
        self.selecionadas = []

        self.info_label = tk.Label(root, text=f"🧑 Você é o Jogador {(self.id_jogador) + 1}", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.info_label.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(10, 2))

        self.placar_label = tk.Label(root, text="Placar - Você: 0 | Adversário: 0", font=("Arial", 11), bg="#f0f0f0")
        self.placar_label.grid(row=1, column=0, columnspan=6, sticky="ew", pady=2)

        self.status_label = tk.Label(root, text="⌛ Aguardando início do jogo...", fg="blue", font=("Arial", 11, "italic"), bg="#e8e8ff")
        self.status_label.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(4, 20))

        # carregar imagem do verso
        img = Image.open("imagens/verso.jpeg").resize((64, 64))
        self.img_verso = ImageTk.PhotoImage(img)

        # carregar imagens dos animais
        self.imagens_animais = {}
        for animal in Animal:
            caminho = f"imagens/{animal.name.lower()}.jpeg"
            img = Image.open(caminho).resize((64, 64))
            self.imagens_animais[animal.value] = ImageTk.PhotoImage(img)


        self.criar_tabuleiro()

        self.root.after(100, self.escutar_servidor)

    def criar_tabuleiro(self):
        for i in range(30):
            btn = tk.Button(self.root, image=self.img_verso, width=64, height=64,
                            command=lambda i=i: self.carta_clicada(i))
            btn.grid(row=3 + i // 6, column=i % 6, padx=2, pady=2)
            self.botoes.append(btn)

    def carta_clicada(self, i):
        if not self.vez_de_jogar:
            self.status_label.config(text="⏳ Aguardando sua vez...", fg="gray")
            return

        if i in self.selecionadas or self.tabuleiro[i] != 0:
            self.status_label.config(text="⚠️ Jogada inválida", fg="red")
            return

        self.selecionadas.append(i)
        self.enviar_jogada()


    def enviar_jogada(self):
        self.socket.sendall(bytearray([3, self.selecionadas[-1]]))
        if len(self.selecionadas) == 2:
            self.vez_de_jogar = False

    def atualizar_tabuleiro(self):
        for i in range(30):
            if self.tabuleiro[i] == 0:
                self.botoes[i].config(image=self.img_verso, text="", compound="center")
            else:
                img = self.imagens_animais.get(self.tabuleiro[i])
                self.botoes[i].config(image=img, text="", compound="center")


    def escutar_servidor(self):
        try:
            self.socket.settimeout(0.1)
            msg = self.socket.recv(1)
            if not msg:
                return

            opcode = msg[0]

            if opcode == 1:
                # Atualização completa do tabuleiro
                buffer = self.socket.recv(30)
                for i in range(30):
                    self.tabuleiro[i] = buffer[i]
                self.atualizar_tabuleiro()

            elif opcode == 2:
                # Sua vez de jogar
                self.vez_de_jogar = True
                self.selecionadas = []
                self.status_label.config(text="🎯 Sua vez de jogar!", fg="green")

            elif opcode == 4:
                # Resultado da jogada
                dados = self.socket.recv(5)
                acerto, pos1, id1, pos2, id2 = dados
                self.botoes[pos1].config(image=self.imagens_animais[id1])
                self.botoes[pos2].config(image=self.imagens_animais[id2])

                if acerto:
                    self.status_label.config(text="🎉 Par encontrado!", fg="green")
                else:
                    self.status_label.config(text="❌ Não foi par", fg="red")
                    self.root.after(1000, lambda: self.resetar([pos1, pos2]))

                self.selecionadas = []

            elif opcode == 5:
                # Atualizar placar
                placares = self.socket.recv(2)
                placar_voce = placares[self.id_jogador]
                placar_adv = placares[(self.id_jogador + 1) % 2]
                self.placar_label.config(
                    text=f"Placar - Você: {placar_voce} | Adversário: {placar_adv}"
                )

            elif opcode == 6:
                # Fim do jogo
                vencedor = self.socket.recv(1)[0]
                if vencedor == self.id_jogador:
                    self.status_label.config(text="🏆 Você venceu!", fg="green")
                else:
                    self.status_label.config(text="😞 Você perdeu!", fg="red")
                self.vez_de_jogar = False

            elif opcode == 7:
                dados = self.socket.recv(4)
                pos1, pos2, id1, id2 = dados

                self.botoes[pos1].config(image=self.imagens_animais[id1])
                self.botoes[pos2].config(image=self.imagens_animais[id2])

                self.status_label.config(
                    text=f"🔄 Adversário jogou {pos1} e {pos2}", fg="gray"
                )

                # Esconde cartas se não forem par após 5 segundos
                self.root.after(5000, lambda: self.resetar([pos1, pos2]))


            elif opcode == 8:
                # Carta revelada momentaneamente
                dados = self.socket.recv(2)
                pos, animal_id = dados
                self.botoes[pos].config(image=self.imagens_animais[animal_id])

            elif opcode == 9:
                # Mensagem de erro
                tam = self.socket.recv(1)[0]
                erro = self.socket.recv(tam).decode()
                messagebox.showerror("Erro", erro)

            elif opcode == 10:
                try:
                    # Pode ser só "vez do adversário" (sem dados) ou com 1 byte indicando acerto
                    self.status_label.config(text="🕒 Vez do adversário...", fg="gray")
                    self.vez_de_jogar = False
                    self.selecionadas = []

                    self.socket.settimeout(0.1)
                    status = self.socket.recv(1)
                    if status and status[0] == 1:
                        self.status_label.config(text="👏 O adversário acertou um par!", fg="blue")
                    elif status and status[0] == 0:
                        self.status_label.config(text="😅 O adversário errou!", fg="gray")
                except:
                    pass

            else:
                print(f"[!] Opcode desconhecido recebido: {opcode}")

        except Exception as e:
            # Debug opcional: print(f"Erro ao escutar servidor: {e}")
            pass

        finally:
            self.root.after(100, self.escutar_servidor)


    def resetar(self, posicoes):
        for i in posicoes:
            if self.tabuleiro[i] == 0:
                self.botoes[i].config(image=self.img_verso, text="")


if __name__ == '__main__':
    root = tk.Tk()
    root.configure(bg="#f0f0f0")  # cor de fundo clara
    app = JogoMemoriaCliente(root)
    root.mainloop()