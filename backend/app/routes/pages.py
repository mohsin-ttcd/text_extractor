"""
Pages management and OCR processing endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
import os
import base64
import json
import threading
import time
import asyncio
from io import BytesIO
from PIL import Image
import fitz
from typing import Optional
from ..models import (
    TextEditRequest,
    PageResetRequest,
    OCRRequest,
    BatchOCRRequest,
    SelectionOCRRequest,
    SaveHighlightsRequest,
)
from ..database import DatabaseManager
from ..ocr_processor import BengaliOcrProcessor
from ..config import get_settings

router = APIRouter(prefix="/api/pages", tags=["pages"])

# Store active processing tasks
processing_tasks = {}


def get_db() -> DatabaseManager:
    """Dependency: get database manager"""
    settings = get_settings()
    return DatabaseManager(settings.db_path)


def get_processor(
    settings=Depends(get_settings), db=Depends(get_db)
) -> BengaliOcrProcessor:
    """Dependency: get OCR processor"""
    return BengaliOcrProcessor(
        db_manager=db, tesseract_path=settings.tesseract_path, dpi=settings.dpi
    )


@router.get("/{book_id}/{page_num}/image")
async def get_page_image(
    book_id: int,
    page_num: int,
):
    """Get raw page image as PNG bytes."""
    try:
        settings = get_settings()
        db = DatabaseManager(settings.db_path)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        doc = fitz.open(row["pdf_path"])
        page = doc[page_num - 1]
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        doc.close()
        return Response(content=buffer.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")


@router.get("/{book_id}/{page_num}")
async def get_page(
    book_id: int,
    page_num: int,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Get page data including:
    - page_image: Base64 encoded PNG of the page
    - raw_text: Original OCR output
    - edited_text: User-edited text
    - status: Current processing status
    """
    try:
        # Get page text data
        page_data = db.get_page(book_id, page_num)
        if not page_data:
            raise HTTPException(status_code=404, detail="Page not found")

        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]

        # Render page to image and convert to base64
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]

        # Render at 150 DPI for faster response
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

        # Convert to PIL Image and then to base64
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        doc.close()

        return {
            "page_num": page_num,
            "book_id": book_id,
            "page_image": f"data:image/png;base64,{img_base64}",
            "raw_text": page_data["raw_text"],
            "edited_text": page_data["edited_text"],
            "status": page_data["status"],
            "error_message": page_data["error_message"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching page: {str(e)}")


@router.post("/{page_id}/ocr")
async def ocr_single_page(
    page_id: int,
    request: OCRRequest,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Process a single page with OCR.

    Returns:
    - raw_text: Extracted Bengali text
    - status: 'ocr_done' or 'error'
    - message: Status message in Bengali
    """
    try:
        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path FROM books WHERE id = ?", (request.book_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]

        # Process the page (this will save to database)
        raw_text, engine_used, error_msg = processor.process_page(
            pdf_path, request.page_num, request.book_id
        )

        return {
            "success": True,
            "page_num": request.page_num,
            "raw_text": raw_text,
            "engine_used": engine_used,
            "status": "ocr_done",
            "message": f"✅ পৃষ্ঠা {request.page_num} সফলভাবে প্রক্রিয়া করা হয়েছে",
        }
    except Exception as e:
        error_str = str(e)
        db.save_page_ocr(
            request.book_id,
            request.page_num,
            "",
            status="error",
            error_message=error_str,
        )
        raise HTTPException(status_code=500, detail=f"OCR error: {error_str}")


@router.post("/batch-ocr")
async def batch_ocr(
    request: BatchOCRRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    Start batch OCR processing for multiple pages in the background.

    Returns:
    - task_id: ID to track progress
    - message: Confirmation message
    """
    try:
        # Get PDF path
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path, total_pages FROM books WHERE id = ?",
                (request.book_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]
        total_pages = row["total_pages"]

        # Determine page range
        page_start = max(1, request.page_start or 1)
        page_end = min(request.page_end or total_pages, total_pages)
        if page_start > page_end:
            raise HTTPException(status_code=400, detail="Invalid page range")

        # Start background processing
        task_id = f"batch_{request.book_id}_{int(time.time())}"
        stop_event = threading.Event()
        processing_tasks[task_id] = {
            "stop_event": stop_event,
            "status": "running",
            "events": [],
        }

        def batch_process_worker():
            """Background worker for batch processing"""
            try:

                def progress_callback(page, status, preview, msg):
                    event = {
                        "page_num": page,
                        "status": status,
                        "preview": preview,
                        "processed": page - page_start + 1,
                        "total": page_end - page_start + 1,
                    }
                    processing_tasks[task_id].setdefault("events", []).append(event)

                    if status == "completed":
                        try:
                            settings = get_settings()
                            if settings.connected_docx_path:
                                page_data = db.get_page(request.book_id, page)
                                if page_data:
                                    text = page_data.get("edited_text") or page_data.get("raw_text") or ""
                                    if text.strip():
                                        from .export import append_via_com
                                        from docx import Document
                                        from docx.opc.exceptions import PackageNotFoundError
                                        docx_path = settings.connected_docx_path
                                        com_success = False
                                        try:
                                            com_success = append_via_com(docx_path, text, page)
                                        except Exception as com_err:
                                            print(f"[COM Batch] Error appending page {page}: {com_err}")
                                        
                                        if not com_success:
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
                                                
                                                doc.add_paragraph(f"[পৃষ্ঠা {page}]")
                                                for line in text.strip().split("\n"):
                                                    if line.strip():
                                                        doc.add_paragraph(line)
                                                doc.add_paragraph("")
                                                doc.save(docx_path)
                                            except Exception as docx_err:
                                                print(f"[docx Batch] Error writing file: {docx_err}")
                        except Exception as e:
                            print(f"[Batch Append] Error in background append: {e}")

                processor.process_book_background(
                    pdf_path,
                    request.book_id,
                    page_start,
                    page_end,
                    progress_callback=progress_callback,
                    stop_event=stop_event,
                )
                processing_tasks[task_id]["status"] = (
                    "stopped" if stop_event.is_set() else "completed"
                )
            except Exception as e:
                processing_tasks[task_id]["error"] = str(e)
                processing_tasks[task_id]["status"] = "failed"

        background_tasks.add_task(batch_process_worker)

        return {
            "success": True,
            "task_id": task_id,
            "book_id": request.book_id,
            "page_start": page_start,
            "page_end": page_end,
            "message": f"✅ ব্যাচ প্রক্রিয়াকরণ শুরু হয়েছে: পৃষ্ঠা {page_start}-{page_end}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting batch OCR: {str(e)}"
        )


@router.get("/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get the status of a batch processing task.

    Returns:
    - status: 'running', 'completed', or 'failed'
    - error: Error message if failed
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    latest_event = task.get("events", [])[-1] if task.get("events") else {}
    return {
        "task_id": task_id,
        "status": task["status"],
        "error": task.get("error", None),
        "processed": latest_event.get("processed", 0),
        "total": latest_event.get("total", 0),
        "current_page": latest_event.get("page_num"),
    }


@router.get("/task/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """SSE endpoint that streams batch OCR progress events."""

    async def event_generator():
        last_count = 0
        while True:
            if task_id not in processing_tasks:
                yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                break

            task = processing_tasks[task_id]
            events = task.get("events", [])

            while last_count < len(events):
                event = events[last_count]
                yield f"data: {json.dumps(event)}\n\n"
                last_count += 1

            if task["status"] == "completed":
                yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
                break
            elif task["status"] == "stopped":
                yield f"event: done\ndata: {json.dumps({'status': 'stopped'})}\n\n"
                break
            elif task["status"] == "failed":
                yield f"event: error\ndata: {json.dumps({'error': task.get('error', 'Unknown error')})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/batch-ocr/stop")
async def stop_batch_ocr(task_id: str = Query(...)):
    """Stop a running batch OCR task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    if task["status"] != "running":
        raise HTTPException(status_code=400, detail="Task is not running")

    task["stop_event"].set()
    task["status"] = "stopped"
    return {"success": True, "message": "Batch OCR stopped"}


@router.post("/{page_id}/ocr-selection")
async def ocr_selection(
    page_id: int,
    request: SelectionOCRRequest,
    db: DatabaseManager = Depends(get_db),
    processor: BengaliOcrProcessor = Depends(get_processor),
):
    """
    OCR a selected region of a page.

    Accepts crop coordinates (x1,y1,x2,y2) relative to the page image,
    renders the page, crops the region, runs Tesseract, returns text.
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path FROM books WHERE id = ?", (request.book_id,)
            )
            row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        doc = fitz.open(row["pdf_path"])
        page = doc[request.page_num - 1]
        zoom = 150 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        # Crop the selected region
        x1, y1 = int(min(request.x1, request.x2)), int(min(request.y1, request.y2))
        x2, y2 = int(max(request.x1, request.x2)), int(max(request.y1, request.y2))
        cropped = pil_img.crop((x1, y1, x2, y2))

        # Run Tesseract on the cropped region
        text = processor.process_cropped_image(cropped)

        return {"success": True, "text": text, "page_num": request.page_num}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Selection OCR error: {str(e)}")


@router.post("/{page_id}/update-text")
async def update_page_text(
    page_id: int, request: TextEditRequest, db: DatabaseManager = Depends(get_db)
):
    """
    Update the edited text for a page.

    This is called when the user manually edits text in the editor.
    """
    try:
        db.save_page_edit(request.book_id, request.page_num, request.edited_text)

        return {
            "success": True,
            "page_num": request.page_num,
            "message": "✅ পাঠ্য সংরক্ষিত হয়েছে",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating text: {str(e)}")


@router.put("/{page_id}/reset")
async def reset_page_text(
    page_id: int, request: PageResetRequest, db: DatabaseManager = Depends(get_db)
):
    """
    Reset edited text back to raw OCR output.

    This allows users to discard manual edits and start over.
    """
    try:
        page_num = request.page_num or page_id
        page_data = db.get_page(request.book_id, page_num)
        if not page_data:
            raise HTTPException(status_code=404, detail="Page not found")

        # Revert edited_text to raw_text
        db.save_page_edit(request.book_id, page_num, page_data["raw_text"])

        return {
            "success": True,
            "page_num": page_num,
            "text": page_data["raw_text"],
            "message": "✅ মূল লেখায় ফিরে গেছেন",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting text: {str(e)}")


@router.post("/{page_id}/save-annotations")
async def save_page_annotations(
    page_id: int,
    request: SaveHighlightsRequest,
    db: DatabaseManager = Depends(get_db),
):
    """
    Save highlight annotations permanently into the PDF file in-place.
    """
    try:
        # 1. Get PDF path from database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_path FROM books WHERE id = ?", (request.book_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Book not found")

        pdf_path = row["pdf_path"]
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail=f"PDF file not found at {pdf_path}")

        # 2. Open PDF and get the page
        doc = fitz.open(pdf_path)
        page = doc[request.page_num - 1]

        # 3. Scale highlights to PDF points
        # The frontend renders image at 150 DPI. PDF is in points (72 points = 1 inch).
        # Scale factor = 72 / 150
        scale = 72.0 / 150.0

        for hl in request.highlights:
            # Scale coordinates
            x1 = hl.startX * scale
            y1 = hl.startY * scale
            x2 = hl.endX * scale
            y2 = hl.endY * scale

            # Ensure coordinates are in correct min/max order
            rx1, rx2 = min(x1, x2), max(x1, x2)
            ry1, ry2 = min(y1, y2), max(y1, y2)

            rect = fitz.Rect(rx1, ry1, rx2, ry2)

            # Add highlight annotation
            annot = page.add_rect_annot(rect)
            
            # Map colors: RGB normalized to [0.0, 1.0]
            color_map = {
                "yellow": [1.0, 0.9, 0.0],
                "green": [0.2, 0.8, 0.2],
                "red": [0.9, 0.2, 0.2]
            }
            c = color_map.get(hl.color, [1.0, 0.9, 0.0])
            
            # Set stroke/fill to be semi-transparent color
            annot.set_colors(stroke=c, fill=c)
            annot.set_opacity(0.35)
            annot.update()

        # 4. Save PDF in-place using incremental save, falling back to temp file if locked
        try:
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
        except Exception:
            import shutil
            temp_path = pdf_path + ".tmp"
            doc.save(temp_path, deflate=True)
            doc.close()
            shutil.move(temp_path, pdf_path)

        return {
            "success": True,
            "page_num": request.page_num,
            "message": "✅ হাইলাইটগুলি পিডিএফ ফাইলে সফলভাবে সংরক্ষণ করা হয়েছে",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving PDF annotations: {str(e)}")
