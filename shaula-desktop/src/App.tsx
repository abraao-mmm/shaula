import React, { useEffect, useMemo, useRef, useState } from "react";
import { convertFileSrc, invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

type Session = {
  session_id: string;
  created_at: string;
  prompt: string;
  answer: string;
  image_filename?: string;
  image_saved_path?: string;
  state_vector?: any; // Adicionado para suportar o Kernel
};

const BACKEND = "http://127.0.0.1:8000";

export default function App() {
  const [lastScreenshot, setLastScreenshot] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Estados de Sessão
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionsError, setSessionsError] = useState<string>("");
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Estado do Kernel (Visualização)
  const [activeWindowTitle, setActiveWindowTitle] = useState<string>("Inativo");

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Calcula a origem da imagem (local ou backend)
  const screenshotSrc = useMemo(() => {
    if (selectedSession?.image_filename) {
      return `${BACKEND}/images/${selectedSession.image_filename}`;
    }
    return lastScreenshot ? convertFileSrc(lastScreenshot) : null;
  }, [lastScreenshot, selectedSession]);

  const loadSessions = async () => {
    setIsLoadingSessions(true);
    setSessionsError("");
    try {
      const res = await fetch(`${BACKEND}/sessions?limit=50`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as Session[];
      setSessions(data || []);
    } catch (e: any) {
      setSessionsError(`Falha ao carregar sessões: ${e?.message ?? String(e)}`);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  useEffect(() => {
    const unsubs: Array<() => void> = [];

    // Heartbeat Inteligente: Monitora janela ativa para o Kernel
    const heartbeatInterval = setInterval(async () => {
        try {
            const currentTitle = await invoke("get_active_window_title") as string;
            if (currentTitle !== activeWindowTitle) {
                setActiveWindowTitle(currentTitle);
                await invoke("sync_active_context", { title: currentTitle });
            }
        } catch (e) {
            console.warn("Heartbeat offline");
        }
    }, 30000);

    (async () => {
      const un1 = await listen<string>("shaula:screenshot_captured", (event) => {
        setLastScreenshot(event.payload);
        setSelectedSession(null); // Volta para a live view ao capturar nova
      });

      const un2 = await listen<string | null>("shaula:overlay_opened", (event) => {
        if (event.payload) setLastScreenshot(event.payload);
        setTimeout(() => {
          textareaRef.current?.focus();
        }, 50);
      });

      const un4 = await listen<Session>("shaula:session_created", (event) => {
        setSelectedSession(event.payload);
        loadSessions();
      });

      unsubs.push(un1, un2, un4);
    })();

    loadSessions();

    return () => {
      unsubs.forEach((u) => u());
      clearInterval(heartbeatInterval);
    };
  }, [activeWindowTitle]);

  const analyze = async () => {
    setResponse("");
    if (!lastScreenshot) {
      setResponse("Nenhuma screenshot capturada ainda. Use Ctrl+Shift+H.");
      return;
    }

    setIsAnalyzing(true);
    setResponse("Shaula está refletindo...");

    try {
      const res = (await invoke("analyze_last", { prompt })) as Session;
      setResponse(res?.answer ?? "(sem resposta)");
      setSelectedSession(res);
      loadSessions();
    } catch (e: any) {
      setResponse("Erro no Cognitive Kernel: " + (e?.toString?.() ?? String(e)));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectSession = (s: Session) => {
    setSelectedSession(s);
    setPrompt(s.prompt ?? "");
    setResponse(s.answer ?? "");
  };

  return (
    <div style={{ height: "100vh", boxSizing: "border-box", padding: 14, background: "#0f0f0f", color: "white", fontFamily: "system-ui", display: "flex", gap: 12 }}>
      
      {/* ===== SIDEBAR ===== */}
      <div style={{ width: 320, border: "1px solid #2a2a2a", borderRadius: 14, background: "#121212", padding: 12, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: 16, fontWeight: 800 }}>Histórico</div>
          <button onClick={loadSessions} disabled={isLoadingSessions} style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #2a2a2a", background: "#1f1f1f", color: "white", cursor: "pointer" }}>
            {isLoadingSessions ? "..." : "Sync"}
          </button>
        </div>

        {/* Status do Kernel */}
        <div style={{ background: "#0b0b0b", padding: 8, borderRadius: 10, border: "1px solid #222", fontSize: 11 }}>
            <div style={{ opacity: 0.6, marginBottom: 4 }}>CONTEXTO ATIVO</div>
            <div style={{ color: "#888", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {activeWindowTitle}
            </div>
        </div>

        <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column", gap: 8, marginTop: 10 }}>
          {sessions.map((s) => (
            <button key={s.session_id} onClick={() => selectSession(s)} style={{ textAlign: "left", borderRadius: 12, border: "1px solid #2a2a2a", background: selectedSession?.session_id === s.session_id ? "#1c1c1c" : "#0b0b0b", color: "white", padding: 10, cursor: "pointer" }}>
              <div style={{ fontWeight: 800, fontSize: 11, opacity: 0.5 }}>{s.created_at.split('T')[1].slice(0, 5)}</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>{s.prompt || "(vazio)"}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ===== MAIN CONTENT ===== */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Shaula <span style={{ color: "#666", fontWeight: 400 }}>System Container</span></div>
          <div style={{ opacity: 0.5, fontSize: 11 }}>v0.2.0-alpha | Extensão de Consciência</div>
        </div>

        {/* Screenshot View */}
        <div style={{ border: "1px solid #2a2a2a", borderRadius: 14, background: "#151515", height: 320, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", position: "relative" }}>
          {screenshotSrc ? (
            <img src={screenshotSrc} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
          ) : (
            <div style={{ opacity: 0.5 }}>Aguardando captura... (Ctrl+Shift+H)</div>
          )}
          {selectedSession && (
             <div style={{ position: "absolute", top: 10, left: 10, background: "rgba(0,0,0,0.7)", padding: "4px 8px", borderRadius: 6, fontSize: 10, border: "1px solid #444" }}>
                MODO HISTÓRICO
             </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && e.ctrlKey && e.shiftKey) analyze(); }}
            placeholder="O que você está pensando?"
            style={{ width: "100%", height: 100, padding: 12, borderRadius: 12, border: "1px solid #2a2a2a", background: "#0b0b0b", color: "white", resize: "none", outline: "none" }}
          />

          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={analyze} disabled={isAnalyzing} style={{ flex: 1, padding: "12px", borderRadius: 12, border: "1px solid #2a2a2a", background: "#1f1f1f", color: "white", fontWeight: 700, cursor: "pointer" }}>
              {isAnalyzing ? "Refletindo..." : "Analisar Contexto (Ctrl+Shift+Enter)"}
            </button>
            <button onClick={() => { setPrompt(""); setResponse(""); setSelectedSession(null); }} style={{ padding: "12px 20px", borderRadius: 12, border: "1px solid #2a2a2a", background: "transparent", color: "#666", cursor: "pointer" }}>
              Reset
            </button>
          </div>
        </div>

        {/* Response Area */}
        <div style={{ flex: 1, border: "1px solid #2a2a2a", borderRadius: 14, background: "#121212", padding: 15, overflow: "auto", fontSize: 14, lineHeight: 1.5 }}>
          <div style={{ fontWeight: 800, color: "#444", marginBottom: 10, fontSize: 12, letterSpacing: 1 }}>RESPOSTA DA SHAULA</div>
          <div style={{ whiteSpace: "pre-wrap" }}>{response}</div>
        </div>
      </div>
    </div>
  );
}