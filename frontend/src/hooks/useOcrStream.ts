import { useEffect, useRef, useCallback } from 'react';
import { pagesAPI } from '../services/api';

interface OcrStreamEvent {
  page_num: number;
  status: string;
  preview: string;
  processed: number;
  total: number;
}

export const useOcrStream = (
  taskId: string | null,
  onEvent: (event: OcrStreamEvent) => void,
  onError?: (error: string) => void,
) => {
  const eventSourceRef = useRef<EventSource | null>(null);

  const stop = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;

    const es = new EventSource(pagesAPI.getTaskStreamUrl(taskId));
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      try {
        const data: OcrStreamEvent = JSON.parse(e.data);
        onEvent(data);
        if (data.status === 'stopped') {
          es.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      onError?.('SSE connection failed');
      es.close();
    };

    es.addEventListener('done', () => {
      onEvent({ status: 'task_completed' } as any);
      es.close();
    });

    es.addEventListener('error', (e: any) => {
      let errMsg = 'Task failed';
      try {
        const data = JSON.parse(e.data);
        errMsg = data.error || errMsg;
      } catch {}
      onError?.(errMsg);
      es.close();
    });

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [taskId, onEvent, onError]);

  return { stop };
};
