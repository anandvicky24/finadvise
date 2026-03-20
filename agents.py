import os, operator, time
from typing import Annotated, List, TypedDict, Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from tools import tools, get_financial_data

load_dotenv()

class AgentState(TypedDict):
    query: str
    market_data: str 
    risk_score: str
    portfolio_rec: str
    current_node: str
    messages: Annotated[List[any], operator.add]
    history: Annotated[List[str], operator.add]
    
fast_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0).bind_tools(tools)
smart_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

def market_analyst(state: AgentState):
    """
    PURPOSE: Only manages the conversation and tool calls.
    DOES NOT write to state['market_data'] to avoid duplication.
    """
    time.sleep(1)
    
    # If a tool message just arrived, we don't call the LLM again.
    # We return an empty update to let the Router move us to 'sync'.
    if isinstance(state["messages"][-1], ToolMessage):
        return {"current_node": "Data Received ✅", "history": ["Tool execution complete."]}

    sys_msg = (
        "You are a Financial Analyst. Use get_financial_data for ALL tickers in the query. "
        "If comparing multiple stocks, call the tool for each one. "
        "Do not add .NS unless the user specifically typed it."
    )
    
    res = fast_llm.invoke([SystemMessage(content=sys_msg)] + state["messages"])
    return {"messages": [res], "current_node": "Analyst Searching...", "history": ["Identifying tickers."]}

def data_sync(state: AgentState):
    """
    PURPOSE: The ONLY node that writes to 'market_data'.
    It uses a set() or unique logic to ensure no duplicates.
    """
    # Extract unique tool messages by content to prevent double-printing
    tool_results = []
    seen = set()
    for msg in state["messages"]:
        if isinstance(msg, ToolMessage) and msg.content not in seen:
            tool_results.append(msg.content)
            seen.add(msg.content)
    
    combined = "\n".join(tool_results)
    return {
        "market_data": combined, 
        "current_node": "Syncing Data...", 
        "history": ["State synchronized with unique records."]
    }

def risk_assessor(state: AgentState):
    res = smart_llm.invoke(f"Compare risks for: {state.get('market_data', '')}")
    return {"risk_score": res.content, "current_node": "Risk Analysis", "history": ["Risk assessed."]}

def portfolio_optimizer(state: AgentState):
    res = smart_llm.invoke(f"Strategy for Data: {state['market_data']} and Risk: {state['risk_score']}")
    # This node now sets the final 'Done' state
    return {
        "portfolio_rec": res.content, 
        "current_node": "Analysis Complete ✅", 
        "history": ["Strategy generated."]
    }

def router(state: AgentState) -> Literal["tools", "sync", "risk"]:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls: return "tools"
    if isinstance(last_msg, ToolMessage): return "sync"
    if state.get("market_data"): return "risk"
    return "risk"

workflow = StateGraph(AgentState)
workflow.add_node("market_analyst", market_analyst)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("sync", data_sync)
workflow.add_node("risk", risk_assessor)
workflow.add_node("portfolio", portfolio_optimizer)

workflow.set_entry_point("market_analyst")
workflow.add_conditional_edges("market_analyst", router, {"tools": "tools", "sync": "sync", "risk": "risk"})
workflow.add_edge("tools", "market_analyst")
workflow.add_edge("sync", "risk")
workflow.add_edge("risk", "portfolio")
workflow.add_edge("portfolio", END)

fin_app = workflow.compile()
