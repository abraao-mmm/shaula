# arquivo: app/main.py
from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(
    title="Shaula Cognitive System",
    description="Arquitetura de Metacognição e Memória Aumentada",
    version="1.2.0"
)

# Inclui todas as rotas que definimos no outro arquivo
app.include_router(endpoints.router)

# Para rodar (agora mudou o comando!):
# uvicorn app.main:app --reload --host 0.0.0.0