from typing import Dict, Any
from langgraph.graph import StateGraph, END

from nodes.planner import plan_query
from nodes.sql_template_matcher import match_sql_template
from nodes.sql_llm_generator import generate_sql
from nodes.sql_executor import execute_sql
from nodes.answer_summarizer import summarize_answer
from nodes.chart_generator import generate_chart


def build_djia_graph():
    graph = StateGraph(dict)

    # Add all nodes
    graph.add_node("plan_query", plan_query)
    graph.add_node("match_sql_template", match_sql_template)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("generate_chart", generate_chart)
    graph.add_node("summarize_answer", summarize_answer)

    # Start with planning
    graph.set_entry_point("plan_query")

    # After planning -> match templates
    graph.add_edge("plan_query", "match_sql_template")

    # If matched, go execute; else generate first
    def need_llm(state: Dict[str, Any]) -> str:
        return "generate_sql" if not state.get("sql") else "execute_sql"

    graph.add_conditional_edges("match_sql_template", need_llm, {"generate_sql": "generate_sql", "execute_sql": "execute_sql"})

    # After generate_sql -> execute
    graph.add_edge("generate_sql", "execute_sql")

    # After execute -> decide if need chart
    def need_chart(state: Dict[str, Any]) -> str:
        return "generate_chart" if state.get("needs_chart", False) else "summarize_answer"

    graph.add_conditional_edges("execute_sql", need_chart, {"generate_chart": "generate_chart", "summarize_answer": "summarize_answer"})

    # After chart -> summarize
    graph.add_edge("generate_chart", "summarize_answer")

    # End
    graph.add_edge("summarize_answer", END)

    return graph.compile()


def run_djia_graph(question: str) -> Dict[str, Any]:
    app = build_djia_graph()
    
    # Khởi tạo luồng hoạt động
    workflow_steps = []
    
    result = app.invoke({"question": question})
    
    # Step 0: Planning (nếu là câu hỏi phức tạp)
    complexity = result.get("complexity", {})
    if complexity.get("is_multi_step"):
        workflow_steps.append({
            "step": 1,
            "node": "plan_query",
            "description": "Phân tích và lên kế hoạch cho câu hỏi phức tạp",
            "status": "completed",
            "result": f"Độ phức tạp: Multi-step, Cần biểu đồ: {complexity.get('needs_chart')}"
        })
    
    # Step 1: Ticker Extraction + SQL Template Matching
    workflow_steps.append({
        "step": len(workflow_steps) + 1,
        "node": "match_sql_template",
        "description": "Trích xuất ticker và tìm SQL mẫu phù hợp",
        "status": "completed",
        "result": f"Ticker: {result.get('ticker', 'Không tìm thấy')}, SQL mẫu: {'Có' if result.get('sql') else 'Không'}"
    })
    
    # Step 2: SQL Generation (nếu cần)
    if not result.get("sql"):
        workflow_steps.append({
            "step": len(workflow_steps) + 1,
            "node": "generate_sql",
            "description": "Sinh SQL bằng Gemini AI",
            "status": "completed",
            "result": "SQL được sinh tự động"
        })
    
    # Step 3: SQL Execution
    workflow_steps.append({
        "step": len(workflow_steps) + 1,
        "node": "execute_sql",
        "description": "Thực thi SQL trên database",
        "status": "completed" if not result.get("error") else "error",
        "result": f"Kết quả: {len(result.get('df', []))} dòng" if result.get("df") is not None else "Lỗi thực thi"
    })
    
    # Step 4: Chart Generation (nếu cần)
    if result.get("needs_chart"):
        workflow_steps.append({
            "step": len(workflow_steps) + 1,
            "node": "generate_chart",
            "description": f"Tạo biểu đồ {result.get('chart_type', 'line')}",
            "status": "completed" if result.get("chart") else "skipped",
            "result": f"Biểu đồ: {'Có' if result.get('chart') else 'Không'}"
        })
    
    # Step 5: Answer Summarization
    workflow_steps.append({
        "step": len(workflow_steps) + 1,
        "node": "summarize_answer",
        "description": "Tạo câu trả lời từ kết quả",
        "status": "completed",
        "result": f"Câu trả lời: {'Có' if result.get('answer') else 'Không'}"
    })
    
    # Kiểm tra có lỗi không
    has_error = result.get("error") is not None
    has_answer = bool(result.get("answer", "").strip())
    has_data = result.get("df") is not None and not result.get("df").empty
    
    success = not has_error and (has_answer or has_data)
    
    # Chuẩn hóa output
    return {
        "success": success,
        "sql": result.get("actual_sql", result.get("sql", "")),
        "actual_sql": result.get("actual_sql", result.get("sql", "")),
        "df": result.get("df"),
        "answer": result.get("answer", ""),
        "used_sample": result.get("used_sample", False),
        "error": result.get("error"),
        "workflow": workflow_steps,
        "chart": result.get("chart"),  # Thêm biểu đồ vào output
        "complexity": complexity,  # Thêm độ phức tạp
    }


