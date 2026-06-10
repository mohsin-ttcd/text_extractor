import axios, { AxiosError } from 'axios';

let cachedApiBaseUrl: string | null = null;

const getApiBaseUrl = async (): Promise<string> => {
  if (cachedApiBaseUrl) return cachedApiBaseUrl;

  if (typeof window !== 'undefined' && window.__TAURI__) {
    try {
      const { invoke } = await import('@tauri-apps/api/tauri');
      const url = await invoke<string>('get_backend_url');
      cachedApiBaseUrl = url + '/api';
    } catch (err) {
      console.error('Failed to get backend URL from Tauri:', err);
      cachedApiBaseUrl = 'http://127.0.0.1:8000/api';
    }
  } else {
    cachedApiBaseUrl = '/api';
  }
  return cachedApiBaseUrl;
};

const api = axios.create({
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Resolve baseURL dynamically and asynchronously before any request is sent
api.interceptors.request.use(
  async (config) => {
    config.baseURL = await getApiBaseUrl();
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

const handleApiError = (error: AxiosError) => {
  let message = 'একটি ত্রুটি ঘটেছে';

  if (error.response) {
    const data = error.response.data as any;
    message = data?.detail || data?.error || error.message;
  } else if (error.request) {
    message = 'সার্ভারের সাথে সংযোগ করা যায়নি। নিশ্চিত করুন যে ব্যাকএন্ড চলছে।';
  } else {
    message = error.message;
  }

  console.error('API Error:', { message, error });
  return Promise.reject({ message, error });
};

api.interceptors.response.use(
  (response) => response,
  (error) => handleApiError(error as AxiosError)
);

export const booksAPI = {
  uploadPDF: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/books/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
  },

  listBooks: () => api.get('/books/'),

  getBook: (bookId: number) => api.get(`/books/${bookId}`),

  getProgress: (bookId: number) => api.get(`/books/${bookId}/progress`),

  deleteBook: (bookId: number) => api.delete(`/books/${bookId}`),
};

export const pagesAPI = {
  getPage: (bookId: number, pageNum: number) =>
    api.get(`/pages/${bookId}/${pageNum}`),

  processPage: (bookId: number, pageNum: number, engine: string = 'tesseract') =>
    api.post(`/pages/${pageNum}/ocr`, {
      book_id: bookId,
      page_num: pageNum,
      engine,
    }),

  startBatchOCR: (
    bookId: number,
    pageStart: number = 1,
    pageEnd?: number,
    engine: string = 'tesseract'
  ) =>
    api.post(`/pages/batch-ocr`, {
      book_id: bookId,
      page_start: pageStart,
      page_end: pageEnd,
      engine,
    }),

  getTaskStatus: (taskId: string) =>
    api.get(`/pages/task/${taskId}/status`),

  stopBatchOCR: (taskId: string) =>
    api.post('/pages/batch-ocr/stop', null, {
      params: { task_id: taskId },
    }),

  getTaskStreamUrl: (taskId: string) =>
    typeof window !== 'undefined' && window.__TAURI__
      ? `http://127.0.0.1:8000/api/pages/task/${taskId}/stream`
      : `/api/pages/task/${taskId}/stream`,

  updatePageText: (bookId: number, pageNum: number, editedText: string) =>
    api.post(`/pages/${pageNum}/update-text`, {
      book_id: bookId,
      page_num: pageNum,
      edited_text: editedText,
    }),

  resetPageText: (bookId: number, pageNum: number) =>
    api.put(`/pages/${pageNum}/reset`, {
      book_id: bookId,
      page_num: pageNum,
    }),

  ocrSelection: (
    bookId: number,
    pageNum: number,
    coords: { x1: number; y1: number; x2: number; y2: number }
  ) =>
    api.post(`/pages/${pageNum}/ocr-selection`, {
      book_id: bookId,
      page_num: pageNum,
      x1: coords.x1,
      y1: coords.y1,
      x2: coords.x2,
      y2: coords.y2,
    }),

  saveAnnotations: (
    bookId: number,
    pageNum: number,
    highlights: Array<{ startX: number; startY: number; endX: number; endY: number; color?: string }>
  ) =>
    api.post(`/pages/${pageNum}/save-annotations`, {
      book_id: bookId,
      page_num: pageNum,
      highlights,
    }),
};

export const configAPI = {
  getConfig: () => api.get('/config'),

  updateConfig: (config: {
    tesseract_path?: string;
    dpi?: number;
    connected_docx_path?: string;
    forget_on_close?: boolean;
  }) => api.put('/config', config),
};

export const exportAPI = {
  exportToWord: (bookId: number) =>
    api.get(`/export/books/${bookId}`, {
      responseType: 'blob',
    }),

  getPreview: (bookId: number, maxLength: number = 500) =>
    api.get(`/export/books/${bookId}/preview`, {
      params: { max_length: maxLength },
    }),

  connectDocx: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/export/connect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    });
  },

  appendToConnectedDocx: (bookId: number, text: string, pageNum?: number) =>
    api.post('/export/append', {
      book_id: bookId,
      text,
      page_num: pageNum,
    }),

  appendAllToConnectedDocx: (bookId: number) =>
    api.post('/export/append-all', {
      book_id: bookId,
    }),

  closeDocx: () => api.post('/export/close'),
};

export default api;
