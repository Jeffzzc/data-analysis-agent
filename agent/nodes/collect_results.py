import json
from typing import Dict
from langchain_core.messages import ToolMessage

def collect_results_node(state: Dict) -> Dict:
    """
    从最近一次工具消息中解析 JSON 结果，存入 state['artifacts']。
    """
    # 找到最后一条 ToolMessage
    tool_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            tool_msg = msg
            break
    if not tool_msg:
        return state

    try:
        data = json.loads(tool_msg.content or "{}")
    except Exception:
        data = {}

    artifacts = state.get("artifacts", {})
    # 累积结果（可能多轮执行）
    artifacts.setdefault("images_b64", []).extend(data.get("images", []) or [])
    if data.get("csv"):
        artifacts["csv_text"] = data["csv"]
    if data.get("stdout"):
        artifacts["stdout"] = data["stdout"]
    if data.get("stderr"):
        artifacts["stderr"] = data["stderr"]
    if data.get("code"):
        artifacts["last_code"] = data["code"]

    state["artifacts"] = artifacts
    return state
