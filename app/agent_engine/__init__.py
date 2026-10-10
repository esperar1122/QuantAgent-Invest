"""
AgentEngine 智能体决策核心引擎
基于 LangGraph 的多智能体协作、辩论推演与综合交易决策系统
"""
from app.agent_engine.graph.trading_graph import TradingAgentsGraph
from app.agent_engine.default_config import DEFAULT_CONFIG
from app.agent_engine.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from app.agent_engine.agents.utils.agent_utils import Toolkit

# 现代化类命名：AgentEngineGraph
AgentEngineGraph = TradingAgentsGraph
DEFAULT_AGENT_CONFIG = DEFAULT_CONFIG

__all__ = [
    "AgentEngineGraph",
    "TradingAgentsGraph",
    "DEFAULT_AGENT_CONFIG",
    "DEFAULT_CONFIG",
    "AgentState",
    "InvestDebateState",
    "RiskDebateState",
    "Toolkit",
]
