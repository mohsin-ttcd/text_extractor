"""
Export endpoints for generating Word documents
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
import os
import tempfile
import shutil
from ..database import DatabaseManager
from ..config import get_settings
from ..models import AppendRequest

try:
    import win32com.client
    import pythoncom
    _HAS_WIN32COM = True
except ImportError:
    _HAS_WIN32COM = False

router = APIRouter(prefix="/api/export", tags=["export"])

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONNECTED_DIR = os.path.join(_BACKEND_DIR, "connected")


def append_via_com(docx_path: str, text: str, page_num: int = None) -> bool:
    """Append text to the document using COM automation if it's currently open in Word."""
    if not _HAS_WIN32COM:
        return False

    pythoncom.CoInitialize()
    try:
        abs_path = os.path.abspath(docx_path).lower()
        try:
            word = win32com.client.GetActiveObject("Word.Application")
        except Exception:
            return False  # Word is not running

        target_doc = None
        for doc in word.Documents:
            try:
                if os.path.abspath(doc.FullName).lower() == abs_path:
                    target_doc = doc
                    break
            except Exception:
                continue

        if not target_doc:
            return False

        # Add range at the end of the document
        end_pos = target_doc.Content.End - 1
        rng = target_doc.Range(Start=end_pos, End=end_pos)

        # Word paragraph mark is \r
        label = f"\r[পৃষ্ঠা {page_num}]\r" if page_num else "\r[টেক্সট এক্সট্র্যাকশন]\r"
        rng.InsertAfter(label)

        content_to_insert = ""
        for line in text.strip().split("\n"):
            if line.strip():
                content_to_insert += line + "\r"
        content_to_insert += "\r"

        rng.InsertAfter(content_to_insert)
        return True
    except Exception as e:
        print(f"[COM] Error appending to Word: {e}")
        return False
    finally:
        pythoncom.CoUninitialize()


def close_open_word_doc(docx_path: str) -> bool:
    """Save and close the specific document if open in Word, without quitting Word application."""
    if not _HAS_WIN32COM:
        return False

    pythoncom.CoInitialize()
    try:
        abs_path = os.path.abspath(docx_path).lower()
        try:
            word = win32com.client.GetActiveObject("Word.Application")
        except Exception:
            return False  # Word is not running

        for doc in word.Documents:
            try:
                if os.path.abspath(doc.FullName).lower() == abs_path:
                    doc.Close(SaveChanges=True)
                    return True
            except Exception:
                continue
    except Exception as e:
        print(f"[COM] Error closing Word doc: {e}")
    finally:
        pythoncom.CoUninitialize()
    return False



def get_db() -> DatabaseManager:
    """Dependency: get database manager"""
    settings = get_settings()
    return DatabaseManager(settings.db_path)


@router.get("/books/{book_id}")
async def export_to_word(book_id: int, db: DatabaseManager = Depends(get_db)):
    """
    Export all pages of a book to a Word document (.docx).

    The exported document includes all edited text, with page breaks between sections.
    """
    try:
        # Get book info
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        book_title = row["title"]

        # Get all pages
        all_pages = db.get_all_pages(book_id)

        # Create Word document
        doc = Document()
        doc.add_heading(f"বাংলা পাঠ্য নিষ্কাশন: {book_title}", level=1)
        doc.add_paragraph(f"মোট পৃষ্ঠা: {len(all_pages)}")
        doc.add_paragraph("")  # Blank separator

        # Add each page's text
        for page in all_pages:
            page_num = page["page_num"]
            edited_text = page["edited_text"] or page["raw_text"]

            # Add page heading
            doc.add_heading(f"পৃষ্ঠা {page_num}", level=2)

            # Add text content
            if edited_text:
                # Split by newlines to preserve original formatting
                for line in edited_text.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line)

            # Page break (except for last page)
            if page_num != len(all_pages):
                doc.add_page_break()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            doc.save(tmp.name)
            tmp_path = tmp.name

        # Return as downloadable file
        filename = f"{book_title}_বাংলা_টেক্সট.docx"
        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting to Word: {str(e)}"
        )


@router.get("/books/{book_id}/preview")
async def export_preview(
    book_id: int, max_length: int = 500, db: DatabaseManager = Depends(get_db)
):
    """
    Get a preview of the export (first 500 characters by default).

    Useful for showing users what the export will look like.
    """
    try:
        # Get all pages
        all_pages = db.get_all_pages(book_id)

        # Compile text
        preview_text = ""
        for page in all_pages:
            edited_text = page["edited_text"] or page["raw_text"]
            preview_text += edited_text + "\n\n"

        # Truncate to preview length
        preview_text = preview_text[:max_length]
        if len(preview_text) >= max_length:
            preview_text += "..."

        return {
            "preview": preview_text,
            "total_length": sum(
                len(p["edited_text"] or p["raw_text"]) for p in all_pages
            ),
            "page_count": len(all_pages),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating preview: {str(e)}"
        )


@router.post("/connect")
async def connect_word_docx(file: UploadFile = File(...)):
    """
    Upload and connect an existing Word document (.docx).
    The file is saved to backend/connected/ and its path is stored in config.
    Returns the filename that can be displayed in the UI.
    """
    filename = file.filename or "document.docx"
    if not filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="শুধুমাত্র .docx ফাইল সমর্থিত")

    try:
        os.makedirs(_CONNECTED_DIR, exist_ok=True)

        # Save with original name (avoid collisions)
        dest_path = os.path.join(_CONNECTED_DIR, filename)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Store in config
        settings = get_settings()
        settings.connected_docx_path = dest_path
        settings.save_config()

        return {
            "success": True,
            "name": filename,
            "path": dest_path,
            "message": f"✅ {file.filename} সংযুক্ত হয়েছে",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting Word file: {str(e)}"
        )


@router.post("/append")
async def append_to_connected_docx(request: AppendRequest):
    """
    Append extracted text to the currently connected Word document.
    Creates the document if it doesn't exist yet.
    """
    settings = get_settings()

    if not settings.connected_docx_path:
        raise HTTPException(
            status_code=400,
            detail="কোনো Word ডকুমেন্ট সংযুক্ত নেই। প্রথমে 'Connect Word' বাটন ব্যবহার করুন।",
        )

    docx_path = settings.connected_docx_path

    # First attempt to append via COM if the document is open in Microsoft Word
    try:
        if append_via_com(docx_path, request.text, request.page_num):
            return {
                "success": True,
                "message": "✅ পাঠ্য সংযুক্ত করা হয়েছে (সরাসরি ওপেন করা ওয়ার্ড ফাইলে)",
                "total_paragraphs": -1,
            }
    except Exception as e:
        print(f"[COM] Fallback to file write due to error: {e}")

    try:
        if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
            # Create a new document if the file was deleted or is an empty 0-byte file
            doc = Document()
            doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
            doc.add_paragraph("")
        else:
            try:
                doc = Document(docx_path)
            except PackageNotFoundError:
                # Fallback to a new document if the file exists but is corrupted or not a valid docx format
                doc = Document()
                doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
                doc.add_paragraph("")

        # Add a source label if page number is provided
        if request.page_num:
            doc.add_paragraph(f"[পৃষ্ঠা {request.page_num}]")
        else:
            doc.add_paragraph("[টেক্সট এক্সট্র্যাকশন]")

        # Append each line as a paragraph
        for line in request.text.strip().split("\n"):
            if line.strip():
                doc.add_paragraph(line)

        doc.add_paragraph("")  # blank separator line

        # Save
        doc.save(docx_path)
    except PermissionError:
        raise HTTPException(
            status_code=400,
            detail="কানেক্টেড ওয়ার্ড ফাইলটি Microsoft Word-এ ওপেন করা আছে। দয়া করে ফাইলটি বন্ধ করে আবার চেষ্টা করুন।"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Word ফাইলে টেক্সট যোগ করতে ব্যর্থ: {str(e)}"
        )

    # Count total paragraphs
    para_count = len(doc.paragraphs)

    return {
        "success": True,
        "message": "✅ পাঠ্য সংযুক্ত করা হয়েছে",
        "total_paragraphs": para_count,
    }


@router.post("/close")
async def close_docx():
    """
    Close the currently connected Word document if it is open in MS Word.
    """
    settings = get_settings()
    if settings.connected_docx_path:
        closed = close_open_word_doc(settings.connected_docx_path)
        return {"success": True, "closed": closed, "message": "ডকুমেন্ট বন্ধ করা হয়েছে"}
    return {"success": True, "closed": False, "message": "কোনো ডকুমেন্ট সংযুক্ত নেই"}

