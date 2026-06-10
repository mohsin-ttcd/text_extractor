import { create } from 'zustand';

export interface PageData {
  page_num: number;
  book_id: number;
  page_image: string; // Base64 data URL
  raw_text: string;
  edited_text: string;
  status: string;
  error_message?: string;
}

export interface Book {
  id: number;
  title: string;
  total_pages: number;
  processed_pages: number;
  pdf_path: string;
}

export interface HighlightRect {
  id: number;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  color?: 'yellow' | 'green' | 'red';
}

export interface AppState {
  // Books
  books: Book[];
  currentBook: Book | null;
  setBooks: (books: Book[]) => void;
  setCurrentBook: (book: Book | null) => void;

  // Pages
  currentPage: number;
  currentPageData: PageData | null;
  setCurrentPage: (page: number) => void;
  setCurrentPageData: (data: PageData | null) => void;

  // Editing
  editedText: string;
  fontSize: number;
  zoom: number;
  setEditedText: (text: string) => void;
  setFontSize: (size: number) => void;
  setZoom: (zoom: number) => void;

  // Processing
  isProcessing: boolean;
  processingProgress: { current: number; total: number };
  setIsProcessing: (processing: boolean) => void;
  updateProgress: (current: number, total: number) => void;

  // UI
  isSettingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;

  // Selection mode
  isSelectionActive: boolean;
  setSelectionActive: (active: boolean) => void;

  // Connected Word doc
  connectedDocxName: string;
  setConnectedDocx: (name: string) => void;
  clearConnectedDocx: () => void;

  // Highlights
  isHighlighterActive: boolean;
  highlights: HighlightRect[];
  unsavedHighlights: { [pageNum: number]: HighlightRect[] };
  activeHighlightColor: 'yellow' | 'green' | 'red';
  setHighlighterActive: (active: boolean) => void;
  setActiveHighlightColor: (color: 'yellow' | 'green' | 'red') => void;
  addHighlight: (rect: Omit<HighlightRect, 'id'>) => void;
  clearHighlights: () => void;

  // Reset all
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial books state
  books: [],
  currentBook: null,
  setBooks: (books) => set({ books }),
  setCurrentBook: (book) =>
    set({
      currentBook: book,
      currentPage: 1,
      currentPageData: null,
      editedText: '',
      processingProgress: book
        ? { current: book.processed_pages, total: book.total_pages }
        : { current: 0, total: 0 },
      highlights: [],
      unsavedHighlights: {},
    }),

  // Initial page state
  currentPage: 1,
  currentPageData: null,
  setCurrentPage: (page) =>
    set((state) => ({
      currentPage: page,
      highlights: state.unsavedHighlights[page] || [],
    })),
  setCurrentPageData: (data) => set({ currentPageData: data }),

  // Initial editing state
  editedText: '',
  fontSize: 19,
  zoom: 1.0,
  setEditedText: (text) => set({ editedText: text }),
  setFontSize: (size) => set({ fontSize: size }),
  setZoom: (zoom) => set({ zoom }),

  // Initial processing state
  isProcessing: false,
  processingProgress: { current: 0, total: 0 },
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  updateProgress: (current, total) =>
    set((state) => {
      const updatedBook = state.currentBook
        ? { ...state.currentBook, processed_pages: current }
        : null;
      return {
        processingProgress: { current, total },
        currentBook: updatedBook,
      };
    }),

  // Initial UI state
  isSettingsOpen: false,
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),

  // Initial connected docx state
  connectedDocxName: '',
  setConnectedDocx: (name) => set({ connectedDocxName: name }),
  clearConnectedDocx: () => set({ connectedDocxName: '' }),

  // Initial selection state
  isSelectionActive: false,
  setSelectionActive: (active) => set({ isSelectionActive: active }),

  // Initial highlight state
  isHighlighterActive: false,
  highlights: [],
  unsavedHighlights: {},
  activeHighlightColor: 'yellow',
  setHighlighterActive: (active) => set({ isHighlighterActive: active }),
  setActiveHighlightColor: (color) => set({ activeHighlightColor: color }),
  addHighlight: (rect) =>
    set((state) => {
      const newRect = { ...rect, id: Date.now() };
      const currentHighlights = [...state.highlights, newRect];
      return {
        highlights: currentHighlights,
        unsavedHighlights: {
          ...state.unsavedHighlights,
          [state.currentPage]: currentHighlights,
        },
      };
    }),
  clearHighlights: () =>
    set((state) => ({
      highlights: [],
      unsavedHighlights: {
        ...state.unsavedHighlights,
        [state.currentPage]: [],
      },
    })),

  // Reset to initial state
  reset: () =>
    set({
      books: [],
      currentBook: null,
      currentPage: 1,
      currentPageData: null,
      editedText: '',
      fontSize: 19,
      zoom: 1.0,
      isProcessing: false,
      processingProgress: { current: 0, total: 0 },
      isSettingsOpen: false,
      connectedDocxName: '',
      isSelectionActive: false,
      isHighlighterActive: false,
      highlights: [],
      unsavedHighlights: {},
      activeHighlightColor: 'yellow',
    }),
}));
