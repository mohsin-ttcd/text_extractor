import { useState, useCallback, useRef } from 'react';
import { useAppStore } from '../store/appStore';

export interface SelectionRect {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export const useSelection = () => {
  const [selection, setSelection] = useState<SelectionRect | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const isHighlighterActive = useAppStore((s) => s.isHighlighterActive);
  const addHighlight = useAppStore((s) => s.addHighlight);
  const activeHighlightColor = useAppStore((s) => s.activeHighlightColor);
  const zoom = useAppStore((s) => s.zoom);

  const getRelativePos = useCallback((clientX: number, clientY: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return {
      x: (clientX - rect.left) / zoom,
      y: (clientY - rect.top) / zoom,
    };
  }, [zoom]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const pos = getRelativePos(e.clientX, e.clientY);
    if (!pos) return;
    setIsDrawing(true);
    setSelection({ startX: pos.x, startY: pos.y, endX: pos.x, endY: pos.y });
  }, [getRelativePos]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDrawing || !selection) return;
    const pos = getRelativePos(e.clientX, e.clientY);
    if (!pos) return;
    setSelection(prev => prev ? { ...prev, endX: pos.x, endY: pos.y } : null);
  }, [isDrawing, selection, getRelativePos]);

  const handleMouseUp = useCallback(() => {
    if (isDrawing && selection && isHighlighterActive) {
      const rect = {
        startX: selection.startX,
        startY: selection.startY,
        endX: selection.endX,
        endY: selection.endY,
        color: activeHighlightColor
      };
      if (Math.abs(rect.endX - rect.startX) > 3 && Math.abs(rect.endY - rect.startY) > 3) {
        addHighlight(rect);
      }
      setSelection(null); // Clear selection box for highlighter mode
    }
    setIsDrawing(false);
  }, [isDrawing, selection, isHighlighterActive, activeHighlightColor, addHighlight]);

  const clearSelection = useCallback(() => {
    setSelection(null);
    setIsDrawing(false);
  }, []);

  return {
    selection,
    isDrawing,
    containerRef,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    clearSelection,
  };
};
