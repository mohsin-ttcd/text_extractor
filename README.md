# Bengali OCR Web Application

A modern, full-stack web application for extracting and editing Bengali text from scanned historical PDF documents. This is a React + FastAPI migration of the original CustomTkinter desktop application, maintaining 100% backward compatibility with the existing Python OCR logic.

## Features

- **Split-screen interface**: PDF viewer on the left, text editor on the right
- **PDF upload**: Drag-and-drop or file browser upload
- **OCR processing**: 
  - Local Tesseract OCR engine (primary)
  - Google Gemini API fallback
  - Batch processing for multiple pages
  - Real-time progress tracking
- **Text editing**: Edit extracted Bengali text with auto-save
- **Text export**: Export all pages to Word (.docx) document
- **Settings management**: Configure Tesseract path, DPI, Gemini API key
- **Book management**: View and switch between previously uploaded PDFs
- **Bengali language support**: Full Bengali font rendering with proper diacritics

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Zustand** for state management
- **Axios** for API communication
- **Vite** as build tool

### Backend
- **FastAPI** (Python web framework)
- **SQLite** database
- **PyMuPDF** for PDF handling
- **Tesseract OCR** for local text recognition
- **Google Generative AI** for Gemini API integration
- **python-docx** for Word export

## Project Structure

```
.
├── frontend/                    # React web application
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client
│   │   ├── store/              # Zustand state management
│   │   ├── styles/             # Global styles & Tailwind
│   │   ├── App.tsx             # Main app component
│   │   └── main.tsx            # React entry point
│   ├── index.html              # HTML template
│   ├── package.json            # Dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── vite.config.ts          # Vite bundler config
│   └── tailwind.config.ts      # Tailwind configuration
│
├── backend/                    # FastAPI server
│   ├── app/
│   │   ├── routes/             # API endpoints
│   │   ├── models.py           # Pydantic schemas
│   │   ├── config.py           # Settings manager
│   │   ├── main.py             # FastAPI app
│   │   ├── database.py         # SQLite manager (unchanged)
│   │   ├── ocr_processor.py    # OCR pipeline (unchanged)
│   │   └── bengali_ocr_gemini.py # Gemini integration (unchanged)
│   ├── requirements.txt        # Python dependencies
│   └── run.py                  # Entry point script
│
├── config.json                 # Application settings
├── bengali_ocr.db              # SQLite database
└── tessdata/
    └── ben.traineddata         # Bengali language pack for Tesseract
```

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Tesseract OCR (optional, for local processing)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional, defaults provided)
cp .env.example .env
```

## Running the Application

### Start Backend

```bash
cd backend
python run.py
# Backend will start at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Start Frontend (in another terminal)

```bash
cd frontend
npm run dev
# Frontend will start at http://localhost:5173
# Automatically proxies /api requests to backend
```

### Access the Application

Open your browser and navigate to: `http://localhost:5173`

## Configuration

Settings are stored in `config.json`:

```json
{
  "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
  "dpi": 200,
  "gemini_api_key": "your-api-key-here",
  "use_gemini_fallback": true,
  "db_path": "bengali_ocr.db"
}
```

Or configure through the Settings modal in the UI.

## API Endpoints

### Books Management
- `POST /api/books/upload` - Upload PDF file
- `GET /api/books/` - List all books
- `GET /api/books/{book_id}/progress` - Get processing progress
- `DELETE /api/books/{book_id}` - Delete book

### Pages & OCR
- `GET /api/pages/{book_id}/{page_num}` - Get page data and image
- `POST /api/pages/{page_num}/ocr` - Process single page
- `POST /api/pages/batch-ocr` - Start batch OCR processing
- `GET /api/pages/task/{task_id}/status` - Check task status
- `POST /api/pages/{page_num}/update-text` - Save edited text
- `PUT /api/pages/{page_num}/reset` - Reset to original OCR text

### Configuration
- `GET /api/config/` - Get current settings
- `PUT /api/config/` - Update settings

### Export
- `GET /api/export/books/{book_id}` - Export to Word format
- `GET /api/export/books/{book_id}/preview` - Preview before export

## Usage Guide

### 1. Upload a PDF
- Click "পিডিএফ ফাইল আপলোড করুন" button, or
- Drag and drop a PDF file onto the application

### 2. Process Pages
- **Single Page**: Select a page and click "এই পৃষ্ঠা প্রক্রিয়া করুন"
- **All Pages**: Click "সব পৃষ্ঠা প্রক্রিয়া করুন"

### 3. Edit Text
- Click on text in the right editor panel to edit
- Changes are automatically saved
- Use font size slider to adjust text size

### 4. View Other PDFs
- Click "📚 আমার বইগুলি" to see all uploaded books
- Click a book to switch to it

### 5. Configure Settings
- Click "⚙️ সেটিংস" to configure:
  - Tesseract path
  - PDF DPI resolution
  - Gemini API key

### 6. Export Results
- Click "📥 Word ফাইলে রপ্তানি করুন" to export all processed pages to .docx

## Testing

### Backend Testing

```bash
# Run FastAPI in development mode with auto-reload
cd backend
python run.py

# View API documentation
# Visit: http://localhost:8000/docs
```

### Frontend Testing

```bash
# Run development server
cd frontend
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Performance Notes

- **DPI Impact**: Higher DPI (300) = better quality but slower processing
- **Batch Processing**: Large batch sizes may take time; check progress bar
- **Memory**: Keep browser DevTools closed for better performance
- **Text Rendering**: Bengali fonts use system fonts with fallbacks for compatibility

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Check if port 8000 is available: `netstat -an | grep 8000`
- Verify all dependencies: `pip install -r requirements.txt`

### Frontend shows blank page
- Check browser console for errors (F12)
- Ensure backend is running at `http://localhost:8000`
- Clear browser cache and reload

### OCR not working
- Verify Tesseract is installed and path is correct in settings
- Check Gemini API key if using fallback
- Try processing with lower DPI first

### Bengali text displays incorrectly
- Ensure Bengali fonts are installed on system
- Check browser font rendering settings
- Try different browser (Chrome/Firefox)

## Database Schema

The application uses SQLite with the following tables:

### Books Table
```sql
CREATE TABLE books (
  book_id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  pdf_path TEXT NOT NULL,
  total_pages INTEGER NOT NULL,
  processed_pages INTEGER DEFAULT 0,
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pages Table
```sql
CREATE TABLE pages (
  page_id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL,
  page_num INTEGER NOT NULL,
  raw_text TEXT,
  edited_text TEXT,
  page_image BLOB,
  status TEXT DEFAULT 'pending',
  error_message TEXT,
  FOREIGN KEY (book_id) REFERENCES books(book_id),
  UNIQUE(book_id, page_num)
);
```

## Future Enhancements

- [ ] WebSocket support for real-time progress updates
- [ ] Multi-language OCR support
- [ ] Document preprocessing optimization
- [ ] Handwriting recognition
- [ ] Batch import multiple PDFs
- [ ] Collaborative editing
- [ ] Cloud storage integration
- [ ] Mobile-responsive interface

## License

This project maintains the structure and dependencies of the original Bengali OCR application with modern web technologies.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API docs at `http://localhost:8000/docs`
3. Check browser console for detailed errors
4. Verify backend logs for processing errors

---

**Last Updated**: June 2026  
**Version**: 1.0.0
#   t e x t _ e x t r a c t o r  
 