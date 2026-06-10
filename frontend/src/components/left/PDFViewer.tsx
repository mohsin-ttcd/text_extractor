import React, { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../store/appStore';
import { usePages } from '../../hooks/useOCR';
import { useSelection } from '../../hooks/useSelection';

const PDFViewer: React.FC = () => {
  const { currentPageData, zoom, highlights, isSelectionActive, isHighlighterActive, setHighlighterActive, clearHighlights, currentBook, currentPage, setCurrentPage, setZoom } = useAppStore();
  const { loading, error } = usePages();
  const { selection, containerRef, handleMouseDown, handleMouseUp, handleMouseMove, clearSelection } = useSelection();
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgKey, setImgKey] = useState(0);
  const [showZoomSlider, setShowZoomSlider] = useState(false);

  // Trigger page animation on new page
  useEffect(() => {
    if (currentPageData) setImgKey(prev => prev + 1);
  }, [currentPageData?.page_num]);

  // Reset selection when page changes
  useEffect(() => {
    clearSelection();
  }, [currentPageData?.page_num]);

  const handlePrev = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentBook && currentPage < currentBook.total_pages) {
      setCurrentPage(currentPage + 1);
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

  return (
    <div className="flex flex-col h-full bg-paper bg-grain rounded-xl border border-warm shadow-lamp overflow-hidden relative">
      {/* Scrollable content */}
      <div
        ref={containerRef}
        className={`flex-1 overflow-auto p-4 relative ${isSelectionActive ? 'cursor-crosshair' : 'cursor-default'}`}
        onMouseDown={isSelectionActive ? handleMouseDown : undefined}
        onMouseMove={isSelectionActive ? handleMouseMove : undefined}
        onMouseUp={isSelectionActive ? handleMouseUp : undefined}
        onMouseLeave={isSelectionActive ? handleMouseUp : undefined}
      >
        <img
          key={imgKey}
          ref={imgRef}
          src={currentPageData.page_image}
          alt={`Page ${currentPageData.page_num}`}
          className="block max-w-full mx-auto animate-page-place"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
          draggable={false}
        />

        {/* Persistent highlights */}
        {highlights.map((h) => (
          <div
            key={h.id}
            className="absolute pointer-events-none"
            style={{
              left: h.startX,
              top: h.startY,
              width: h.endX - h.startX,
              height: h.endY - h.startY,
              background: 'rgba(201,150,42,0.25)',
              borderRadius: '2px',
            }}
          />
        ))}

        {/* Active selection overlay */}
        {selection && selStyle && (
          <div
            className="absolute pointer-events-none"
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

        {/* Floating controls — standalone buttons, dark green */}
        <div className="sticky bottom-0 z-20 mx-4 flex items-center justify-between pointer-events-none">
          {/* Left: Highlighter */}
          <div className="pointer-events-auto">
            <button
              onClick={() => setHighlighterActive(!isHighlighterActive)}
              onContextMenu={(e) => { e.preventDefault(); clearHighlights(); }}
              className={`btn-action w-9 h-9 rounded-lg flex items-center justify-center text-lg transition-all duration-150 ${
                isHighlighterActive
                  ? 'text-gold border border-gold/60'
                  : 'text-ink-green hover:text-ink-green-bright'
              }`}
              title={isHighlighterActive ? 'হাইলাইটার সক্রিয় (ডান-ক্লিক করুন সব হাইলাইট মুছতে)' : 'হাইলাইটার'}
            >
              🖍
            </button>
          </div>

          {/* Center: Page nav */}
          <div className="flex items-center gap-1.5 pointer-events-auto">
            <button
              onClick={handlePrev}
              disabled={!currentBook || currentPage === 1}
              className="btn-action w-9 h-9 rounded-lg flex items-center justify-center text-sm text-ink-green hover:text-ink-green-bright disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150"
            >
              ◀
            </button>
            <span className="font-dm-mono text-sm text-ink-green w-16 text-center tracking-wider select-none">
              {String(currentPage).padStart(2, '0')} / {String(currentBook?.total_pages || 0).padStart(2, '0')}
            </span>
            <button
              onClick={handleNext}
              disabled={!currentBook || (currentBook && currentPage === currentBook.total_pages)}
              className="btn-action w-9 h-9 rounded-lg flex items-center justify-center text-sm text-ink-green hover:text-ink-green-bright disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150"
            >
              ▶
            </button>
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
