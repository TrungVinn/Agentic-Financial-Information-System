from django.urls import path
from .views import (
    djia_query,
    list_conversations,
    conversation_messages,
    login_view,
    logout_view,
    me_view,
    register_view,
    delete_conversation,
    execute_sql,
)

urlpatterns = [
    path("query/", djia_query, name="djia-query"),
    path("conversations/", list_conversations, name="conversation-list"),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        conversation_messages,
        name="conversation-messages",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        delete_conversation,
        name="conversation-delete",
    ),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/me/", me_view, name="auth-me"),
    path("auth/register/", register_view, name="auth-register"),
    path("execute-sql/", execute_sql, name="execute-sql"),
]


