import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SANDBOX_URL: str = os.getenv("SANDBOX_URL", "http://localhost:5000/run")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    UPLOADS_DIR: str = os.getenv("UPLOADS_DIR", "uploads")
    MODEL: str = os.getenv("MODEL", "gpt-4o")  # 可改用你有权限的模型

    def ensure_dirs(self):
        Path(self.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

CONFIG = Config()
CONFIG.ensure_dirs()
