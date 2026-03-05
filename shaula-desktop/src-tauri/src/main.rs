#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use tauri::{Emitter, Manager, RunEvent};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

use image::{ImageBuffer, Rgba};
use screenshots::Screen;
use uuid::Uuid;

use serde::{Deserialize, Serialize};

#[derive(Default)]
struct AppState {
    last_path: Mutex<Option<String>>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct AnalyzeResponse {
    session_id: String,
    created_at: String,
    prompt: String,
    answer: String,
    image_filename: String,
    image_saved_path: String,
}

fn capture_screenshot_to_file(app: &tauri::AppHandle) -> Result<String, String> {
    use std::fs;

    let screens = Screen::all().map_err(|e| e.to_string())?;
    let screen = screens.get(0).ok_or("Nenhuma tela encontrada")?;

    let img = screen.capture().map_err(|e| e.to_string())?;
    let (w, h) = (img.width(), img.height());
    let raw = img.into_raw();

    let rgba: ImageBuffer<Rgba<u8>, Vec<u8>> =
        ImageBuffer::from_raw(w, h, raw).ok_or("Falha ao montar buffer RGBA")?;

    let mut dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    dir.push("screenshots");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    let filename = format!("{}.png", Uuid::new_v4());
    dir.push(filename);

    rgba.save(&dir)
        .map_err(|e: image::ImageError| e.to_string())?;

    Ok(dir.to_string_lossy().to_string())
}

#[tauri::command]
async fn analyze_last(
    app: tauri::AppHandle,
    state: tauri::State<'_, AppState>,
    prompt: String,
) -> Result<AnalyzeResponse, String> {
    let path_opt = state.last_path.lock().unwrap().clone();
    let path = path_opt.ok_or("Nenhuma screenshot capturada ainda (use Ctrl+Shift+H).")?;

    let bytes = std::fs::read(&path).map_err(|e| format!("Falha ao ler screenshot: {e}"))?;
    let filename = std::path::Path::new(&path)
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("screenshot.png")
        .to_string();

    let client = reqwest::Client::new();
    let form = reqwest::multipart::Form::new()
        .text("prompt", prompt)
        .part(
            "image",
            reqwest::multipart::Part::bytes(bytes)
                .file_name(filename)
                .mime_str("image/png")
                .map_err(|e| e.to_string())?,
        );

    let resp = client
        .post("http://127.0.0.1:8000/analyze")
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Erro ao chamar backend: {e}"))?;

    let status = resp.status();
    if !status.is_success() {
        let txt = resp.text().await.unwrap_or_default();
        return Err(format!("Backend respondeu erro: {} - {}", status, txt));
    }

    let data = resp
        .json::<AnalyzeResponse>()
        .await
        .map_err(|e| format!("Falha ao parsear resposta: {e}"))?;

    // avisa UI que uma sessão foi criada
    let _ = app.emit("shaula:session_created", data.clone());

    Ok(data)
}

fn main() {
    let context = tauri::generate_context!();

    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![analyze_last])
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .build(context)
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Ready = event {
                let window = match app_handle.get_webview_window("main") {
                    Some(w) => w,
                    None => {
                        eprintln!("Janela 'main' não encontrada. Coloque label:'main' no tauri.conf.json.");
                        return;
                    }
                };

                // Debounces
                let last_capture = Arc::new(Mutex::new(Instant::now() - Duration::from_secs(2)));
                let last_open = Arc::new(Mutex::new(Instant::now() - Duration::from_secs(2)));
                let last_toggle = Arc::new(Mutex::new(Instant::now() - Duration::from_secs(2)));

                // =========================
                // CAPTURE (Ctrl+Shift+H)
                // =========================
                let hk_capture: Shortcut = "Ctrl+Shift+H".parse().unwrap();
                {
                    let app_register = app_handle.clone();
                    let app_in_handler = app_handle.clone();
                    let last_capture = last_capture.clone();

                    let _ = app_register
                        .global_shortcut()
                        .on_shortcut(hk_capture, move |_, _, _| {
                            // debounce
                            {
                                let mut t = last_capture.lock().unwrap();
                                if t.elapsed() < Duration::from_millis(250) {
                                    return;
                                }
                                *t = Instant::now();
                            }

                            let app2 = app_in_handler.clone();
                            tauri::async_runtime::spawn(async move {
                                match capture_screenshot_to_file(&app2) {
                                    Ok(path) => {
                                        // salva no estado
                                        {
                                            let state = app2.state::<AppState>();
                                            *state.last_path.lock().unwrap() = Some(path.clone());
                                        }
                                        let _ = app2.emit("shaula:screenshot_captured", path);
                                    }
                                    Err(e) => {
                                        let _ = app2.emit("shaula:error", format!("screenshot: {e}"));
                                    }
                                }
                            });
                        });
                }

                // =========================
                // OPEN (Ctrl+Shift+Enter) - só abre se estiver fechado
                // =========================
                let hk_open: Shortcut = "Ctrl+Shift+Enter".parse().unwrap();
                {
                    let app_register = app_handle.clone();
                    let app_in_handler = app_handle.clone();
                    let window = window.clone();
                    let last_open = last_open.clone();

                    let _ = app_register
                        .global_shortcut()
                        .on_shortcut(hk_open, move |_, _, _| {
                            // debounce
                            {
                                let mut t = last_open.lock().unwrap();
                                if t.elapsed() < Duration::from_millis(250) {
                                    return;
                                }
                                *t = Instant::now();
                            }

                            if window.is_visible().unwrap_or(false) {
                                return;
                            }

                            let _ = window.show();
                            let _ = window.unminimize();
                            let _ = window.set_always_on_top(true);
                            let _ = window.set_focus();

                            let payload = {
                                let state = app_in_handler.state::<AppState>();
                                let x = state.last_path.lock().unwrap().clone();
                                x
                            };

                            let _ = app_in_handler.emit("shaula:overlay_opened", payload);
                        });
                }

                // =========================
                // TOGGLE (Ctrl+Shift+Alt+P)
                // =========================
                let hk_toggle: Shortcut = "Ctrl+Shift+Alt+P".parse().unwrap();
                {
                    let app_register = app_handle.clone();
                    let app_in_handler = app_handle.clone();
                    let window = window.clone();
                    let last_toggle = last_toggle.clone();

                    let _ = app_register
                        .global_shortcut()
                        .on_shortcut(hk_toggle, move |_, _, _| {
                            // debounce
                            {
                                let mut t = last_toggle.lock().unwrap();
                                if t.elapsed() < Duration::from_millis(250) {
                                    return;
                                }
                                *t = Instant::now();
                            }

                            let visible = window.is_visible().unwrap_or(false);
                            if visible {
                                let _ = window.hide();
                                return;
                            }

                            let _ = window.show();
                            let _ = window.unminimize();
                            let _ = window.set_always_on_top(true);
                            let _ = window.set_focus();

                            let payload = {
                                let state = app_in_handler.state::<AppState>();
                                let x = state.last_path.lock().unwrap().clone();
                                x
                            };

                            let _ = app_in_handler.emit("shaula:overlay_opened", payload);
                        });
                }

                println!("Hotkeys prontos:");
                println!(" - Ctrl+Shift+H: capturar screenshot");
                println!(" - Ctrl+Shift+Enter: abrir overlay (se fechado)");
                println!(" - Ctrl+Shift+Alt+P: toggle overlay");
            }
        });
}
