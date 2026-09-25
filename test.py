import tkinter as tk
from PIL import Image, ImageTk, ImageSequence

class TestePet:
    def __init__(self, root):
        self.root = root
        
        # 1. Configurações para o "Desktop Pet" (Janela sem bordas e flutuante)
        self.root.overrideredirect(True) # Remove as bordas da janela (X, Minimizar, etc.)
        self.root.attributes("-topmost", True) # Mantém o pet sempre no topo de outras janelas
        
        # 2. Cria o Label que vai segurar o GIF
        self.label_pet = tk.Label(root, bg="systemTransparent" if root.tk.call('tk', 'windowingsystem') == 'aqua' else 'gray')
        # Nota: Se o seu Fedora suportar transparência total, pode definir o bg do root.
        # Para o teste rápido, usamos um fundo simples.
        self.label_pet.pack()

        # 3. Carrega o GIF e inicia a animação
        self.next_frame()

    def next_frame(self):
        # Abre o seu arquivo walk.gif
        img = Image.open("/home/deitamacho/Downloads/Projetos/desktop_pet/frames/gifs/walk.gif")
        
        # Guarda todos os frames na memória para o Tkinter não os apagar
        self.frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(img)]
        
        # Inicia o loop de animação no frame 0
        self.animar(0)

    def animar(self, indice):
        # Faz o GIF voltar ao início quando os frames acabarem
        if indice >= len(self.frames):
            indice = 0
            
        # Atualiza a imagem no ecrã
        frame_atual = self.frames[indice]
        self.label_pet.config(image=frame_atual)
        
        # Agenda o próximo frame (100ms = rápido / 200ms = mais lento)
        self.root.after(100, lambda: self.animar(indice + 1))

# Inicializa o teste
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("200x200+500+300") # Define o tamanho da janela e a posição no ecrã (X=500, Y=300)
    app = TestePet(root)
    root.mainloop()
