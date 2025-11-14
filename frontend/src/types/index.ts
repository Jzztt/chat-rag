// API Types
export interface ChatRequest {
  question: string
  conversation_id?: string
  project_id: string
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  conversation_id: string
}

export interface Source {
  id: string
  filename: string
  filepath: string
  file_type: string
  file_size: number
  indexed_at: string
  chunk_count: number
  page_count?: number
}

export interface Conversation {
  id: string
  project_id: string
  title: string
  messages: Message[]
  created_at: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: string
}

export interface Project {
  id: string
  name: string
  description: string
  created_at: string
  chroma_db_path: string
}

export interface UploadResponse {
  file_ids: string[]
  status: 'processing' | 'completed' | 'error'
}

