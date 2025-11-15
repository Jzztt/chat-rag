// API Types
export interface ChatRequest {
  question: string
  conversation_id?: string
  project_id: string
  enable_llm_decision?: boolean  // LLM decides if RAG is needed
  enable_multi_hop?: boolean  // Enable multi-hop reasoning
  max_hops?: number  // Maximum number of search hops
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  conversation_id: string
  confidence?: 'high' | 'medium' | 'low'
  eval_scores?: {
    avg_similarity?: number
    max_similarity?: number
    min_similarity?: number
    relevant_count?: number
  }
  used_rag?: boolean  // Whether RAG was used
  hops?: number  // Number of search hops performed
}

export interface Source {
  id: string
  project_id: string
  conversation_id?: string | null
  filename: string
  filepath: string
  file_type: string
  file_size: number
  file_size_mb?: number
  indexed_at: string
  chunk_count: number
  page_count?: number
  file_hash?: string
  chunk_id?: string
  citation?: string
  similarity?: number
  content?: string
  content_preview?: string
}

export interface SourceStats {
  total_files: number
  total_size_mb: number
  total_chunks: number
  by_type: Record<string, number>
}

export interface FileDetails {
  id: string
  filename: string
  filepath: string
  file_type: string
  file_size: number
  file_size_mb: number
  file_hash: string
  chunk_count: number
  page_count?: number
  indexed_at: string
  author?: string
  title?: string
}

export interface SearchInFileRequest {
  question: string
  filename: string
}

export interface SearchInFileResponse {
  question: string
  answer: string
  sources: Array<{
    citation: string
    filename: string
    content: string
  }>
  file: string
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
  used_rag?: boolean  // Whether RAG was used for this message
  hops?: number  // Number of search hops performed
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

