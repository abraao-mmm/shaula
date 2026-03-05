from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pathlib import Path
import json
import uuid

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SESSIONS_FILE = DATA_DIR / "sessions.jsonl"


app = FastAPI(title="Shaula Backend", version="0.1.0")

# CORS (pra facilitar se você testar via browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.post("/analyze")
async def analyze(
    prompt: str = Form(""),
    image: UploadFile = File(...)
):
    session_id = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat()

    # salva imagem da sessão (opcional)
    img_dir = DATA_DIR / "images"
    img_dir.mkdir(exist_ok=True)
    img_path = img_dir / f"{session_id}_{image.filename}"

    content = await image.read()
    img_path.write_bytes(content)

    # RESPOSTA FAKE por enquanto (depois a gente pluga sua Shaula)
    answer = (
        "✅ Recebi a imagem.\n"
        f"- filename: {image.filename}\n"
        f"- bytes: {len(content)}\n"
        f"- prompt: {prompt.strip() or '(vazio)'}\n\n"
        "Próximo passo: integrar com o motor da Shaula para análise real."
    )

    record = {
        "session_id": session_id,
        "created_at": ts,
        "prompt": prompt,
        "image_filename": image.filename,
        "image_saved_path": str(img_path),
        "answer": answer,
    }

    # salva sessão em jsonl
    with SESSIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record

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
