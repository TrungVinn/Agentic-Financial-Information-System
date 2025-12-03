from datetime import date, datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.io as pio
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from graphs.djia_graph import run_djia_graph
from nodes.sql_executor import run_sql
from .models import Conversation, Message


def _normalize_value(val: Any) -> Any:
    if isinstance(val, (pd.Timestamp, datetime, date)):
        return val.isoformat()
    return val


def _df_to_rows(df: pd.DataFrame, max_rows: int = 100) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    trimmed = df.head(max_rows).copy()
    return trimmed.applymap(_normalize_value).to_dict(orient="records")


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def djia_query(request):
    """
    Nhận câu hỏi tự nhiên, chạy multi-agent DJIA và trả về kết quả JSON cho FE.

    Body:
        { "question": "..." }
    """
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response({"detail": "Thiếu trường 'question'."}, status=400)

    # Kiểm tra force_chart flag từ frontend
    force_chart = request.data.get("force_chart", False)

    user = request.user if request.user.is_authenticated else None

    # ========== TRƯỜNG HỢP CHƯA ĐĂNG NHẬP: KHÔNG LƯU DB ==========
    if user is None:
        try:
            result = run_djia_graph(question, force_chart=force_chart)
        except Exception as e:
            return Response(
                {"success": False, "error": f"Lỗi nội bộ khi chạy agent: {e}"},
                status=500,
            )

        df = result.get("df")
        rows = _df_to_rows(df) if isinstance(df, pd.DataFrame) else []

        chart = result.get("chart")
        chart_json = None
        if chart is not None:
            try:
                chart_json = pio.to_json(chart)
            except Exception:
                chart_json = None

        payload: Dict[str, Any] = {
            "success": bool(result.get("success")),
            "answer": result.get("answer", ""),
            "sql": result.get("actual_sql") or result.get("sql") or "",
            "used_sample": bool(result.get("used_sample", False)),
            "error": result.get("error"),
            "rows": rows,
            "workflow": result.get("workflow", []),
            "complexity": result.get("complexity", {}),
            "chart_json": chart_json,
            "conversation_id": None,
        }

        return Response(payload)

    # ========== ĐÃ ĐĂNG NHẬP: LƯU THEO USER ==========
    conversation_id = request.data.get("conversation_id")
    conversation: Conversation
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=user)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation không tồn tại."}, status=404)
    else:
        title = question[:80]
        conversation = Conversation.objects.create(user=user, title=title)

    # Lưu message của user
    Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_USER,
        content=question,
    )

    # ========== CHẠY AGENT ==========
    try:
        result = run_djia_graph(question, force_chart=force_chart)
    except Exception as e:
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=f"Lỗi nội bộ khi chạy agent: {e}",
            error=str(e),
        )
        return Response(
            {"success": False, "error": f"Lỗi nội bộ khi chạy agent: {e}"},
            status=500,
        )

    df = result.get("df")
    rows = _df_to_rows(df) if isinstance(df, pd.DataFrame) else []

    chart = result.get("chart")
    chart_json = None
    if chart is not None:
        try:
            chart_json = pio.to_json(chart)
        except Exception:
            chart_json = None

    payload: Dict[str, Any] = {
        "success": bool(result.get("success")),
        "answer": result.get("answer", ""),
        "sql": result.get("actual_sql") or result.get("sql") or "",
        "used_sample": bool(result.get("used_sample", False)),
        "error": result.get("error"),
        "rows": rows,
        "workflow": result.get("workflow", []),
        "complexity": result.get("complexity", {}),
        "chart_json": chart_json,
        "conversation_id": str(conversation.id),
    }

    # Lưu message của assistant
    Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=payload["answer"],
        sql=payload["sql"],
        used_sample=payload["used_sample"],
        error=str(payload["error"] or ""),
        rows_json=rows,
        metadata={
            "workflow": payload["workflow"],
            "complexity": payload["complexity"],
            "chart_json": chart_json,
        },
    )

    return Response(payload)


@api_view(["GET"])
def list_conversations(request):
    """
    Trả về danh sách các phiên chat (để FE hiển thị sidebar / lịch sử).
    """
    if not request.user.is_authenticated:
        return Response([])

    conversations = Conversation.objects.filter(user=request.user)
    data = [
        {
            "id": str(conv.id),
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]
    return Response(data)


@api_view(["GET"])
def conversation_messages(request, conversation_id: str):
    """
    Trả về toàn bộ message trong một phiên chat.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Cần đăng nhập."}, status=401)

    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"detail": "Conversation không tồn tại."}, status=404)

    messages = conversation.messages.all()
    data = [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sql": msg.sql,
            "used_sample": msg.used_sample,
            "error": msg.error,
            "rows": msg.rows_json,
            "metadata": msg.metadata,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]
    return Response({"id": str(conversation.id), "title": conversation.title, "messages": data})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Đăng nhập sử dụng session Django.
    """
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    if not username or not password:
        return Response({"detail": "Thiếu username hoặc password."}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "Sai tên đăng nhập hoặc mật khẩu."}, status=400)

    login(request, user)
    return Response({"username": user.username})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Đăng xuất khỏi session hiện tại.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Chưa đăng nhập."}, status=400)
    logout(request)
    return Response({"success": True})


@api_view(["GET"])
def me_view(request):
    """
    Trả về thông tin user hiện tại (nếu đã đăng nhập).
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Chưa đăng nhập."}, status=401)
    return Response({"username": request.user.username})


User = get_user_model()


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """
    Đăng ký tài khoản mới (đơn giản: username + password).
    """
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    if not username or not password:
        return Response({"detail": "Thiếu username hoặc password."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "Username đã tồn tại."}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"username": username})


@api_view(["DELETE"])
def delete_conversation(request, conversation_id: str):
    """
    Xóa một phiên chat (và toàn bộ messages thuộc nó) của user hiện tại.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Cần đăng nhập."}, status=401)

    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"detail": "Conversation không tồn tại."}, status=404)

    conversation.delete()
    return Response({"success": True})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def execute_sql(request):
    """
    Chạy SQL trực tiếp trên database (không qua LLM).
    
    Body:
        { "sql": "SELECT * FROM prices WHERE ticker = 'AAPL' LIMIT 10" }
    
    Returns:
        {
            "success": true/false,
            "rows": [...],
            "sql": "SQL đã chạy",
            "error": null hoặc error message
        }
    """
    sql = (request.data.get("sql") or "").strip()
    if not sql:
        return Response({"detail": "Thiếu trường 'sql'."}, status=400)
    
    try:
        # Chạy SQL trực tiếp (không có parameters)
        df, display_sql = run_sql(sql, {})
        rows = _df_to_rows(df)
        
        return Response({
            "success": True,
            "rows": rows,
            "sql": display_sql,
            "error": None,
        })
    except Exception as e:
        return Response({
            "success": False,
            "rows": [],
            "sql": sql,
            "error": str(e),
        }, status=500)
