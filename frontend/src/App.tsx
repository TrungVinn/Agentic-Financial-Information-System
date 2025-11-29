import { useState, useCallback, useEffect } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type DjiaQueryResponse = {
  success: boolean
  answer: string
  sql: string
  used_sample: boolean
  error?: string | null
  rows: Record<string, unknown>[]
  conversation_id: string | null
}

type LocalSession = {
  sessionId: string
  title: string // Câu hỏi đầu tiên
  messages: {
    question: string
    answer: string
    sql: string
    rows: Record<string, unknown>[]
  }[]
  createdAt: string
  updatedAt: string
}

type UserInfo = {
  username: string
}

type ConversationSummary = {
  id: string
  title: string
  updated_at: string
}

type ConversationDetail = {
  id: string
  title: string
  messages: {
    id: number
    role: 'user' | 'assistant'
    content: string
    sql?: string | null
    used_sample?: boolean
    error?: string | null
    rows?: Record<string, unknown>[] | null
    created_at: string
  }[]
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  answerData?: {
    sql?: string
    rows?: Record<string, unknown>[]
    used_sample?: boolean
  }
}

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<DjiaQueryResponse | null>(null)
  const [loadingQuery, setLoadingQuery] = useState(false)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [history, setHistory] = useState<LocalSession[]>(() => {
    try {
      const raw = window.localStorage.getItem('afs:history')
      if (!raw) return []
      const parsed = JSON.parse(raw)
      // Migrate old format if needed (old format was ChatTurn[])
      if (Array.isArray(parsed) && parsed.length > 0 && 'question' in parsed[0] && !('sessionId' in parsed[0])) {
        // Convert old format to new format: each turn becomes a session
        return parsed.map((turn: any) => ({
          sessionId: turn.conversationId || `local-${Date.now()}-${Math.random()}`,
          title: turn.question,
          messages: [{ question: turn.question, answer: turn.answer, sql: turn.sql, rows: turn.rows }],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }))
      }
      return parsed as LocalSession[]
    } catch {
      return []
    }
  })
  const [user, setUser] = useState<UserInfo | null>(null)
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ username: '', password: '' })
  const [authError, setAuthError] = useState<string | null>(null)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [activeLocalSessionId, setActiveLocalSessionId] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState<'chat' | 'auth'>('chat')
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [collapsedSections, setCollapsedSections] = useState<Record<string, { sql: boolean; table: boolean }>>({})

  const fetchConversations = useCallback(async () => {
    if (!user) return
    try {
      setLoadingConversations(true)
      const res = await fetch('/api/conversations/', { credentials: 'include' })
      if (!res.ok) return
      const data = (await res.json()) as ConversationSummary[]
      setConversations(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingConversations(false)
    }
  }, [user])

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await fetch('/api/auth/me/', { credentials: 'include' })
        if (res.ok) {
          const data = (await res.json()) as UserInfo
          setUser(data)
        }
      } catch (err) {
        console.error(err)
      }
    }
    fetchMe()
  }, [])

  useEffect(() => {
    if (user) {
      fetchConversations()
      setActiveLocalSessionId(null) // Clear local session when logged in
    } else {
      setConversations([])
      setActiveConversationId(null)
    }
  }, [user, fetchConversations])

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault()
    setAuthError(null)
    if (!loginForm.username || !loginForm.password) {
      setAuthError('Vui lòng nhập username và password.')
      return
    }
    try {
      const res = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(loginForm),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Đăng nhập thất bại.' }))
        setAuthError(data.detail || 'Đăng nhập thất bại.')
        return
      }
      const data = (await res.json()) as UserInfo
      setUser(data)
      setLoginForm({ username: '', password: '' })
      setAuthError(null)
      setActiveLocalSessionId(null) // Clear local session when logged in
      setCurrentPage('chat')
    } catch (err) {
      setAuthError('Không thể kết nối máy chủ.')
    }
  }

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout/', {
        method: 'POST',
        credentials: 'include',
      })
    } catch (err) {
      console.error(err)
    } finally {
      setUser(null)
      setConversations([])
      setActiveConversationId(null)
      setActiveLocalSessionId(null)
      setCurrentPage('chat')
    }
  }

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault()
    setAuthError(null)
    if (!registerForm.username || !registerForm.password) {
      setAuthError('Vui lòng nhập username và password.')
      return
    }
    try {
      const res = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setAuthError(data.detail || 'Đăng ký thất bại.')
        return
      }
      // Đăng ký xong tự chuyển sang tab đăng nhập
      setAuthMode('login')
      setLoginForm({ username: registerForm.username, password: '' })
      setRegisterForm({ username: '', password: '' })
      setAuthError('Đăng ký thành công, hãy đăng nhập.')
    } catch (err) {
      setAuthError('Không thể kết nối máy chủ.')
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      const res = await fetch(`/api/conversations/${conversationId}/messages/`, {
        credentials: 'include',
      })
      if (!res.ok) {
        if (res.status === 401) {
          setUser(null)
        }
        return
      }
      const data = (await res.json()) as ConversationDetail
      const assistantMessages = data.messages.filter((msg) => msg.role === 'assistant')
      const last = assistantMessages[assistantMessages.length - 1]
      if (last) {
        setAnswer({
          success: !last.error,
          answer: last.content,
          sql: last.sql || '',
          used_sample: Boolean(last.used_sample),
          error: last.error,
          rows: (last.rows as Record<string, unknown>[] | null) || [],
          conversation_id: conversationId,
        })
      }
      const mapped: ChatMessage[] = data.messages.map((msg) => ({
        id: String(msg.id),
        role: msg.role,
        content: msg.content,
        answerData: msg.role === 'assistant' ? {
          sql: msg.sql || undefined,
          rows: msg.rows || undefined,
          used_sample: msg.used_sample || false,
        } : undefined,
      }))
      setMessages(mapped)
      
      // Khởi tạo collapsed state cho tất cả messages
      const initialCollapsed: Record<string, { sql: boolean; table: boolean }> = {}
      mapped.forEach((msg) => {
        if (msg.role === 'assistant' && msg.answerData) {
          initialCollapsed[msg.id] = { sql: false, table: false }
        }
      })
      setCollapsedSections(initialCollapsed)
      setActiveConversationId(conversationId)
      setActiveLocalSessionId(null) // Clear local session when loading server conversation
    } catch (err) {
      console.error(err)
    }
  }

  const loadLocalSession = (session: LocalSession) => {
    setActiveLocalSessionId(session.sessionId)
    setActiveConversationId(null) // Clear server conversation ID
    
    // Reconstruct messages from session
    const sessionMessages: ChatMessage[] = []
    session.messages.forEach((msg, idx) => {
      sessionMessages.push({
        id: `local-user-${idx}`,
        role: 'user',
        content: msg.question,
      })
      sessionMessages.push({
        id: `local-assistant-${idx}`,
        role: 'assistant',
        content: msg.answer,
        answerData: {
          sql: msg.sql,
          rows: msg.rows,
          used_sample: false,
        },
      })
    })
    setMessages(sessionMessages)
    
    // Khởi tạo collapsed state cho tất cả messages
    const initialCollapsed: Record<string, { sql: boolean; table: boolean }> = {}
    sessionMessages.forEach((msg) => {
      if (msg.role === 'assistant' && msg.answerData) {
        initialCollapsed[msg.id] = { sql: false, table: false }
      }
    })
    setCollapsedSections(initialCollapsed)
    
    // Set answer to last message if exists
    const lastMsg = session.messages[session.messages.length - 1]
    if (lastMsg) {
      setAnswer({
        success: true,
        answer: lastMsg.answer,
        sql: lastMsg.sql,
        used_sample: false,
        error: null,
        rows: lastMsg.rows,
        conversation_id: session.sessionId,
      })
    } else {
      setAnswer(null)
    }
  }

  const formatDateTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('vi-VN', {
        hour12: false,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return iso
    }
  }

  const handleAsk = async (e: FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    try {
      setLoadingQuery(true)
      setQueryError(null)
      setAnswer(null)

      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: question,
      }
      setMessages((prev) => [...prev, userMsg])

      const payload: Record<string, unknown> = { question }
      if (user && activeConversationId) {
        payload.conversation_id = activeConversationId
      }

      const res = await fetch('/api/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status}: ${text}`)
      }

      const data = (await res.json()) as DjiaQueryResponse
      setAnswer(data)
      
      const assistantMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: data.answer,
        answerData: {
          sql: data.sql,
          rows: data.rows,
          used_sample: data.used_sample,
        },
      }
      setMessages((prev) => [...prev, assistantMsg])
      
      // Mặc định mở tất cả sections cho message mới
      const msgId = assistantMsg.id
      setCollapsedSections((prev) => ({
        ...prev,
        [msgId]: { sql: false, table: false },
      }))

      if (user) {
        // User đã đăng nhập: dùng conversation_id từ server
        setActiveConversationId(data.conversation_id)
        setActiveLocalSessionId(null) // Clear local session
        fetchConversations()
      } else {
        // User chưa đăng nhập: quản lý local session
        const now = new Date().toISOString()
        let sessionId = activeLocalSessionId
        
        if (!sessionId) {
          // Tạo session mới
          sessionId = `local-${Date.now()}`
          setActiveLocalSessionId(sessionId)
          
          const newSession: LocalSession = {
            sessionId,
            title: question, // Câu hỏi đầu tiên làm title
            messages: [{ question, answer: data.answer, sql: data.sql, rows: data.rows }],
            createdAt: now,
            updatedAt: now,
          }
          const nextHistory = [...history, newSession]
          setHistory(nextHistory)
          window.localStorage.setItem('afs:history', JSON.stringify(nextHistory))
        } else {
          // Cập nhật session hiện có
          const sessionIndex = history.findIndex((s) => s.sessionId === sessionId)
          if (sessionIndex >= 0) {
            const updatedHistory = [...history]
            updatedHistory[sessionIndex] = {
              ...updatedHistory[sessionIndex],
              messages: [
                ...updatedHistory[sessionIndex].messages,
                { question, answer: data.answer, sql: data.sql, rows: data.rows },
              ],
              updatedAt: now,
            }
            setHistory(updatedHistory)
            window.localStorage.setItem('afs:history', JSON.stringify(updatedHistory))
          }
        }
      }
    } catch (err) {
      setQueryError((err as Error).message)
    } finally {
      setLoadingQuery(false)
    }
  }

  const toggleSection = (messageId: string, section: 'sql' | 'table') => {
    setCollapsedSections((prev) => ({
      ...prev,
      [messageId]: {
        ...prev[messageId],
        [section]: !prev[messageId]?.[section],
      },
    }))
  }

  const handleNewChat = () => {
    setActiveConversationId(null)
    setActiveLocalSessionId(null) // Reset local session
    setAnswer(null)
    setQuestion('')
    setMessages([])
    setCollapsedSections({})
  }

  const handleDeleteConversation = async (id: string) => {
    if (!user) return
    try {
      const res = await fetch(`/api/conversations/${id}/`, {
        method: 'DELETE',
        credentials: 'include',
      })
      if (!res.ok) return
      const next = conversations.filter((c) => c.id !== id)
      setConversations(next)
      if (activeConversationId === id) {
        setActiveConversationId(null)
        setAnswer(null)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleDeleteLocalSession = (sessionId: string) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa phiên chat này?')) return
    
    const next = history.filter((s) => s.sessionId !== sessionId)
    setHistory(next)
    window.localStorage.setItem('afs:history', JSON.stringify(next))
    
    // Nếu đang xem session này, clear chat
    if (activeLocalSessionId === sessionId) {
      handleNewChat()
    }
  }

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : ''} ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className={`history-sidebar ${sidebarOpen ? 'open' : ''} ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="history-sidebar-header">
          <button
            className="sidebar-toggle-button"
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? "Mở rộng sidebar" : "Thu gọn sidebar"}
          >
            ☰
          </button>
        </div>
        <div className="history-sidebar-body">
          <button
            type="button"
            className="new-chat-button"
            onClick={() => {
              handleNewChat()
              setCurrentPage('chat')
              if (sidebarCollapsed) setSidebarCollapsed(false)
            }}
            title={sidebarCollapsed ? "Đoạn chat mới" : undefined}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"></path>
            </svg>
            {!sidebarCollapsed && <span>Đoạn chat mới</span>}
          </button>
          
          {!sidebarCollapsed && (
            <div className="sidebar-section">
              <h3 className="sidebar-section-title">Các đoạn chat của bạn</h3>
              {user ? (
                <>
                  {loadingConversations && <p className="sidebar-hint">Đang tải lịch sử...</p>}
                  {conversations.length === 0 && !loadingConversations && (
                    <p className="sidebar-hint">Chưa có phiên chat nào.</p>
                  )}
                  {conversations.length > 0 && (
                    <ul className="history-list">
                      {conversations.map((conv) => (
                        <li key={conv.id}>
                          <div className="history-row">
                            <button
                              className={`history-button ${activeConversationId === conv.id ? 'active' : ''}`}
                              onClick={() => {
                                loadConversation(conv.id)
                                setCurrentPage('chat')
                              }}
                            >
                              <span className="history-title">{conv.title || 'Phiên không tiêu đề'}</span>
                            </button>
                            <button
                              className="history-delete"
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteConversation(conv.id)
                              }}
                              title="Xóa"
                            >
                              ✕
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : (
                <>
                  {history.length > 0 ? (
                    <ul className="history-list">
                      {history.map((session) => (
                        <li key={session.sessionId}>
                          <div className="history-row">
                            <button
                              className={`history-button ${activeLocalSessionId === session.sessionId ? 'active' : ''}`}
                              onClick={() => {
                                loadLocalSession(session)
                                setCurrentPage('chat')
                              }}
                            >
                              <span className="history-title">{session.title}</span>
                            </button>
                            <button
                              className="history-delete"
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteLocalSession(session.sessionId)
                              }}
                              title="Xóa"
                            >
                              ✕
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </>
              )}
            </div>
          )}
        </div>
        
        {user && (
          <div className="sidebar-footer">
            {!sidebarCollapsed && (
              <div className="sidebar-user">
                <div className="sidebar-user-avatar">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="sidebar-user-info">
                  <div className="sidebar-user-name">{user.username}</div>
                  <div className="sidebar-user-status">Free</div>
                </div>
              </div>
            )}
            {sidebarCollapsed && (
              <div className="sidebar-user-avatar-only">
                {user.username.charAt(0).toUpperCase()}
              </div>
            )}
            <button
              className="sidebar-logout-button"
              type="button"
              onClick={handleLogout}
              title="Đăng xuất"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        )}
      </aside>

      <div className="app-root">
        <header className="app-header">
          <h1 className="app-title">Agentic Financial System</h1>
          <div className="app-header-actions">
            {user ? (
              <>
                <span className="app-user-label">{user.username}</span>
                <button className="header-button" type="button" onClick={handleLogout}>
                  Đăng xuất
                </button>
              </>
            ) : (
              <button
                className="header-button"
                type="button"
                onClick={() => {
                  setCurrentPage('auth')
                  setAuthMode('login')
                }}
              >
                Đăng nhập / Đăng ký
              </button>
            )}
          </div>
        </header>

        {currentPage === 'chat' && (
          <main className="chat-main">
            {messages.length === 0 && !loadingQuery && (
              <div className="chat-welcome">
                <h2 className="chat-welcome-title">Hệ thống hỏi đáp thông minh về dữ liệu chứng khoán DJIA</h2>
              </div>
            )}

            <div className="chat-messages">
              {messages.map((msg) => {
                const isCollapsed = collapsedSections[msg.id] || { sql: false, table: false }
                const answerData = msg.answerData
                const rows = answerData?.rows || []
                const columns = rows[0] ? Object.keys(rows[0]) : []

                return (
                  <div key={msg.id}>
                    <div
                      className={`chat-message ${msg.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'}`}
                    >
                      <div className="chat-message-content">
                        <div className="chat-bubble">
                          <p>{msg.content}</p>
                        </div>
                      </div>
                    </div>

                    {msg.role === 'assistant' && answerData && (
                      <>
                        {answerData.sql && (
                          <div className="chat-message chat-message-assistant">
                            <div className="chat-message-content">
                              <div className="chat-bubble chat-bubble-result">
                                <div className="result-header">
                                  <h3 
                                    className="result-header-title clickable"
                                    onClick={() => toggleSection(msg.id, 'sql')}
                                  >
                                    SQL đã chạy
                                    <span className="collapse-icon">
                                      {isCollapsed.sql ? '▼' : '▲'}
                                    </span>
                                  </h3>
                                  {answerData.used_sample && <span className="badge badge-success">Dùng SQL mẫu</span>}
                                </div>
                                {!isCollapsed.sql && (
                                  <pre className="sql-block">{answerData.sql}</pre>
                                )}
                              </div>
                            </div>
                          </div>
                        )}

                        {rows.length > 0 && (
                          <div className="chat-message chat-message-assistant">
                            <div className="chat-message-content">
                              <div className="chat-bubble chat-bubble-result">
                                <h3 
                                  className="result-header-title clickable"
                                  onClick={() => toggleSection(msg.id, 'table')}
                                >
                                  Bảng dữ liệu
                                  <span className="collapse-icon">
                                    {isCollapsed.table ? '▼' : '▲'}
                                  </span>
                                </h3>
                                {!isCollapsed.table && (
                                  <div className="table-wrapper">
                                    <table className="data-table">
                                      <thead>
                                        <tr>
                                          {columns.map((col) => (
                                            <th key={col}>{col}</th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {rows.map((row, idx) => (
                                          <tr key={idx}>
                                            {columns.map((col) => (
                                              <td key={col}>{String(row[col] ?? '')}</td>
                                            ))}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )
              })}

              {loadingQuery && (
                <div className="chat-message chat-message-assistant">
                  <div className="chat-message-content">
                    <div className="chat-bubble">
                      <div className="loading-indicator">
                        <div className="spinner" />
                        <p>Agent đang phân tích câu hỏi, sinh SQL và truy vấn dữ liệu...</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </main>
        )}

        {currentPage === 'auth' && (
          <main className="auth-main">
            <div className="auth-container">
              <h2 className="auth-title">Agentic Financial System</h2>
              <div className="auth-tabs">
                <button
                  type="button"
                  className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
                  onClick={() => {
                    setAuthMode('login')
                    setAuthError(null)
                  }}
                >
                  Đăng nhập
                </button>
                <button
                  type="button"
                  className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
                  onClick={() => {
                    setAuthMode('register')
                    setAuthError(null)
                  }}
                >
                  Đăng ký
                </button>
      </div>

              {authMode === 'login' ? (
                <form className="login-form" onSubmit={handleLogin}>
                  <input
                    type="text"
                    className="text-input"
                    placeholder="Username"
                    value={loginForm.username}
                    onChange={(e) => setLoginForm((prev) => ({ ...prev, username: e.target.value }))}
                  />
                  <input
                    type="password"
                    className="text-input"
                    placeholder="Password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm((prev) => ({ ...prev, password: e.target.value }))}
                  />
                  {authError && <p className="error-text">{authError}</p>}
                  <button className="auth-button" type="submit">
                    Đăng nhập
                  </button>
                  <p className="hint-text">Đăng nhập để đồng bộ lịch sử phiên chat lên máy chủ.</p>
                </form>
              ) : (
                <form className="login-form" onSubmit={handleRegister}>
                  <input
                    type="text"
                    className="text-input"
                    placeholder="Username"
                    value={registerForm.username}
                    onChange={(e) => setRegisterForm((prev) => ({ ...prev, username: e.target.value }))}
                  />
                  <input
                    type="password"
                    className="text-input"
                    placeholder="Password"
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm((prev) => ({ ...prev, password: e.target.value }))}
                  />
                  {authError && <p className="error-text">{authError}</p>}
                  <button className="auth-button" type="submit">
                    Đăng ký
        </button>
                  <p className="hint-text">Sau khi đăng ký, bạn có thể đăng nhập và xem lại lịch sử các phiên chat.</p>
                </form>
              )}
            </div>
          </main>
        )}
      </div>

      {currentPage === 'chat' && (
        <form className="chat-input-bar" onSubmit={handleAsk}>
          <div className="chat-input-wrapper">
            <input
              type="text"
              className="chat-input"
              placeholder="Nhập câu hỏi tài chính (VI/EN)..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button className="chat-send-button" type="submit" disabled={loadingQuery}>
              Gửi
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

export default App
