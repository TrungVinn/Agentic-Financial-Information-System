from typing import Dict, Any
from langgraph.graph import StateGraph, END

from nodes.alias_resolver import resolve_alias
from nodes.sql_template_matcher import match_sql_template
from nodes.sql_llm_generator import generate_sql
from nodes.sql_executor import execute_sql
from nodes.answer_summarizer import summarize_answer


def build_djia_graph():
    graph = StateGraph(dict)

    graph.add_node("resolve_alias", resolve_alias)
    graph.add_node("match_sql_template", match_sql_template)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("summarize_answer", summarize_answer)

    graph.set_entry_point("resolve_alias")

    # resolve_alias -> match template
    graph.add_edge("resolve_alias", "match_sql_template")

    # If matched, go execute; else generate first
    def need_llm(state: Dict[str, Any]) -> str:
        return "generate_sql" if not state.get("sql") else "execute_sql"

    graph.add_conditional_edges("match_sql_template", need_llm, {"generate_sql": "generate_sql", "execute_sql": "execute_sql"})

    # After generate_sql -> execute
    graph.add_edge("generate_sql", "execute_sql")

    # After execute -> summarize
    graph.add_edge("execute_sql", "summarize_answer")

    # End
    graph.add_edge("summarize_answer", END)

    return graph.compile()


def run_djia_graph(question: str) -> Dict[str, Any]:
    app = build_djia_graph()
    result = app.invoke({"question": question})
    # Chuẩn hóa output
    return {
        "sql": result.get("sql", ""),
        "df": result.get("df"),
        "answer": result.get("answer", ""),
        "used_sample": result.get("used_sample", False),
    }


