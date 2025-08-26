from typing import List, TypedDict

class AgentState(TypedDict):
    """
    定义 Agent 的状态。

    Attributes:
        user_request (str): 用户的原始请求。
        input_filepath (str): 输入数据文件的路径。
        code (str): LLM 生成的 Python 代码。
        stdout (str): 代码执行的标准输出。
        stderr (str): 代码执行的标准错误。
        output_dir (str): 包含输出文件的目录路径。
        error_message (str): 一个结构化的错误消息，用于反馈给 LLM。
        messages (list): 与 LLM 的对话历史。
        iteration (int): 当前的迭代次数。
    """
    user_request: str
    input_filepath: str
    code: str
    stdout: str
    stderr: str
    output_dir: str
    error_message: str
    messages: List
    iteration: int