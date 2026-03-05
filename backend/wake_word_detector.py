# backend/wake_word_detector.py (VERSÃO CORRIGIDA FINAL)

import os
import struct
import pyaudio
import pvporcupine
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner

console = Console()
load_dotenv()

def detectar_wake_word() -> bool:
    """
    Ouve continuamente o microfone e retorna True quando a palavra "Shaula" é detectada.
    """
    access_key = os.getenv("PICOVOICE_ACCESS_KEY")
    if not access_key:
        console.print("[bold red]Erro: PICOVOICE_ACCESS_KEY não encontrada no arquivo .env[/bold red]")
        return False

    pa = None
    stream = None
    porcupine = None
    
    try:
        # --- INÍCIO DA CORREÇÃO ---
        # Agora, procuramos os DOIS arquivos na pasta principal do projeto.
        
        model_path = 'porcupine_params_pt.pv'
        keyword_path = 'Laboratório_pt_windows_v3_0_0.ppn' 

        # Verifica se os arquivos realmente existem antes de tentar carregar
        if not os.path.exists(model_path) or not os.path.exists(keyword_path):
            console.print(f"[bold red]Erro: Arquivos de modelo não encontrados![/bold red]")
            console.print(f"Verifique se '{model_path}' e '{keyword_path}' estão na pasta principal do projeto.")
            return False
        # --- FIM DA CORREÇÃO ---

        porcupine = pvporcupine.create(
            access_key=access_key,
            model_path=model_path,
            keyword_paths=[keyword_path]
        )

        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        spinner = Spinner("dots", text=" [dim]Aguardando wake word ('Laboratório')...[/dim]")
        with console.status(spinner) as status:
            while True:
                pcm = stream.read(porcupine.frame_length)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    console.print(Panel("✨ Wake Word 'Laboratório' detectado!", title="[bold green]Atenção[/bold green]", border_style="green"))
                    return True

    except Exception as e:
        console.print(f"[bold red]Erro no detector de wake word: {e}[/bold red]")
        return False
    finally:
        if stream is not None:
            stream.close()
        if pa is not None:
            pa.terminate()
        if porcupine is not None:
            porcupine.delete()