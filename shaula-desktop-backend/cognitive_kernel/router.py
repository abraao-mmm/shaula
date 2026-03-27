# backend/cognitive_kernel/router.py
from .state_vector import StateVector

class CognitiveRouter:
    """
    O Lobo Frontal da Shaula. Decide a profundidade do processamento, 
    o tom da resposta e o orçamento de tokens.
    """
    def __init__(self):
        # Pesos para o orçamento dinâmico de tokens
        self.pesos_tokens = {
            "base": 300,
            "reflexao": 800,
            "energia": 400
        }

    def planejar_execucao(self, intent: dict, state: StateVector) -> dict:
        """Avalia a intenção e o estado mental para gerar um plano de ação."""
        
        # 1. Token Budgeter Dinâmico
        # Calcula os tokens com base na necessidade de reflexão e energia disponível
        budget = int(
            self.pesos_tokens["base"] + 
            (state.reflection_pressure * self.pesos_tokens["reflexao"]) + 
            (state.cognitive_energy * self.pesos_tokens["energia"])
        )

        # Plano base por defeito
        plano = {
            "fluxo": "DIRECT_RESPONSE",
            "modulos": ["memory_gateway"], # Sempre consulta a identidade base
            "max_tokens": budget,
            "tom": "analítico_e_amigável"
        }

        # 2. Anti-Rumination Guard (Fadiga alta / Energia baixa)
        # Se a energia estiver abaixo de 25%, corta o processamento pesado
        if state.cognitive_energy < 0.25:
            plano["fluxo"] = "MINIMAL_STABILIZATION"
            plano["max_tokens"] = 150  # Orçamento mínimo de sobrevivência
            plano["tom"] = "gentil_e_breve"
            plano["modulos"] = []      # Desativa RAG e reflexões para poupar energia
            return plano

        # 3. Gatilho de Reflexão Profunda
        if state.reflection_pressure > 0.6:
            plano["fluxo"] = "DEEP_REFLECTION"
            plano["modulos"].extend(["senso_critico", "ruminacao"])
            plano["tom"] = "reflexivo_e_filosófico"
            
        # 4. Gatilho Tático (Contexto ambiental complexo, ex: IDE de código ou Jogo)
        elif state.environmental_complexity > 0.7:
            plano["fluxo"] = "TACTICAL_ANALYSIS"
            plano["tom"] = "focado_e_eficiente"

        # 5. Ajuste Relacional de Tom
        # Se houver muita intimidade e for uma conversa normal, aquece o tom
        if state.relational_intensity > 0.8 and plano["fluxo"] == "DIRECT_RESPONSE":
            plano["tom"] = "íntimo_e_afetivo"

        return plano