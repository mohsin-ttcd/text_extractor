import React, { useRef } from 'react';
import { useAppStore } from '../../store/appStore';
import { exportAPI, configAPI } from '../../services/api';

interface RightToolbarProps {
  onDocxConnect: (file: File) => void;
}

const RightToolbar: React.FC<RightToolbarProps> = ({ onDocxConnect }) => {
  const { currentBook, connectedDocxName, editedText, setConnectedDocx } = useAppStore();
  const docxInputRef = useRef<HTMLInputElement>(null);

  const handleConnectClick = async () => {
    if (typeof window !== 'undefined' && window.__TAURI__) {
      try {
        const { open } = await import('@tauri-apps/api/dialog');
        const selected = await open({
          filters: [{ name: 'Word Document', extensions: ['docx'] }],
        });

        if (selected && typeof selected === 'string') {
          await configAPI.updateConfig({ connected_docx_path: selected });
          const name = selected.split(/[\\/]/).pop() || selected;
          setConnectedDocx(name);
          alert(`✅ ${name} সফলভাবে সংযুক্ত হয়েছে`);
        }
      } catch (err) {
        console.error('Failed to open Tauri file dialog:', err);
        docxInputRef.current?.click();
      }
    } else {
      docxInputRef.current?.click();
    }
  };

  const handleDocxFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.docx')) {
        alert('❌ শুধুমাত্র .docx ফাইল সমর্থিত');
        return;
      }
      onDocxConnect(file);
    }
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const handleAppend = async () => {
    if (!currentBook || !editedText.trim()) return;
    try {
      const response = await exportAPI.appendToConnectedDocx(currentBook.id, editedText, currentBook.processed_pages + 1);
      alert(response.data.message);
    } catch (err: any) {
      alert(`❌ ত্রুটি: ${err.message || 'সংযুক্ত করতে ব্যর্থ'}`);
    }
  };

  const isConnected = connectedDocxName.length > 0;
  const hasText = editedText.trim().length > 0;

  return (
    <div className="flex items-center gap-2">
      <input
        ref={docxInputRef}
        type="file"
        accept=".docx"
        onChange={handleDocxFileChange}
        className="hidden"
      />
      <button
        onClick={handleConnectClick}
        className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-xs border ${
          isConnected
            ? 'bg-ink-green/10 border-ink-green/30 text-ink-green'
            : 'bg-subtle border-border-dim text-text-secondary hover:text-text-primary hover:bg-border-warm'
        }`}
        title="Word ডকুমেন্ট সংযুক্ত করুন"
      >
        {isConnected ? `✓ ${connectedDocxName}` : '📂 Connect Word'}
      </button>
      <button
        onClick={handleAppend}
        disabled={!isConnected || !hasText}
        className="btn-action flex-1 py-2 rounded-lg font-dm-mono text-xs font-bold border relative disabled:opacity-40 bg-gold/10 border-gold/40 text-gold hover:bg-gold/20"
        title="সংযুক্ত ডকুমেন্টে পাঠ্য যোগ করুন"
      >
        📝 Append
        <span className="ml-1.5 inline-flex items-center px-1 py-0.5 text-[9px] rounded bg-gold/10 text-gold/60 leading-none">
          ⌃⇧A
        </span>
      </button>
    </div>
  );
};

export default RightToolbar;
