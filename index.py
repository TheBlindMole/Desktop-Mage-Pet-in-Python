import tkinter as tk

root = tk.Tk()

# Definições da janela
root.overrideredirect(True)
root.attributes('-topmost', True) # Sempre no topo
root.title("Tk Example")
root.minsize(300, 300)
root.attributes('-fullscreen', True)

# CORREÇÃO PARA LINUX (GNOME): Força o sistema a carregar a janela primeiro
root.wait_visibility(root)

# CORREÇÃO DO VALOR: Mude de 1.0 para 0.5 (50% de transparência)
root.attributes("-alpha", 0.4)

# Botão de fechar
btn = tk.Button(root, text="exit", command=root.destroy)
btn.pack(pady=20)

root.mainloop()
