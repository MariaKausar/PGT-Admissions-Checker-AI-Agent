"""LangChain tool-calling agent for interactive admissions Q&A.

Used by the /chat endpoint so admissions staff can ask free-form questions and
have the agent reason with the rule tools. The batch /assess endpoint uses the
deterministic engine for auditable decisions; this agent explains and answers.
"""
from __future__ import annotations

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools import AGENT_TOOLS
from app.services.llm import get_llm

# Simple in-process session store (swap for Redis/DB in production).
_SESSION_STORE: dict[str, InMemoryChatMessageHistory] = {}


def _get_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = InMemoryChatMessageHistory()
    return _SESSION_STORE[session_id]


def build_agent() -> RunnableWithMessageHistory:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, AGENT_TOOLS, prompt)
    executor = AgentExecutor(agent=agent, tools=AGENT_TOOLS, verbose=False, max_iterations=6)

    return RunnableWithMessageHistory(
        executor,
        _get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


_agent_singleton: RunnableWithMessageHistory | None = None


def get_agent() -> RunnableWithMessageHistory:
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = build_agent()
    return _agent_singleton


def _coerce_output(output) -> str:
    # Anthropic can return the final answer as a list of content blocks.
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        parts = []
        for block in output:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts).strip()
    return str(output)


def chat(message: str, session_id: str) -> str:
    agent = get_agent()
    result = agent.invoke(
        {"input": message},
        config={"configurable": {"session_id": session_id}},
    )
    output = result.get("output") if isinstance(result, dict) else result
    return _coerce_output(output)
