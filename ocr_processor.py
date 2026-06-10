import os
import io
import time
import gc
import socket
import urllib.request
import numpy as np
import cv2
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


class TesseractLanguageError(Exception):
    """Raised when Tesseract is missing the required Bengali language pack."""

    pass


class TesseractNotFoundError(Exception):
    """Raised when Tesseract executable is not found on the local filesystem."""

    pass


class BengaliOcrProcessor:
    def __init__(self, db_manager, tesseract_path=None, dpi=300):
        self.db = db_manager
        self.dpi = dpi

        # Configure Tesseract Path
        if tesseract_path:
            self.tesseract_path = tesseract_path
        else:
            # Look in standard locations
            paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                "tesseract.exe",
            ]
            self.tesseract_path = paths[0]
            for p in paths:
                if os.path.exists(p):
                    self.tesseract_path = p
                    break

        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def get_pdf_page_count(self, pdf_path):
        """Returns the total number of pages in the PDF file."""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count

    def preprocess_image(self, pil_image):
        """
        Applies OpenCV adaptive thresholding, denoising, and deskewing
        to optimize historical 1850s text legibility for Tesseract OCR.
        """
        # Convert PIL Image to OpenCV BGR format
        cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # 1. Grayscale
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # 2. Bilateral Denoising (preserves sharp character edges better than Gaussian blur)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 3. Sauvola/Adaptive Thresholding (binarizes yellowed paper and handles shadows)
        binarized = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
        )

        # 4. Deskewing (Rotates page slightly if tilted)
        coords = np.column_stack(np.where(binarized == 0))
        angle = 0.0
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle

            if abs(angle) < 10.0 and abs(angle) > 0.5:
                (h, w) = binarized.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                binarized = cv2.warpAffine(
                    binarized,
                    M,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=255,
                )

        # Convert back to PIL Image
        return Image.fromarray(binarized)

    def extract_text_tesseract(self, pil_image):
        """Extracts text using local Tesseract OCR engine with explicit language pack checks."""
        local_tessdata_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "tessdata"
        )
        target_file = os.path.join(local_tessdata_dir, "ben.traineddata")

        # Proactively ensure the file exists locally
        if not os.path.exists(target_file):
            try:
                if not os.path.exists(local_tessdata_dir):
                    os.makedirs(local_tessdata_dir)
                url = (
                    "https://github.com/tesseract-ocr/tessdata/raw/main/ben.traineddata"
                )
                urllib.request.urlretrieve(url, target_file)
            except Exception:
                pass

        # Check standard global path first, or default to local folder if present
        global_tessdata = r"C:\Program Files\Tesseract-OCR\tessdata"
        global_ben_file = os.path.join(global_tessdata, "ben.traineddata")

        if os.path.exists(global_ben_file):
            # If the user has it in their main Tesseract installation, clear TESSDATA_PREFIX
            # to let Tesseract fallback to its native directory smoothly
            if "TESSDATA_PREFIX" in os.environ:
                del os.environ["TESSDATA_PREFIX"]
        elif os.path.exists(target_file):
            # Otherwise use our local workspace fallback directory
            os.environ["TESSDATA_PREFIX"] = local_tessdata_dir

        config_str = "--psm 3"
        try:
            return pytesseract.image_to_string(
                pil_image, lang="ben+eng", config=config_str
            )
        except pytesseract.TesseractNotFoundError:
            raise TesseractNotFoundError(
                "টেসারেক্ট ওসিআর (Tesseract OCR) আপনার কম্পিউটারে খুঁজে পাওয়া যায়নি।\n\n"
                "দয়া করে এটি ইনস্টল করুন এবং সেটিংস থেকে এর সঠিক পাথ সিলেক্ট করুন।"
            )
        except pytesseract.TesseractError as e:
            err_msg = str(e)
            if (
                "ben.traineddata" in err_msg
                or "ben" in err_msg
                or "Failed loading language" in err_msg
            ):
                raise TesseractLanguageError(
                    "টেসারেক্ট বাংলা ল্যাঙ্গুয়েজ প্যাক (ben.traineddata) খুঁজে পাওয়া যায়নি।\n\n"
                    "১. https://github.com/tesseract-ocr/tessdata/raw/main/ben.traineddata থেকে ফাইলটি ডাউনলোড করুন।\n"
                    "২. ফাইলটি Tesseract-OCR ইনস্টলেশন ডিরেক্টরির 'tessdata' ফোল্ডারে রাখুন (যেমন: C:\\Program Files\\Tesseract-OCR\\tessdata\\)।"
                )
            raise e

    def process_page(self, pdf_path, page_num, book_id):
        """
        Loads, renders, preprocesses, and extracts text for a single page.
        Saves OCR result directly to the SQLite database.
        """
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]

        # Render PDF page to high-res image
        zoom = self.dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        doc.close()

        # Preprocess
        processed_img = self.preprocess_image(pil_img)

        raw_text = ""
        engine_used = "Tesseract-OCR (ben+eng)"
        error_msg = ""

        try:
            raw_text = self.extract_text_tesseract(processed_img)
        except Exception as e:
            error_msg = str(e)
            raise e

        # Save result to DB
        self.db.save_page_ocr(
            book_id,
            page_num,
            raw_text,
            status="ocr_done",
            error_message=error_msg,
            overwrite_edited=True,
        )

        # Memory cleanup
        del processed_img
        del pil_img
        gc.collect()

        return raw_text, engine_used, error_msg

    def process_cropped_image(self, pil_image, engine_choice=None):
        """
        Extracts text from a cropped image area (representing targeted lines or words).
        Does not write to database automatically.
        """
        # Preprocess the cropped area
        processed_img = self.preprocess_image(pil_image)
        return self.extract_text_tesseract(processed_img)

    def process_book_background(
        self, pdf_path, book_id, page_start, page_end, progress_callback, stop_event
    ):
        """
        Background worker that processes a book page-by-page.
        Can be stopped at any time via the stop_event.
        """
        pdf_path = os.path.abspath(pdf_path)

        for page_num in range(page_start, page_end + 1):
            if stop_event.is_set():
                break

            try:
                # Retrieve current state to check if page is already processed
                page_data = self.db.get_page(book_id, page_num)

                if (
                    page_data
                    and page_data["status"] == "ocr_done"
                    and page_data["raw_text"].strip() != ""
                ):
                    progress_callback(
                        page_num, "skipped", page_data["raw_text"][:100], ""
                    )
                    continue

                # Process the page
                text, engine, err = self.process_page(pdf_path, page_num, book_id)
                preview = text[:100].replace("\n", " ") if text else ""

                progress_callback(
                    page_num, "completed", preview, f"Engine: {engine}. {err}"
                )

            except TesseractLanguageError as tle:
                progress_callback(page_num, "tess_lang_error", "", str(tle))
                break
            except TesseractNotFoundError as tne:
                progress_callback(page_num, "tess_not_found", "", str(tne))
                break
            except Exception as e:
                self.db.save_page_ocr(
                    book_id, page_num, "", status="error", error_message=str(e)
                )
                progress_callback(page_num, "error", "", str(e))

            time.sleep(0.1)
