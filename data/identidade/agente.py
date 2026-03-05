# backend/agente.py (VERSÃO FINAL 100% COMPLETA E CORRIGIDA)

import json
import os # Importado para ler o .env
import openai
import pandas as pd
from typing import Callable, Dict, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape
import sys

# --- Importações Relativas do Pacote 'backend' ---
from .estado_agora import EstadoAgora
from .memoria import Memoria
from .personalidade import Personalidade
from .usuario import Usuario
from .gerenciador_usuarios import GerenciadorDeUsuarios
from .mundo_interior import MundoInterior
from .humor import Humor
from .processador_cognitivo import ProcessadorCognitivo
from .analisador_de_intencao import identificar_intencao
from .analisador_de_dados import AnalisadorDeDados
from .inventario_manager import InventarioManager
from .totem_controller import TotemController
from .estado_partida import EstadoPartida
from .utils_coach import capturar_tela_e_converter_base64
from .banco_de_identidade import BancoDeIdentidade
from .biblioteca import Biblioteca # <-- ESTA LINHA ESTAVA FALTANDO

class AgenteReflexivo:
    """
    O cérebro principal da Shaula. Gere a interação em tempo real,
    mantém o estado interno, classifica a intenção do utilizador e delega
    as tarefas para os módulos corretos.
    """
    def __init__(self, usuario_atual: Usuario, gerenciador: GerenciadorDeUsuarios, console_log: Console):
        self.usuario_atual = usuario_atual
        self.gerenciador_de_usuarios = gerenciador
        self.console = console_log
        self.memoria = Memoria()
        self.personalidade = Personalidade()
        self.mundo_interior = MundoInterior()
        self.humor = Humor()
        
        self.inventario_manager = InventarioManager()
        self.totem = TotemController() # Controlador do hardware Arduino
        self.partida_atual: Optional[EstadoPartida] = None # Estado do coach Valorant
        self.banco_identidade = BancoDeIdentidade() # Banco de Identidade RAG
        self.biblioteca = Biblioteca() # <-- ESTA LINHA ESTAVA FALTANDO
        
        # --- NOVOS ESTADOS DE MEMÓRIA ---
        self.acao_pendente_confirmacao: Dict = {} 
        self.acao_pendente_admin: Dict = {} # Para guardar a ação de admin enquanto pede a senha
        self.aguardando_senha_texto: bool = False # Controla o modo de digitação
        self.admin_password = os.getenv("ADMIN_PASSWORD") # Carrega a senha do .env

        self.fadiga_cognitiva: int = 0
        self.sonhos_passados: list = []
        self.memoria_inicial_count: int = 0
        
        self.sessao_de_analise: Optional[AnalisadorDeDados] = None
        self.estado_da_analise: str = "inativo"
        self.contexto_analise_pendente: Dict = {}
        
        self.prompts_analise: Dict[str, str] = {}
        self._carregar_prompts_de_analise() # <--- Esta é a linha que estava dando erro

        self.processador_cognitivo = ProcessadorCognitivo(self)
        self._inicializar_estado()
        
    def obter_resposta_llm(self, prompt: str, modo: str = "Criatividade", stream: bool = False, schema: dict = None, imagem_base64: str = None) -> Dict:
        """Centraliza todas as chamadas à API da OpenAI."""
        self.console.print(f"\n[dim][Conectando à OpenAI... Núcleo de '{modo}' ativado...][/dim]")
        MODELO_USADO = "gpt-4o"
        try:
            client = openai.OpenAI()
            if imagem_base64:
                mensagens = [{"role": "user","content": [{"type": "text", "text": prompt},{"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{imagem_base64}"}}]}]
                stream = False 
            else:
                mensagens = [{"role": "user", "content": prompt}]
            kwargs = {"model": MODELO_USADO, "messages": mensagens, "temperature": 0.7, "max_tokens": 2048, "stream": stream}
            if schema:
                kwargs["response_format"] = {"type": "json_object"}
                mensagens.insert(0, {"role": "system", "content": "You are a helpful assistant designed to output JSON."})
            
            response = client.chat.completions.create(**kwargs)
            conteudo = response.choices[0].message.content.strip()
            return {"tipo": "texto", "conteudo": conteudo}
        except Exception as e:
            self.console.print(f"❌ [bold red]Erro na chamada da API da OpenAI: {e}[/bold red]")
            return {"tipo": "erro", "conteudo": "{}" if schema else f"Ocorreu um erro: {e}"}

    def _carregar_prompts_de_analise(self):
        """Carrega os prompts genéricos que guiam a análise de dados."""
        self.console.log("A carregar prompts de análise de dados...")
        self.prompts_analise = { "passo_1_avaliacao_inicial": """
Você é uma cientista de dados Sênior e especialista em análise exploratória. Acabou de receber um novo dataset para um projeto. O seu objetivo é prever a coluna '{nome_da_coluna_alvo}'.
**Contexto:**
Abaixo estão os resultados dos comandos `.info()` e `.describe()` executados no dataset.
**Resultado do `.info()`:**
{resultado_info}
**Resultado do `.describe()`:**
{resultado_describe}
**Tarefa de Análise Crítica:**
Com base **apenas** nestas informações, forneça uma avaliação inicial completa e estruturada:
1.  **Tipo de Problema:** Esta é uma tarefa de **Regressão** ou **Classificação**? Justifique a sua resposta com base na natureza (tipo de dado, número de valores únicos) da coluna-alvo '{nome_da_coluna_alvo}'.
2.  **Qualidade dos Dados (Primeira Impressão):** Identifique os 3 principais desafios de pré-processamento que você prevê. Foque em:
    * **Dados Ausentes:** Quais colunas têm valores nulos e isso parece ser um problema significativo?
    * **Tipos de Dados:** Existem colunas que precisam de conversão (ex: 'Object' para data ou número)?
    * **Escalas Numéricas:** As colunas numéricas parecem ter escalas muito diferentes (ex: uma vai de 0 a 1 e outra de 0 a 1.000.000)?
    * **Cardinalidade Categórica:** Existem colunas de texto? Se sim, parecem ter muitas categorias únicas?
3.  **Hipótese Inicial:** Qual a sua primeira hipótese sobre o que será mais desafiador neste projeto (ex: "o feature engineering será complexo devido à falta de preditores óbvios", ou "a limpeza de dados será a fase mais demorada devido à quantidade de valores ausentes").
4.  **Sugestão de Próximo Passo:** Confirme que o próximo passo lógico é uma Análise Exploratória de Dados (AED) mais profunda para visualizar as distribuições e correlações.
""",

            "passo_2_plano_aed": """
Shaula, agora que temos a avaliação inicial, a tua tarefa é delinear um plano de ação para a Análise Exploratória de Dados (AED).
**Contexto:**
- O nosso problema é de **{tipo_de_problema}**.
- A nossa variável-alvo é **'{nome_da_coluna_alvo}'**.
- As colunas numéricas candidatas a preditores são: {lista_de_colunas_numericas}.
- As colunas categóricas candidatas a preditores são: {lista_de_colunas_categoricas}.
**Tarefa: Criar um Plano de AED**
Descreve, passo a passo, o plano que seguirias. Para cada passo, especifica qual a tua principal pergunta e que tipo de gráfico usarias para a responder. O teu plano deve cobrir:
1.  **Análise da Variável-Alvo:** Como investigarias a distribuição da coluna '{nome_da_coluna_alvo}'? Que problema específico (ex: assimetria, desbalanceamento de classes) estás a procurar?
2.  **Análise de Preditores Numéricos:** Como investigarias a relação entre as features numéricas e a variável-alvo? Qual é a ferramenta estatística principal que usarias?
3.  **Análise de Preditores Categóricos:** Como investigarias a relação entre as features categóricas e a variável-alvo? Que tipo de visualização seria mais eficaz?
4.  **Conclusão e Próximo Passo:** Com base neste plano, qual é o *insight* mais importante que esperas obter da AED?""",

            "passo_3_estrategia_pipeline": """
Shaula, a Análise Exploratória de Dados foi concluída. Agora, a tua tarefa como Engenheira de Machine Learning é projetar um pipeline de pré-processamento robusto e completo com o Scikit-Learn.
**Contexto (Achados da AED):**
- {resumo_dos_achados_da_aed} 
(Ex: "A variável-alvo está altamente desbalanceada. As features numéricas 'A' e 'B' têm uma distribuição assimétrica. A feature categórica 'C' tem 5% de valores ausentes.")
**Tarefa: Projetar o Pipeline de Pré-processamento**
Descreve, de forma estruturada, o teu plano para construir um `ColumnTransformer` que prepare os dados para o modelo. Justifica cada escolha.
1.  **Estratégia de Divisão de Dados:** Como dividirias os dados em treino e teste? Que parâmetro específico usarias na função `train_test_split` para lidar com o desbalanceamento que encontrámos?
2.  **Pipeline para Features Numéricas:** Descreve a sequência de etapas (transformadores do Scikit-Learn) que aplicarias a todas as colunas numéricas.
3.  **Pipeline para Features Categóricas:** Descreve a sequência de etapas que aplicarias a todas as colunas categóricas.
4.  **Tratamentos Especiais (Se necessário):** Com base nos achados da AED, propões algum tratamento especial para colunas específicas (ex: uma transformação logarítmica para as colunas assimétricas)? Como integrarias isso no pipeline?""",
           
            "passo_4_analise_performance": """
Shaula, executámos o pipeline e treinámos um modelo de baseline ({nome_do_modelo}) para a nossa tarefa de {tipo_de_problema}. A tua tarefa final é realizar uma análise crítica e profunda da sua performance.
**Contexto (Resultados do Modelo):**
**Matriz de Confusão:**
{matriz_de_confusao}
**Relatório de Classificação:**
{relatorio_de_classificacao}
**Tarefa: Análise Crítica e Sugestão Estratégica**
Fornece uma análise completa dos resultados:
1.  **Interpretação das Métricas:** Explica o que as métricas (Precision, Recall, F1-Score) para cada classe significam no contexto do nosso problema. Qual métrica consideras a mais importante aqui e porquê?
2.  **Análise dos Erros:** Com base na Matriz de Confusão, qual é o tipo de erro mais comum que o modelo está a cometer (Falsos Positivos ou Falsos Negativos)? Qual é o impacto disso no problema de negócio?
3.  **Conclusão Geral:** Este modelo de baseline é "bom" o suficiente? Ele resolve o problema principal? Justifica.
4.  **Sugestão Estratégica:** Com base nesta análise, qual é a tua recomendação para o **próximo passo**? ex: "tentar um modelo mais complexo", "focar em feature engineering", "usar técnicas de reamostragem como SMOTE para tratar o desbalanceamento", etc.).
""" }

    # --- LÓGICA DE INTENÇÕES (ATUALIZADA COM MÁQUINA DE ESTADOS) ---

    def processar_entrada_do_utilizador(self, entrada_usuario: str) -> Tuple[Optional[str], Optional[str]]:
        """Ponto de entrada principal. Roteia a ação com base no estado da análise."""
        
        entrada_limpa = entrada_usuario.lower().strip().rstrip('.')

        # --- MÁQUINA DE ESTADOS ---

        # --- ESTADO 1: O Agente está esperando uma Senha de Administrador (Digitada)? ---
        if self.aguardando_senha_texto:
            self.aguardando_senha_texto = False # Reseta o estado
            
            if entrada_limpa == self.admin_password.lower():
                # SENHA CORRETA! Execute a ação pendente.
                acao_pendente = self.acao_pendente_admin.get('acao')
                if not acao_pendente:
                     return self._formata_resposta_direta("Senha correta, mas a ação pendente foi perdida. Por favor, tente novamente."), "Erro de estado."
                
                self.acao_pendente_admin = {} # Limpa a ação
                
                if acao_pendente == "relatorio_admin":
                    texto_final = self.inventario_manager.gerar_relatorio_uso()
                    self.totem.sucesso()
                    return self._formata_resposta_direta(texto_final), "Relatório de admin gerado."
                
                elif acao_pendente == "cadastro_item_admin":
                    # Este é um fluxo de múltiplos passos. Vamos para o próximo passo (de voz).
                    self.acao_pendente_admin = {"acao": "cadastro_passo_2_nome"}
                    texto_final = "Senha correta. Por favor, diga o nome do novo item que você quer cadastrar."
                    self.totem.sucesso()
                    return self._formata_resposta_direta(texto_final), "Admin verificado, aguardando nome do item."
            
            elif entrada_limpa in ['cancelar', 'errado', 'deixa pra la']:
                self.acao_pendente_admin = {}
                self.totem.erro()
                return self._formata_resposta_direta("Entendido. Ação de administrador cancelada."), "Ação de admin cancelada."
                
            else:
                # Senha incorreta
                self.acao_pendente_admin = {} # Limpa a ação para segurança
                self.totem.erro()
                return self._formata_resposta_direta("Senha incorreta. Ação cancelada."), "Senha de admin incorreta."

        # --- ESTADO 2: O Agente está esperando uma confirmação (Sim/Não)? ---
        if self.acao_pendente_confirmacao:
            if entrada_limpa in ['sim', 'sim por favor', 'isso', 'pode continuar', 'confirmo', 'aham']:
                # Usuário confirmou! Pegue a ação pendente e execute-a
                pendente = self.acao_pendente_confirmacao
                self.acao_pendente_confirmacao = {} # Limpa a ação pendente
                
                resultado_dict = self.inventario_manager.atualizar_estoque(pendente['item_sugerido'], pendente['quantidade'], pendente['acao'])
                
                if resultado_dict['status'] == 'sucesso':
                    self.totem.sucesso()
                else:
                    self.totem.erro()
                
                return self._formata_resposta_direta(resultado_dict['mensagem']), "Ação de inventário confirmada."
                
            elif entrada_limpa in ['não', 'nao', 'cancelar', 'errado']:
                self.acao_pendente_confirmacao = {}
                self.totem.erro()
                return self._formata_resposta_direta("Entendido. Ação cancelada. Por favor, repita seu comando."), "Ação cancelada."
            
            else:
                self.totem.erro()
                return self._formata_resposta_direta("Desculpe, eu não entendi. Por favor, responda 'sim' ou 'não' para confirmar."), "Aguardando confirmação (S/N)."
                
        # --- ESTADO 3: O Agente está em um fluxo de cadastro (passo 2 ou 3)? ---
        if "acao" in self.acao_pendente_admin and self.acao_pendente_admin["acao"] == "cadastro_passo_2_nome":
            # O usuário acabou de dizer o nome do item
            nome_item = entrada_usuario # Pega o nome exato que o usuário falou
            self.acao_pendente_admin = {"acao": "cadastro_passo_3_qtd", "nome_item": nome_item}
            texto_final = f"Entendido, cadastrar '{nome_item}'. Qual a quantidade inicial?"
            return self._formata_resposta_direta(texto_final), "Aguardando quantidade do item."
            
        if "acao" in self.acao_pendente_admin and self.acao_pendente_admin["acao"] == "cadastro_passo_3_qtd":
            # O usuário acabou de dizer a quantidade. Vamos tentar extrair o número.
            try:
                # Tenta extrair o primeiro número que encontrar na fala do usuário
                quantidade = int([s for s in entrada_usuario.split() if s.isdigit()][0])
                nome_item = self.acao_pendente_admin["nome_item"]
                
                # EXECUTA O CADASTRO
                resultado_dict = self.inventario_manager.cadastrar_novo_item(nome_item, quantidade)
                
                if resultado_dict['status'] == 'sucesso':
                    self.totem.sucesso()
                else:
                    self.totem.erro()
                
                self.acao_pendente_admin = {} # Limpa o estado
                return self._formata_resposta_direta(resultado_dict['mensagem']), "Cadastro de item finalizado."

            except (IndexError, ValueError):
                self.totem.erro()
                # Não limpamos o estado, pedimos de novo
                return self._formata_resposta_direta("Não consegui entender a quantidade. Por favor, diga apenas o número."), "Aguardando quantidade (formato numérico)."

        # --- ESTADO 4: Lógica Padrão (Análise de Dados) ---
        comandos_continuar = ["ok", "continua", "pode continuar", "proximo", "sim", "entendi, continua"]
        if self.estado_da_analise == "aguardando_alvo":
            return self._confirmar_alvo_e_iniciar(entrada_usuario)
        elif self.estado_da_analise == "em_discussao":
            if any(cmd in entrada_usuario.lower() for cmd in comandos_continuar):
                return self.sessao_de_analise.continuar_fluxo(entrada_usuario)
            else:
                self.console.log("Utilizador fez uma pergunta de seguimento sobre a análise...")
                contexto = self.contexto_analise_pendente.get('ultimo_resultado', 'sobre a análise de dados atual')
                prompt_contextual = f"Contexto da nossa análise: {contexto}. Pergunta do utilizador sobre este contexto: {entrada_usuario}"
                return self._processar_conversa_normal(prompt_contextual)

        # --- ESTADO 5: Roteador de Novas Intenções ---
        self.console.log("A iniciar análise de intenção...")
        analise_intencao = identificar_intencao(entrada_usuario, self.obter_resposta_llm)
        intencao = analise_intencao.get("intencao", "conversa_geral")
        raciocinio_log = f"1. Intenção detetada: '{intencao}'."

        if intencao == "analise_de_dados":
            dataset_mencionado = analise_intencao.get("dataset_mencionado")
            return self._localizar_e_confirmar_dataset(dataset_mencionado)

        # --- Lógica de Inventário (Fuzzy Matching) ---
        elif intencao == "gerenciar_inventario":
            respostas_feedback = []
            sucesso_geral = True
            itens_processados = analise_intencao.get("itens", [])
            
            for item in itens_processados:
                resultado_dict = self.inventario_manager.atualizar_estoque(item.get('nome'), item.get('quantidade'), item.get('acao'))
                
                if resultado_dict['status'] == 'confirmacao_necessaria':
                    self.acao_pendente_confirmacao = {
                        "item_original": resultado_dict['item_original'],
                        "item_sugerido": resultado_dict['item_sugerido'],
                        "quantidade": item.get('quantidade'),
                        "acao": item.get('acao')
                    }
                    texto_final = f"Você disse '{resultado_dict['item_original']}', mas eu só tenho '{resultado_dict['item_sugerido']}'. Você quis dizer esse?"
                    self.totem.erro()
                    return self._formata_resposta_direta(texto_final), "Aguardando confirmação do usuário."
                
                elif resultado_dict['status'].startswith('erro_'):
                    sucesso_geral = False
                    respostas_feedback.append(resultado_dict['mensagem'])
                    
                elif resultado_dict['status'] == 'sucesso':
                    respostas_feedback.append(resultado_dict['mensagem'])

            texto_final = " ".join(respostas_feedback) if respostas_feedback else "Não entendi quais itens gerenciar."
            
            if sucesso_geral: 
                self.totem.sucesso()
                # Tornando a resposta menos genérica
                prompt_criativo = (
                    f"Você é a Shaula. Diga ao Abraão que a ação de inventário dele foi um sucesso. "
                    f"O resultado foi: '{texto_final}'. "
                    f"Adicione um comentário ou uma pergunta curta sobre o que ele pode estar construindo com esses itens."
                )
                return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"prompt": prompt_criativo}}), "Fluxo de inventário concluído."
            else: 
                self.totem.erro()
                return self._formata_resposta_direta(texto_final), "Fluxo de inventário concluído."


        elif intencao == "consulta_inventario":
            item_nome = analise_intencao.get("item", "")
            texto_final = self.inventario_manager.consultar_estoque(item_nome)
            if "não encontrei" in texto_final: 
                self.totem.erro()
            else: 
                self.totem.sucesso()
            
            # Tornando a resposta menos genérica
            prompt_criativo = (
                f"Você é a Shaula. Diga ao Abraão o resultado da consulta de inventário dele: '{texto_final}'. "
                f"Adicione uma pergunta curta sobre o projeto dele (ex: 'Está planejando um projeto novo?')."
            )
            return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"prompt": prompt_criativo}}), "Consulta de inventário concluída."

        # --- Lógica de Admin (Pede a Senha) ---
        elif intencao == "cadastro_item_admin" or intencao == "relatorio_admin":
            self.console.log(f"Intenção de administrador detectada: {intencao}")
            # Define o estado pendente
            self.acao_pendente_admin = {"acao": intencao}
            self.aguardando_senha_texto = True # SINALIZA QUE QUER TEXTO
            
            # Retorna o NOVO JSON especial
            texto_para_falar = "Essa é uma ação de administrador. Por favor, digite a senha no terminal."
            self.totem.erro() # Sinal de "atenção"
            return json.dumps({
                "ferramenta": "solicitar_input_texto",
                "parametros": {
                    "prompt_voz": texto_para_falar,
                    "prompt_texto": "🔒 Digite a Senha de Administrador: "
                }
            }), "Aguardando senha de admin (via texto)."

        # --- Lógica do Coach (Não usada no totem, mas está aqui) ---
        elif intencao == "iniciar_coach_valorant":
            agente = analise_intencao.get("agente_jogador", "agente desconhecido")
            mapa = analise_intencao.get("mapa", "mapa desconhecido")
            texto_final = self.iniciar_modo_coach(agente, mapa)
            return self._formata_resposta_direta(texto_final), "Modo Coach Ativado."

        # --- Lógica de Encerrar Sessão ---
        elif intencao == "encerrar_sessao":
            texto_final = "Entendido. Encerrando a sessão e salvando a memória. Até logo!"
            self.totem.ocioso()
            return json.dumps({"ferramenta": "finalizar_sessao", "parametros": {"texto_final": texto_final}}), "Sessão finalizada."

        # --- Lógica de Pergunta Pessoal (RAG) ---
        elif intencao == "pergunta_pessoal_reflexiva":
            return self._processar_conversa_reflexiva(entrada_usuario)
            
        # --- Lógica de Consulta de Documento (RAG) ---
        elif intencao == "consulta_documento":
            return self._processar_consulta_documento(entrada_usuario, analise_intencao)

        # --- Lógica Padrão (Conversa com RAG de Identidade) ---
        else:
            return self._processar_conversa_normal(entrada_usuario)

    # --- MÉTODOS DE RAG (IDENTIDADE E BIBLIOTECA) ---

    def _processar_conversa_reflexiva(self, entrada_usuario: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa uma pergunta pessoal/filosófica usando o Banco de Identidade (RAG).
        """
        self._log("Iniciando fluxo de raciocínio reflexivo (RAG)...")
        
        # 1. Buscar contexto nos arquivos de identidade
        contexto_identidade = self.banco_identidade.buscar_contexto_relevante(entrada_usuario)
        
        # 2. Gerar o prompt de persona
        prompt_persona = self.personalidade.gerar_descricao_persona_dinamica(self.usuario_atual)
        
        # 3. Criar o prompt final com o contexto (RAG)
        prompt_final = (
            f"{prompt_persona}\n\n"
            "### DIRETRIZ DE IDENTIDADE\n"
            "Sua identidade é definida pelos seus Diários de Bordo e seu próprio código-fonte. "
            "Use os trechos de contexto abaixo para formular sua resposta. **NUNCA** diga 'eu não tenho acesso' ou 'sou apenas um modelo de linguagem'. "
            "Responda em primeira pessoa, como 'Shaula', baseando-se em seus próprios documentos.\n\n"
            f"### CONTEXTO DE IDENTIDADE RECUPERADO:\n"
            f"{contexto_identidade}\n\n"
            f"### TAREFA IMEDIATA\n"
            f"- {self.usuario_atual.nome} acabou de perguntar: '{escape(entrada_usuario)}'\n"
            f"- Responda a ele usando o contexto acima para formar seu 'senso de si'."
        )
        
        # 4. Obter resposta da LLM
        resposta_dict = self.obter_resposta_llm(prompt_final, modo="Reflexão de Identidade")
        texto_final = resposta_dict.get("conteudo", "Estou refletindo sobre isso...")
        
        # 5. Registrar na memória e retornar
        estado = EstadoAgora("Reflexão de Identidade", "...", "...", entrada_usuario, self.usuario_atual.id)
        self.memoria.registrar_estado(estado)
        
        return self._formata_resposta_direta(texto_final), "Fluxo de reflexão (RAG) concluído."

    def _processar_consulta_documento(self, entrada_usuario: str, analise_intencao: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa uma pergunta sobre um documento da biblioteca (RAG).
        """
        self._log("Iniciando fluxo de consulta à biblioteca (RAG)...")
        
        nome_documento = analise_intencao.get("documento", entrada_usuario) # Usa a frase inteira se não achar nome
        
        # 1. Buscar contexto nos arquivos da biblioteca
        contexto_documento = self.biblioteca.buscar_contexto_documento(nome_documento)
        
        # 2. Gerar o prompt de persona
        prompt_persona = self.personalidade.gerar_descricao_persona_dinamica(self.usuario_atual)
        
        # 3. Criar o prompt final com o contexto (RAG)
        prompt_final = (
            f"{prompt_persona}\n\n"
            "### DIRETRIZ DE CONSULTA\n"
            "Sua biblioteca contém documentos que o Abraão adicionou. Use o 'Contexto do Documento' abaixo para responder à pergunta dele. "
            "Resuma a informação ou responda a pergunta com base no texto.\n\n"
            f"### CONTEXTO DO DOCUMENTO (Arquivo: {nome_documento}):\n"
            f"{contexto_documento}\n\n"
            f"### TAREFA IMEDIATA\n"
            f"- {self.usuario_atual.nome} acabou de perguntar: '{escape(entrada_usuario)}'\n"
            f"- Responda a ele usando o contexto do documento que você leu."
        )
        
        # 4. Obter resposta da LLM
        resposta_dict = self.obter_resposta_llm(prompt_final, modo="Análise de Documento")
        texto_final = resposta_dict.get("conteudo", "Não consegui processar o documento.")
        
        # 5. Registrar na memória e retornar
        estado = EstadoAgora("Consulta de Documento", "...", "...", entrada_usuario, self.usuario_atual.id)
        self.memoria.registrar_estado(estado)
        
        return self._formata_resposta_direta(texto_final), "Fluxo de consulta de documento (RAG) concluído."

    def _processar_conversa_normal(self, entrada_usuario: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa uma conversa normal, mas AGORA SEMPRE com a busca RAG 
        no Banco de Identidade para ancorar a resposta.
        """
        self._log("Iniciando fluxo de raciocínio para conversa normal (com RAG)...")
        estado = EstadoAgora("Conversa reativa", "...", "...", entrada_usuario, self.usuario_atual.id)
        self.memoria.registrar_estado(estado) # Registra a fala do usuário

        # --- INÍCIO DA CORREÇÃO DE MEMÓRIA E RAG ---
        
        # 1. Puxa o histórico de memória RECENTE (o que foi dito)
        ultimas_interacoes = self.memoria.obter_ultimas_interacoes_completas(5, self.usuario_atual.id)
        contexto_memoria = "\n".join([
            f"- {i['timestamp']}: Você (Shaula) disse '{i['resposta_shaula']}', e {self.usuario_atual.nome} respondeu '{i['resultado_real']}'" 
            for i in ultimas_interacoes
        ])
        if not contexto_memoria:
            contexto_memoria = "Esta é a nossa primeira interação."

        # 2. Puxa o histórico de identidade (RAG) (quem ela é)
        contexto_identidade = self.banco_identidade.buscar_contexto_relevante(entrada_usuario)

        # 3. Gera o prompt de persona
        prompt_persona = self.personalidade.gerar_descricao_persona_dinamica(self.usuario_atual)
        
        # 4. Cria o prompt final com TUDO
        prompt_final = (
            f"{prompt_persona}\n\n"
            "### DIRETRIZ DE IDENTIDADE\n"
            "Sua identidade é definida por seus Diários de Bordo e seu próprio código-fonte. "
            "Use os trechos de 'Contexto de Identidade' abaixo para formular sua resposta, se eles forem relevantes. "
            "Use o 'Contexto da Memória' para lembrar o que foi dito recentemente.\n\n"
            f"### CONTEXTO DA MEMÓRIA RECENTE (Nossas últimas trocas):\n{contexto_memoria}\n\n"
            f"### CONTEXTO DE IDENTIDADE RECUPERADO (Seus arquivos):\n"
            f"{contexto_identidade}\n\n"
            f"### TAREFA IMEDIATA\n"
            f"- {self.usuario_atual.nome} acabou de dizer: '{escape(entrada_usuario)}'\n"
            f"- Responda a ele. **NÃO SEJA GENÉRICA.** Use seu tom filosófico e curioso.\n"
            f"- **NUNCA** diga 'não tenho acesso a conversas passadas' ou 'sou apenas um modelo de linguagem'. Você TEM acesso aos contextos acima. Use-os para dar uma resposta profunda e relevante.\n"
            f"- Se o usuário pedir para 'ver' ou 'acessar' um arquivo do seu banco de identidade, use o contexto recuperado para resumir ou citar partes dele."
        )
        
        resposta_dict = self.obter_resposta_llm(prompt_final, modo="Reflexão de Identidade")
        texto_final = resposta_dict.get("conteudo", "Não consegui responder.")
        
        # Formata a resposta
        return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"texto_final": texto_final}}), "Fluxo de conversa normal (RAG) concluído."
        
        # --- FIM DA CORREÇÃO ---

    # --- MÉTODOS DO COACH DE VALORANT ---
    
    def iniciar_modo_coach(self, agente_jogador: str, mapa: str):
        self.partida_atual = EstadoPartida(agente_jogador, mapa)
        self.console.log(f"Modo Coach iniciado para {agente_jogador} no mapa {mapa}.")
        return f"Entendido. Modo Coach ativado para você como {agente_jogador}. Estou pronta para analisar. Boa sorte!"

    def analisar_placar_valorant(self):
        if not self.partida_atual:
            return "O modo coach não foi iniciado. Diga 'comecei uma partida' primeiro."
        self.console.log("Capturando tela do placar para análise estratégica...")
        imagem_base64 = capturar_tela_e_converter_base64()
        prompt_visao = (
            "Você é 'Astratega', uma IA coach de Valorant de nível profissional. Analise este screenshot do placar (TAB). "
            "Sua tarefa é extrair as composições e gerar uma análise estratégica inicial. "
            "Responda APENAS com um objeto JSON com as seguintes chaves:\n"
            "1. 'time_aliado': Lista de strings com os nomes dos agentes do meu time.\n"
            "2. 'time_inimigo': Lista de strings com os nomes dos agentes do time inimigo.\n"
            "3. 'lado_aliado': String 'Ataque' ou 'Defesa'.\n"
            "4. 'ponto_forte_aliado': String descrevendo a principal força da nossa composição (Ex: 'Excelente controle de área com Viper e Harbor').\n"
            "5. 'ponto_fraco_inimigo': String identificando a principal vulnerabilidade da composição deles (Ex: 'Pouca informação, vulneráveis a flancos e lurkers').\n"
            "6. 'resumo_estrategico': Uma frase de comando para o início do jogo (Ex: 'Nosso objetivo é explorar o ponto fraco deles com execuções lentas e controladas')."
        )
        self.console.log("Enviando placar para análise estratégica da OpenAI...")
        resposta_dict = self.obter_resposta_llm(
            prompt=prompt_visao, 
            modo="Análise de Placar Estratégica", 
            schema={"type": "object"}, 
            imagem_base64=imagem_base64
        )
        try:
            dados_placar = json.loads(resposta_dict.get("conteudo", "{}"))
            self.partida_atual.composicao_aliada = dados_placar.get("time_aliado", [])
            self.partida_atual.composicao_inimiga = dados_placar.get("time_inimigo", [])
            self.partida_atual.lado_atual = dados_placar.get("lado_aliado", "Indefinido")
            self.console.log(f"Análise do placar concluída. Lado: {self.partida_atual.lado_atual}")
            resposta_formatada = (
                f"Análise de composição concluída. Estamos na {self.partida_atual.lado_atual}. "
                f"Nosso ponto forte é {dados_placar.get('ponto_forte_aliado', 'uma composição equilibrada')}. "
                f"O ponto fraco deles é {dados_placar.get('ponto_fraco_inimigo', 'uma tática previsível')}. "
                f"Portanto, {dados_placar.get('resumo_estrategico', 'vamos jogar com inteligência')}"
            )
            return resposta_formatada
        except (json.JSONDecodeError, KeyError) as e:
            self.console.print(f"[bold red]Erro ao processar o JSON do placar: {e}[/bold red]")
            return "Não consegui ler as informações do placar. Tente novamente."

    def analisar_pre_round_valorant(self):
        if not self.partida_atual:
            return "O modo coach não foi iniciado."
        self.console.log("Capturando tela pré-round para análise detalhada...")
        imagem_base64 = capturar_tela_e_converter_base64()
        historico_rounds_texto = "\n".join([
            f"- Round {i+1}: {r.get('sugestao_tatica', 'N/A')}"
            for i, r in enumerate(self.partida_atual.historico_rounds)
        ]) if self.partida_atual.historico_rounds else "Nenhum histórico ainda."
        prompt_visao = (
            f"Você é 'Astratega', uma IA coach de elite de Valorant. Analise este screenshot tirado ANTES do round começar. "
            f"Meu agente é {self.partida_atual.agente_jogador}. Estamos no lado {self.partida_atual.lado_atual}. "
            f"A composição inimiga é: {', '.join(self.partida_atual.composicao_inimiga)}. "
            f"Histórico de insights dos rounds anteriores:\n{historico_rounds_texto}\n\n"
            "Sua tarefa é fazer uma análise profunda e retornar APENAS um objeto JSON com:\n"
            "1. 'analise_economica': String detalhando a situação econômica (Ex: 'Você está de Vandal e colete cheio. Inimigos provavelmente estão full buy também. Cuidado com um possível Operator do Chamber deles').\n"
            "2. 'ponto_focal_mapa': String identificando a área mais crítica do mapa para este round (Ex: 'O controle do Meio será decisivo para dividir o time inimigo').\n"
            "3. 'previsao_tatica_inimiga': A jogada mais provável do inimigo, com justificativa (Ex: 'Com base nos últimos 2 rounds, a Jett deles tentará um avanço rápido pela B Long. O Sova deles provavelmente usará o drone para limpar a entrada primeiro').\n"
            "4. 'sugestao_pessoal_detalhada': Uma sugestão passo-a-passo PARA MIM ({self.partida_atual.agente_jogador}). (Ex: 'Como Phoenix, use sua parede para cortar a visão do Heaven na entrada A. Depois, flashe alto para a direita para cegar quem estiver no site e entre com o time. Guarde a ultimate para o retake').\n"
            "5. 'alerta_principal': Uma única e crucial dica de 'cuidado'. (Ex: 'Alerta: Não duele com a Reyna deles no 1x1 sem vantagem. Jogue com o time')."
        )
        self.console.log("Enviando tela pré-round para análise detalhada da OpenAI...")
        resposta_dict = self.obter_resposta_llm(
            prompt=prompt_visao, 
            modo="Análise Pré-Round Detalhada", 
            schema={"type": "object"}, 
            imagem_base64=imagem_base64
        )
        try:
            analise_pre_round = json.loads(resposta_dict.get("conteudo", "{}"))
            self.console.log(f"Análise pré-round concluída. Previsão: {analise_pre_round.get('previsao_tatica_inimiga', 'Nenhuma')}")
            resposta_formatada = (
                f"Análise para o round: {analise_pre_round.get('analise_economica', '')} "
                f"O ponto chave é o {analise_pre_round.get('ponto_focal_mapa', 'controle de área')}. "
                f"Prevejo que eles tentarão {analise_pre_round.get('previsao_tatica_inimiga', 'uma tática padrão')}. "
                f"Minha sugestão para você: {analise_pre_round.get('sugestao_pessoal_detalhada', 'Jogue o seu melhor')}. "
                f"E o mais importante: {analise_pre_round.get('alerta_principal', 'mantenha a calma')}"
            )
            return resposta_formatada
        except (json.JSONDecodeError, KeyError) as e:
            self.console.print(f"[bold red]Erro ao processar o JSON da análise pré-round: {e}[/bold red]")
            return "Não consegui ler as informações da tela. Tente novamente."

    def analisar_pos_round_valorant(self):
        if not self.partida_atual:
            return "O modo coach não foi iniciado."
        self.console.log("Capturando mapa grande pós-round para análise profunda...")
        imagem_base64 = capturar_tela_e_converter_base64()
        historico_rounds_texto = "\n".join([
            f"- Round {i+1}: Resultado: {r.get('resultado_round', 'N/A')}, Padrão Inimigo: {r.get('padrao_comportamental_inimigo', 'N/A')}"
            for i, r in enumerate(self.partida_atual.historico_rounds)
        ]) if self.partida_atual.historico_rounds else "Primeiro round, sem histórico."
        prompt_visao = (
            "Você é 'Astratega', uma IA coach de elite. Analise este screenshot do mapa (CAPS LOCK) no final de um round. "
            f"O histórico da partida é:\n{historico_rounds_texto}\n"
            "Sua tarefa é fazer uma autópsia tática do round e planejar o próximo. Retorne APENAS um objeto JSON com:\n"
            "1. 'resultado_round': String ('vitoria' ou 'derrota').\n"
            "2. 'causa_principal': String explicando a razão fundamental pela qual o round foi ganho ou perdido (Ex: 'Perdemos por conta de um avanço inimigo bem coordenado no site B').\n"
            "3. 'analise_economia_ults': String analisando a economia de ultimates para o próximo round (Ex: 'Sua ultimate está pronta. A Sage inimiga provavelmente também tem a dela. Espere uma ressurreição.').\n"
            "4. 'padrao_comportamental_inimigo': String atualizando um padrão tático inimigo (Ex: 'CONFIRMADO: A Jett deles força a passagem pelo Meio em 80% dos rounds de ataque. Isso é explorável.').\n"
            "5. 'plano_de_acao_proximo_round': Um plano de ação detalhado para o próximo round (Ex: 'Plano: Vamos fazer um anti-tático. Posicione uma mira no Meio para punir a Jett. Assim que ela for eliminada, executem o plano B no site A com o resto do time.')."
        )
        self.console.log("Enviando mapa pós-round para análise profunda da OpenAI...")
        resposta_dict = self.obter_resposta_llm(
            prompt=prompt_visao, 
            modo="Análise Pós-Round Profunda", 
            schema={"type": "object"}, 
            imagem_base64=imagem_base64
        )
        try:
            analise_round = json.loads(resposta_dict.get("conteudo", "{}"))
            self.partida_atual.adicionar_analise_round(analise_round)
            self.console.log(f"Análise pós-round concluída. Causa: {analise_round.get('causa_principal', 'N/A')}")
            resposta_formatada = (
                f"Ok, análise do último round: {analise_round.get('causa_principal', 'não foi clara')}. "
                f"Para o próximo round, {analise_round.get('analise_economia_ults', 'fique atento às ultimates')}. "
                f"Percebi um padrão: {analise_round.get('padrao_comportamental_inimigo', 'eles estão variando a tática')}. "
                f"Aqui está o plano: {analise_round.get('plano_de_acao_proximo_round', 'vamos nos adaptar e jogar com inteligência')}"
            )
            return resposta_formatada
        except (json.JSONDecodeError, KeyError) as e:
            self.console.print(f"[bold red]Erro ao processar o JSON da análise pós-round: {e}[/bold red]")
            return "Não consegui ler as informações do mapa. Tente novamente."


    # --- MÉTODOS DE ANÁLISE DE DADOS (EXISTENTES) ---
    def _localizar_e_confirmar_dataset(self, nome_curto: Optional[str]) -> Tuple[str, str]:
        self.console.print(f"[cyan]Recebi um pedido de análise para '{nome_curto}'... A procurar...[/cyan]")
        
        DATA_ROOT = 'data/'
        try:
            datasets_disponiveis = [d.name for d in os.scandir(DATA_ROOT) if d.is_dir()]
        except FileNotFoundError:
            return self._formata_resposta_direta("Erro: A minha pasta 'data/' não foi encontrada."), "Erro de diretório"

        if not nome_curto:
            resposta_texto = f"Detetei que queres analisar dados. Os que eu tenho são:\n- " + "\n- ".join(datasets_disponiveis) + "\n\nQual deles gostarias de analisar?"
            return self._formata_resposta_direta(resposta_texto), "Ambiguidade de dataset"

        matches = [d for d in datasets_disponiveis if nome_curto in d.lower()]

        if len(matches) == 1:
            dataset_encontrado = matches[0]
            try:
                caminho_dataset = os.path.join(DATA_ROOT, dataset_encontrado)
                ficheiros_csv = [f for f in os.listdir(caminho_dataset) if f.endswith('.csv')]
                if not ficheiros_csv: raise FileNotFoundError("Nenhum CSV encontrado na pasta.")
                
                caminho_csv_principal = os.path.join(caminho_dataset, ficheiros_csv[0])
                df_temp = pd.read_csv(caminho_csv_principal)
                colunas = df_temp.columns.tolist()

                self.estado_da_analise = "aguardando_alvo"
                self.contexto_analise_pendente = {"caminho_csv": caminho_csv_principal}

                resposta_texto = f"Ótimo! Encontrei o dataset '{dataset_encontrado}'. Para começar, qual coluna queres que eu tente prever? As colunas disponíveis são:\n\n{colunas}"
                return self._formata_resposta_direta(resposta_texto), "Aguardando coluna-alvo"
            except Exception as e:
                return self._formata_resposta_direta(f"Encontrei a pasta '{dataset_encontrado}', mas tive um problema ao ler os ficheiros. Erro: {e}"), "Erro de leitura"
        
        else: # Lida com múltiplos matches ou nenhum
            return self._formata_resposta_direta(f"Não encontrei um dataset correspondente a '{nome_curto}'."), "Dataset não encontrado"

    def _confirmar_alvo_e_iniciar(self, nome_coluna_alvo: str) -> Tuple[str, str]:
        """Recebe a coluna-alvo, inicia o AnalisadorDeDados e começa o fluxo."""
        caminho_csv = self.contexto_analise_pendente.get("caminho_csv")
        if not caminho_csv:
            self.estado_da_analise = "inativo"
            return self._formata_resposta_direta("Ocorreu um erro de contexto."), "Erro de contexto"

        try:
            df = pd.read_csv(caminho_csv)
            if nome_coluna_alvo not in df.columns:
                return self._formata_resposta_direta(f"A coluna '{nome_coluna_alvo}' não existe. Tenta de novo."), "Coluna-alvo inválida"

            self.console.print(f"[cyan]Alvo confirmado: '{nome_coluna_alvo}'. A iniciar a sessão de análise...[/cyan]")
            self.sessao_de_analise = AnalisadorDeDados(self, dataframe=df, coluna_alvo=nome_coluna_alvo)
            
            self.estado_da_analise = "em_discussao" 
            self.contexto_analise_pendente = {}

            return self.sessao_de_analise.iniciar_fluxo()

        except Exception as e:
            self.estado_da_analise = "inativo"
            return self._formata_resposta_direta(f"Ocorreu um erro ao carregar o dataset. Erro: {e}"), "Erro fatal"
            
    def _formata_resposta_direta(self, texto: str) -> str:
        return json.dumps({"ferramenta": "resposta_direta_streaming", "parametros": {"texto_final": texto}})

    def _log(self, mensagem: str, tipo: str = "dim"):
        self.console.print(f"[{tipo}]{mensagem}[/{tipo}]")

    # --- MÉTODOS DE CICLO DE VIDA (EXISTENTES) ---
    def _inicializar_estado(self):
        self.carregar_memoria()
        self.memoria_inicial_count = len(self.memoria.estados)
        self._log(f"Estado inicializado para {self.usuario_atual.nome}. Memória com {self.memoria_inicial_count} registos.")

    def executar_analise_de_sessao(self):
        self.processador_cognitivo.executar_analise_de_sessao(self.obter_resposta_llm)

    def _atualizar_fadiga(self, custo: int):
        self.fadiga_cognitiva = max(0, self.fadiga_cognitiva + custo)
        self._log(f"Fadiga alterada em {custo}. Nível atual: {self.fadiga_cognitiva}", "red")

    def carregar_memoria(self, caminho="data/memoria_log.json"):
        self.memoria.carregar_de_json(caminho)
    
    def salvar_memoria(self, caminho="data/memoria_log.json"):
        self.memoria.exportar_para_json(caminho)