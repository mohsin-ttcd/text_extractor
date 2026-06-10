import React, { useState } from 'react';
import { useAppStore } from '../../store/appStore';
import { useOCR } from '../../hooks/useOCR';

const BottomNavBar: React.FC = () => {
  const { currentBook, currentPage, isProcessing } = useAppStore();
  const { processPage, startBatchOCR, stopBatchOCR } = useOCR();
  const [taskInProgress, setTaskInProgress] = useState(false);

  const handleProcessPage = async () => {
    try {
      setTaskInProgress(true);
      await processPage(currentPage);
      alert('✅ পৃষ্ঠা প্রক্রিয়া করা হয়েছে');
    } catch {
      alert('❌ ত্রুটি: পৃষ্ঠা প্রক্রিয়া করতে ব্যর্থ');
    } finally {
      setTaskInProgress(false);
    }
  };

  const handleBatchOCR = async () => {
    if (!currentBook) return;
    try {
      await startBatchOCR(1, currentBook.total_pages);
    } catch {
      alert('❌ ত্রুটি: ব্যাচ প্রক্রিয়াকরণ শুরু করতে ব্যর্থ');
    }
  };

  const handleStopBatchOCR = async () => {
    try {
      await stopBatchOCR();
    } catch {
      alert('âŒ à¦¤à§à¦°à§à¦Ÿà¦¿: à¦¬à§à¦¯à¦¾à¦š à¦ªà§à¦°à¦•à§à¦°à¦¿à¦¯à¦¼à¦¾à¦•à¦°à¦£ à¦¬à¦¨à§à¦§ à¦•à¦°à¦¤à§‡ à¦¬à§à¦¯à¦°à§à¦¥');
    }
  };

  const isRunning = isProcessing || taskInProgress;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleProcessPage}
        disabled={!currentBook || isRunning}
        className="btn-action flex-1 py-3 rounded-xl bg-ink-teal hover:bg-ink-teal-bright disabled:opacity-35 text-white font-dm-mono text-xs font-bold"
        style={currentBook && !isRunning ? { boxShadow: '0 4px 16px rgba(26,107,107,0.4)' } : undefined}
      >
        {taskInProgress ? '⏳ প্রক্রিয়া করছে...' : '📄 এই পৃষ্ঠা প্রক্রিয়া করুন'}
      </button>
      <button
        onClick={isProcessing ? handleStopBatchOCR : handleBatchOCR}
        disabled={!currentBook}
        className={`btn-action flex-1 py-3 rounded-xl font-dm-mono text-xs font-bold ${
          isProcessing
            ? 'bg-ink-red text-white animate-pulse-border'
            : 'bg-gold text-text-on-gold'
        }`}
        style={!isProcessing && currentBook ? { boxShadow: '0 4px 16px rgba(201,150,42,0.3)' } : undefined}
      >
        {isProcessing ? '■ বন্ধ করুন' : '🚀 সব পৃষ্ঠা প্রক্রিয়া করুন'}
      </button>
    </div>
  );
};

export default BottomNavBar;
