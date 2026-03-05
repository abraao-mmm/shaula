from fastapi import FastAPI, HTTPException, Query
from modelos_cognitivos import Pensamento
from gerenciador_pensamentos import GerenciadorPensamentos
from modelos_cognitivos import StatusPensamento

app = FastAPI(title="Shaula Mobile Bridge", description="Interface de Preservação de Estado Cognitivo")

# Instancia o Gerenciador (Na versão final, o AgenteReflexivo instanciaria isso)
cognicao = GerenciadorPensamentos()

@app.post("/capture", response_model=dict)
async def capturar_pensamento(pensamento: Pensamento):
    """
    Recebe input, valida (Pydantic) e persiste (Gerenciador).
    """
    try:
        # AQUI OCORRE A PRESERVAÇÃO DE ESTADO
        resultado = cognicao.salvar(pensamento)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context")
async def obter_contexto(projeto: str, limit: int = Query(default=5, le=20)):
    """
    Recupera contexto filtrado para o App Mobile.
    Limit travado em max 20 para evitar overload.
    """
    dados = cognicao.recuperar_contexto(projeto, limit)
    return {
        "projeto": projeto, 
        "total_recuperado": len(dados),
        "itens": dados
    }

# Para rodar: uvicorn mobile_bridge:app --reload

# Adicione isso no final do mobile_bridge.py, antes de rodar

@app.get("/health")
async def check_health():
    """
    Monitoramento de Engenharia: Verifica se o cérebro está intacto.
    """
    try:
        metricas = cognicao.obter_saude_sistema()
        return metricas
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}
    
@app.patch("/thoughts/{thought_id}/status")
async def mudar_status(thought_id: str, status: StatusPensamento):
    """
    Endpoint para Gerenciamento de Ciclo de Vida (Ativo -> Resolvido).
    """
    sucesso = cognicao.atualizar_status(thought_id, status.value)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Pensamento não encontrado")
    return {"status": "atualizado", "id": thought_id, "novo_estado": status}
    
@app.get("/analysis")
async def obter_analise_cognitiva():
    """
    Retorna o 'Check-up' da mente do usuário.
    """
    return cognicao.analisar_divida_cognitiva()