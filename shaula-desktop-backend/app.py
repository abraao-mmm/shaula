from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pathlib import Path
import json
import uuid

# --- Importações do Ecossistema Shaula ---
# (Certifique-se de que o app.py consiga importar o agente e o gerenciador)
from agente import AgenteReflexivo
from gerenciador_usuarios import GerenciadorDeUsuarios
from rich.console import Console

console = Console()

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Pasta específica para as imagens
IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

SESSIONS_FILE = DATA_DIR / "sessions.jsonl"

app = FastAPI(title="Shaula System Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. SERVIR IMAGENS ESTÁTICAS (Conserta as imagens quebradas no Modo Histórico)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Inicia o gerenciador de usuários globalmente
gerenciador_usuarios = GerenciadorDeUsuarios()

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat(), "mode": "cognitive_kernel"}

@app.post("/analyze")
async def analyze(
    prompt: str = Form(""),
    image: UploadFile = File(...)
):
    session_id = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat()

    # Salva imagem da sessão
    img_filename = f"{session_id}_{image.filename}"
    img_path = IMAGES_DIR / img_filename
    content = await image.read()
    img_path.write_bytes(content)

    # 2. CONEXÃO COM O COGNITIVE KERNEL
    try:
        # Pega ou cria o seu usuário
        usuario = gerenciador_usuarios.obter_ou_criar_usuario_atual("Abraão")
        
        # Instancia o Agente (que agora tem o Router e o StateConsolidator embutidos)
        agente = AgenteReflexivo(usuario_atual=usuario, gerenciador=gerenciador_usuarios, console_log=console)
        
        # Roda o processamento cognitivo real!
        resposta_complexa, tipo_fluxo = agente.processar_entrada_do_utilizador(prompt)
        
        # Limpa a resposta se ela vier no formato JSON de ferramenta
        try:
            resp_json = json.loads(resposta_complexa)
            answer_text = resp_json.get("parametros", {}).get("texto_final", resposta_complexa)
        except:
            answer_text = resposta_complexa

    except Exception as e:
        answer_text = f"🧠 Falha Cognitiva (Erro no Kernel): {str(e)}"
        tipo_fluxo = "ERRO"

    record = {
        "session_id": session_id,
        "created_at": ts,
        "prompt": prompt,
        "image_filename": img_filename,
        "image_saved_path": str(img_path),
        "answer": answer_text,
        "fluxo_utilizado": tipo_fluxo
    }

    # Salva sessão em jsonl
    with SESSIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record

# 3. ENDPOINT DO HEARTBEAT (Consciência Passiva da Janela)
@app.post("/sync_context")
async def sync_context(data: dict):
    titulo_janela = data.get("title", "Desconhecido")
    contexto_file = DATA_DIR / "active_context.json"
    
    with open(contexto_file, "w", encoding="utf-8") as f:
        json.dump({"janela_ativa": titulo_janela, "ts": datetime.utcnow().isoformat()}, f)
        
    return {"status": "synced"}

@app.get("/sessions")
def list_sessions(limit: int = 50):
    if not SESSIONS_FILE.exists():
        return []
    lines = SESSIONS_FILE.read_text(encoding="utf-8").splitlines()
    items = [json.loads(x) for x in lines[-limit:]]
    items.reverse()
    return items

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    if not SESSIONS_FILE.exists():
        return {"error": "no sessions"}
    lines = SESSIONS_FILE.read_text(encoding="utf-8").splitlines()
    for x in reversed(lines):
        obj = json.loads(x)
        if obj.get("session_id") == session_id:
            return obj
    return {"error": "not found", "session_id": session_id}