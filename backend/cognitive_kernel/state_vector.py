# backend/cognitive_kernel/state_vector.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class StateVector:
    cognitive_energy: float
    emotional_load: float
    relational_intensity: float
    environmental_complexity: float
    purpose_alignment: float
    reflection_pressure: float

class StateConsolidator:
    def __init__(self, agente):
        self.agente = agente
        # Pesos calibráveis
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
        relational_intensity = min(self.agente.usuario_atual.peso_afetivo / 10.0, 1.0) #
        
        estado_agora = self.agente.processador_cognitivo.obter_estado_agora() #
        contexto = estado_agora.janela_ativa.lower() if estado_agora else ""
        
        environmental_complexity = self._calc_env_complexity(contexto)
        purpose_alignment = self._calc_purpose(contexto)

        # NOVA FÓRMULA: Energia agora SOMA para permitir reflexão
        reflection_pressure = min(1.0, (
            emotional_load * self.pesos["emocao"] +
            cognitive_energy * self.pesos["energia"] + # Inversão corretiva
            (1.0 - purpose_alignment) * self.pesos["proposito"] +
            relational_intensity * self.pesos["relacional"]
        ))

        return StateVector(
            cognitive_energy, emotional_load, relational_intensity,
            environmental_complexity, purpose_alignment, reflection_pressure
        )

    def _calc_emotional_load(self):
        #
        base = self.agente.humor.intensidade / 10.0
        if self.agente.humor.estado_atual.lower() in ["ansioso", "triste", "conflito"]:
            return base
        return base * 0.5

    def _calc_env_complexity(self, ctx):
        if any(x in ctx for x in ["code", "visual studio", "terminal"]): return 0.8
        if any(x in ctx for x in ["valorant", "game"]): return 0.9 #
        return 0.4

    def _calc_purpose(self, ctx):
        #
        if any(x in ctx for x in ["shaula", "python", "research"]): return 0.9
        return 0.5