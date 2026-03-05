# arquivo: app/api/endpoints.py
from fastapi import APIRouter, HTTPException, Query
from app.data.modelos import Pensamento, StatusPensamento, EstadoCognitivoGlobal, Tendencia
from app.data.repositorio import RepositorioPensamentos
from app.data.modelos import BriefingExecutivo # <--- Adicione
from app.core.rumiar import MotorRuminacao
from app.data.modelos import RegistroEstado 

router = APIRouter()
cognicao = RepositorioPensamentos()

@router.post("/capture", response_model=dict)
async def capturar_pensamento(pensamento: Pensamento):
    try:
        return cognicao.salvar(pensamento)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context")
async def obter_contexto(projeto: str, limit: int = Query(default=10, le=50)):
    dados = cognicao.recuperar_contexto(projeto, limit)
    return {"projeto": projeto, "itens": dados}

@router.patch("/thoughts/{thought_id}/status")
async def mudar_status(thought_id: str, status: StatusPensamento):
    sucesso = cognicao.atualizar_status(thought_id, status.value)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Pensamento não encontrado")
    return {"status": "atualizado"}

# 👇 AQUI ESTAVA O "ERRO" (estava chamando a versão antiga)
@router.get("/analysis", response_model=EstadoCognitivoGlobal)
async def obter_analise_cognitiva():
    """
    Retorna o Estado Cognitivo Global (Briefing).
    """
    # Agora chamamos explicitamente o método NOVO
    return cognicao.analisar_estado_global()

@router.get("/health")
async def health_check():
    return {"status": "sistema_cognitivo_online", "versao": "1.3"}

cerebro = MotorRuminacao()

@router.get("/briefing", response_model=BriefingExecutivo)
async def obter_briefing():
    """
    Retorna a estratégia completa: Diagnóstico + Plano de Ação.
    """
    return cerebro.gerar_briefing()

@router.post("/state", response_model=dict)
async def registrar_estado(estado: RegistroEstado):
    """
    Registra Crises, Rotinas ou Observações Pessoais.
    """
    return cognicao.salvar_estado(estado)