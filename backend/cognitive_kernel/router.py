# backend/cognitive_kernel/router.py
from .state_vector import StateVector

class CognitiveRouter:
    def __init__(self):
        # Pesos iniciais que podem ser calibrados no futuro
        self.pesos_tokens = {"base": 300, "reflexao": 800, "energia": 400}

    def planejar_execucao(self, intent: dict, state: StateVector) -> dict:
        # Orçamento adaptativo de tokens
        budget = int(
            self.pesos_tokens["base"] + 
            (state.reflection_pressure * self.pesos_tokens["reflexao"]) + 
            (state.cognitive_energy * self.pesos_tokens["energia"])
        )

        plano = {
            "fluxo": "DIRECT_RESPONSE",
            "modulos": ["memory_gateway"],
            "max_tokens": budget,
            "tom": "analítico"
        }

        # Anti-Rumination Guard (Agora com a regra de fadiga unificada)
        if state.cognitive_energy < 0.25:
            plano["fluxo"] = "MINIMAL_STABILIZATION" # Padronizado
            plano["max_tokens"] = 150
            plano["tom"] = "gentil_breve"
            return plano

        # Decisão de profundidade
        if state.reflection_pressure > 0.6:
            plano["fluxo"] = "DEEP_REFLECTION"
            plano["modulos"].extend(["senso_critico", "ruminacao"]) #
        
        elif state.environmental_complexity > 0.7:
            plano["fluxo"] = "TACTICAL_ANALYSIS" #

        return plano