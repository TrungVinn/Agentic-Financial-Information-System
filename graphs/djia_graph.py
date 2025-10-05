from typing import Dict, Any
from langgraph.graph import StateGraph, END

from nodes.sql_template_matcher import match_sql_template
from nodes.sql_llm_generator import generate_sql
from nodes.sql_executor import execute_sql
from nodes.answer_summarizer import summarize_answer


def build_djia_graph():
    graph = StateGraph(dict)

    graph.add_node("match_sql_template", match_sql_template)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("summarize_answer", summarize_answer)

    graph.set_entry_point("match_sql_template")

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
    
    # Khởi tạo luồng hoạt động
    workflow_steps = []
    
    result = app.invoke({"question": question})
    
    # Step 1: Ticker Extraction + SQL Template Matching (gộp lại)
    workflow_steps.append({
        "step": 1,
        "node": "match_sql_template",
        "description": "Trích xuất ticker và tìm SQL mẫu phù hợp",
        "status": "completed",
        "result": f"Ticker: {result.get('ticker', 'Không tìm thấy')}, SQL mẫu: {'Có' if result.get('sql') else 'Không'}"
    })
    
    # Step 2: SQL Generation (nếu cần)
    if not result.get("sql"):
        workflow_steps.append({
            "step": 2,
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
    
    # Step 4: Answer Summarization
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
        "sql": result.get("actual_sql", result.get("sql", "")),  # Ưu tiên actual_sql đã thay thế parameters
        "actual_sql": result.get("actual_sql", result.get("sql", "")),  # Đảm bảo actual_sql được trả về
        "df": result.get("df"),
        "answer": result.get("answer", ""),
        "used_sample": result.get("used_sample", False),
        "error": result.get("error"),
        "workflow": workflow_steps,  # Thêm luồng hoạt động
    }


