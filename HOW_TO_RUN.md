# How to Run the Bengali OCR Web App

## Both Servers Need to Run Together

The application requires **two separate terminal windows/tabs** to run simultaneously:

### Terminal 1: Backend Server

```bash
cd backend
python run.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Leave this terminal running** - Backend will stay active and serve API requests.

### Terminal 2: Frontend Server (in a NEW terminal/tab)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.4.21  ready in 351 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Leave this terminal running** - Frontend will stay active and serve the web app.

## Access the Application

Open your web browser and go to:

```
http://localhost:5173
```

You should see the Bengali OCR Web App with:
- Header with upload button
- Split-screen layout (when a book is loaded)
- Empty state message if no book is loaded

## Step-by-Step First Use

1. **Click "📂 পিডিএফ ফাইল আপলোড করুন"** button
2. **Select a PDF file** from your computer
3. **Wait for upload** - Progress notification will appear
4. **PDF loads** - You'll see the first page in the left panel
5. **Click "📄 এই পৃষ্ঠা প্রক্রিয়া করুন"** to extract text from current page
6. **Text appears** in the right panel editor
7. **Edit the text** as needed
8. **Click "✓ সংরক্ষণ করুন"** to save changes
9. **Navigate** to other pages using Previous/Next buttons

## What Each Feature Does

### Upload
- Click button or drag-drop PDF onto the screen

### Settings (⚙️)
- Configure Tesseract path
- Set PDF DPI resolution
- Add Gemini API key for fallback

### Books (📚)
- View all uploaded PDFs
- Switch between books
- Delete books

### Process Page
- "📄 এই পৃষ্ঠা প্রক্রিয়া করুন" = Extract text from current page
- "🚀 সব পৃষ্ঠা প্রক্রিয়া করুন" = Batch process all pages

### Export
- "📥 Word ফাইলে রপ্তানি করুন" = Download as .docx file

## Stopping the App

**To Stop Backend:**
- In Terminal 1: Press `Ctrl+C`

**To Stop Frontend:**
- In Terminal 2: Press `Ctrl+C`

## Troubleshooting

### "Cannot connect to server"
- Make sure Terminal 1 is running: `python run.py`
- Check http://localhost:8000/docs to verify backend

### "npm: command not found"
- Install Node.js from https://nodejs.org/

### "Port 8000 already in use"
- Another app is using port 8000
- Either close that app or change backend port in `backend/run.py`

### "Port 5173 already in use"
- Close the app in Terminal 2 and try again

### Frontend shows blank/error page
- Open Developer Console (F12)
- Check for errors
- Make sure backend is running and accessible

## Verifying Everything is Working

### Check Backend Health

```bash
# In a new terminal, run:
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

### Check API Documentation

Visit: http://localhost:8000/docs

You should see the FastAPI documentation with all available endpoints.

## Files That Matter

```
backend/
├── run.py                 # Start script (python run.py)
├── app/main.py           # FastAPI app
└── requirements.txt      # Dependencies

frontend/
├── src/App.tsx           # Main React component
├── package.json          # Dependencies
└── vite.config.ts        # Build config
```

## Environment Setup

If you want to customize settings, create `.env` files:

**backend/.env:**
```
TESSERACT_PATH=/path/to/tesseract
DPI=200
GEMINI_API_KEY=your-key-here
DB_PATH=bengali_ocr.db
```

**frontend/.env:**
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
```

## Next Time

Just run these two commands in separate terminals:

```bash
# Terminal 1
cd backend && python run.py

# Terminal 2
cd frontend && npm run dev
```

---

**Backend**: http://localhost:8000 (API server)
**Frontend**: http://localhost:5173 (Web app)
**API Docs**: http://localhost:8000/docs

For full documentation, see: **README.md**
