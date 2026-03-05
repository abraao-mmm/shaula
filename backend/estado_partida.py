import uuid
from typing import List, Dict

class EstadoPartida:
    """
    Armazena todas as informações acumuladas de uma única partida de Valorant.
    """
    def __init__(self, agente_jogador: str, mapa: str):
        self.id_partida: str = str(uuid.uuid4())
        self.agente_jogador: str = agente_jogador
        self.mapa: str = mapa
        self.composicao_aliada: List[str] = []
        self.composicao_inimiga: List[str] = []
        self.historico_rounds: List[Dict] = []
        self.lado_atual: str = "Indefinido"

    def adicionar_analise_round(self, analise: Dict):
        """Adiciona os dados de um novo round ao histórico."""
        self.historico_rounds.append(analise)
        
    def para_dict(self):
        """Converte o estado atual para um dicionário para fácil visualização."""
        return self.__dict__