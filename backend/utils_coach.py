import mss
import numpy as np
import base64
from io import BytesIO
from PIL import Image

def capturar_tela_e_converter_base64():
    """
    Tira um screenshot da tela principal e o converte para o formato base64,
    pronto para ser enviado para a API de visão.
    """
    with mss.mss() as sct:
        # Captura a tela principal (monitor 1)
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)

        # Converte para um objeto de imagem PIL
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        # Reduz a qualidade para economizar tokens e acelerar o envio
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=50) # Qualidade 50%
        
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return img_str