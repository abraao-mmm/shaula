from app.data.repositorio import RepositorioPensamentos
from app.data.modelos import BriefingExecutivo, EstadoCognitivoGlobal
from datetime import datetime

class MotorRuminacao:
    def __init__(self):
        self.repo = RepositorioPensamentos()

    def gerar_briefing(self) -> BriefingExecutivo:
        """
        Lógica Refinada:
        1. Crise Grave (>3) -> Proteção Total.
        2. Crise Leve (<=3) -> Apoio Motivacional (Empurrãozinho).
        3. Rotina -> Modo Aprendizado (Acompanhamento, não bloqueio).
        4. Score -> Gestão de Tarefas.
        """
        
        # Pega dados básicos
        estado_base = self.repo.analisar_estado_global()
        crise_ativa = self.repo.buscar_crise_ativa()
        rotina_ativa = self.repo.buscar_rotina_ativa()

        # --- CENÁRIO 1: CRISE (O ESTADO HUMANO) ---
        if crise_ativa:
            intensidade = crise_ativa.get("intensidade", 1)
            
            # 1.1 Crise Grave (Burnout, Pânico, Doença)
            if intensidade >= 4:
                return BriefingExecutivo(
                    estado_atual=estado_base,
                    gargalos_identificados=["Estado Crítico"],
                    estrategia_do_momento="🛡️ MODO DE PROTEÇÃO",
                    acao_tatica_sugerida="Cancele tudo. Sua saúde é inegociável hoje.",
                    mensagem_motivacional=f"Registro: '{crise_ativa['conteudo']}'. Descanse."
                )
            
            # 1.2 Crise Leve (Cansaço, Preguiça, Desânimo) - O "Empurrãozinho"
            else:
                # Aqui ela não bloqueia, ela motiva!
                msg_apoio = "Eu sei que é difícil, mas o esforço de hoje constrói o amanhã."
                if rotina_ativa:
                    return BriefingExecutivo(
                        estado_atual=estado_base,
                        gargalos_identificados=["Baixa Energia"],
                        estrategia_do_momento="💪 MODO DE SUPERAÇÃO",
                        acao_tatica_sugerida=f"Vá para o '{rotina_ativa['nome']}' mesmo cansado. Só ouça.",
                        mensagem_motivacional=f"Você disse: '{crise_ativa['conteudo']}'. Respire fundo e vá."
                    )
                else:
                    return BriefingExecutivo(
                        estado_atual=estado_base,
                        gargalos_identificados=["Baixa Energia"],
                        estrategia_do_momento="☕ MODO DE RECALIBRAGEM",
                        acao_tatica_sugerida="Comece com uma tarefa ridícula de fácil para pegar no tranco.",
                        mensagem_motivacional="Ação gera motivação, não o contrário."
                    )

        # --- CENÁRIO 2: ROTINA (O CONTEXTO EXTERNO) ---
        # Se não tem crise (ou já tratamos a crise leve acima), vemos a rotina.
        if rotina_ativa:
            return BriefingExecutivo(
                estado_atual=estado_base,
                gargalos_identificados=[],
                estrategia_do_momento="🧠 MODO APRENDIZADO", # Mudou de Bloqueio para Aprendizado
                acao_tatica_sugerida=f"Estou ciente do '{rotina_ativa['nome']}'. Capture apenas insights da aula.",
                mensagem_motivacional="Concentre-se no professor. Eu guardo suas ideias."
            )

        # --- CENÁRIO 3: VIDA NORMAL (Produtividade baseada no Score) ---
        # (Lógica padrão que você já tinha)
        estrategia = ""
        acao = ""
        gargalos = []
        msg = ""

        if estado_base.score_atual < 50:
            estrategia = "🚨 PROTOCOLO DE EMERGÊNCIA"
            msg = "Sua dívida está matando sua criatividade."
            if estado_base.projeto_foco:
                gargalos.append(estado_base.projeto_foco)
                acao = f"Resolva 3 pendências de '{estado_base.projeto_foco}' agora."
            else:
                acao = "Limpe as tarefas antigas de prioridade ALTA."

        elif estado_base.score_atual < 80:
            estrategia = "⚠️ Modo de Manutenção"
            msg = "Você está começando a acumular bagunça."
            gargalos.append(estado_base.projeto_foco or "Geral")
            acao = f"Processar pendências de '{estado_base.projeto_foco}'."

        else:
            estrategia = "✨ Modo de Exploração"
            msg = "Mente limpa. Ótimo momento para criar."
            acao = "Capture uma nova ideia ambiciosa."

        return BriefingExecutivo(
            estado_atual=estado_base,
            gargalos_identificados=gargalos,
            estrategia_do_momento=estrategia,
            acao_tatica_sugerida=acao,
            mensagem_motivacional=msg
        )