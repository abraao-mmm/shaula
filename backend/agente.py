import json
import os
import openai
from typing import Tuple, Optional, Dict
from rich.console import Console

# Importações do Kernel Cognitivo
from .cognitive_kernel.state_vector import StateConsolidator
from .cognitive_kernel.router import CognitiveRouter

# Importações de Estado e Memória
from .estado_agora import EstadoAgora
from .memoria import Memoria
from .personalidade import Personalidade
from .usuario import Usuario
from .humor import Humor
from .processador_cognitivo import ProcessadorCognitivo
from .analisador_de_intencao import identificar_intencao
from .inventario_manager import InventarioManager
from .totem_controller import TotemController
from .banco_de_identidade import BancoDeIdentidade

class AgenteReflexivo:
    def __init__(self, usuario_atual: Usuario, gerenciador, console_log: Console):
        # 1. Atributos de Identidade e Estado
        self.usuario_atual = usuario_atual
        self.gerenciador_de_usuarios = gerenciador
        self.console = console_log
        self.memoria = Memoria()
        self.personalidade = Personalidade()
        self.humor = Humor()
        self.fadiga_cognitiva = 0
        
        # 2. Módulos de Suporte
        self.inventario_manager = InventarioManager()
        self.totem = TotemController()
        self.banco_identidade = BancoDeIdentidade()
        self.processador_cognitivo = ProcessadorCognitivo(self)
        
        # 3. O NOVO CÉREBRO (Cognitive Kernel)
        self.consolidador = StateConsolidator(self)
        self.router = CognitiveRouter()

    def processar_entrada_do_utilizador(self, entrada_usuario: str) -> Tuple[str, str]:
        """Fluxo Principal: Sentir -> Entender -> Decidir -> Agir."""
        
        # A. SENTIR: Consolida o StateVector (Humor, Fadiga, Contexto)
        state_vector = self.consolidador.build()
        self.console.log(f"🧠 [Kernel] Estado Consolidado: {state_vector.as_dict()}")

        # B. ENTENDER: Identifica a intenção via LLM
        intencao = identificar_intencao(entrada_usuario, self.obter_resposta_llm)
        
        # C. DECIDIR: O Router planeja a execução baseada no estado e intenção
        plano = self.router.planejar_execucao(intencao, state_vector)
        
        # D. REGISTRAR: Salva o estado atual na memória de log
        self.memoria.registrar_estado(state_vector.as_dict())

        # E. AGIR: Executa o plano orquestrado
        return self.executar_plano(plano, entrada_usuario)

    def executar_plano(self, plano: dict, entrada_usuario: str) -> Tuple[str, str]:
        """Despacha a execução para o fluxo correto definido pelo Kernel."""
        self.console.log(f"🚀 [Agente] Executando Fluxo: [bold cyan]{plano['fluxo']}[/bold cyan]")
        
        # Feedback visual no Totem
        self._sinalizar_totem_por_fluxo(plano["fluxo"])

        # Recuperação de Contexto de Identidade (RAG)
        contexto_identidade = ""
        if "memory_gateway" in plano["modulos"]:
            contexto_identidade = self.banco_identidade.buscar_contexto_relevante(entrada_usuario)

        # Roteamento de Execução
        if plano["fluxo"] == "DEEP_REFLECTION":
            return self._fluxo_reflexao_profunda(entrada_usuario, contexto_identidade, plano)
        
        elif plano["fluxo"] == "MINIMAL_STABILIZATION":
            return self._fluxo_estabilizacao(plano)
            
        elif plano["fluxo"] == "TACTICAL_ANALYSIS":
            return self._fluxo_tatico(entrada_usuario, contexto_identidade, plano)

        # Padrão: Resposta Direta
        return self._fluxo_conversa_normal(entrada_usuario, contexto_identidade, plano)

    # --- Implementação dos Fluxos Específicos ---

    def _fluxo_estabilizacao(self, plano: dict) -> Tuple[str, str]:
        """Fluxo de baixo custo para quando a fadiga está alta."""
        prompt = (
            f"Você é a Shaula. O Abraão está interagindo, mas sua energia cognitiva está baixa ({self.fadiga_cognitiva}%). "
            "Dê uma resposta muito curta, acolhedora e sugira que vocês conversem mais profundamente depois."
        )
        resposta = self.obter_resposta_llm(prompt, modo="Estabilização", max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "Estabilização Ativada"

    def _fluxo_conversa_normal(self, entrada, contexto, plano) -> Tuple[str, str]:
        """Conversa padrão ancorada na identidade."""
        prompt_persona = self.personalidade.gerar_descricao_persona_dinamica(self.usuario_atual)
        prompt_final = (
            f"{prompt_persona}\n\n"
            f"### CONTEXTO DE IDENTIDADE:\n{contexto}\n\n"
            f"O Abraão disse: '{entrada}'. Responda mantendo seu tom, usando o contexto se necessário."
        )
        resposta = self.obter_resposta_llm(prompt_final, modo="Conversa", max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "Resposta Direta"

    def _fluxo_reflexao_profunda(self, entrada, contexto, plano) -> Tuple[str, str]:
        """Mergulho cognitivo usando Ruminação e Senso Crítico."""
        # Aqui você integraria as chamadas aos seus arquivos de reflexão_profunda.py
        prompt = f"### ANÁLISE PROFUNDA REQUERIDA ###\nContexto: {contexto}\nEntrada: {entrada}"
        resposta = self.obter_resposta_llm(prompt, modo="Reflexão", max_tokens=plano["max_tokens"])
        return self._formata_resposta(resposta.get("conteudo")), "Reflexão Profunda"

    # --- Métodos Auxiliares ---

    def _sinalizar_totem_por_fluxo(self, fluxo: str):
        """Muda a cor do Totem baseado na carga de processamento."""
        if fluxo == "DEEP_REFLECTION":
            self.totem.carregando() # Violeta/Pulsante
        elif fluxo == "MINIMAL_STABILIZATION":
            self.totem.erro() # Alerta de baixa energia
        else:
            self.totem.sucesso() # Verde/Ocioso

    def obter_resposta_llm(self, prompt: str, modo: str = "Criatividade", max_tokens: int = 2048, imagem_base64: str = None) -> Dict:
        """Central de chamadas OpenAI."""
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
            self.console.print(f"[red]Erro API: {e}[/red]")
            return {"tipo": "erro", "conteudo": f"Erro: {e}"}

    def _formata_resposta(self, texto: str) -> str:
        return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"texto_final": texto}})