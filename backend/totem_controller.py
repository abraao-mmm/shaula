import serial
import time
from rich.console import Console

console = Console()

class TotemController:
    def __init__(self, porta_com='COM5'): # Mude 'COM5' para a porta COM do seu Arduino
        self.porta_com = porta_com # <--- CORREÇÃO 1: Salva a porta como um atributo
        try:
            self.arduino = serial.Serial(port=self.porta_com, baudrate=9600, timeout=1)
            # <--- CORREÇÃO 2: Removemos o console.print daqui ---
        except Exception as e:
            console.print(f"[bold red]Erro ao conectar ao Totem ({self.porta_com}):[/bold red] {e}")
            console.print("O protótipo funcionará sem feedback físico.")
            self.arduino = None

    def _enviar_comando(self, comando: str):
        if self.arduino:
            self.arduino.write(comando.encode())

    def sucesso(self):
        self._enviar_comando('s')

    def erro(self):
        self._enviar_comando('e')

    def ocioso(self):
        self._enviar_comando('o')