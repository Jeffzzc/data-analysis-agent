from typing import Any, Dict, List
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class GraphState(TypedDict):
    # LangGraph 会把新消息 append 进来
    messages: Annotated[List[BaseMessage], add_messages]
    # 主机文件路径（uploads/ 下）
    file_path: str
    # 容器内读取路径（/app/data/ 下）
    sandbox_file_path: str
    # 在工具执行后收集的产物（图片b64、csv文本、代码等）
    artifacts: Dict[str, Any]
    # 在 finalize 阶段写出的实际文件路径列表
    output_paths: List[str]
