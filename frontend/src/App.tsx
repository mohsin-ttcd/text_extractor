import { useRef, useState, DragEvent, useEffect } from 'react';
import { useAppStore } from './store/appStore';
import { booksAPI, configAPI } from './services/api';
import LeftToolbar from './components/left/LeftToolbar';
import PDFViewer from './components/left/PDFViewer';
import BottomNavBar from './components/left/BottomNavBar';
import RightToolbar from './components/right/RightToolbar';
import { exportAPI } from './services/api';
import TextEditor from './components/right/TextEditor';
import StatusBar from './components/right/StatusBar';
import SettingsModal from './components/modals/SettingsModal';
import BooksList from './components/BooksList';
import { usePages } from './hooks/useOCR';
import './styles/globals.css';

function App() {
  const { setCurrentBook, currentBook, setEditedText, setConnectedDocx, processingProgress, currentPage } = useAppStore();
  const { loadPage } = usePages();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [booksListOpen, setBooksListOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [prevBookId, setPrevBookId] = useState<number | null>(null);

  // Initialize dark mode based on system preference & Load config to restore connected doc
  useEffect(() => {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.classList.toggle('dark', prefersDark);
    const listener = (e: MediaQueryListEvent) => {
      document.documentElement.classList.toggle('dark', e.matches);
    };
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', listener);

    configAPI.getConfig().then((response) => {
      const path = response.data.connected_docx_path;
      if (path) {
        const name = path.split(/[\\/]/).pop() || path;
        setConnectedDocx(name);
      }
    }).catch(console.error);

    return () => window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', listener);
  }, [setConnectedDocx]);

  // Handle PDF close or switch (Word auto-close & forget logic)
  useEffect(() => {
    if (prevBookId !== null && (currentBook === null || currentBook.id !== prevBookId)) {
      const cleanupWord = async () => {
        try {
          await exportAPI.closeDocx();
          const configRes = await configAPI.getConfig();
          if (configRes.data.forget_on_close) {
            await configAPI.updateConfig({ connected_docx_path: '' });
            setConnectedDocx('');
          }
        } catch (err) {
          console.error('Failed to cleanup Word connection on book change:', err);
        }
      };
      cleanupWord();
    }
    setPrevBookId(currentBook ? currentBook.id : null);
  }, [currentBook, prevBookId, setConnectedDocx]);

  // Handle Tauri application exit (Word auto-close cleanup)
  useEffect(() => {
    let unlistenPromise: Promise<() => void> | null = null;
    if (typeof window !== 'undefined' && window.__TAURI__) {
      unlistenPromise = import('@tauri-apps/api/window').then(({ appWindow }) => {
        return appWindow.onCloseRequested(async (event) => {
          event.preventDefault();
          try {
            await exportAPI.closeDocx();
          } catch (err) {
            console.error('Cleanup Word on app close failed:', err);
          }
          appWindow.close();
        });
      });
    }
    return () => {
      if (unlistenPromise) {
        unlistenPromise.then((unlisten) => unlisten());
      }
    };
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file.type.includes('pdf')) {
      alert('❌ শুধুমাত্র পিডিএফ ফাইল সমর্থিত');
      return;
    }
    try {
      const response = await booksAPI.uploadPDF(file);
      const { book_id, title, total_pages } = response.data;
      setCurrentBook({
        id: book_id,
        title,
        total_pages,
        processed_pages: 0,
        pdf_path: file.name,
      });
      setEditedText('');
      alert(response.data.message);
    } catch (error: any) {
      alert(`❌ আপলোড ব্যর্থ: ${error.message}`);
    }
  };

  const handleDocxConnect = async (file: File) => {
    try {
      const response = await exportAPI.connectDocx(file);
      setConnectedDocx(response.data.name);
      alert(response.data.message);
    } catch {
      alert('❌ ত্রুটি: Word ডকুমেন্ট সংযুক্ত করতে ব্যর্থ');
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileUpload(files[0]);
  };

  return (
    <div
      className="w-full h-screen bg-void p-6 overflow-hidden"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {isDragging && (
        <div className="absolute inset-0 bg-gold/10 border-4 border-dashed border-gold rounded-2xl flex items-center justify-center z-40 pointer-events-none">
          <div className="text-center">
            <p className="text-2xl font-bold text-gold font-libre-baskerville">
              📂 পিডিএফ এখানে ফেলুন
            </p>
          </div>
        </div>
      )}

      <div className="h-full bg-surface rounded-2xl p-6 flex flex-col shadow-lamp">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            {currentBook && (
              <div className="flex flex-col">
                <span className="text-sm font-semibold font-libre-baskerville text-text-primary">
                  {currentBook.title}
                </span>
                <span className="text-xs font-dm-mono text-text-secondary">
                  {processingProgress.current} / {processingProgress.total} পৃষ্ঠা প্রক্রিয়া করা হয়েছে
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {currentBook && (
              <>
                <button
                  onClick={() => loadPage(currentPage)}
                  className="btn-action px-3 py-2 bg-subtle hover:bg-border-warm text-text-secondary rounded-lg font-dm-mono text-xs"
                  title="রিফ্রেশ করুন"
                >
                  🔄
                </button>
                <button
                  onClick={() => setCurrentBook(null)}
                  className="btn-action px-3 py-2 bg-subtle hover:bg-ink-red/10 hover:text-ink-red text-text-secondary rounded-lg font-dm-mono text-xs"
                  title="বই বন্ধ করুন"
                >
                  ❌
                </button>
              </>
            )}
            <button
              onClick={() => setBooksListOpen(true)}
              className="btn-action px-3 py-2 bg-subtle hover:bg-border-warm text-text-secondary rounded-lg font-dm-mono text-xs"
            >
              📚 বই
            </button>
          </div>
        </div>

        {currentBook ? (
          <div className="flex-1 flex gap-4 min-h-0">
            {/* Left Panel (60%) */}
            <div className="flex-[6] flex flex-col min-w-0 animate-panel-enter">
              <LeftToolbar onSettingsClick={() => setSettingsOpen(true)} onUploadClick={handleUploadClick} />
              <div className="flex-1 min-h-0 mt-3">
                <PDFViewer />
              </div>
              <div className="mt-3">
                <BottomNavBar />
              </div>
            </div>

            {/* Right Panel (40%) */}
            <div className="flex-[4] flex flex-col min-w-0 animate-panel-enter-delayed">
              <RightToolbar onDocxConnect={handleDocxConnect} />
              <div className="flex-1 min-h-0 mt-3">
                <TextEditor />
              </div>
              <div className="mt-3">
                <StatusBar />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-6">
              <p className="text-5xl text-text-muted">📄</p>
              <p className="text-xl font-semibold font-libre-baskerville text-text-secondary">
                পিডিএফ বই লোড করুন
              </p>
              <p className="text-sm font-dm-mono text-text-muted">
                উপরে সবুজ বাটনে ক্লিক করুন অথবা পিডিএফ এখানে টেনে আনুন
              </p>
              <button
                onClick={handleUploadClick}
                className="btn-action px-6 py-3 bg-gold hover:bg-gold-bright text-text-on-gold rounded-lg font-dm-mono text-sm font-bold"
              >
                📂 পিডিএফ ফাইল নির্বাচন করুন
              </button>
            </div>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileUpload(file);
        }}
        className="hidden"
      />

      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <BooksList isOpen={booksListOpen} onClose={() => setBooksListOpen(false)} />
    </div>
  );
}

export default App;
