import React, { useState, useEffect } from 'react';
import { configAPI, exportAPI } from '../../services/api';
import { useAppStore } from '../../store/appStore';

interface Config {
  tesseract_path: string;
  dpi: number;
  connected_docx_path: string;
  forget_on_close: boolean;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { clearConnectedDocx } = useAppStore();
  const [config, setConfig] = useState<Config>({
    tesseract_path: '',
    dpi: 200,
    connected_docx_path: '',
    forget_on_close: false,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      setIsDark(document.documentElement.classList.contains('dark'));
    }
  }, [isOpen]);

  const handleThemeChange = (dark: boolean) => {
    setIsDark(dark);
    document.documentElement.classList.toggle('dark', dark);
  };

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await configAPI.getConfig();
      setConfig(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      await configAPI.updateConfig(config);
      setSuccess(true);
      setTimeout(() => onClose(), 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async () => {
    setError(null);
    try {
      await exportAPI.closeDocx();
      const updatedConfig = { ...config, connected_docx_path: '' };
      await configAPI.updateConfig(updatedConfig);
      setConfig(updatedConfig);
      clearConnectedDocx();
      alert('✅ Word সংযোগ বিচ্ছিন্ন করা হয়েছে');
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect Word document');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div
        className="bg-raised rounded-2xl border border-warm w-[460px] p-8 shadow-lamp"
        style={{ animation: 'panelEnter 250ms ease-out' }}
      >
        <h2 className="font-libre-baskerville font-bold text-xl text-text-primary pb-4 mb-6 border-b border-border-dim">
          কনফিগারেশন
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-ink-red/10 border border-ink-red/30 rounded-lg text-ink-red font-dm-mono text-xs">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-ink-green/10 border border-ink-green/30 rounded-lg text-ink-green font-dm-mono text-xs">
            সেটিংস সফলভাবে সংরক্ষিত হয়েছে ✓
          </div>
        )}

        {loading ? (
          <p className="text-center text-text-muted font-dm-mono text-sm">লোড করছে...</p>
        ) : (
          <div className="space-y-6">
            {/* Tesseract Path */}
            <div>
              <label className="block font-dm-mono text-[11px] uppercase tracking-wider text-text-muted mb-2">
                টেসারেক্ট পাথ
              </label>
              <input
                type="text"
                value={config.tesseract_path}
                onChange={(e) => setConfig({ ...config, tesseract_path: e.target.value })}
                className="w-full px-3 py-2 bg-subtle border border-border-dim rounded-lg font-dm-mono text-xs text-text-primary focus:outline-none focus:border-gold placeholder:text-text-muted"
                placeholder="C:/Program Files/Tesseract-OCR/tesseract.exe"
              />
            </div>

            {/* DPI */}
            <div>
              <label className="block font-dm-mono text-[11px] uppercase tracking-wider text-text-muted mb-2">
                ডিপিআই
              </label>
              <div className="flex gap-2">
                {[150, 200, 300].map((val) => (
                  <button
                    key={val}
                    onClick={() => setConfig({ ...config, dpi: val })}
                    className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-sm font-medium ${
                      config.dpi === val
                        ? 'bg-gold text-text-on-gold'
                        : 'bg-subtle text-text-secondary hover:bg-border-warm'
                    }`}
                  >
                    {val}
                  </button>
                ))}
              </div>
            </div>

            {/* Connected Word Document */}
            <div className="border-t border-border-dim pt-4">
              <label className="block font-dm-mono text-[11px] uppercase tracking-wider text-text-muted mb-2">
                সংযুক্ত Word ডকুমেন্ট
              </label>
              {config.connected_docx_path ? (
                <div className="flex items-center justify-between gap-3 bg-subtle border border-border-dim rounded-lg px-3 py-2">
                  <span className="font-dm-mono text-xs text-text-primary truncate flex-1" title={config.connected_docx_path}>
                    {config.connected_docx_path.split(/[\\/]/).pop() || config.connected_docx_path}
                  </span>
                  <button
                    onClick={handleDisconnect}
                    type="button"
                    className="px-2.5 py-1 bg-ink-red/10 border border-ink-red/30 text-ink-red rounded hover:bg-ink-red/20 font-dm-mono text-[10px] uppercase font-bold"
                  >
                    Disconnect
                  </button>
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">কোনো Word ডকুমেন্ট সংযুক্ত নেই</p>
              )}
            </div>

            {/* Forget/Remember Toggle */}
            <div>
              <label className="block font-dm-mono text-[11px] uppercase tracking-wider text-text-muted mb-2">
                কানেকশন স্থায়িত্ব
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setConfig({ ...config, forget_on_close: false })}
                  className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-[11px] font-medium transition-colors ${
                    !config.forget_on_close
                      ? 'bg-gold text-text-on-gold'
                      : 'bg-subtle text-text-secondary hover:bg-border-warm'
                  }`}
                >
                  Remember (সংরক্ষণ)
                </button>
                <button
                  type="button"
                  onClick={() => setConfig({ ...config, forget_on_close: true })}
                  className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-[11px] font-medium transition-colors ${
                    config.forget_on_close
                      ? 'bg-gold text-text-on-gold'
                      : 'bg-subtle text-text-secondary hover:bg-border-warm'
                  }`}
                >
                  Forget on Close (পিডিএফ বন্ধ হলে মুছে ফেলুন)
                </button>
              </div>
            </div>

            {/* Theme Toggle */}
            <div className="border-t border-border-dim pt-4">
              <label className="block font-dm-mono text-[11px] uppercase tracking-wider text-text-muted mb-2">
                থিম (Theme)
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleThemeChange(false)}
                  className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-[11px] font-medium transition-colors ${
                    !isDark
                      ? 'bg-gold text-text-on-gold'
                      : 'bg-subtle text-text-secondary hover:bg-border-warm'
                  }`}
                >
                  Light Mode (লাইট মোড)
                </button>
                <button
                  type="button"
                  onClick={() => handleThemeChange(true)}
                  className={`btn-action flex-1 py-2 rounded-lg font-dm-mono text-[11px] font-medium transition-colors ${
                    isDark
                      ? 'bg-gold text-text-on-gold'
                      : 'bg-subtle text-text-secondary hover:bg-border-warm'
                  }`}
                >
                  Dark Mode (ডার্ক মোড)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-border-dim">
          <button
            onClick={onClose}
            disabled={saving}
            className="btn-action px-4 py-2 text-text-secondary hover:text-text-primary font-dm-mono text-sm"
          >
            বাতিল
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="btn-action px-6 py-2 bg-gold hover:bg-gold-bright disabled:opacity-35 text-text-on-gold rounded-lg font-dm-mono text-sm font-medium"
          >
            {saving ? '⏳' : 'সংরক্ষণ'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
