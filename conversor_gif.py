import os
import sys
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip

def converter_para_gif(caminho_imagem, caminho_saida=None):
    """Converte uma única imagem para o formato GIF."""
    try:
        # Abre a imagem
        imagem = Image.open(caminho_imagem)
        
        # Define o caminho de saída se não for especificado
        if caminho_saida is None:
            nome_base = os.path.splitext(caminho_imagem)[0]
            caminho_saida = f"{nome_base}.gif"
        
        # Salva como GIF
        imagem.save(caminho_saida, 'GIF')
        print(f"Imagem convertida com sucesso: {caminho_saida}")
        return True
    except Exception as e:
        print(f"Erro ao converter a imagem: {e}")
        return False

def converter_video_para_gif(caminho_video, caminho_saida=None, inicio=0, duracao=None, fps=10, largura=None):
    """Converte um vídeo para GIF.
    
    Args:
        caminho_video: Caminho para o arquivo de vídeo
        caminho_saida: Caminho onde o GIF será salvo
        inicio: Tempo de início em segundos (padrão: 0)
        duracao: Duração do GIF em segundos (padrão: vídeo inteiro)
        fps: Frames por segundo do GIF (padrão: 10)
        largura: Largura do GIF em pixels (mantém proporção se especificado)
    """
    try:
        # Carrega o vídeo, aplicando redimensionamento se especificado
        if largura:
            video = VideoFileClip(caminho_video, target_resolution=(largura, None))
        else:
            video = VideoFileClip(caminho_video)
        
        # Define o caminho de saída se não for especificado
        if caminho_saida is None:
            nome_base = os.path.splitext(caminho_video)[0]
            caminho_saida = f"{nome_base}.gif"
        
        # Corta o vídeo se especificado
        if duracao:
            video = video.subclipped(inicio, inicio + duracao)
        elif inicio > 0:
            video = video.subclipped(inicio)
        
        # Converte para GIF
        video.write_gif(caminho_saida, fps=fps)
        
        # Fecha o vídeo para liberar recursos
        video.close()
        
        print(f"Vídeo convertido para GIF com sucesso: {caminho_saida}")
        return True
    except Exception as e:
        print(f"Erro ao converter o vídeo: {e}")
        return False

def criar_gif_animado(lista_imagens, caminho_saida, duracao=100):
    """Cria um GIF animado a partir de uma lista de imagens.
    
    Args:
        lista_imagens: Lista de caminhos para as imagens
        caminho_saida: Caminho onde o GIF será salvo
        duracao: Duração de cada frame em milissegundos
    """
    try:
        # Abre todas as imagens
        imagens = [Image.open(img) for img in lista_imagens]
        
        # Pega a primeira imagem
        primeira_imagem = imagens[0]
        
        # Salva o GIF animado
        primeira_imagem.save(
            caminho_saida,
            format='GIF',
            append_images=imagens[1:],
            save_all=True,
            duration=duracao,
            loop=0  # 0 significa loop infinito
        )
        print(f"GIF animado criado com sucesso: {caminho_saida}")
        return True
    except Exception as e:
        print(f"Erro ao criar GIF animado: {e}")
        return False

def main():
    """Função principal para executar o conversor via linha de comando."""
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Para converter uma imagem: python conversor_gif.py imagem.jpg [saida.gif]")
        print("  Para converter vídeo: python conversor_gif.py --video video.mp4 [saida.gif] [--inicio 0] [--duracao 10] [--fps 10] [--largura 480]")
        print("  Para criar GIF animado: python conversor_gif.py --animado saida.gif imagem1.jpg imagem2.jpg ...")
        return
    
    if sys.argv[1] == "--video":
        if len(sys.argv) < 3:
            print("Erro: Especifique o arquivo de vídeo.")
            return
        
        caminho_video = sys.argv[2]
        caminho_saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
        
        # Parâmetros opcionais
        inicio = 0
        duracao = None
        fps = 10
        largura = None
        
        i = 4 if caminho_saida else 3
        while i < len(sys.argv):
            if sys.argv[i] == "--inicio" and i + 1 < len(sys.argv):
                inicio = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--duracao" and i + 1 < len(sys.argv):
                duracao = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--fps" and i + 1 < len(sys.argv):
                fps = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--largura" and i + 1 < len(sys.argv):
                largura = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        
        converter_video_para_gif(caminho_video, caminho_saida, inicio, duracao, fps, largura)
        
    elif sys.argv[1] == "--animado":
        if len(sys.argv) < 4:
            print("Erro: Especifique pelo menos o arquivo de saída e uma imagem.")
            return
        
        caminho_saida = sys.argv[2]
        lista_imagens = sys.argv[3:]
        criar_gif_animado(lista_imagens, caminho_saida)
    else:
        caminho_imagem = sys.argv[1]
        caminho_saida = sys.argv[2] if len(sys.argv) > 2 else None
        converter_para_gif(caminho_imagem, caminho_saida)

if __name__ == "__main__":
    main()