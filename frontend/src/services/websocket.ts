import { ref, onUnmounted } from 'vue'

type EventPayload = Record<string, any>

function wsBaseUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}`
}

function makeSocket(getUrl: () => string, onMessage: (data: EventPayload) => void) {
  let ws: WebSocket | null = null
  let stopped = false
  let retryDelay = 1000
  let pingInterval: ReturnType<typeof setInterval> | null = null

  const connected = ref(false)

  function clearPing() {
    if (pingInterval !== null) {
      clearInterval(pingInterval)
      pingInterval = null
    }
  }

  function attemptConnect() {
    if (stopped) return
    try {
      ws = new WebSocket(getUrl())
    } catch {
      schedule()
      return
    }

    ws.onopen = () => {
      connected.value = true
      retryDelay = 1000
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }))
        }
      }, 25_000)
    }

    ws.onmessage = ({ data }) => {
      try {
        const parsed = JSON.parse(data as string)
        if (parsed.event !== 'pong') onMessage(parsed)
      } catch { /* ignore malformed frames */ }
    }

    ws.onerror = () => ws?.close()

    ws.onclose = () => {
      connected.value = false
      clearPing()
      if (!stopped) schedule()
    }
  }

  function schedule() {
    setTimeout(() => {
      retryDelay = Math.min(retryDelay * 2, 30_000)
      attemptConnect()
    }, retryDelay)
  }

  function send(payload: Record<string, any>) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
    }
  }

  function stop() {
    stopped = true
    clearPing()
    ws?.close()
  }

  return { connected, connect: attemptConnect, send, stop }
}

// ─── Teacher ─────────────────────────────────────────────────────────────────

export interface TeacherWSHandlers {
  onStudentJoined?: (e: { session_id: string; student_name: string; online_count?: number }) => void
  onStudentLeft?: (e: { session_id: string; student_name: string; online_count?: number }) => void
  onStudentAnswered?: (e: { session_id: string; question_index: string; is_correct: boolean | null }) => void
}

export function useTeacherWS(assignmentId: string, handlers: TeacherWSHandlers = {}) {
  const token = localStorage.getItem('access_token') ?? ''
  const socket = makeSocket(
    () => `${wsBaseUrl()}/ws/assignment/${assignmentId}?token=${encodeURIComponent(token)}`,
    (data) => {
      switch (data.event) {
        case 'student_joined':   handlers.onStudentJoined?.(data as any);   break
        case 'student_left':     handlers.onStudentLeft?.(data as any);     break
        case 'student_answered': handlers.onStudentAnswered?.(data as any); break
      }
    },
  )
  onUnmounted(socket.stop)
  return socket
}

// ─── Student ─────────────────────────────────────────────────────────────────

export interface StudentWSHandlers {
  onFinished?: () => void
  onNextQuestion?: (e: { question_index: number }) => void
  onTestStarted?: () => void
}

export function useStudentWS(sessionId: string, handlers: StudentWSHandlers = {}) {
  const socket = makeSocket(
    () => `${wsBaseUrl()}/ws/student/${sessionId}`,
    (data) => {
      switch (data.event) {
        case 'assignment_finished': handlers.onFinished?.();                  break
        case 'next_question':       handlers.onNextQuestion?.(data as any);  break
        case 'test_started':        handlers.onTestStarted?.();               break
      }
    },
  )
  onUnmounted(socket.stop)
  return socket
}
