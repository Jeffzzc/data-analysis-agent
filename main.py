import os
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from agent_state import AgentState
from graph_nodes import CodeGenerator, CodeExecutor

# --- 加载环境变量 ---
load_dotenv()
# 确保你已经设置了 OPENAI_API_KEY
# os.environ["OPENAI_API_KEY"] = "sk-..."

# --- 初始化模型和节点 ---
llm = ChatOpenAI(model="gpt-4o", temperature=0)
code_generator_node = CodeGenerator(llm)
code_executor_node = CodeExecutor()

# --- 定义图的逻辑流 ---
MAX_ITERATIONS = 5

def should_continue(state: AgentState) -> str:
    """
    条件路由：决定是结束还是重试。
    """
    print("--- 步骤: 评估执行结果 ---")
    if state['error_message']:
        if state['iteration'] >= MAX_ITERATIONS:
            print("达到最大迭代次数，结束。")
            return "end"
        print("代码执行失败，将反馈错误并重试。")
        return "retry"
    else:
        print("代码执行成功，任务完成。")
        return "end"

# --- 构建图 ---
workflow = StateGraph(AgentState)

workflow.add_node("generate_code", code_generator_node)
workflow.add_node("execute_code", code_executor_node)

workflow.set_entry_point("generate_code")

workflow.add_edge("generate_code", "execute_code")
workflow.add_conditional_edges(
    "execute_code",
    should_continue,
    {
        "retry": "generate_code",
        "end": END,
    },
)

# --- 编译并运行 ---
app = workflow.compile()

def run_agent(user_request: str, input_filepath: str):
    """
    运行 Agent 的主函数。
    """
    initial_state = {
        "user_request": user_request,
        "input_filepath": input_filepath,
        "messages": [
            SystemMessage(content="你将根据用户的请求，通过编写和执行代码来解决问题。")
        ],
        "iteration": 0,
    }
    
    # 流式输出，可以看到每一步的状态变化
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"--- Event: {key} ---")
            print(value)
            print("\n")
            
    final_state = app.invoke(initial_state)
    print("--- Agent 执行完成 ---")
    if not final_state['error_message']:
        print(f"✅ 成功！输出文件已保存在: {final_state['output_dir']}")
    else:
        print(f"❌ 失败。最终错误信息: {final_state['error_message']}")


if __name__ == "__main__":
    # 确保文件夹存在
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("output"):
        os.makedirs("output")
        
    # 示例用法
    user_request = "请分析 `sample_data.csv` 文件，计算每个区域（region）的总销售额（sales），并生成一个条形图来展示结果，将图表保存为 'sales_by_region.png'。"
    input_file = "data/sample_data.csv"
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在。请先创建它。")
    else:
        run_agent(user_request, input_file)