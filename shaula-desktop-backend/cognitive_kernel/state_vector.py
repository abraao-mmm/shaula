# backend/cognitive_kernel/state_vector.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StateVector:
    cognitive_energy: float
    emotional_load: float
    relational_intensity: float
    environmental_complexity: float
    purpose_alignment: float
    reflection_pressure: float

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__

class StateConsolidator:
    def __init__(self, agente):
        self.agente = agente
        # Pesos calibráveis (Opção B - Preparando para o Feedback Loop)
        self.pesos = {
            "emocao": 0.4,
            "energia": 0.2,
            "proposito": 0.2,
            "relacional": 0.2
        }

    def build(self) -> StateVector:
        # Energia: 1.0 (cheia) a 0.0 (exaurida)
        cognitive_energy = max(0.0, 1.0 - (self.agente.fadiga_cognitiva / 100.0))
        
        emotional_load = self._calc_emotional_load()
        relational_intensity = min(self.agente.usuario_atual.peso_afetivo / 10.0, 1.0) 
        
        # Pega o contexto atual da memória/estado
        estado_agora = self.agente.processador_cognitivo.obter_estado_agora() 
        contexto = estado_agora.janela_ativa.lower() if estado_agora and hasattr(estado_agora, 'janela_ativa') else ""
        
        environmental_complexity = self._calc_env_complexity(contexto)
        purpose_alignment = self._calc_purpose(contexto)

        # A NOVA FÓRMULA: Alta emoção + Energia disponível = Reflexão.
        # Baixa energia impede a pressão de subir, evitando loops de ruminação.
        reflection_pressure = min(1.0, (
            emotional_load * self.pesos["emocao"] +
            cognitive_energy * self.pesos["energia"] + 
            (1.0 - purpose_alignment) * self.pesos["proposito"] +
            relational_intensity * self.pesos["relacional"]
        ))

        return StateVector(
            cognitive_energy=round(cognitive_energy, 3),
            emotional_load=round(emotional_load, 3),
            relational_intensity=round(relational_intensity, 3),
            environmental_complexity=round(environmental_complexity, 3),
            purpose_alignment=round(purpose_alignment, 3),
            reflection_pressure=round(reflection_pressure, 3)
        )

    def _calc_emotional_load(self) -> float:
        base = self.agente.humor.intensidade / 10.0
        # Emoções densas geram mais carga
        if self.agente.humor.estado_atual.lower() in ["ansioso", "triste", "conflito", "tenso"]:
            return base
        return base * 0.5

    def _calc_env_complexity(self, ctx: str) -> float:
        if any(x in ctx for x in ["code", "visual studio", "terminal", "pycharm"]): return 0.8
        if any(x in ctx for x in ["valorant", "game", "partida"]): return 0.9
        if any(x in ctx for x in ["youtube", "netflix", "social"]): return 0.3
        return 0.5

    def _calc_purpose(self, ctx: str) -> float:
        if any(x in ctx for x in ["shaula", "python", "research", "ifmaker"]): return 0.9
        return 0.5