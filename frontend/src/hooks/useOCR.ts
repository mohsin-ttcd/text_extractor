import { useState, useCallback, useEffect } from 'react';
import { pagesAPI, booksAPI } from '../services/api';
import { useAppStore } from '../store/appStore';
import { useOcrStream } from './useOcrStream';

export const usePages = () => {
  const { currentBook, currentPage, setCurrentPageData } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPage = useCallback(
    async (pageNum: number) => {
      if (!currentBook) return;

      setLoading(true);
      setError(null);

      try {
        const response = await pagesAPI.getPage(currentBook.id, pageNum);
        setCurrentPageData(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load page');
        console.error('Error loading page:', err);
      } finally {
        setLoading(false);
      }
    },
    [currentBook, setCurrentPageData]
  );

  // Load page when current page changes
  useEffect(() => {
    if (currentBook && currentPage) {
      loadPage(currentPage);
    }
  }, [currentBook, currentPage, loadPage]);

  return { loading, error, loadPage };
};

export const useOCR = () => {
  const { currentBook, currentPage, updateProgress, setIsProcessing, setCurrentPageData } = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  const processPage = useCallback(
    async (pageNum: number) => {
      if (!currentBook) return;

      try {
        const response = await pagesAPI.processPage(
          currentBook.id,
          pageNum,
          'tesseract'
        );
        // Refresh page after single page OCR
        const pageResponse = await pagesAPI.getPage(currentBook.id, pageNum);
        setCurrentPageData(pageResponse.data);
        
        // Refresh book progress
        const progressResponse = await booksAPI.getProgress(currentBook.id);
        updateProgress(
          progressResponse.data.processed_pages,
          progressResponse.data.total_pages
        );
        
        return response.data;
      } catch (err: any) {
        setError(err.message || 'OCR processing failed');
        throw err;
      }
    },
    [currentBook, setCurrentPageData, updateProgress]
  );

  const startBatchOCR = useCallback(
    async (pageStart: number = 1, pageEnd?: number) => {
      if (!currentBook) return;

      setIsProcessing(true);
      setError(null);

      try {
        const response = await pagesAPI.startBatchOCR(
          currentBook.id,
          pageStart,
          pageEnd || currentBook.total_pages,
          'tesseract'
        );

        setActiveTaskId(response.data.task_id);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to start batch OCR');
        setIsProcessing(false);
        throw err;
      }
    },
    [currentBook, setIsProcessing]
  );

  const stopBatchOCR = useCallback(async () => {
    if (!activeTaskId) return;

    try {
      await pagesAPI.stopBatchOCR(activeTaskId);
      setIsProcessing(false);
      setActiveTaskId(null);
    } catch (err: any) {
      setError(err.message || 'Failed to stop batch OCR');
      throw err;
    }
  }, [activeTaskId, setIsProcessing]);

  // Hook into the live stream using the task ID
  useOcrStream(
    activeTaskId,
    useCallback((event) => {
      // Update progress bar
      updateProgress(event.processed, event.total);

      // If page completed/skipped, refresh progress counts and current page view
      if (event.status === 'completed' || event.status === 'skipped') {
        booksAPI.getProgress(currentBook!.id).then((progressRes) => {
          updateProgress(
            progressRes.data.processed_pages,
            progressRes.data.total_pages
          );
        }).catch(console.error);

        // If the processed page is the page currently open, reload its data to show the OCR result
        if (event.page_num === currentPage) {
          pagesAPI.getPage(currentBook!.id, currentPage).then((pageRes) => {
            setCurrentPageData(pageRes.data);
          }).catch(console.error);
        }
      }
      
      if (event.status === 'task_completed') {
        setIsProcessing(false);
        setActiveTaskId(null);
        if (currentBook) {
          pagesAPI.getPage(currentBook.id, currentPage).then((pageRes) => {
            setCurrentPageData(pageRes.data);
          }).catch(console.error);
        }
        alert('✅ ব্যাচ প্রক্রিয়াকরণ সফলভাবে সম্পন্ন হয়েছে');
      } else if (event.status === 'failed') {
        setIsProcessing(false);
        setActiveTaskId(null);
        setError('Batch OCR failed');
        alert('❌ ব্যাচ প্রক্রিয়াকরণ ব্যর্থ হয়েছে');
      }
    }, [currentBook, currentPage, updateProgress, setIsProcessing, setCurrentPageData]),
    useCallback((err: any) => {
      setError(err);
      setIsProcessing(false);
      setActiveTaskId(null);
      alert(`❌ ব্যাচ প্রক্রিয়াকরণে সমস্যা দেখা দিয়েছে: ${err}`);
    }, [])
  );

  return { processPage, startBatchOCR, stopBatchOCR, taskId: activeTaskId, error };
};

export const useTextEditor = () => {
  const { currentBook, currentPage, editedText, setEditedText } = useAppStore();
  const [saving, setSaving] = useState(false);

  const saveText = useCallback(
    async (text: string) => {
      if (!currentBook || !currentPage) return;

      setSaving(true);
      try {
        await pagesAPI.updatePageText(currentBook.id, currentPage, text);
        setEditedText(text);
        return true;
      } catch (err) {
        console.error('Error saving text:', err);
        return false;
      } finally {
        setSaving(false);
      }
    },
    [currentBook, currentPage, setEditedText]
  );

  const resetText = useCallback(
    async (originalText: string) => {
      if (!currentBook || !currentPage) return;

      setSaving(true);
      try {
        await pagesAPI.resetPageText(currentBook.id, currentPage);
        setEditedText(originalText);
        return true;
      } catch (err) {
        console.error('Error resetting text:', err);
        return false;
      } finally {
        setSaving(false);
      }
    },
    [currentBook, currentPage, setEditedText]
  );

  return { editedText, setEditedText, saveText, resetText, saving };
};
