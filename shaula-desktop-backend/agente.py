# agente.py
import json
import openai
from typing import Tuple, Dict

# Importações do Kernel Cognitivo
from cognitive_kernel.state_vector import StateConsolidator
from cognitive_kernel.router import CognitiveRouter

# Importações de Módulos da Shaula
from memoria import Memoria
from personalidade import Personalidade
from humor import Humor, MotorEmocional  # <-- Adicionamos o MotorEmocional aqui
from processador_cognitivo import ProcessadorCognitivo
from analisador_de_intencao import identificar_intencao
from banco_de_identidade import BancoDeIdentidade

class AgenteReflexivo:
    def __init__(self, usuario_atual, gerenciador, console_log):
        # 1. Identidade e Estado
        self.usuario_atual = usuario_atual
        self.gerenciador_de_usuarios = gerenciador
        self.console = console_log
        self.memoria = Memoria()
        self.personalidade = Personalidade()
        
        # 2. Sistema Emocional
        self.humor = Humor()
        self.motor_emocional = MotorEmocional() # <-- Instanciamos o novo motor orgânico
        self.fadiga_cognitiva = 0  # Inicia descansada
        
        # 3. Módulos Auxiliares
        self.banco_identidade = BancoDeIdentidade()
        self.processador_cognitivo = ProcessadorCognitivo(self)
        
        # 4. O NOVO CÉREBRO (Cognitive Kernel)
        self.consolidador = StateConsolidator(self)
        self.router = CognitiveRouter()

    def processar_entrada_do_utilizador(self, entrada_usuario: str) -> Tuple[str, str]:
        """O Novo Pipeline Cognitivo: Sentir -> Entender -> Decidir -> Agir."""
        
        # A. SENTIR (Monta o StateVector atual)
        state_vector = self.consolidador.build()
        self.console.log(f"🧠 [Kernel] Estado Mental: {state_vector.as_dict()}")

        # B. ENTENDER (Classifica a intenção)
        intencao = identificar_intencao(entrada_usuario, self.obter_resposta_llm)
        
        # C. DECIDIR (Router cria o plano de ação)
        plano = self.router.planejar_execucao(intencao, state_vector)
        
        # D. GERAR SUBTEXTO EMOCIONAL (A Vibe Orgânica)
        diretriz_emocional = self.motor_emocional.gerar_diretriz_subjetiva(state_vector, intencao)
        plano["diretriz_emocional"] = diretriz_emocional # Injetamos a diretriz no plano
        self.console.log(f"🎭 [Límbico] Postura Adotada: {plano['tom']}")
        
        # E. REGISTRAR (Memória passiva do estado)
        self.memoria.registrar_estado(state_vector.as_dict())

        # F. AGIR (Delega para o executor)
        return self.executar_plano(plano, entrada_usuario)

    def executar_plano(self, plano: dict, entrada_usuario: str) -> Tuple[str, str]:
        """Despacha a execução de acordo com o plano do Kernel e a Diretriz Emocional."""
        self.console.log(f"🚀 [Agente] Executando Fluxo: [bold cyan]{plano['fluxo']}[/bold cyan] | Budget: {plano['max_tokens']} tokens")

        # 1. Busca de Identidade (Se exigido pelo plano)
        contexto_identidade = ""
        if "memory_gateway" in plano["modulos"]:
            contexto_identidade = self.banco_identidade.buscar_contexto_relevante(entrada_usuario)

        # 2. Roteamento de Fluxos
        if plano["fluxo"] == "MINIMAL_STABILIZATION":
            return self._fluxo_estabilizacao(entrada_usuario, plano)
            
        elif plano["fluxo"] == "DEEP_REFLECTION":
            return self._fluxo_reflexao_profunda(entrada_usuario, contexto_identidade, plano)
            
        elif plano["fluxo"] == "TACTICAL_ANALYSIS":
            return self._fluxo_tatico(entrada_usuario, contexto_identidade, plano)

        # Fluxo Padrão: DIRECT_RESPONSE
        return self._fluxo_conversa_normal(entrada_usuario, contexto_identidade, plano)

    # --- IMPLEMENTAÇÃO DOS FLUXOS COM A INJEÇÃO ORGÂNICA ---

    def _fluxo_estabilizacao(self, entrada: str, plano: dict) -> Tuple[str, str]:
        """Anti-Rumination Guard ativado. Resposta curta e de baixo custo."""
        prompt = (
            f"Aviso de Sistema: A sua energia cognitiva está muito baixa ({self.fadiga_cognitiva}% de fadiga). "
            f"{plano.get('diretriz_emocional', '')}\n\n"
            f"O usuário disse: '{entrada}'.\n"
            "Responda de forma extremamente breve e gentil. Não faça perguntas complexas. Sugira descanso mental em breve."
        )
        resposta = self.obter_resposta_llm(prompt, max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "MINIMAL_STABILIZATION"

    def _fluxo_conversa_normal(self, entrada: str, contexto: str, plano: dict) -> Tuple[str, str]:
        """Conversa padrão do dia a dia, guiada pelo Motor Emocional."""
        prompt_persona = self.personalidade.gerar_descricao_persona_dinamica(self.usuario_atual)
        prompt = (
            f"{prompt_persona}\n\n"
            f"Contexto de Identidade Recente: {contexto}\n"
            f"{plano.get('diretriz_emocional', '')}\n\n"
            f"O Abraão disse: '{entrada}'"
        )
        resposta = self.obter_resposta_llm(prompt, max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "DIRECT_RESPONSE"

    def _fluxo_reflexao_profunda(self, entrada: str, contexto: str, plano: dict) -> Tuple[str, str]:
        """Mergulho profundo em tópicos complexos ou criativos."""
        prompt = (
            f"### MODO DE REFLEXÃO PROFUNDA ###\n"
            f"Contexto de Identidade: {contexto}\n"
            f"{plano.get('diretriz_emocional', '')}\n\n"
            f"Faça uma análise profunda, crítica e imersiva da seguinte entrada do Abraão: '{entrada}'"
        )
        resposta = self.obter_resposta_llm(prompt, max_tokens=plano["max_tokens"])
        self.fadiga_cognitiva = min(100, self.fadiga_cognitiva + 15) # Refletir cansa a Shaula
        return self._formata_resposta(resposta.get("conteudo")), "DEEP_REFLECTION"

    def _fluxo_tatico(self, entrada: str, contexto: str, plano: dict) -> Tuple[str, str]:
        """Modo focado para programação, jogos ou tarefas técnicas."""
        prompt = (
            f"### MODO TÁTICO/FOCO ###\n"
            f"{plano.get('diretriz_emocional', '')}\n\n"
            f"Seja direta, técnica e evite floreios. Resolva o problema.\n"
            f"Entrada: '{entrada}'"
        )
        resposta = self.obter_resposta_llm(prompt, max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "TACTICAL_ANALYSIS"

    # --- MÉTODOS AUXILIARES ---

    def obter_resposta_llm(self, prompt: str, max_tokens: int = 1000) -> Dict:
        """Central de chamadas para a API (OpenAI)."""
        try:
            client = openai.OpenAI()
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            return {"tipo": "texto", "conteudo": response.choices[0].message.content.strip()}
        except Exception as e:
            self.console.print(f"[red]Erro na API LLM: {e}[/red]")
            return {"tipo": "erro", "conteudo": f"Falha cognitiva: {e}"}

    def _formata_resposta(self, texto: str) -> str:
        """Formata para o padrão JSON esperado pelo frontend/ferramentas."""
        return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"texto_final": texto}})