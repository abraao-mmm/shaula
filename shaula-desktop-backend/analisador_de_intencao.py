# backend/analisador_de_intencao.py (VERSÃO 2.0 - COM FEW-SHOT LEARNING)

import json
from typing import Callable, Dict

def identificar_intencao(entrada_usuario: str, obter_resposta_llm_func: Callable) -> Dict:
    """
    Usa uma chamada à LLM com exemplos (Few-Shot) para classificar a intenção
    do utilizador de forma muito mais precisa.
    """
    
    # --- ESQUEMA ATUALIZADO ---
    # Adicionamos 'arquivo_solicitado' para a intenção reflexiva
    schema = {
        "type": "object",
        "properties": {
            "intencao": { "type": "string", "enum": ["analise_de_dados", "conversa_geral", "comando_sistema", "pergunta_pessoal_reflexiva", "gerenciar_inventario", "consulta_inventario", "encerrar_sessao", "cadastro_item_admin", "relatorio_admin", "iniciar_coach_valorant"] },
            "dataset_mencionado": { "type": "string" },
            "arquivo_solicitado": { "type": "string" },
            "itens": { "type": "array", "items": {"type": "object"} },
            "item": { "type": "string" },
            "agente_jogador": { "type": "string" },
            "mapa": { "type": "string" },
            "comando_especifico": { "type": "string" }
        },
        "required": ["intencao"]
    }

    prompt = (
        "Você é um classificador de intenções NLU (Natural Language Understanding) de alta precisão. Analise a frase do utilizador e classifique-a de acordo com o schema JSON fornecido, baseando-se nos exemplos abaixo.\n\n"
        
        "**Exemplo 1: Análise de Dados (Distinção Importante)**\n"
        "Frase: 'shaula, analisa o dataset olist que eu coloquei na sua DATA'\n"
        "JSON: {\"intencao\": \"analise_de_dados\", \"dataset_mencionado\": \"olist\"}\n\n"
        
        "**Exemplo 2: Pergunta Pessoal (Sua Falha Corrigida)**\n"
        "Frase: 'Tu consegue acessar o arquivo chamado AGENTE que tá no teu banco de identidade?'\n"
        "JSON: {\"intencao\": \"pergunta_pessoal_reflexiva\", \"arquivo_solicitado\": \"agente.py\"}\n\n"
        
        "**Exemplo 3: Pergunta Pessoal (Sua Segunda Falha Corrigida)**\n"
        "Frase: 'Vê se tu encontra um arquivo chamado diário de bordo na tua identidade.'\n"
        "JSON: {\"intencao\": \"pergunta_pessoal_reflexiva\", \"arquivo_solicitado\": \"diario_de_bordo\"}\n\n"

        "**Exemplo 4: Pergunta Pessoal (Geral)**\n"
        "Frase: 'no que você tem pensado ultimamente?'\n"
        "JSON: {\"intencao\": \"pergunta_pessoal_reflexiva\", \"arquivo_solicitado\": null}\n\n"

        "**Exemplo 5: Gerenciamento de Inventário**\n"
        "Frase: 'shaula, peguei 3 placas arduino uno e 20 resistores de 330'\n"
        "JSON: {\"intencao\": \"gerenciar_inventario\", \"itens\": [{\"nome\": \"placa arduino uno\", \"quantidade\": 3, \"acao\": \"remover\"}, {\"nome\": \"resistor 330\", \"quantidade\": 20, \"acao\": \"remover\"}]}\n\n"

        "**Exemplo 6: Consulta de Inventário**\n"
        "Frase: 'quantos leds vermelhos ainda tem?'\n"
        "JSON: {\"intencao\": \"consulta_inventario\", \"item\": \"led vermelho\"}\n\n"

        "**Exemplo 7: Encerrar Sessão**\n"
        "Frase: 'Saye'\n"
        "JSON: {\"intencao\": \"encerrar_sessao\"}\n\n"

        "**Exemplo 8: Ação de Gestor**\n"
        "Frase: 'gere um relatório de uso do inventário'\n"
        "JSON: {\"intencao\": \"relatorio_admin\"}\n\n"

        "**Exemplo 15: Consulta de Documento (Sua Falha Corrigida)**\n"
        "Frase: 'Vê se tu encontra um arquivo chamado diário de bordo na tua identidade.'\n"
        "JSON: {\"intencao\": \"consulta_documento\", \"documento\": \"diário de bordo\"}\n\n"
        
        "**Exemplo 16: Pergunta Pessoal (Distinção)**\n"
        "Frase: 'fala sobre o teu código chamado agente'\n"
        "JSON: {\"intencao\": \"pergunta_pessoal_reflexiva\", \"arquivo_solicitado\": \"agente\"}\n\n"

        "--- TAREFA ATUAL ---\n"
        f"**Frase do Utilizador para Analisar:**\n\"{entrada_usuario}\"\n\n"
        "Responda APENAS com o objeto JSON."
    )
    
    # Passamos o 'schema' para a LLM para forçar o formato JSON
    resposta_dict = obter_resposta_llm_func(prompt, modo="Análise de Intenção", schema=schema)
    
    try:
        # Tenta carregar o conteúdo da resposta como JSON
        return json.loads(resposta_dict.get("conteudo", "{}"))
    except json.JSONDecodeError:
        # Se a LLM falhar em retornar um JSON válido, retorna para 'conversa_geral'
        return {"intencao": "conversa_geral"} # Fallback seguro