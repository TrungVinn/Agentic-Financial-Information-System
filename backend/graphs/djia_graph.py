"""
DJIA Multi-Agent Workflow - LangGraph Implementation.

Module này định nghĩa workflow chính của hệ thống multi-agent,
sử dụng LangGraph để điều phối các nodes chuyên biệt.

WORKFLOW:
┌─────────────────────────────────────────────────────────────┐
│                     START: User Question                     │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
           ┌───────────────────────┐
           │   1. Query Planner    │  Phân tích độ phức tạp
           │   (plan_query)        │  Phát hiện yêu cầu vẽ biểu đồ
           └───────────┬───────────┘
                       ↓
        ┌──────────────────────────────┐
        │  2. SQL Template Matcher     │  Tìm SQL mẫu phù hợp
        │  (match_sql_template)        │  Trích xuất ticker
        └──────────┬──────┬────────────┘
                   │      │
           Có SQL? │      │ Không có
                   │      ↓
                   │  ┌─────────────────────┐
                   │  │  3. SQL Generator   │  Gemini AI sinh SQL
                   │  │  (generate_sql)     │
                   │  └─────────┬───────────┘
                   ↓            ↓
           ┌────────────────────────────┐
           │   4. SQL Executor          │  Thực thi SQL
           │   (execute_sql)            │  Trả về DataFrame
           └────────────┬───────────────┘
                        ↓
              Cần biểu đồ?
                   ↙    ↘
             Có  ↙        ↘  Không
                ↙            ↘
    ┌─────────────────┐    ┌──────────────────────┐
    │  5. Chart Gen   │    │  6. Answer Summary   │
    │  (generate)     │ →  │  (summarize_answer)  │
    └─────────────────┘    └──────────┬───────────┘
                                       ↓
                           ┌───────────────────────┐
                           │   END: Return Result  │
                           └───────────────────────┘
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

# Import các nodes từ nodes/
from nodes.planner import plan_query
from nodes.sql_template_matcher import match_sql_template
from nodes.sql_llm_generator import generate_sql
from nodes.sql_executor import execute_sql
from nodes.answer_summarizer import summarize_answer
from nodes.chart_generator import generate_chart


def build_djia_graph():
    """
    Xây dựng LangGraph workflow với các nodes và edges.

    Workflow gồm 6 nodes chính:
    1. plan_query: Phân tích câu hỏi, xác định độ phức tạp
    2. match_sql_template: Tìm SQL mẫu từ 80+ templates
    3. generate_sql: Sinh SQL bằng Gemini AI (nếu không có mẫu)
    4. execute_sql: Thực thi SQL trên PostgreSQL database
    5. generate_chart: Vẽ biểu đồ (nếu cần)
    6. summarize_answer: Tạo câu trả lời tự nhiên

    Returns:
        Compiled LangGraph workflow ready để invoke
    """
    # Khởi tạo StateGraph với state type là dictionary
    graph = StateGraph(dict)

    # ========== THÊM NODES VÀO GRAPH ==========
    graph.add_node("plan_query", plan_query)
    graph.add_node("match_sql_template", match_sql_template)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("generate_chart", generate_chart)
    graph.add_node("summarize_answer", summarize_answer)

    # ========== ĐỊNH NGHĨA WORKFLOW FLOW ==========

    # Start: Bắt đầu với planning
    graph.set_entry_point("plan_query")

    # Step 1→2: Sau planning → match SQL templates
    graph.add_edge("plan_query", "match_sql_template")

    # Step 2→3/4: Conditional - Có SQL mẫu hay không?
    def need_llm(state: Dict[str, Any]) -> str:
        """
        Quyết định có cần gọi LLM để sinh SQL không.

        Returns:
            "generate_sql" nếu chưa có SQL (không tìm thấy mẫu)
            "execute_sql" nếu đã có SQL từ template
        """
        return "generate_sql" if not state.get("sql") else "execute_sql"

    graph.add_conditional_edges(
        "match_sql_template",
        need_llm,
        {"generate_sql": "generate_sql", "execute_sql": "execute_sql"},
    )

    # Step 3→4: Sau generate SQL → execute
    graph.add_edge("generate_sql", "execute_sql")

    # Step 4→5/6: Conditional - Có cần vẽ biểu đồ không?
    def need_chart(state: Dict[str, Any]) -> str:
        """
        Quyết định có cần vẽ biểu đồ không.

        Dựa trên flag "needs_chart" được set bởi planner.

        Returns:
            "generate_chart" nếu cần vẽ biểu đồ
            "summarize_answer" nếu không cần
        """
        return (
            "generate_chart" if state.get("needs_chart", False) else "summarize_answer"
        )

    graph.add_conditional_edges(
        "execute_sql",
        need_chart,
        {"generate_chart": "generate_chart", "summarize_answer": "summarize_answer"},
    )

    # Step 5→6: Sau vẽ biểu đồ → summarize
    graph.add_edge("generate_chart", "summarize_answer")

    # Step 6→END: Kết thúc workflow
    graph.add_edge("summarize_answer", END)

    # Compile graph thành executable workflow
    return graph.compile()


def run_djia_graph(question: str, force_chart: bool = False) -> Dict[str, Any]:
    """
    Entry point chính để chạy workflow DJIA.

    Hàm này:
    1. Build workflow graph
    2. Invoke với câu hỏi từ user
    3. Track workflow steps để debug
    4. Trả về kết quả cuối cùng với metadata

    Args:
        question: Câu hỏi từ người dùng (tiếng Việt hoặc tiếng Anh)
        force_chart: Force vẽ biểu đồ bất kể câu hỏi có chứa keyword "plot" hay không

    Returns:
        Dictionary chứa:
        - success: Boolean - workflow thành công hay không
        - answer: String - câu trả lời tự nhiên
        - sql: String - SQL đã thực thi (để hiển thị)
        - df: DataFrame - dữ liệu kết quả
        - chart: Plotly Figure - biểu đồ (nếu có)
        - used_sample: Boolean - có dùng SQL mẫu không
        - error: String - error message (nếu có lỗi)
        - workflow: List - các bước đã thực hiện
        - complexity: Dict - thông tin độ phức tạp

    Examples:
        >>> result = run_djia_graph("What was Apple's closing price on 2024-01-15?")
        >>> print(result['answer'])
        'The closing price of Apple on January 15, 2024 was $185.92'

        >>> result = run_djia_graph("Vẽ biểu đồ giá Apple trong Q1 2024")
        >>> result['chart']  # Plotly figure object
    """
    # Build và compile workflow
    app = build_djia_graph()

    # Track workflow steps để debugging/logging
    workflow_steps = []

    # Invoke workflow với initial state
    initial_state = {"question": question}
    if force_chart:
        initial_state["force_chart"] = True
    result = app.invoke(initial_state)

    # ========== TRACK WORKFLOW STEPS ==========

    # Lấy thông tin complexity để quyết định steps nào đã chạy
    complexity = result.get("complexity", {})

    # Step 0: Planning (chỉ log nếu là multi-step query)
    if complexity.get("is_multi_step"):
        workflow_steps.append(
            {
                "step": 1,
                "node": "plan_query",
                "description": "Phân tích và lên kế hoạch cho câu hỏi phức tạp",
                "status": "completed",
                "result": f"Độ phức tạp: Multi-step, Cần biểu đồ: {complexity.get('needs_chart')}",
            }
        )

    # Step 1: SQL Template Matching
    workflow_steps.append(
        {
            "step": len(workflow_steps) + 1,
            "node": "match_sql_template",
            "description": "Trích xuất ticker và tìm SQL mẫu phù hợp",
            "status": "completed",
            "result": f"Ticker: {result.get('ticker', 'N/A')}, SQL mẫu: {'✓' if result.get('used_sample') else '✗'}",
        }
    )

    # Step 2: SQL Generation (nếu không có mẫu)
    if not result.get("used_sample"):
        workflow_steps.append(
            {
                "step": len(workflow_steps) + 1,
                "node": "generate_sql",
                "description": "Sinh SQL bằng Gemini AI",
                "status": "completed",
                "result": "SQL được sinh tự động bởi LLM",
            }
        )

    # Step 3: SQL Execution
    workflow_steps.append(
        {
            "step": len(workflow_steps) + 1,
            "node": "execute_sql",
            "description": "Thực thi SQL trên PostgreSQL database",
            "status": "completed" if not result.get("error") else "error",
            "result": (
                f"Trả về {len(result.get('df', []))} dòng dữ liệu"
                if result.get("df") is not None
                else "Lỗi thực thi"
            ),
        }
    )

    # Step 4: Chart Generation (nếu cần)
    if result.get("needs_chart"):
        workflow_steps.append(
            {
                "step": len(workflow_steps) + 1,
                "node": "generate_chart",
                "description": f"Tạo biểu đồ {result.get('chart_type', 'line')}",
                "status": "completed" if result.get("chart") else "skipped",
                "result": f"Biểu đồ: {'✓ Đã tạo' if result.get('chart') else '✗ Không tạo được'}",
            }
        )

    # Step 5: Answer Summarization
    workflow_steps.append(
        {
            "step": len(workflow_steps) + 1,
            "node": "summarize_answer",
            "description": "Tạo câu trả lời tự nhiên từ kết quả",
            "status": "completed",
            "result": f"Câu trả lời: {'✓' if result.get('answer') else '✗'}",
        }
    )

    # ========== VALIDATE KẾT QUẢ ==========
    has_error = result.get("error") is not None
    has_answer = bool(result.get("answer", "").strip())
    has_data = result.get("df") is not None and not result.get("df").empty

    # Workflow thành công nếu không có lỗi và có kết quả (answer hoặc data)
    success = not has_error and (has_answer or has_data)

    # ========== CHUẨN HÓA OUTPUT ==========
    return {
        "success": success,  # Workflow thành công?
        "sql": result.get("actual_sql", result.get("sql", "")),  # SQL đã thực thi
        "actual_sql": result.get("actual_sql", result.get("sql", "")),
        "df": result.get("df"),  # DataFrame kết quả
        "answer": result.get("answer", ""),  # Câu trả lời tự nhiên
        "used_sample": result.get("used_sample", False),  # Có dùng SQL mẫu?
        "error": result.get("error"),  # Error message (nếu có)
        "workflow": workflow_steps,  # Steps đã thực hiện
        "chart": result.get("chart"),  # Plotly figure (nếu có)
        "complexity": complexity,  # Thông tin độ phức tạp
    }
