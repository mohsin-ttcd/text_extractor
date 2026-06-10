import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../store/appStore';
import { usePages } from '../../hooks/useOCR';
import { useSelection } from '../../hooks/useSelection';
import { pagesAPI } from '../../services/api';

const PDFViewer: React.FC = () => {
  const {
    currentPageData,
    zoom,
    highlights,
    isSelectionActive,
    isHighlighterActive,
    setHighlighterActive,
    clearHighlights,
    currentBook,
    currentPage,
    setCurrentPage,
    setZoom,
    editedText,
    setEditedText,
    setSelectionActive,
    activeHighlightColor,
    setActiveHighlightColor,
  } = useAppStore();
  const { loading, error, loadPage } = usePages();
  const {
    selection,
    isDrawing,
    containerRef,
    handleMouseDown,
    handleMouseUp,
    handleMouseMove,
    clearSelection,
  } = useSelection();
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgKey, setImgKey] = useState(0);
  const [showZoomSlider, setShowZoomSlider] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [savingHighlights, setSavingHighlights] = useState(false);

  // Trigger page animation on new page
  useEffect(() => {
    if (currentPageData) setImgKey(prev => prev + 1);
  }, [currentPageData?.page_num]);

  // Reset selection when page changes
  useEffect(() => {
    clearSelection();
  }, [currentPageData?.page_num]);

  // Keyboard listener for Escape key to deselect and deactivate modes
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearSelection();
        setSelectionActive(false);
        setHighlighterActive(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [clearSelection, setSelectionActive, setHighlighterActive]);

  const handlePrev = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentBook && currentPage < currentBook.total_pages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handleExtractSelection = async () => {
    if (!currentBook || !selection || !imgRef.current) return;

    setExtracting(true);
    try {
      const img = imgRef.current;

      // Selection box relative to image wrapper (unzoomed layout pixels)
      const selX1 = Math.min(selection.startX, selection.endX);
      const selY1 = Math.min(selection.startY, selection.endY);
      const selX2 = Math.max(selection.startX, selection.endX);
      const selY2 = Math.max(selection.startY, selection.endY);

      // Scale to natural image size (150 DPI resolution)
      const x1 = Math.max(0, (selX1 / img.clientWidth) * img.naturalWidth);
      const y1 = Math.max(0, (selY1 / img.clientHeight) * img.naturalHeight);
      const x2 = Math.min(img.naturalWidth, (selX2 / img.clientWidth) * img.naturalWidth);
      const y2 = Math.min(img.naturalHeight, (selY2 / img.clientHeight) * img.naturalHeight);

      console.log('[Extract Selection Debug]:', {
        selection,
        imageLayout: { clientWidth: img.clientWidth, clientHeight: img.clientHeight },
        imageNatural: { naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight },
        scaledCoords: { x1, y1, x2, y2 }
      });

      // Verify that width/height are reasonable
      if (Math.abs(x2 - x1) < 2 || Math.abs(y2 - y1) < 2) {
        alert('❌ নির্বাচিত এলাকাটি খুব ছোট। দয়া করে আবার চেষ্টা করুন।');
        setExtracting(false);
        return;
      }

      console.log('[Extract Selection API Call] Sending selection OCR request to server...');
      const response = await pagesAPI.ocrSelection(currentBook.id, currentPage, { x1, y1, x2, y2 });
      console.log('[Extract Selection API Response] Received:', response.data);
      const extractedText = response.data.text || '';

      if (extractedText.trim()) {
        // Find text area element and insert at cursor if focused, else append at end
        const textarea = document.querySelector('textarea') as HTMLTextAreaElement | null;
        if (textarea) {
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          const currentText = textarea.value;
          const before = currentText.substring(0, start);
          const after = currentText.substring(end, currentText.length);
          const newText = before + (before.endsWith('\n') || !before ? '' : '\n') + extractedText + after;
          setEditedText(newText);
          
          // Refocus and place cursor after inserted text
          setTimeout(() => {
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = start + extractedText.length + (before.endsWith('\n') || !before ? 0 : 1);
          }, 50);
        } else {
          setEditedText(editedText ? `${editedText}\n${extractedText}` : extractedText);
        }
        alert('✅ টেক্সট সফলভাবে নিষ্কাশন করা হয়েছে');
      } else {
        alert('⚠️ নির্বাচিত অংশ থেকে কোনো টেক্সট পাওয়া যায়নি');
      }

      clearSelection();
    } catch (err: any) {
      console.error('[Extract Selection Error]:', err);
      alert(`❌ টেক্সট নিষ্কাশন ব্যর্থ হয়েছে: ${err.message || 'সার্ভার ত্রুটি'}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleSaveAnnotations = async () => {
    if (!currentBook || highlights.length === 0) return;
    setSavingHighlights(true);
    try {
      const img = imgRef.current;
      if (!img) return;

      // Scale highlights to natural image size (150 DPI resolution)
      const scaledHighlights = highlights.map(hl => {
        const x1 = (hl.startX / img.clientWidth) * img.naturalWidth;
        const y1 = (hl.startY / img.clientHeight) * img.naturalHeight;
        const x2 = (hl.endX / img.clientWidth) * img.naturalWidth;
        const y2 = (hl.endY / img.clientHeight) * img.naturalHeight;
        return {
          startX: x1,
          startY: y1,
          endX: x2,
          endY: y2,
          color: hl.color
        };
      });

      const response = await pagesAPI.saveAnnotations(
        currentBook.id,
        currentPage,
        scaledHighlights
      );

      alert(response.data.message);
      clearHighlights();
      // Force reload page image by incrementing key
      setImgKey(prev => prev + 1);
      // Reload page state from backend
      loadPage(currentPage);
    } catch (err: any) {
      console.error('[Save Annotations Error]:', err);
      alert(`❌ হাইলাইট সংরক্ষণ ব্যর্থ হয়েছে: ${err.message || 'সার্ভার ত্রুটি'}`);
    } finally {
      setSavingHighlights(false);
    }
  };

  if (!currentPageData && loading) {
    return (
      <div className="flex flex-col h-full bg-paper bg-grain rounded-xl border border-warm shadow-lamp items-center justify-center">
        <div className="text-text-muted font-dm-mono text-sm">⏳ পৃষ্ঠা লোড করছে...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full bg-paper bg-grain rounded-xl border border-warm shadow-lamp items-center justify-center">
        <div className="text-ink-red font-dm-mono text-sm mb-2">❌ পৃষ্ঠা লোড ব্যর্থ</div>
        <div className="text-text-muted font-dm-mono text-xs">{error}</div>
      </div>
    );
  }

  if (!currentPageData) {
    return (
      <div className="flex flex-col h-full bg-paper bg-grain rounded-xl border border-warm shadow-lamp items-center justify-center">
        <p className="text-4xl text-text-muted mb-3">📖</p>
        <p className="text-lg font-libre-baskerville italic text-text-muted">পিডিএফ বই লোড করুন</p>
        <p className="text-xs font-dm-mono text-text-muted mt-2">নিচে পেন্সিল আইকনে ক্লিক করুন</p>
      </div>
    );
  }

  const selStyle = selection ? {
    left: Math.min(selection.startX, selection.endX),
    top: Math.min(selection.startY, selection.endY),
    width: Math.abs(selection.endX - selection.startX),
    height: Math.abs(selection.endY - selection.startY),
  } : null;

  const canDrag = isSelectionActive || isHighlighterActive;

  return (
    <div className="flex flex-col h-full bg-paper bg-grain rounded-xl border border-warm shadow-lamp overflow-hidden relative">
      {/* Scrollable content */}
      <div className="flex-1 overflow-auto p-4 relative">
        {/* Zoom wrapper container matching image bounds */}
        <div
          ref={containerRef}
          className={`relative mx-auto ${canDrag ? 'cursor-crosshair' : 'cursor-default'}`}
          style={{
            width: 'fit-content',
            height: 'fit-content',
            transform: `scale(${zoom})`,
            transformOrigin: 'top center',
          }}
          onMouseDown={canDrag ? handleMouseDown : undefined}
          onMouseMove={canDrag ? handleMouseMove : undefined}
          onMouseUp={canDrag ? handleMouseUp : undefined}
          onMouseLeave={canDrag ? handleMouseUp : undefined}
        >
          <img
            key={imgKey}
            ref={imgRef}
            src={currentPageData.page_image}
            alt={`Page ${currentPageData.page_num}`}
            className="block max-w-full"
            draggable={false}
          />

          {/* Transparent selection overlay to block browser dragging */}
          {canDrag && (
            <div className="absolute inset-0 z-10 bg-transparent" />
          )}

          {/* Persistent highlights */}
          {highlights.map((h) => {
            let bg = 'rgba(234, 179, 8, 0.3)'; // yellow fallback
            if (h.color === 'green') bg = 'rgba(34, 197, 94, 0.3)';
            else if (h.color === 'red') bg = 'rgba(239, 68, 68, 0.3)';

            return (
              <div
                key={h.id}
                className="absolute pointer-events-none"
                style={{
                  left: h.startX,
                  top: h.startY,
                  width: h.endX - h.startX,
                  height: h.endY - h.startY,
                  background: bg,
                  borderRadius: '2px',
                }}
              />
            );
          })}

          {/* Active selection overlay (only show in selection active mode) */}
          {isSelectionActive && selection && selStyle && (
            <div
              className="absolute pointer-events-none z-20"
              style={{
                left: selStyle.left,
                top: selStyle.top,
                width: selStyle.width,
                height: selStyle.height,
                border: '2px dashed var(--gold)',
                background: 'rgba(201,150,42,0.08)',
                borderRadius: '4px',
              }}
            />
          )}

          {/* Active highlight drag preview overlay (only show in highlighter mode while drawing) */}
          {isHighlighterActive && isDrawing && selection && selStyle && (
            <div
              className="absolute pointer-events-none z-20"
              style={{
                left: selStyle.left,
                top: selStyle.top,
                width: selStyle.width,
                height: selStyle.height,
                background:
                  activeHighlightColor === 'green'
                    ? 'rgba(34, 197, 94, 0.3)'
                    : activeHighlightColor === 'red'
                    ? 'rgba(239, 68, 68, 0.3)'
                    : 'rgba(234, 179, 8, 0.3)',
                borderRadius: '2px',
              }}
            />
          )}

          {/* Floating "Process It" button next to selection box */}
          {isSelectionActive && selection && selStyle && !isDrawing && (
            <div
              className="absolute z-30 pointer-events-auto"
              style={{
                left: selStyle.left + selStyle.width + 8,
                top: selStyle.top + (selStyle.height / 2) - 16,
                transform: `scale(${1 / zoom})`,
                transformOrigin: 'left center',
              }}
              onMouseDown={(e) => e.stopPropagation()}
              onMouseUp={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={handleExtractSelection}
                disabled={extracting}
                className="px-3 py-1.5 bg-ink-teal hover:bg-ink-teal-bright text-white rounded-lg font-dm-mono text-xs font-bold shadow-lamp flex items-center gap-1.5 transition-all duration-150 disabled:opacity-45 whitespace-nowrap"
                title="নির্বাচিত অংশ থেকে টেক্সট নিষ্কাশন করুন"
              >
                {extracting ? '⏳...' : '✏️ প্রক্রিয়া করুন'}
              </button>
            </div>
          )}
        </div>

        {/* Floating controls — standalone buttons, dark green */}
        <div className="sticky bottom-0 z-20 mx-4 flex items-center justify-between pointer-events-none">
          {/* Left container */}
          <div className="relative flex items-center pointer-events-auto">
            {/* Brush & Save Button Wrapper (fixed size) */}
            <div className="relative w-9 h-9">
              {/* Floating Save Button (Absolute, Transparent, Above the Brush) */}
              <button
                onClick={handleSaveAnnotations}
                disabled={savingHighlights || highlights.length === 0}
                className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-9 h-9 flex items-center justify-center text-lg transition-all duration-150 bg-transparent border-0 outline-none ${
                  highlights.length > 0
                    ? 'text-gold hover:text-gold-bright drop-shadow-md cursor-pointer'
                    : 'text-text-muted opacity-30 cursor-not-allowed'
                }`}
                title="হাইলাইটগুলি পিডিএফ ফাইলে সংরক্ষণ করুন (Save PDF with Highlights)"
              >
                {savingHighlights ? '⏳' : '💾'}
              </button>

              <button
                onClick={() => {
                  const nextState = !isHighlighterActive;
                  setHighlighterActive(nextState);
                  if (nextState) {
                    setSelectionActive(false);
                  }
                }}
                onContextMenu={(e) => { e.preventDefault(); clearHighlights(); }}
                className={`btn-action w-9 h-9 rounded-lg flex items-center justify-center text-lg transition-all duration-150 ${
                  isHighlighterActive
                    ? 'bg-gold/10 text-gold border border-gold/40'
                    : 'text-ink-green hover:text-ink-green-bright'
                }`}
                title={isHighlighterActive ? 'হাইলাইটার সক্রিয় (ডান-ক্লিক করুন সব হাইলাইট মুছতে)' : 'হাইলাইটার'}
              >
                🖍
              </button>
            </div>

            {/* Color selector circles visible when highlighter mode is active (absolutely positioned to the right) */}
            {isHighlighterActive && (
              <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5 bg-raised border border-border-dim px-2 py-1.5 rounded-lg shadow-lamp whitespace-nowrap">
                <button
                  onClick={() => setActiveHighlightColor('yellow')}
                  className={`w-4 h-4 rounded-full bg-[#EAB308] border transition-all duration-100 ${
                    activeHighlightColor === 'yellow' ? 'ring-2 ring-gold scale-110 border-white' : 'border-transparent hover:scale-105'
                  }`}
                  title="হলুদ হাইলাইট"
                />
                <button
                  onClick={() => setActiveHighlightColor('green')}
                  className={`w-4 h-4 rounded-full bg-[#22C55E] border transition-all duration-100 ${
                    activeHighlightColor === 'green' ? 'ring-2 ring-gold scale-110 border-white' : 'border-transparent hover:scale-105'
                  }`}
                  title="সবুজ হাইলাইট"
                />
                <button
                  onClick={() => setActiveHighlightColor('red')}
                  className={`w-4 h-4 rounded-full bg-[#EF4444] border transition-all duration-100 ${
                    activeHighlightColor === 'red' ? 'ring-2 ring-gold scale-110 border-white' : 'border-transparent hover:scale-105'
                  }`}
                  title="লাল হাইলাইট"
                />
              </div>
            )}
          </div>

          {/* Center: Page nav */}
          <div className="flex items-center gap-3 pointer-events-auto">
            <div className="flex items-center gap-1.5">
              <button
                onClick={handlePrev}
                disabled={!currentBook || currentPage === 1}
                className="btn-action w-9 h-9 rounded-lg flex items-center justify-center text-sm text-ink-green hover:text-ink-green-bright disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150"
              >
                ◀
              </button>
              <span className="font-dm-mono text-xs text-ink-green w-32 text-center tracking-wider select-none">
                Page {currentPage} of {currentBook?.total_pages || 0}
              </span>
              <button
                onClick={handleNext}
                disabled={!currentBook || (currentBook && currentPage === currentBook.total_pages)}
                className="btn-action w-9 h-9 rounded-lg flex items-center justify-center text-sm text-ink-green hover:text-ink-green-bright disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150"
              >
                ▶
              </button>
            </div>
          </div>

          {/* Right: Zoom */}
          <div className="relative pointer-events-auto">
            <button
              onClick={() => setShowZoomSlider(!showZoomSlider)}
              className="btn-action h-9 rounded-lg flex items-center justify-center font-dm-mono text-sm text-ink-green hover:text-ink-green-bright transition-all duration-150 px-2"
            >
              +{Math.round(zoom * 100)}%
            </button>
            {showZoomSlider && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowZoomSlider(false)} />
                <div className="absolute bottom-full mb-2 right-0 z-20 bg-raised border border-border-dim rounded-lg p-3 shadow-lamp w-40">
                  <input
                    type="range"
                    min={50}
                    max={200}
                    value={Math.round(zoom * 100)}
                    onChange={(e) => setZoom(parseInt(e.target.value) / 100)}
                    className="w-full accent-gold"
                  />
                  <div className="flex justify-between text-xs font-dm-mono text-text-muted mt-1">
                    <span>50%</span>
                    <span>200%</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
