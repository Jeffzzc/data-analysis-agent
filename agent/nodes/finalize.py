import base64
import os
from datetime import datetime
from typing import Dict
from ..config import CONFIG

def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def finalize_node(state: Dict) -> Dict:
    """
    将 artifacts 写入磁盘：代码、CSV、图像。
    """
    outdir = CONFIG.OUTPUT_DIR
    os.makedirs(outdir, exist_ok=True)
    outputs = []

    arts = state.get("artifacts", {}) or {}

    # 写代码
    code = arts.get("last_code")
    if code:
        code_path = os.path.join(outdir, "analysis_code.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)
        outputs.append(code_path)

    # 写 CSV
    csv_text = arts.get("csv_text")
    if csv_text:
        csv_path = os.path.join(outdir, "result.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_text)
        outputs.append(csv_path)

    # 写图片
    for idx, b64 in enumerate(arts.get("images_b64", []), start=1):
        png_path = os.path.join(outdir, f"plot_{idx}.png")
        try:
            with open(png_path, "wb") as f:
                f.write(base64.b64decode(b64))
            outputs.append(png_path)
        except Exception:
            # 忽略单张失败
            pass

    state["output_paths"] = outputs
    return state
