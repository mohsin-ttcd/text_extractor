import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/appStore';
import { booksAPI } from '../services/api';

interface BooksListProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * BooksList Component
 * Shows all uploaded books and allows selecting one to process
 */
export const BooksList: React.FC<BooksListProps> = ({ isOpen, onClose }) => {
  const { setCurrentBook, books, setBooks } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load books on mount
  useEffect(() => {
    if (isOpen) {
      loadBooks();
    }
  }, [isOpen]);

  const loadBooks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await booksAPI.listBooks();
      setBooks(response.data.books);
    } catch (err: any) {
      setError(err.message || 'Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectBook = (book: any) => {
    setCurrentBook({
      id: book.id,           // API returns 'id', not 'book_id'
      title: book.title,
      total_pages: book.total_pages,
      processed_pages: book.processed_pages ?? 0,
      pdf_path: book.pdf_path,
    });
    onClose();
  };

  const handleDeleteBook = async (bookId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('এই বই মুছে ফেলতে নিশ্চিত? এটি পূর্ববত করা যাবে না।')) {
      return;
    }
    try {
      await booksAPI.deleteBook(bookId);
      await loadBooks();
    } catch (err: any) {
      alert('ত্রুটি: বই মোছা যায়নি');
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            📚 আপনার বইগুলি
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded">
            {error}
          </div>
        )}

        {/* Loading state */}
        {loading ? (
          <p className="text-center text-gray-600 dark:text-gray-400 py-8">
            লোড করছে...
          </p>
        ) : books.length === 0 ? (
          <p className="text-center text-gray-600 dark:text-gray-400 py-8">
            কোন বই পাওয়া যায়নি। প্রথমে একটি পিডিএফ ফাইল আপলোড করুন।
          </p>
        ) : (
          <div className="space-y-3">
            {books.map((book: any) => {
              const progress = Math.round(
                ((book.processed_pages ?? 0) / (book.total_pages || 1)) * 100
              );
              return (
                <div
                  key={book.id}
                  onClick={() => handleSelectBook(book)}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {book.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {book.total_pages} পৃষ্ঠা
                      </p>
                    </div>
                    <button
                      onClick={(e) => handleDeleteBook(book.id, e)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 text-sm font-medium"
                    >
                      🗑️ মোছা
                    </button>
                  </div>

                  {/* Progress bar */}
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400 w-10 text-right">
                      {progress}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer buttons */}
        <div className="mt-6 flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-700 text-gray-900 dark:text-white rounded transition font-medium"
          >
            বন্ধ করুন
          </button>
          <button
            onClick={loadBooks}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition font-medium"
          >
            রিফ্রেশ করুন
          </button>
        </div>
      </div>
    </div>
  );
};

export default BooksList;
