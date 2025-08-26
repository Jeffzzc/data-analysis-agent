import json
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from ..config import CONFIG

class SandboxInput(BaseModel):
    code: str = Field(description="需要在沙盒中执行的 Python 代码")

@tool("run_code_in_sandbox", args_schema=SandboxInput)
def run_code_in_sandbox(code: str) -> str:
    """
    在隔离的 Docker 沙盒中执行 Python 代码。
    返回 JSON 字符串：{stdout, stderr, images:[b64,...], csv, code}
    """
    try:
        resp = requests.post(CONFIG.SANDBOX_URL, json={"code": code}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        data = {"stdout": "", "stderr": f"{type(e).__name__}: {e}", "images": [], "csv": "", "code": code}
    # 将 code 回传，便于后续保存
    data.setdefault("code", code)
    # LangChain 工具返回必须是字符串；我们用 JSON 字符串承载结构化数据
    return json.dumps(data, ensure_ascii=False)
