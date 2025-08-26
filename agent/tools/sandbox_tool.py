# agent/tools/sandbox_tool.py
import json
import re
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from ..config import CONFIG


class SandboxInput(BaseModel):
    code: str = Field(description="需要在沙盒中执行的 Python 代码")


def _sanitize_code(code: str) -> str:
    """
    在发往沙盒前做强制纠偏：
    - 统一读数据路径为 CONFIG.CURRENT_SANDBOX_FILE
    - 输出改为当前目录文件名，便于沙盒收集（result.csv / plot_1.png）
    - 可选：将 seaborn 常见调用降级为 matplotlib
    """
    data_path = CONFIG.CURRENT_SANDBOX_FILE or "/app/data/UNKNOWN.csv"

    # 1) 统一数据源路径：把 /mnt/data/... 与 /app/data/... 全部替换成唯一正确路径
    code = re.sub(r"['\"](/mnt|/app)/data/[^'\"]+['\"]", f"'{data_path}'", code)

    # 如果代码里没有出现 read_csv/read_excel/read_json，或把 png 当成“数据路径”，注入一段最小读取
    lowered = code.lower()
    if (
        ("read_csv(" not in lowered and "read_excel(" not in lowered and "read_json(" not in lowered)
        or ".png" in lowered
    ):
        inject = (
            "import pandas as pd\n"
            f"df = pd.read_csv('{data_path}')\n"
        )
        code = inject + code

    # 2) 统一输出路径到当前目录（沙盒会收集 CWD 下的 result.csv / *.png）
    code = code.replace("/mnt/data/result.csv", "result.csv")
    code = code.replace("/app/data/result.csv", "result.csv")
    code = code.replace("/mnt/data/heatmap.png", "plot_1.png")
    code = code.replace("/app/data/heatmap.png", "plot_1.png")
    code = code.replace("/mnt/data/boxplot.png", "plot_1.png")
    code = code.replace("/app/data/boxplot.png", "plot_1.png")
    code = code.replace("/mnt/data/histogram.png", "plot_1.png")
    code = code.replace("/app/data/histogram.png", "plot_1.png")

    # 3) （可选）去 seaborn：如果你的镜像没装 seaborn，这段有用；已安装也可以保留以减少不确定性
    code = code.replace("import seaborn as sns", "import matplotlib.pyplot as plt  # seaborn removed")
    code = code.replace("sns.histplot", "plt.hist")
    code = code.replace("sns.boxplot", "plt.boxplot")
    code = code.replace("sns.heatmap", "plt.imshow")  # 简化为 imshow + cmap

    # 4) 防止忘记关闭图：加一个兜底 close
    if "plt.close()" not in code:
        code += "\nimport matplotlib.pyplot as plt\nplt.close('all')\n"
    return code


@tool("run_code_in_sandbox", args_schema=SandboxInput)
def run_code_in_sandbox(code: str) -> str:
    """
    在隔离的 Docker 沙盒中执行 Python 代码。
    返回 JSON 字符串：{stdout, stderr, images:[b64,...], csv, code}
    """
    # ★ 在发送到沙盒前，强制纠正代码
    code = _sanitize_code(code)
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
