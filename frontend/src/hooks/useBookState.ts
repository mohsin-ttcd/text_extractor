import { useCallback } from 'react';
import { useAppStore, Book } from '../store/appStore';

export const useBookState = () => {
  const { books, currentBook, currentPage, setBooks, setCurrentBook, setCurrentPage } = useAppStore();

  const selectBook = useCallback((book: Book) => {
    setCurrentBook(book);
  }, [setCurrentBook]);

  const clearBook = useCallback(() => {
    setCurrentBook(null);
  }, [setCurrentBook]);

  return { books, currentBook, currentPage, setBooks, selectBook, clearBook, setCurrentPage };
};
