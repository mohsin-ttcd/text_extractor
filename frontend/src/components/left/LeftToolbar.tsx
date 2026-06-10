import React from 'react';
import { useAppStore } from '../../store/appStore';

interface LeftToolbarProps {
  onSettingsClick: () => void;
  onUploadClick: () => void;
}

const LeftToolbar: React.FC<LeftToolbarProps> = ({ onSettingsClick, onUploadClick }) => {
  const { isSelectionActive, setSelectionActive, setHighlighterActive } = useAppStore();

  return (
    <div className="flex items-center justify-between">
      {/* Left: Settings */}
      <div>
        <button
          onClick={onSettingsClick}
          className="btn-action px-3 py-2 bg-subtle hover:bg-border-warm border border-border-dim rounded-lg text-text-secondary hover:text-text-primary font-dm-mono text-xs"
          title="সেটিংস"
        >
          ⚙️
        </button>
      </div>

      {/* Center: Upload with text */}
      <button
        onClick={onUploadClick}
        className="btn-action px-5 py-2 bg-ink-teal hover:bg-ink-teal-bright text-white rounded-lg font-dm-mono text-sm font-medium"
        title="পিডিএফ ফাইল আপলোড করুন"
      >
        📂 পিডিএফ ফাইল আপলোড করুন
      </button>

      {/* Right: Selection pencil */}
      <div>
        <button
          onClick={() => {
            const nextState = !isSelectionActive;
            setSelectionActive(nextState);
            if (nextState) {
              setHighlighterActive(false);
            }
          }}
          className={`btn-action px-3 py-2 rounded-lg font-dm-mono text-xs border ${
            isSelectionActive
              ? 'bg-gold/20 border-gold text-gold'
              : 'bg-subtle border-border-dim text-text-secondary hover:text-text-primary hover:bg-border-warm'
          }`}
          title="টেক্সট নির্বাচন"
        >
          ✏️
        </button>
      </div>
    </div>
  );
};

export default LeftToolbar;
