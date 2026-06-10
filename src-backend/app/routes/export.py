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
from ..models import AppendRequest, AppendAllRequest

try:
    import win32com.client
    import pythoncom
    _HAS_WIN32COM = True
except ImportError as e:
    _HAS_WIN32COM = False
    try:
        import time
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "com_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- [Import Error at {time.ctime()}] ---\n")
            f.write(f"Failed to import win32com or pythoncom: {e}\n")
    except Exception:
        pass

router = APIRouter(prefix="/api/export", tags=["export"])

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONNECTED_DIR = os.path.join(_BACKEND_DIR, "connected")


def append_via_com(docx_path: str, text: str, page_num: int = None, force_launch: bool = False) -> bool:
    """Append text to the document using COM automation."""
    if not _HAS_WIN32COM:
        return False

    # Ensure file exists
    if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
        try:
            doc = Document()
            doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
            doc.add_paragraph("")
            doc.save(docx_path)
        except Exception as e:
            print(f"[File] Error creating file: {e}")

    pythoncom.CoInitialize()
    try:
        abs_path = os.path.abspath(docx_path).lower()
        try:
            word = win32com.client.GetActiveObject("Word.Application")
        except Exception:
            if not force_launch:
                return False  # Word is not running, and we don't want to launch it
            # Word is not running - launch it
            try:
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = True
            except Exception as e:
                print(f"[COM] Failed to Dispatch Word: {e}")
                return False

        target_doc = None
        for doc in word.Documents:
            try:
                doc_fullname = os.path.abspath(doc.FullName).lower()
                from urllib.parse import unquote
                clean_doc_fullname = unquote(doc_fullname)
                if (doc_fullname == abs_path or 
                    os.path.basename(doc_fullname) == os.path.basename(abs_path) or
                    os.path.basename(clean_doc_fullname) == os.path.basename(abs_path)):
                    target_doc = doc
                    break
            except Exception:
                continue

        if not target_doc:
            if not force_launch:
                return False  # Document is not open, and we don't want to open it
            try:
                target_doc = word.Documents.Open(os.path.abspath(docx_path))
            except Exception as e:
                print(f"[COM] Failed to open document: {e}")
                return False
        else:
            try:
                target_doc.Activate()
            except Exception:
                pass

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

        # Save document
        try:
            target_doc.Save()
        except Exception as e:
            print(f"[COM] Error saving document: {e}")

        return True
    except Exception as e:
        import traceback
        import time
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "com_error.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- [append_via_com Error at {time.ctime()}] ---\n")
                f.write(f"docx_path: {docx_path}\n")
                f.write(f"Exception: {e}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        print(f"[COM] Error appending to Word: {e}")
        return False
    finally:
        pythoncom.CoUninitialize()


def append_all_via_com(docx_path: str, pages: list, force_launch: bool = False) -> bool:
    """Append all processed pages to the Word document using a single COM transaction (very fast)."""
    if not _HAS_WIN32COM:
        return False

    # Ensure file exists
    if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
        try:
            doc = Document()
            doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
            doc.add_paragraph("")
            doc.save(docx_path)
        except Exception as e:
            print(f"[File] Error creating file: {e}")

    pythoncom.CoInitialize()
    try:
        abs_path = os.path.abspath(docx_path).lower()
        try:
            word = win32com.client.GetActiveObject("Word.Application")
        except Exception:
            if not force_launch:
                return False
            # Word is not running - launch it
            try:
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = True
            except Exception as e:
                print(f"[COM] Failed to Dispatch Word: {e}")
                return False

        target_doc = None
        for doc in word.Documents:
            try:
                doc_fullname = os.path.abspath(doc.FullName).lower()
                from urllib.parse import unquote
                clean_doc_fullname = unquote(doc_fullname)
                if (doc_fullname == abs_path or 
                    os.path.basename(doc_fullname) == os.path.basename(abs_path) or
                    os.path.basename(clean_doc_fullname) == os.path.basename(abs_path)):
                    target_doc = doc
                    break
            except Exception:
                continue

        if not target_doc:
            if not force_launch:
                return False
            try:
                target_doc = word.Documents.Open(os.path.abspath(docx_path))
            except Exception as e:
                print(f"[COM] Failed to open document: {e}")
                return False
        else:
            try:
                target_doc.Activate()
            except Exception:
                pass

        # Add range at the end of the document
        end_pos = target_doc.Content.End - 1
        rng = target_doc.Range(Start=end_pos, End=end_pos)

        # Build a single unified string to insert (efficient)
        full_content = ""
        for p in pages:
            page_num = p["page_num"]
            text = p["edited_text"] or p["raw_text"] or ""
            if not text.strip():
                continue

            full_content += f"\r[পৃষ্ঠা {page_num}]\r"
            for line in text.strip().split("\n"):
                if line.strip():
                    full_content += line + "\r"
            full_content += "\r"

        if full_content:
            rng.InsertAfter(full_content)

        # Save document
        try:
            target_doc.Save()
        except Exception as e:
            print(f"[COM] Error saving document: {e}")

        return True
    except Exception as e:
        import traceback
        import time
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "com_error.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- [append_all_via_com Error at {time.ctime()}] ---\n")
                f.write(f"docx_path: {docx_path}\n")
                f.write(f"Exception: {e}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        print(f"[COM] Error appending all to Word: {e}")
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

    # 1. First attempt to append via COM, but ONLY if Word is open and document is open in Word
    try:
        if append_via_com(docx_path, request.text, request.page_num, force_launch=False):
            return {
                "success": True,
                "message": "✅ পাঠ্য সংযুক্ত করা হয়েছে (সরাসরি ওপেন করা ওয়ার্ড ফাইলে)",
                "total_paragraphs": -1,
            }
    except Exception as e:
        print(f"[COM] Initial append_via_com failed: {e}")

    # 2. If Word is closed/off, try to append silently to the file on disk using python-docx
    try:
        if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
            doc = Document()
            doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
            doc.add_paragraph("")
        else:
            try:
                doc = Document(docx_path)
            except PackageNotFoundError:
                doc = Document()
                doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
                doc.add_paragraph("")

        if request.page_num:
            doc.add_paragraph(f"[পৃষ্ঠা {request.page_num}]")
        else:
            doc.add_paragraph("[টেক্সট এক্সট্র্যাকশন]")

        for line in request.text.strip().split("\n"):
            if line.strip():
                doc.add_paragraph(line)

        doc.add_paragraph("")
        doc.save(docx_path)
        
        para_count = len(doc.paragraphs)
        return {
            "success": True,
            "message": "✅ পাঠ্য সংযুক্ত করা হয়েছে",
            "total_paragraphs": para_count,
        }

    except PermissionError:
        # 3. If python-docx throws a PermissionError (locked file due to background ghost/sync issues),
        # fall back to COM force-opening Word as a recovery option to bypass the lock!
        try:
            if append_via_com(docx_path, request.text, request.page_num, force_launch=True):
                return {
                    "success": True,
                    "message": "✅ পাঠ্য সংযুক্ত করা হয়েছে (ওয়ার্ড ফাইলের লকিং সমস্যার কারণে ওয়ার্ড ওপেন করে)",
                    "total_paragraphs": -1,
                }
        except Exception as e2:
            print(f"[COM] Fallback force launch failed: {e2}")

        raise HTTPException(
            status_code=400,
            detail="কানেক্টেড ওয়ার্ড ফাইলটি লক করা আছে বা অন্য প্রোগ্রামে ওপেন আছে। দয়া করে এটি বন্ধ করে আবার চেষ্টা করুন।"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Word ফাইলে টেক্সট যোগ করতে ব্যর্থ: {str(e)}"
        )


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


@router.post("/append-all")
async def append_all_to_connected_docx(request: AppendAllRequest, db: DatabaseManager = Depends(get_db)):
    """
    Append all processed pages of a book to the connected Word document.
    """
    settings = get_settings()

    if not settings.connected_docx_path:
        raise HTTPException(
            status_code=400,
            detail="কোনো Word ডকুমেন্ট সংযুক্ত নেই। প্রথমে 'Connect Word' বাটন ব্যবহার করুন।",
        )

    docx_path = settings.connected_docx_path

    # Get all pages
    all_pages = db.get_all_pages(request.book_id)
    if not all_pages:
        raise HTTPException(status_code=404, detail="বইটির কোনো পৃষ্ঠা খুঁজে পাওয়া যায়নি।")

    # Filter processed pages
    processed_pages = [p for p in all_pages if p["status"] == "ocr_done"]
    if not processed_pages:
        raise HTTPException(
            status_code=400,
            detail="বইটির কোনো পৃষ্ঠা এখনও প্রক্রিয়াকরণ করা হয়নি। প্রথমে 'সব পৃষ্ঠা প্রক্রিয়া করুন' চাপুন।",
        )

    # Sort by page number
    processed_pages.sort(key=lambda x: x["page_num"])

    # 1. First attempt to append via COM, but ONLY if Word is open and document is open in Word
    try:
        if append_all_via_com(docx_path, processed_pages, force_launch=False):
            return {
                "success": True,
                "message": f"✅ সব পৃষ্ঠা ({len(processed_pages)} টি পৃষ্ঠা) Word ফাইলে যুক্ত করা হয়েছে (সরাসরি ওপেন করা ফাইলে)",
                "total_pages_appended": len(processed_pages),
            }
    except Exception as e:
        print(f"[COM] Initial append_all_via_com failed: {e}")

    # 2. If Word is closed/off, try to append silently to the file on disk using python-docx
    try:
        if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
            doc = Document()
            doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
            doc.add_paragraph("")
        else:
            try:
                doc = Document(docx_path)
            except PackageNotFoundError:
                doc = Document()
                doc.add_heading("বাংলা পাঠ্য নিষ্কাশন", level=1)
                doc.add_paragraph("")

        for p in processed_pages:
            page_num = p["page_num"]
            text = p["edited_text"] or p["raw_text"] or ""
            if not text.strip():
                continue

            doc.add_paragraph(f"[পৃষ্ঠা {page_num}]")
            for line in text.strip().split("\n"):
                if line.strip():
                    doc.add_paragraph(line)
            doc.add_paragraph("")  # spacing separator

        doc.save(docx_path)
        return {
            "success": True,
            "message": f"✅ সব পৃষ্ঠা ({len(processed_pages)} টি পৃষ্ঠা) Word ফাইলে যুক্ত করা হয়েছে",
            "total_pages_appended": len(processed_pages),
        }

    except PermissionError:
        # 3. If python-docx throws a PermissionError (locked file), fall back to COM force-opening Word as a recovery option to bypass the lock
        try:
            if append_all_via_com(docx_path, processed_pages, force_launch=True):
                return {
                    "success": True,
                    "message": f"✅ সব পৃষ্ঠা ({len(processed_pages)} টি পৃষ্ঠা) Word ফাইলে যুক্ত করা হয়েছে (ওয়ার্ড ফাইলের লকিং সমস্যার কারণে ওয়ার্ড ওপেন করে)",
                    "total_pages_appended": len(processed_pages),
                }
        except Exception as e2:
            print(f"[COM] Fallback force launch failed: {e2}")

        raise HTTPException(
            status_code=400,
            detail="কানেক্টেড ওয়ার্ড ফাইলটি লক করা আছে বা অন্য প্রোগ্রামে ওপেন আছে। দয়া করে এটি বন্ধ করে আবার চেষ্টা করুন।"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Word ফাইলে টেক্সট যোগ করতে ব্যর্থ: {str(e)}"
        )

