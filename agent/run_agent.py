import argparse
import os
from langchain_core.messages import HumanMessage
from .graph.build import get_app
from .config import CONFIG

def main():
    parser = argparse.ArgumentParser(description="Run LangGraph Data Analysis Agent")
    parser.add_argument("--file", required=True, help="Path to data file in uploads/")
    parser.add_argument("--task", default="统计描述、可视化", help="分析任务描述")
    args = parser.parse_args()

    # 校验文件在 uploads/ 下
    file_path = args.file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    if not os.path.abspath(file_path).startswith(os.path.abspath(CONFIG.UPLOADS_DIR)):
        raise ValueError(f"请将数据文件放在 {CONFIG.UPLOADS_DIR}/ 目录下")

    app = get_app()

    # 初始化状态
    state = {
        "messages": [HumanMessage(content=f"请根据我上传的数据文件执行 {args.task} 分析。")],
        "file_path": file_path,
        "sandbox_file_path": "",
        "artifacts": {},
        "output_paths": [],
    }

    final_state = app.invoke(state)

    # 打印结果
    print("\n==== 分析完成 ====")
    # 找最后一个 AI 文本消息
    for msg in reversed(final_state["messages"]):
        if msg.type == "ai" and not getattr(msg, "tool_calls", None):
            print("\n[LLM 总结输出]\n")
            print(msg.content)
            break

    print("\n[输出文件]")
    for p in final_state.get("output_paths", []):
        print(" -", p)

if __name__ == "__main__":
    # 让相对导入在直接运行时也能工作
    # python -m agent.run_agent.py ... 的场景可忽略；这里支持直接 python agent/run_agent.py
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from run_agent import main as _main  # type: ignore
    _main()
