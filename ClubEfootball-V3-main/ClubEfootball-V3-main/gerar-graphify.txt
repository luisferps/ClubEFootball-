import os

def ler_codigo_telas():
    # Caminho do arquivo de telas dentro da pasta programas
    caminho_telas = os.path.join("programas", "telas.py")
    
    if os.path.exists(caminho_telas):
        print(f"--- LENDO O ARQUIVO: {caminho_telas} ---")
        with open(caminho_telas, "r", encoding="utf-8") as f:
            conteudo = f.read()
            
        # Exibe os primeiros 3000 caracteres para entendermos a estrutura
        print(conteudo[:3000])
        print("----------------------------------------")
        if len(conteudo) > 3000:
            print("... (O arquivo possui mais linhas abaixo) ...")
    else:
        print(f"Erro: Não encontrei o arquivo {caminho_telas}. Verifique se a pasta está correta.")

if __name__ == "__main__":
    ler_codigo_telas()
