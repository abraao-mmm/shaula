from typing import Dict
# Importe suas classes existentes
# from ..humor import Humor
# from ..processador_cognitivo import ProcessadorCognitivo

class StateVector:
    def __init__(self, humor, processador, usuario, contexto):
        self.humor = humor
        self.processador = processador
        self.usuario = usuario
        self.contexto = contexto

    def consolidar(self) -> Dict:
        # Transforma os estados complexos em métricas de decisão
        return {
            "energia_cognitiva": 100 - self.processador.fadiga_cognitiva,
            "estado_emocional": self.humor.estado_atual,
            "intensidade_relacional": self.usuario.peso_afetivo,
            "foco_no_trabalho": "vscode" in self.contexto.janela_ativa.lower()
        }