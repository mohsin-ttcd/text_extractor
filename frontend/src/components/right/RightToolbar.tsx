import React, { useRef } from 'react';
import { useAppStore } from '../../store/appStore';
import { exportAPI, configAPI } from '../../services/api';

interface RightToolbarProps {
  onDocxConnect: (file: File) => void;
}

const RightToolbar: React.FC<RightToolbarProps> = ({ onDocxConnect }) => {
  const { currentBook, connectedDocxName, setConnectedDocx } = useAppStore();
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

  const handleDownload = async () => {
    if (!currentBook) return;
    try {
      const response = await exportAPI.exportToWord(currentBook.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${currentBook.title}_বাংলা_টেক্সট.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert(`❌ ডাউনলোড ব্যর্থ হয়েছে: ${err.message || 'ডাউনলোড করতে ব্যর্থ'}`);
    }
  };

  const isConnected = connectedDocxName.length > 0;

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
        {isConnected ? `✓ ${connectedDocxName}` : '📂 ওয়ার্ড ফাইল যুক্ত করুন'}
      </button>
      <button
        onClick={handleDownload}
        disabled={!currentBook}
        className="btn-action flex-1 py-2 rounded-lg font-dm-mono text-xs font-bold border relative disabled:opacity-40 bg-gold/10 border-gold/40 text-gold hover:bg-gold/20"
        title="সম্পূর্ণ বইটি ডাউনলোড করুন"
      >
        📥 ডাউনলোড করুন
      </button>
    </div>
  );
};

export default RightToolbar;
