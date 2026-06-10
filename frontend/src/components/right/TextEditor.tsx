import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../../store/appStore';
import { useTextEditor } from '../../hooks/useOCR';

const TextEditor: React.FC = () => {
  const { currentPageData, fontSize, setFontSize, editedText, setEditedText } = useAppStore();
  const { saveText, saving } = useTextEditor();
  const [hasChanges, setHasChanges] = useState(false);
  const [justLoaded, setJustLoaded] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (currentPageData) {
      const text = currentPageData.edited_text || currentPageData.raw_text || '';
      setEditedText(text);
      setHasChanges(false);
      setJustLoaded(true);
      const timer = setTimeout(() => setJustLoaded(false), 700);
      return () => clearTimeout(timer);
    }
  }, [currentPageData, setEditedText]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setEditedText(newText);
    setHasChanges(newText !== (currentPageData?.edited_text || currentPageData?.raw_text || ''));
  };

  const handleSave = async () => {
    const success = await saveText(editedText);
    if (success) setHasChanges(false);
  };

  return (
    <div className="flex flex-col h-full bg-raised rounded-xl border border-warm overflow-hidden">
      {/* Font size row */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-dim">
        <label className="font-dm-mono text-[10px] uppercase tracking-wider text-text-muted">আকার</label>
        <div className="flex items-center gap-2">
          <input
            type="range"
            min={12}
            max={30}
            value={fontSize}
            onChange={(e) => setFontSize(parseInt(e.target.value))}
            className="w-20 accent-gold"
          />
          <span className="font-dm-mono text-xs text-text-muted w-8 text-right">{fontSize}px</span>
        </div>
      </div>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={editedText}
        onChange={handleChange}
        className={`flex-1 w-full resize-none p-6 bg-transparent text-text-primary font-tiro-bangla leading-[2.0] caret-gold outline-none placeholder:text-text-muted placeholder:italic ${justLoaded ? 'animate-text-reveal' : ''}`}
        style={{ fontSize: `${fontSize}px` }}
        placeholder="নিষ্কাশিত পাঠ্য এখানে দেখাবে..."
      />

      {/* Save bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-border-dim">
        {hasChanges && (
          <span className="text-xs font-semibold font-dm-mono text-gold">অসংরক্ষিত পরিবর্তন</span>
        )}
        {!hasChanges && <span />}
        <button
          onClick={handleSave}
          disabled={!hasChanges || saving}
          className="btn-action px-4 py-1.5 bg-gold hover:bg-gold-bright disabled:opacity-35 text-text-on-gold rounded-lg font-dm-mono text-xs font-medium"
        >
          {saving ? '⏳' : '✓ সংরক্ষণ করুন'}
        </button>
      </div>
    </div>
  );
};

export default TextEditor;
