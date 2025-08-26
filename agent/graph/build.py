from typing import Dict
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage
from .state import GraphState
from ..config import CONFIG
from ..nodes.prepare import prepare_node
from ..nodes.collect_results import collect_results_node
from ..nodes.finalize import finalize_node
from ..tools.sandbox_tool import run_code_in_sandbox

def make_agent_node(llm):
    def agent_node(state: Dict) -> Dict:
        # LLM 读 messages，可能产生工具调用
        ai_msg = llm.invoke(state["messages"])
        state["messages"].append(ai_msg)
        return state
    return agent_node

def route_after_agent(state: Dict) -> str:
    # 如果最后一条是 AI 消息且包含 tool_calls，则去 tools；否则 finalize
    last: BaseMessage = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "finalize"

def build_graph():
    llm = ChatOpenAI(model=CONFIG.MODEL, temperature=0.1)
    llm_with_tools = llm.bind_tools([run_code_in_sandbox])

    builder = StateGraph(GraphState)

    # 节点
    builder.add_node("prepare", prepare_node)
    builder.add_node("agent", make_agent_node(llm_with_tools))
    builder.add_node("tools", ToolNode(tools=[run_code_in_sandbox]))
    builder.add_node("collect", collect_results_node)
    builder.add_node("finalize", finalize_node)

    # 边
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "finalize": "finalize"})
    builder.add_edge("tools", "collect")
    builder.add_edge("collect", "agent")
    builder.add_edge("finalize", END)

    return builder.compile()

def get_app():
    return build_graph()
