"""
Model registry for hot-swapping active model.
Watches reload.flag and reloads on change.
"""
import os
import json
import joblib
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / 'models'
RELOAD_FLAG = MODELS_DIR / 'reload.flag'


class ModelRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = None
            cls._instance.scaler = None
            cls._instance.threshold = 0.5
            cls._instance.meta = {}
            cls._instance.version_tag = None
            cls._instance.reload_flag_mtime = 0
        return cls._instance

    def load(self, force=False):
        """Load or reload model artifacts."""
        with self._lock:
            current_mtime = RELOAD_FLAG.stat().st_mtime if RELOAD_FLAG.exists() else 0

            if not force and self.model is not None \
               and current_mtime <= self.reload_flag_mtime:
                return self

            try:
                self.model = joblib.load(MODELS_DIR / 'fraud_model.pkl')
                self.scaler = joblib.load(MODELS_DIR / 'scaler.pkl')
                self.threshold = joblib.load(MODELS_DIR / 'threshold.pkl')

                meta_path = MODELS_DIR / 'model_meta.json'
                if meta_path.exists():
                    with open(meta_path) as f:
                        self.meta = json.load(f)

                version_file = MODELS_DIR / 'current_version.txt'
                self.version_tag = version_file.read_text().strip() \
                    if version_file.exists() else 'v1'

                self.reload_flag_mtime = current_mtime
                print(f"✅ Model loaded: {self.version_tag} "
                      f"(threshold={self.threshold:.4f})")
            except Exception as e:
                print(f"⚠️  Failed to load model: {e}")

            return self

    def check_reload(self):
        """Check if reload flag changed; reload if yes."""
        if not RELOAD_FLAG.exists():
            return
        current_mtime = RELOAD_FLAG.stat().st_mtime
        if current_mtime > self.reload_flag_mtime:
            print("🔄 Reload flag detected — reloading model...")
            self.load(force=True)

    @property
    def is_loaded(self):
        return self.model is not None


registry = ModelRegistry()