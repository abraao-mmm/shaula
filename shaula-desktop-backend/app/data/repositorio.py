import json
import os
from typing import List, Optional
from datetime import datetime, timezone
from app.data.modelos import Pensamento, EstadoCognitivoGlobal, Tendencia, RegistroEstado

# Caminhos dos arquivos JSON
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARQUIVO_MEMORIA = os.path.join(BASE_DIR, "data", "memoria_cognitiva.json")
ARQUIVO_ESTADO = os.path.join(BASE_DIR, "data", "estado_humano.json")
ARQUIVO_ROTINAS = os.path.join(BASE_DIR, "data", "rotinas.json")

class RepositorioPensamentos:
    def __init__(self):
        self._garantir_arquivos()

    def _garantir_arquivos(self):
        # Garante pasta data
        diretorio = os.path.dirname(ARQUIVO_MEMORIA)
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)
        
        # Garante JSON de Pensamentos
        if not os.path.exists(ARQUIVO_MEMORIA):
            with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
                json.dump([], f)

        # Garante JSON de Estado Humano (NOVO)
        if not os.path.exists(ARQUIVO_ESTADO):
            with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _carregar_dados(self) -> List[dict]:
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
            return json.load(f)

    def _salvar_dados(self, dados: List[dict]):
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    # --- MÉTODOS DE PENSAMENTO (Camada 1) ---
    def salvar(self, pensamento: Pensamento) -> dict:
        dados = self._carregar_dados()
        pensamento_dict = json.loads(pensamento.model_dump_json())
        dados.append(pensamento_dict)
        self._salvar_dados(dados)
        return {"status": "ok", "id": pensamento.id}

    def recuperar_contexto(self, projeto: str = None, limit: int = 10) -> List[dict]:
        dados = self._carregar_dados()
        # Filtra por projeto se especificado
        if projeto:
            filtrados = [p for p in dados if p.get("projeto_associado") == projeto and p.get("status") == "ativo"]
        else:
            filtrados = [p for p in dados if p.get("status") == "ativo"]
            
        # Ordena por data (mais recente primeiro)
        filtrados.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Atualiza last_accessed dos itens retornados
        agora = datetime.now(timezone.utc).isoformat()
        ids_visualizados = [p["id"] for p in filtrados[:limit]]
        
        for p in dados:
            if p["id"] in ids_visualizados:
                p["last_accessed"] = agora
        self._salvar_dados(dados)
        
        return filtrados[:limit]

    def atualizar_status(self, id_pensamento: str, novo_status: str) -> bool:
        dados = self._carregar_dados()
        encontrou = False
        for item in dados:
            if item["id"] == id_pensamento:
                item["status"] = novo_status
                item["last_accessed"] = datetime.now(timezone.utc).isoformat()
                encontrou = True
                break
        if encontrou:
            self._salvar_dados(dados)
            return True
        return False

    # --- MÉTODOS DE ESTADO HUMANO (Camada 3 - NOVO) ---
    def salvar_estado(self, estado: RegistroEstado) -> dict:
        """Salva uma crise, rotina ou observação no novo JSON."""
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        dados.append(json.loads(estado.model_dump_json()))
        
        with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
            
        return {"status": "registrado", "id": estado.id}

    def buscar_crise_ativa(self) -> Optional[dict]:
        """Verifica se existe crise nas últimas 12h."""
        if not os.path.exists(ARQUIVO_ESTADO):
            return None
            
        with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        agora = datetime.now(timezone.utc)
        crises_recentes = []

        for item in dados:
            if item["tipo"] == "Crise":
                criado_em = datetime.fromisoformat(item["created_at"])
                # Calcula horas passadas
                horas_passadas = (agora - criado_em).total_seconds() / 3600
                
                # Regra: Crise dura 12 horas no sistema (ou até ser resolvida futuramente)
                if horas_passadas < 12: 
                    crises_recentes.append(item)
        
        if crises_recentes:
            # Retorna a mais recente
            return sorted(crises_recentes, key=lambda x: x["created_at"], reverse=True)[0]
        return None

    # --- MÉTODOS DE ANÁLISE (Camada 2) ---
    def analisar_estado_global(self) -> EstadoCognitivoGlobal:
        dados = self._carregar_dados()
        agora = datetime.now(timezone.utc)
        
        total_ativos = 0
        penalidade_total = 0
        contagem_por_projeto = {}
        
        PESOS_PRIORIDADE = {"Alta": 5, "Media": 2, "Baixa": 0}
        TOLERANCIA_DIAS = 1 

        for item in dados:
            if item["status"] == "ativo":
                total_ativos += 1
                proj = item.get("projeto_associado") or "Geral"
                contagem_por_projeto[proj] = contagem_por_projeto.get(proj, 0) + 1
                
                criado_em = datetime.fromisoformat(item["created_at"])
                idade_dias = (agora - criado_em).days
                confianca = item.get("confianca", "Media")
                
                if idade_dias > TOLERANCIA_DIAS:
                    dias_atraso = idade_dias - TOLERANCIA_DIAS
                    peso = PESOS_PRIORIDADE.get(confianca, 1)
                    penalidade_total += (dias_atraso * peso)

        score_foco = max(0, 100 - penalidade_total)
        
        projeto_critico = None
        if contagem_por_projeto:
            projeto_critico = max(contagem_por_projeto, key=contagem_por_projeto.get)
        else:
            projeto_critico = "Nenhum"

        if total_ativos == 0:
            nivel = "Leve"
            diagnostico = "Estado Limpo: Nenhuma pendência ativa."
            projeto_critico = None
        elif score_foco < 50:
            nivel = "Critica"
            diagnostico = f"ALERTA CRÍTICO: Dívida severa em '{projeto_critico}'."
        elif score_foco < 80:
            nivel = "Moderada"
            diagnostico = f"Atenção: Acúmulo em '{projeto_critico}'."
        else:
            nivel = "Leve"
            diagnostico = f"Fluxo Saudável. Foco em '{projeto_critico}'."

        return EstadoCognitivoGlobal(
            score_atual=score_foco,
            tendencia=Tendencia.ESTAVEL,
            nivel_carga=nivel,
            projeto_foco=projeto_critico,
            total_pendencias=total_ativos,
            diagnostico_resumido=diagnostico,
            timestamp=agora
        )
    
    def buscar_rotina_ativa(self) -> Optional[dict]:
        """
        Verifica se o usuário está em um compromisso fixo AGORA.
        """
        ARQUIVO_ROTINAS = os.path.join(BASE_DIR, "data", "rotinas.json")
        
        if not os.path.exists(ARQUIVO_ROTINAS):
            return None
            
        with open(ARQUIVO_ROTINAS, "r", encoding="utf-8") as f:
            rotinas = json.load(f)
            
        # Pega hora local (Ajuste o timezone se seu servidor estiver UTC e vc -4)
        # Assumindo que o servidor roda no seu PC (horário local):
        agora = datetime.now() 
        dia_semana_hoje = agora.weekday() # 0=Seg, 1=Ter...
        hora_atual = agora.strftime("%H:%M")
        
        for rotina in rotinas:
            # 1. Checa o dia
            if dia_semana_hoje in rotina["dias_semana"]:
                # 2. Checa o horário (Comparação simples de strings funciona para HH:MM)
                if rotina["horario_inicio"] <= hora_atual <= rotina["horario_fim"]:
                    return rotina
                    
        return None