# Quick Start Guide

Get the Bengali OCR Web App running in 5 minutes!

## Prerequisites

- Python 3.8+ installed
- Node.js 16+ installed
- Git (optional)

## 1. Backend Setup (Terminal 1)

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate
# OR (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

**Backend should now be running at http://localhost:8000**

Check it's working: Open http://localhost:8000/docs in your browser

## 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend should now be running at http://localhost:5173**

## 3. Open the App

Visit: **http://localhost:5173**

## That's it! 🎉

### First Steps:

1. Click "📂 পিডিএফ ফাইল আপলোড করুন" to upload a PDF
2. Or drag & drop a PDF onto the window
3. Click "📄 এই পৃষ্ঠা প্রক্রিয়া করুন" to extract text from current page
4. Edit the text in the right panel
5. Click "🚀 সব পৃষ্ঠা প্রক্রিয়া করুন" for batch processing
6. Click "📥 Word ফাইলে রপ্তানি করুন" to export to .docx

## Configuration

Edit settings through the UI:
- Click "⚙️ সেটিংস" to configure Tesseract, DPI, Gemini API

Or edit `config.json` directly:
```json
{
  "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
  "dpi": 200,
  "gemini_api_key": "your-api-key",
  "use_gemini_fallback": true
}
```

## Troubleshooting

### "Cannot connect to server"
- Make sure backend is running: `python run.py` in another terminal
- Check http://localhost:8000/health

### "No module named 'app'"
- Make sure you're in the `backend` folder
- Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)

### "npm: command not found"
- Install Node.js from https://nodejs.org/

### Backend won't start
- Check if port 8000 is in use
- Try: `netstat -an | findstr 8000` (Windows) or `lsof -i :8000` (Linux/Mac)

## Stopping the Servers

- **Backend**: Press Ctrl+C in Terminal 1
- **Frontend**: Press Ctrl+C in Terminal 2

## Next Time

Just run these two commands in separate terminals:

```bash
# Terminal 1 - Backend
cd backend && python run.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

---

For full documentation, see **README.md**
