import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agent_state import AgentState
from sandbox import DockerSandbox

# --- 1. 代码生成节点 ---

CODE_GEN_PROMPT = """
你是一个高级数据分析师。你的任务是根据用户的请求，编写 Python 代码来分析数据。

**重要规则:**
1.  你生成的代码将在一个隔离的 Docker 环境中执行。
2.  输入数据始终位于 `/workspace/` 目录下，其文件名与用户提供的文件名相同。
3.  你生成的任何输出文件（例如，图表、CSV）也必须保存到 `/workspace/` 目录下。
4.  代码必须是独立的，不依赖于任何外部 API 或需要身份验证的服务。
5.  使用 `pandas` 进行数据操作，使用 `matplotlib` 或 `seaborn` 进行绘图。确保将图表保存为文件（例如 PNG）。
6.  不要使用 `plt.show()`，因为它在非交互式环境中无效。请将图表保存到文件中。
7.  最后，打印一条确认消息，指明已生成的输出文件名。例如：`print("成功生成了 sales_by_region.png")`

**用户请求:**
{user_request}

**输入文件名:**
{input_filename}

**修正指示 (如果适用):**
{error_feedback}

请生成完整的、可直接执行的 Python 代码。
"""

class CodeGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(CODE_GEN_PROMPT)

    def __call__(self, state: AgentState):
        print("--- 步骤: 生成代码 ---")
        
        # 构建反馈信息
        error_feedback = ""
        if state.get('error_message'):
            error_feedback = (
                "你之前的尝试失败了。请修正以下错误并重新生成代码。\n"
                f"错误信息: {state['error_message']}\n"
                f"失败的代码:\n```python\n{state['code']}\n```"
            )

        # 构建消息历史
        messages = state['messages']
        messages.append(HumanMessage(
            content=self.prompt.format(
                user_request=state['user_request'],
                input_filename=os.path.basename(state['input_filepath']),
                error_feedback=error_feedback
            )
        ))
        
        response = self.llm.invoke(messages)
        
        # 从 LLM 响应中提取代码块
        code = response.content.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.endswith("```"):
            code = code[:-3]
        
        messages.append(response)

        return {
            "code": code,
            "messages": messages,
            "iteration": state['iteration'] + 1,
        }

# --- 2. 代码执行节点 ---

class CodeExecutor:
    def __init__(self):
        self.sandbox = DockerSandbox()

    def __call__(self, state: AgentState):
        print("--- 步骤: 在沙盒中执行代码 ---")
        
        stdout, stderr, output_dir = self.sandbox.execute(
            code=state['code'],
            input_filepath=state['input_filepath']
        )
        
        error_message = ""
        if stderr:
            error_message = f"代码执行失败，返回了非空的 stderr:\n{stderr}"
        
        return {
            "stdout": stdout,
            "stderr": stderr,
            "output_dir": output_dir,
            "error_message": error_message
        }