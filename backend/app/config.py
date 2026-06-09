"""
Shared dependencies and utilities for FastAPI
"""

import os
import json
from functools import lru_cache

# Always resolve paths relative to THIS file (backend/app/),
# not relative to wherever the process was launched from.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_APP_DIR)  # backend/
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)  # project root


class Settings:
    """Application settings — all paths are absolute."""

    def __init__(self):
        # config.json lives in the project root (same level as frontend/)
        self.config_path = os.path.join(_PROJECT_DIR, "config.json")
        # DB lives inside backend/
        self.db_path = os.path.join(_BACKEND_DIR, "bengali_ocr.db")

        # Defaults
        self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        self.dpi = 200
        self.connected_docx_path = ""
        self.forget_on_close = False

        self.load_config()

    def load_config(self):
        """Load configuration from config.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.tesseract_path = config.get(
                        "tesseract_path", self.tesseract_path
                    )
                    self.dpi = config.get("dpi", self.dpi)
                    self.connected_docx_path = config.get("connected_docx_path", "")
                    self.forget_on_close = config.get("forget_on_close", False)

            except Exception as e:
                print(f"[Settings] Error loading config from {self.config_path}: {e}")
        else:
            print(
                f"[Settings] No config.json found at {self.config_path}, using defaults."
            )
            # Create default config file so next run loads cleanly
            self.save_config()

    def save_config(self):
        """Save current configuration to config.json."""
        try:
            config = {
                "tesseract_path": self.tesseract_path,
                "dpi": self.dpi,
                "connected_docx_path": self.connected_docx_path,
                "forget_on_close": self.forget_on_close,
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"[Settings] Config saved to {self.config_path}")
        except Exception as e:
            print(f"[Settings] Error saving config: {e}")


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached singleton)."""
    return Settings()
