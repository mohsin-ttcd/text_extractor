#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{Manager, State};

const BACKEND_URL: &str = "http://127.0.0.1:8000";

struct BackendProcess(Mutex<Option<Child>>);

impl Drop for BackendProcess {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

fn get_backend_command() -> Command {
    if cfg!(debug_assertions) {
        let mut cmd = Command::new("python");
        let mut base_path = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let mut script_path = base_path.join("src-backend/__main__.py");
        
        if !script_path.exists() {
            if base_path.ends_with("src-tauri") {
                if let Some(parent) = base_path.parent() {
                    script_path = parent.join("src-backend/__main__.py");
                    base_path = parent.to_path_buf();
                }
            }
        }
        
        cmd.arg(script_path);
        cmd.current_dir(base_path);
        cmd
    } else {
        let current_exe = std::env::current_exe().ok();
        let exe_dir = current_exe.as_ref().and_then(|p| p.parent()).map(|p| p.to_path_buf());
        let backend_path = exe_dir
            .map(|d| d.join("backend.exe"))
            .unwrap_or_else(|| PathBuf::from("backend.exe"));
        Command::new(backend_path)
    }
}

#[tauri::command]
fn get_backend_url() -> String {
    BACKEND_URL.to_string()
}

#[tauri::command]
fn start_backend(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    if guard.is_some() {
        return Ok(());
    }

    let mut cmd = get_backend_command();
    cmd.stdout(Stdio::null()).stderr(Stdio::null());
    let child = cmd.spawn().map_err(|e| format!("Failed to start backend: {}", e))?;
    *guard = Some(child);
    Ok(())
}

#[tauri::command]
fn stop_backend(state: State<'_, BackendProcess>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = guard.take() {
        child.kill().map_err(|e| format!("Failed to stop backend: {}", e))?;
        child.wait().map_err(|e| format!("Failed to wait for backend: {}", e))?;
    }
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle();
            std::thread::spawn(move || {
                std::thread::sleep(std::time::Duration::from_secs(2));
                let state = handle.state::<BackendProcess>();
                let mut guard = match state.0.lock() {
                    Ok(g) => g,
                    Err(_) => return,
                };
                if guard.is_some() {
                    return;
                }
                let mut cmd = get_backend_command();
                cmd.stdout(Stdio::null()).stderr(Stdio::null());
                match cmd.spawn() {
                    Ok(child) => {
                        *guard = Some(child);
                    }
                    Err(e) => {
                        eprintln!("Failed to start backend: {}", e);
                    }
                }
            });
            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                let state = event.window().state::<BackendProcess>();
                let result = state.0.lock();
                if let Ok(mut guard) = result {
                    if let Some(ref mut child) = *guard {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            start_backend,
            stop_backend
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
