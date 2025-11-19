import axios from 'axios'
import type { 
  ChatRequest, 
  ChatResponse, 
  Source, 
  Conversation, 
  UploadResponse,
  SourceStats,
  FileDetails,
  SearchInFileRequest,
  SearchInFileResponse
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Chat API - Streaming only
export const chatApi = {
  sendMessage: async (
    data: ChatRequest,
    onChunk: (chunk: string) => void,
    onDone: (response: ChatResponse) => void,
    onError: (error: string) => void
  ): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.slice(6))
              
              if (jsonData.type === 'chunk') {
                onChunk(jsonData.content || '')
              } else if (jsonData.type === 'done') {
                onDone({
                  answer: jsonData.answer || '',
                  sources: jsonData.sources || [],
                  conversation_id: jsonData.conversation_id || '',
                  confidence: jsonData.confidence || 'medium',
                  eval_scores: jsonData.eval_scores || {},
                  used_rag: jsonData.used_rag !== undefined ? jsonData.used_rag : true,
                  hops: jsonData.hops || 1,
                  timing: jsonData.timing || undefined
                })
                return
              } else if (jsonData.type === 'error') {
                onError(jsonData.error || 'Unknown error')
                return
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error: any) {
      onError(error.message || 'Failed to stream response')
    }
  },

  getConversations: async (): Promise<Conversation[]> => {
    const response = await api.get<{ conversations: Conversation[] }>('/conversations')
    return response.data.conversations
  },

  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await api.post<Conversation>('/conversations', {
      title: title || 'New Conversation'
    })
    return response.data
  },

  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get<Conversation>(`/conversations/${conversationId}`)
    return response.data
  },

  updateConversation: async (conversationId: string, title: string): Promise<Conversation> => {
    const response = await api.patch<Conversation>(`/conversations/${conversationId}`, { title })
    return response.data
  },

  deleteConversation: async (conversationId: string): Promise<void> => {
    await api.delete(`/conversations/${conversationId}`)
  },
}

// File Management API
export const fileApi = {
  uploadFiles: async (files: File[], conversationId?: string): Promise<UploadResponse> => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    const params = conversationId 
      ? `?conversation_id=${conversationId}`
      : ''
    
    const response = await api.post<UploadResponse>(`/upload${params}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getSources: async (conversationId?: string): Promise<Source[]> => {
    const params = conversationId
      ? `?conversation_id=${conversationId}`
      : ''
    const response = await api.get<{ sources: Source[] }>(`/sources${params}`)
    return response.data.sources
  },

  getSourceStats: async (): Promise<SourceStats> => {
    const response = await api.get<SourceStats>('/sources/stats')
    return response.data
  },

  getSourceDetails: async (sourceId: string): Promise<FileDetails> => {
    const response = await api.get<FileDetails>(`/sources/${sourceId}`)
    return response.data
  },

  searchInFile: async (
    sourceId: string,
    request: SearchInFileRequest
  ): Promise<SearchInFileResponse> => {
    const response = await api.post<SearchInFileResponse>(
      `/sources/${sourceId}/search`,
      request
    )
    return response.data
  },

  rebuildIndex: async (force: boolean = false): Promise<{ message: string; stats: SourceStats }> => {
    const response = await api.post<{ message: string; stats: SourceStats }>(
      `/sources/rebuild?force=${force}`
    )
    return response.data
  },

  deleteSource: async (sourceId: string, conversationId?: string): Promise<void> => {
    const params = conversationId
      ? `?conversation_id=${conversationId}`
      : ''
    await api.delete(`/sources/${sourceId}${params}`)
  },
}
export default api

