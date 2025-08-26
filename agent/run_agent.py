# agent/run_agent.py
import argparse
import os
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage

# 允许脚本直接运行：把项目根目录加入 sys.path（对 python agent/run_agent.py 有用）
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.argv and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.graph.build import get_app
from agent.config import CONFIG


def main():
    parser = argparse.ArgumentParser(description="Run LangGraph Data Analysis Agent")
    parser.add_argument("--file", required=True, help="Path to data file in uploads/")
    parser.add_argument("--task", default="统计描述、可视化", help="分析任务描述")
    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    if not os.path.abspath(file_path).startswith(os.path.abspath(CONFIG.UPLOADS_DIR)):
        raise ValueError(f"请将数据文件放在 {CONFIG.UPLOADS_DIR}/ 目录下")

    app = get_app()

    state = {
        "messages": [HumanMessage(content=f"请根据我上传的数据文件执行 {args.task} 分析。")],
        "file_path": file_path,
        "sandbox_file_path": "",
        "artifacts": {},
        "output_paths": [],
    }

    final_state = app.invoke(state)

    print("\n==== 分析完成 ====")
    for msg in reversed(final_state["messages"]):
        if msg.type == "ai" and not getattr(msg, "tool_calls", None):
            print("\n[LLM 总结输出]\n")
            print(msg.content)
            break

    print("\n[输出文件]")
    for p in final_state.get("output_paths", []):
        print(" -", p)


if __name__ == "__main__":
    main()
