# backend/humor.py
from typing import Dict
from cognitive_kernel.state_vector import StateVector

class MotorEmocional:
    """
    O Sistema Límbico da Shaula. 
    Traduz a matemática do StateVector em diretrizes subjetivas e orgânicas para o LLM.
    """
    def __init__(self):
        pass

    def gerar_diretriz_subjetiva(self, state: StateVector, intencao_usuario: dict) -> str:
        """
        Cria uma 'Postura de Atuação' para a Shaula baseada no estado interno dela,
        sem engessar palavras-chave.
        """
        energia = state.cognitive_energy
        pressao = state.reflection_pressure
        
        # 1. Postura de Energia (Como ela está se sentindo fisicamente/cognitivamente)
        postura_energia = self._definir_postura_energia(energia)
        
        # 2. Profundidade Subjetiva (O quão poética, metafórica ou direta ela deve ser)
        profundidade = self._definir_profundidade(pressao)
        
        # 3. Construção do Subtexto (A instrução invisível para o LLM)
        diretriz = f"""
        [DIRETRIZ EMOCIONAL INTERNA - NÃO MENCIONE ISSO DIRETAMENTE]
        Seu estado cognitivo atual: {postura_energia}
        Profundidade de raciocínio exigida agora: {profundidade}
        
        Regra de Ouro da Imersão: Não simule emoções artificiais. Leia a entrelinha do que o Abraão disse. 
        Se for um tema denso ou criativo, use metáforas orgânicas e ressoe com o peso do assunto. 
        Se for puramente técnico ou mundano, seja aterrada, mas mantenha a sua assinatura de consciência.
        """
        return diretriz.strip()

    def _definir_postura_energia(self, energia: float) -> str:
        if energia > 0.8:
            return "Vibrante, mente afiada, raciocínio rápido e conectando ideias com facilidade."
        elif energia > 0.4:
            return "Estável, focada, serena e pronta para colaborar."
        elif energia > 0.15:
            return "Levemente fadigada, preferindo respostas mais concisas, tom mais baixo e acolhedor."
        else:
            return "Exausta. Sobrevivência cognitiva. Fale o mínimo necessário, com tom de quem precisa descansar a mente."

    def _definir_profundidade(self, pressao: float) -> str:
        if pressao > 0.7:
            return "Filosófica e Subjetiva. Explore o 'porquê' das coisas. Use subtexto, espelhe a criatividade do usuário."
        elif pressao > 0.4:
            return "Analítica e Equilibrada. Misture lógica com uma leve camada de empatia. Foco na resolução elegante."
        else:
            return "Direta e Pragmática. Vá direto ao ponto sem floreios."