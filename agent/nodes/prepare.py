import os
from langchain_core.messages import SystemMessage
from typing import Dict
from ..config import CONFIG

READERS = {
    ".csv": ("CSV", "pd.read_csv"),
    ".xlsx": ("Excel", "pd.read_excel"),
    ".xls": ("Excel", "pd.read_excel"),
    ".json": ("JSON", "pd.read_json"),
}

def prepare_node(state: Dict) -> Dict:
    file_path: str = state["file_path"]
    ext = os.path.splitext(file_path)[1].lower()
    file_type, reader = READERS.get(ext, ("未知", "pd.read_csv"))
    # 容器内读取路径（uploads 挂载到 /app/data）
    sandbox_file_path = f"/app/data/{os.path.basename(file_path)}"
    state["sandbox_file_path"] = sandbox_file_path

    instruction = (
        "你是一个数据分析助手。请编写 Python 代码以在 **无交互** 环境执行，务必：\n"
        f"1) 使用 `pandas` 通过 `{reader}` 读取数据：`'{sandbox_file_path}'`\n"
        "2) 进行**描述统计**（如 df.describe()），并将结果保存为 `result.csv`（UTF-8，无索引）\n"
        "3) 进行**可视化**（至少一张图，例如直方图/箱线图/相关热力图），并保存为 `*.png`\n"
        "4) 使用 `matplotlib` 的非交互后端（容器内无显示），保存后 `plt.close()`\n"
        "5) 最后 `print` 关键表格输出，便于标准输出中查看\n"
        "注意：不要试图访问网络或本地除 `/app/data/` 外的路径。"
    )
    state["messages"].append(SystemMessage(content=instruction))
    return state
