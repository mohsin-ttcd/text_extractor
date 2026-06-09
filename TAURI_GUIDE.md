# Bengali OCR - Tauri Desktop Application

## Overview

The Bengali OCR application has been converted from a browser-based web app to a **native Windows desktop application** using Tauri. The app now runs as a proper desktop window with no localhost URLs visible, no terminal windows, and all features preserved.

## Architecture

```
┌─────────────────────────────────────────┐
│           Tauri Desktop App             │
├─────────────────────────────────────────┤
│  React Frontend (TypeScript + Tailwind) │
│  Tauri Rust Backend (main.exe)          │
│  FastAPI Python Backend (spawned)       │
│      ───────────────────────────        │
│  SQLite DB  │  Tesseract  │  Gemini API │
└─────────────────────────────────────────┘
```

## Quick Start (Development)

### Prerequisites
- Node.js 18+
- Python 3.10+
- Rust (stable channel)
- MinGW-w64 (for Rust compilation on Windows)

### Step 1: Install Rust
```bash
rustup default stable-x86_64-pc-windows-gnu
```

### Step 2: Install MinGW
Download from: https://winlibs.com/
Or install via winget:
```bash
winget install "WinLibs (POSIX threads, UCRT runtime)"
```

### Step 3: Set Environment Variable
```bash
set PATH=C:\mingw64\bin;%PATH%
```
(Adjust path to where MinGW is installed)

### Step 4: Run in Dev Mode
```bash
run-tauri-dev.bat
```
Or manually:
```bash
# Terminal 1: Start Python backend
python src-backend/__main__.py

# Terminal 2: Start Tauri dev
cd frontend
npx tauri dev
```

## Production Build

### Build Backend (.exe)
```bash
pyinstaller backend.spec --clean --noconfirm
```

### Build Complete App
```bash
set CARGO_TARGET_DIR=C:\build-cache
npm run build-tauri
```

The NSIS installer will be at:
`src-tauri\target\release\bundle\nsis\Bengali OCR Setup.exe`

## Files Structure

```
project-root/
├── src-tauri/                    # Tauri Rust backend
│   ├── src/main.rs               # Tauri app entry (backend spawner)
│   ├── Cargo.toml                # Rust dependencies
│   ├── tauri.conf.json           # Tauri configuration
│   ├── build.rs                  # Build script
│   └── icons/                    # App icons
├── src-backend/                  # Python FastAPI backend
│   ├── __main__.py               # Entry point for PyInstaller
│   └── app/                      # FastAPI app modules
├── frontend/src/                 # React frontend
│   ├── App.tsx                   # Main component
│   ├── components/               # UI components
│   ├── services/api.ts           # API client (Tauri-aware)
│   └── store/                    # Zustand state
├── backend.spec                  # PyInstaller spec file
├── run-tauri-dev.bat             # Dev launch script
└── package.json                  # Root package.json
```

## Features Status

All original 140+ features are preserved:
- ✅ PDF upload with drag-and-drop
- ✅ OCR processing (Tesseract + Gemini)
- ✅ Text editor with auto-save
- ✅ Word export
- ✅ Settings management
- ✅ Books history
- ✅ Dark mode
- ✅ Bengali localization
- ✅ **NEW: Native desktop window** (no browser)
- ✅ **NEW: Auto-update** (updater configured)
- ✅ **NEW: Single .exe installer**

## Troubleshooting

### "dlltool.exe not found"
Install MinGW-w64 and add to PATH:
```bash
set PATH=C:\mingw64\mingw64\bin;%PATH%
```

### "link.exe not found" (MSVC)
Switch to GNU toolchain:
```bash
rustup default stable-x86_64-pc-windows-gnu
```

### "distDir path doesn't exist"
Build the frontend first:
```bash
cd frontend && npm run build
```

### Backend won't start
Run backend separately to debug:
```bash
python src-backend/__main__.py
```
