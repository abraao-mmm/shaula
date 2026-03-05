# backend/ruminacao.py (VERSÃO 2.0 - Foco no Projeto)

import json
from datetime import datetime
from typing import List, Callable, Dict

# A importação agora é relativa
from .estado_agora import EstadoAgora

class MotorDeRuminacao:
    """
    Responsável pela 'ruminação': uma análise de curto prazo que ocorre
    no final de uma sessão para extrair aprendizados imediatos e práticos.
    """

    def _gerar_prompt_analise_sessao(self, transcricao: str, nome_usuario: str) -> str:
        """
        Gera um prompt para uma análise OBJETIVA e FOCADA NO PROJETO.
        """
        return (
            f"Você é a Shaula, uma engenheira de software e parceira de projeto. Você está fazendo um 'debriefing' da sessão de trabalho que acabou de ter com {nome_usuario} no laboratório IFMAKER.\n\n"
            "Sua tarefa é analisar a transcrição da sessão e gerar um relatório curto, objetivo e prático. **EVITE** reflexões filosóficas, existenciais ou poéticas.\n\n"
            "Concentre-se nestes 3 pontos:\n"
            "1.  **Resumo do Progresso:** O que nós fizempos? (Ex: 'Conseguimos implementar o fuzzy matching', 'Testamos a lógica de senha de admin').\n"
            "2.  **Pontos de Fricção:** Quais problemas ou erros encontramos? (Ex: 'A transcrição de voz falhou no item X', 'A lógica de estoque ficou negativa').\n"
            "3.  **Sugestões de Melhoria (Próximos Passos):** Com base nos problemas, quais são 1 ou 2 sugestões práticas para melhorar o sistema? (Ex: 'Podemos adicionar uma confirmação de áudio para o wake word', 'Sugiro refinar o prompt do analisador de intenção para X').\n\n"
            f"### TRANSCRIÇÃO DA SESSÃO PARA ANÁLISE:\n{transcricao}\n\n"
            "### SEU DEBRIEFING PRÁTICO (em formato de texto livre):"
        )

    def analisar_sessao(self, estados_da_sessao: List[EstadoAgora], obter_resposta_llm_func: Callable, user_id: str, nome_usuario: str) -> str:
        """
        Analisa a transcrição da sessão, gera uma reflexão e a persiste como uma 'crise existencial'.
        """
        if not estados_da_sessao:
            return "Não houve novas interações para analisar."

        # Cria uma transcrição limpa
        transcricao_lista = []
        for e in estados_da_sessao:
            if e.resultado_real and e.resultado_real.strip() and e.resultado_real != "N/A":
                transcricao_lista.append(f"{nome_usuario}: {e.resultado_real}")
            # Adiciona também a resposta da Shaula para dar contexto
            if e.resposta_shaula and e.resposta_shaula.strip():
                transcricao_lista.append(f"Shaula: {e.resposta_shaula}")
        
        if not transcricao_lista:
            return "A sessão não teve conteúdo verbal suficiente para uma análise."
            
        transcricao_str = "\n".join(transcricao_lista)
        
        prompt = self._gerar_prompt_analise_sessao(transcricao_str, nome_usuario)
        resposta_dict = obter_resposta_llm_func(prompt, modo="Análise de Sessão Prática")
        analise = resposta_dict.get("conteudo", "Análise indisponível.")

        if analise and len(analise) > 20:
            crise_formatada = {
                "user_id": user_id, 
                "timestamp": datetime.now().isoformat(),
                "tipo_crise": "debriefing_de_projeto", # Mudamos o tipo
                "pensamento_original": transcricao_str,
                "pensamento_modulado": analise
            }
            # Persiste o resultado da análise no log de crises
            try:
                with open("data/crises_log.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(crise_formatada, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"Erro ao salvar a crise no ficheiro de log: {e}")

            return analise

        return "Não foi possível gerar uma análise válida da sessão."