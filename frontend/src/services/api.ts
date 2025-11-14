import axios from 'axios'
import type { 
  ChatRequest, 
  ChatResponse, 
  Source, 
  Conversation, 
  Project,
  UploadResponse 
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Chat API
export const chatApi = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', data)
    return response.data
  },

  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await api.get<Conversation>(`/conversations/${conversationId}`)
    return response.data
  },
}

// File Management API
export const fileApi = {
  uploadFiles: async (files: File[]): Promise<UploadResponse> => {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    const response = await api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getSources: async (): Promise<Source[]> => {
    const response = await api.get<{ sources: Source[] }>('/sources')
    return response.data.sources
  },

  deleteSource: async (sourceId: string): Promise<void> => {
    await api.delete(`/sources/${sourceId}`)
  },
}

// Project API
export const projectApi = {
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get<{ projects: Project[] }>('/projects')
    return response.data.projects
  },

  createProject: async (data: { name: string; description?: string }): Promise<Project> => {
    const response = await api.post<Project>('/projects', data)
    return response.data
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${projectId}`)
    return response.data
  },

  updateProject: async (projectId: string, data: Partial<Project>): Promise<Project> => {
    const response = await api.put<Project>(`/projects/${projectId}`, data)
    return response.data
  },

  deleteProject: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`)
  },
}

export default api

