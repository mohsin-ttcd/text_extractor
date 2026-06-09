# Bengali OCR Web App - Running Instructions

## Status: ✅ READY TO RUN

The application has been successfully built and is ready for use.

## Quick Commands

### Terminal 1 - Backend
```bash
cd backend
python run.py
```

### Terminal 2 - Frontend (in a NEW terminal/tab)
```bash
cd frontend
npm run dev
```

### Open Browser
```
http://localhost:5173
```

---

## Detailed Instructions

See: **HOW_TO_RUN.md** for step-by-step guide

---

## System Requirements Met ✅

- [x] Python 3.8+ with FastAPI
- [x] Node.js 16+ with React
- [x] Backend database (SQLite)
- [x] Frontend build tool (Vite)
- [x] All dependencies installed

---

## What's Included

### Backend ✅
- FastAPI server on localhost:8000
- SQLite database with OCR data
- Tesseract OCR integration
- Gemini API fallback support
- API documentation at /docs

### Frontend ✅
- React web app on localhost:5173
- Split-screen interface
- PDF viewer with zoom
- Text editor with auto-save
- Drag-and-drop upload
- Progress tracking
- Settings configuration
- Book management

### Features ✅
- PDF upload and processing
- Bengali text extraction
- Text editing and saving
- Batch OCR processing
- Word export (.docx)
- Real-time progress tracking
- Full Bengali localization
- Dark mode support
- Responsive design

---

## Documentation

- **README.md** - Complete project guide
- **QUICKSTART.md** - 5-minute setup
- **HOW_TO_RUN.md** - Running instructions
- **PHASE2_SUMMARY.md** - What was built
- **FEATURE_CHECKLIST.md** - All features listed

---

## First Time Use

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev` (new terminal)
3. Open: http://localhost:5173
4. Click upload button
5. Select a PDF file
6. Click "Extract Text" button
7. Edit text in right panel
8. Export to Word when done

---

## Troubleshooting

**Backend won't start:**
- Make sure you're in the `backend` folder
- Run: `python run.py`

**Frontend won't start:**
- Make sure you're in the `frontend` folder
- Run: `npm run dev`

**Can't access app:**
- Check both terminals are running
- Open: http://localhost:5173

**Port already in use:**
- Close other apps using those ports
- Or modify backend/run.py to use different port

---

## API Endpoints

All available at: http://localhost:8000/docs

```
Books:
  POST   /api/books/upload         - Upload PDF
  GET    /api/books/               - List all books
  DELETE /api/books/{id}           - Delete book

Pages:
  GET    /api/pages/{book}/{page}  - Get page
  POST   /api/pages/{page}/ocr     - Process page
  POST   /api/pages/batch-ocr      - Batch process

Export:
  GET    /api/export/books/{id}    - Export to Word
```

---

## Next Steps

After verifying the app works:

1. **Phase 3**: Containerization (Docker)
2. **Phase 3**: Final testing
3. **Phase 3**: Deployment setup

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Built**: June 2026

Visit http://localhost:5173 to get started!
