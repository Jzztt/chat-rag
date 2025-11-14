export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const SUPPORTED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'text/plain',
  'text/csv',
]

export const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

export const CHUNK_SIZE_OPTIONS = [100, 250, 500, 1000]
export const CHUNK_OVERLAP_OPTIONS = [0, 25, 50, 100]

