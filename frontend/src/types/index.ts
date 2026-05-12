export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface SourceMeta {
  name: string
  type: 'file' | 'url' | 'text'
  size?: number
  language?: string
  content?: string | null
  fetch_error?: boolean
}

export interface Lesson {
  id: string
  teacher_id: string
  title: string
  language: string
  source_type: 'url' | 'file' | 'text'
  source_content?: string
  cluster_data?: ClusterData
  sources_metadata?: SourceMeta[]
  created_at: string
  updated_at: string
}

export interface ClusterData {
  main_topic: string
  subtopics: string[]
  key_concepts: string[]
  difficulty_estimate: 'beginner' | 'intermediate' | 'advanced'
  suggested_question_count: number
}

export type AssignmentType = 'test' | 'battle' | 'analysis' | 'cards' | 'retelling'
export type AssignmentStatus = 'draft' | 'active' | 'finished' | 'archived'

export interface Assignment {
  id: string
  lesson_id: string
  assignment_type: AssignmentType
  status: AssignmentStatus
  questions_data?: any
  settings_data?: any
  session_token?: string
  session_expires_at?: string
  question_count: number
  timer_seconds: number
  show_results: boolean
  created_at: string
}

export interface Question {
  level: 'easy' | 'medium' | 'hard'
  question: string
  answers: { text: string; correct: boolean }[]
  explanation: string
}

export interface FlashCard {
  term: string
  definition: string
}

export interface StudentSession {
  id: string
  assignment_id: string
  student_name: string
  joined_at: string
}

export interface StudentResponse {
  id: string
  student_session_id: string
  question_index: string
  question_difficulty?: string
  answer_data: any
  is_correct?: boolean
  teacher_grade?: string
  answered_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface AssignmentHistoryItem {
  id: string
  lesson_id: string
  lesson_title: string
  assignment_type: AssignmentType
  status: AssignmentStatus
  question_count: number
  student_count: number
  response_count: number
  created_at: string
}

export interface TeacherStats {
  total_lessons: number
  total_assignments: number
  total_student_sessions: number
  total_responses: number
}
