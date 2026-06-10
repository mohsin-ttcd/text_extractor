import React from 'react';
import { useAppStore } from '../../store/appStore';

const StatusBar: React.FC = () => {
  const { currentBook, processingProgress } = useAppStore();
  const { current: processed, total } = processingProgress;
  const percentage = total > 0 ? Math.round((processed / total) * 100) : 0;

  return (
    <div className="space-y-1">
      {/* Progress bar */}
      {total > 0 && (
        <div className="h-[2px] bg-border-dim rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-400 ease-out"
            style={{
              width: `${percentage}%`,
              background: 'linear-gradient(to right, var(--ink-teal), var(--gold))',
            }}
          />
        </div>
      )}

      {/* Status text */}
      <p className="font-dm-mono text-[11px] text-text-muted truncate">
        {currentBook
          ? `পৃষ্ঠা ${processed} / ${total} সম্পন্ন — Tesseract-OCR`
          : 'কোনো বই লোড হয়নি'}
      </p>
    </div>
  );
};

export default StatusBar;
