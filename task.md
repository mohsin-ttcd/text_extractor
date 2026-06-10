# Task List: Historical Bengali PDF OCR Desktop App (Tauri + React + FastAPI)

- `[x]` Define Python dependencies in `requirements.txt`
- `[x]` Implement local persistence layer in `database.py` (SQLite schema, save, resume, and tracking)
- `[x]` Implement image preprocessing and OCR pipeline in `ocr_processor.py`
    - Include OpenCV adaptive thresholding and deskewing
    - Implement Tesseract OCR
- `[x]` Implement client-server Tauri desktop application
    - Tauri Rust backend that manages application lifecycle and spawns FastAPI Python server
    - React (TypeScript + Tailwind CSS) frontend for modern, accessible UI
- `[x]` Implement backend REST API endpoints in FastAPI
    - Page rendering and OCR triggers
    - Settings configuration and persistence
    - Word document compilation (.docx) with line-breaks
- `[x]` Manual verification of functionality (mock PDF processing, database persistence, Word document generation)
- `[x]` Implement Tesseract language exception checks in `ocr_processor.py`
