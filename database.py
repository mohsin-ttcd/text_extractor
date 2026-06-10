import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="bengali_ocr.db"):
        self.db_path = db_path
        self.initialize_db()

    def get_connection(self):
        """Returns a connection to the SQLite database with row factory enabled."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self):
        """Initializes tables for books and pages if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_path TEXT UNIQUE,
                    title TEXT,
                    total_pages INTEGER,
                    processed_pages INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    page_num INTEGER,
                    raw_text TEXT DEFAULT '',
                    edited_text TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    error_message TEXT DEFAULT '',
                    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                    UNIQUE(book_id, page_num)
                )
            """)
            conn.commit()

    def register_book(self, pdf_path, total_pages):
        """
        Registers a new book in the database, or retrieves details if it already exists.
        Initializes entries for all pages in a 'pending' state if new.
        """
        pdf_path = os.path.abspath(pdf_path)
        title = os.path.splitext(os.path.basename(pdf_path))[0]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if book already exists
            cursor.execute("SELECT id, total_pages FROM books WHERE pdf_path = ?", (pdf_path,))
            row = cursor.fetchone()
            
            if row:
                book_id = row['id']
                # If total pages changed, update it
                if row['total_pages'] != total_pages:
                    cursor.execute("UPDATE books SET total_pages = ? WHERE id = ?", (total_pages, book_id))
                    conn.commit()
                return book_id
            
            # Insert new book
            cursor.execute(
                "INSERT INTO books (pdf_path, title, total_pages) VALUES (?, ?, ?)",
                (pdf_path, title, total_pages)
            )
            book_id = cursor.lastrowid
            
            # Create page entries in a 'pending' state
            for page_num in range(1, total_pages + 1):
                cursor.execute(
                    "INSERT OR IGNORE INTO pages (book_id, page_num, status) VALUES (?, ?, 'pending')",
                    (book_id, page_num)
                )
            
            conn.commit()
            return book_id

    def get_book_progress(self, book_id):
        """Returns the number of processed pages and total pages for a book."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as processed FROM pages WHERE book_id = ? AND status = 'ocr_done'",
                (book_id,)
            )
            processed = cursor.fetchone()['processed']
            
            cursor.execute("SELECT total_pages FROM books WHERE id = ?", (book_id,))
            total = cursor.fetchone()['total_pages']
            
            # Sync processed_pages count in the books table
            cursor.execute("UPDATE books SET processed_pages = ? WHERE id = ?", (processed, book_id))
            conn.commit()
            
            return processed, total

    def get_page(self, book_id, page_num):
        """Retrieves page details for a specific page number in a book."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_text, edited_text, status, error_message FROM pages WHERE book_id = ? AND page_num = ?",
                (book_id, page_num)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_page_ocr(self, book_id, page_num, raw_text, status='ocr_done', error_message='', overwrite_edited=False):
        """Saves initial OCR results for a page and updates status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT status, edited_text FROM pages WHERE book_id = ? AND page_num = ?", (book_id, page_num))
            row = cursor.fetchone()
            
            edited_text = raw_text
            if row:
                prev_status = row['status']
                prev_edited = row['edited_text']
                # Overwrite edited_text if:
                # - We explicitly requested to overwrite (overwrite_edited=True)
                # - The previous status was an error or pending (meaning any text in it is just a placeholder)
                if not overwrite_edited and prev_status not in ('error', 'pending') and prev_edited and prev_edited.strip() != "":
                    edited_text = prev_edited

            cursor.execute(
                """
                UPDATE pages 
                SET raw_text = ?, edited_text = ?, status = ?, error_message = ? 
                WHERE book_id = ? AND page_num = ?
                """,
                (raw_text, edited_text, status, error_message, book_id, page_num)
            )
            conn.commit()
            
            # Trigger progress sync in books table
            self.get_book_progress(book_id)

    def save_page_edit(self, book_id, page_num, edited_text):
        """Saves manual edits made to a page's transcription."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE pages SET edited_text = ? WHERE book_id = ? AND page_num = ?",
                (edited_text, book_id, page_num)
            )
            conn.commit()

    def get_all_pages(self, book_id):
        """Retrieves all pages for a book ordered by page number."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT page_num, raw_text, edited_text, status FROM pages WHERE book_id = ? ORDER BY page_num ASC",
                (book_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_book(self, book_id):
        """Deletes a book and all associated page records (Cascaded)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
