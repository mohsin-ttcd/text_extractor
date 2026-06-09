# Updated Implementation Plan: Selection OCR & Tesseract Language Pack Configuration

We are implementing two major updates to resolve Tesseract fallback errors and support targeted text extraction:
1.  **Detailed Tesseract Language Error Handling**: Catching missing `ben.traineddata` errors and displaying helpful setup guides to the user.
2.  **Selective PDF OCR (Page/Line-level Selection)**: Adding mouse drag-to-select functionality on the PDF canvas to crop and extract specific regions/lines, alongside "Extract Current Page" and "Batch Extract" controls.

---

## User Review Required

> [!IMPORTANT]
> **1. Handling Missing Tesseract Language Packs**
> When the offline engine runs without the Bengali language file (`ben.traineddata`), Tesseract crashes.
> *   **Solution**: We will catch `TesseractError` inside `ocr_processor.py`. If it matches missing language data, we will raise a `TesseractLanguageError`. The GUI will catch this and show a descriptive dialog detailing how to download the file from Tesseract's GitHub and place it in the correct directory.
> 
> **2. Bounding Box Selection Mapping**
> To allow the user to extract a specific line or region, they will drag their mouse on the PDF preview pane to draw a red dashed bounding box.
> *   **Solution**: We will map Tkinter canvas coordinates `(canvasx, canvasy)` directly to the PIL Image dimensions. When the user clicks "Extract Selected Region", the app will crop that region and send only the cropped sub-image to the OCR engines. The resulting text will be inserted at the current editor cursor position (`INSERT`).

---

## Proposed System & UI Changes

```
+--------------------------------------------------------------------------+
|  [Select Book]            [⚙️ settings]                        User: Prof|
+--------------------------------------------------------------------------+
|  LEFT PANE (Original Scan)            | RIGHT PANE (Editor panel)        |
|  +---------------------------------+  |                                  |
|  | [ + ] [ - ]    [নির্বাচিত অংশ অনুবাদ] |  |  --- পৃষ্ঠা ৫ ---                 |
|  | +-----------------------------+ |  |                                  |
|  | |                             | |  |  ১৮৫২ সালের...                   |
|  | |  [=================]        | |  |                                  |
|  | |  [  Selected Region  ]      | |  |  [Cursor here]                   |
|  | |  [=================]        | |  |                                  |
|  | +-----------------------------+ |  |                                  |
|  +---------------------------------+  +----------------------------------+
|  [পূর্ববর্তী] [পৃষ্ঠা ৫ / ১২০] [পরবর্তী]  [অনুবাদ শুরু] [এই পৃষ্ঠা] [সেভ] [এক্সপোর্ট] |
+--------------------------------------------------------------------------+
```

### 1. Canvas Selection Logic
We will bind three mouse events to `self.scroll_canvas` in `app_gui.py`:
*   `ButtonPress-1` (Left Click): Clear any existing rectangle, record start positions using `canvas.canvasx(event.x)` and `canvas.canvasy(event.y)`.
*   `B1-Motion` (Left Drag): Draw/resize a dashed red rectangle using `self.scroll_canvas.create_rectangle`.
*   `ButtonRelease-1` (Release): Record end coordinates. If the selection area is larger than 10x10 pixels, enable the floating `[নির্বাচিত অংশ অনুবাদ করুন]` button.

### 2. Page & Region OCR Execution
*   **Extract Current Page**: We will add a button `[এই পৃষ্ঠাটি নিষ্কাশন করুন]` to run OCR solely on the active page image, updating only the current page database record.
*   **Extract Selection**: A floating button `self.btn_extract_selection` will appear near the selection. Clicking it crops the PIL image, runs the background OCR worker, inserts the resulting Bengali text directly at the cursor position in the text editor, and clears the selection rectangle.

---

## Proposed Changes

### [PDF text extractor Workspace]

#### [MODIFY] [ocr_processor.py](file:///f:/Programing%20Project/CLI/PDF%20text%20ectractor/ocr_processor.py)
*   Define a custom `TesseractLanguageError` exception class.
*   Update `extract_text_tesseract()` and `process_page()` to check for language load errors and raise this custom exception.
*   Add a `process_cropped_image(pil_image, engine_choice)` function to handle OCR on sub-regions.

#### [MODIFY] [app_gui.py](file:///f:/Programing%20Project/CLI/PDF%20text%20ectractor/app_gui.py)
*   Implement mouse bindings for selection rectangles on the canvas.
*   Add a floating `[নির্বাচিত অংশ নিষ্কাশন করুন]` button over the left pane.
*   Add a bottom bar button `[শুধুমাত্র এই পৃষ্ঠা]` to extract the current page.
*   Implement `extract_selection()` and `extract_current_page()` background thread runners.
*   Implement warning dialog popups for missing Tesseract language packs.

---

## Verification Plan

1.  **Tesseract Failure Emulation**: Move or rename `ben.traineddata` in the local Tesseract directory, run OCR, and verify that the GUI shows the helpful instruction window instead of crashing.
2.  **Visual Selection Test**: Open a PDF, click and drag to draw a box around a single line, click "Extract Selection", and verify the text is successfully inserted at the editor cursor.
3.  **Current Page Test**: Verify that clicking `[শুধুমাত্র এই পৃষ্ঠা]` extracts text only for the current page and does not advance pages or start batch loops.
