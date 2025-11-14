import { create } from 'zustand'
import type { Project, Conversation, Source } from '@/types'

interface AppState {
  // Projects
  currentProject: Project | null
  projects: Project[]
  setCurrentProject: (project: Project | null) => void
  setProjects: (projects: Project[]) => void

  // Conversations
  conversations: Conversation[]
  activeConversationId: string | null
  setConversations: (conversations: Conversation[]) => void
  setActiveConversationId: (id: string | null) => void
  addConversation: (conversation: Conversation) => void

  // Sources
  sources: Source[]
  setSources: (sources: Source[]) => void
  addSource: (source: Source) => void
  removeSource: (sourceId: string) => void

  // UI State
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

// Mock data for development
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'GenAI Team',
    description: 'Gen-related docs',
    created_at: new Date().toISOString(),
    chroma_db_path: './chroma_db',
  },
]

const mockConversations: Conversation[] = [
  {
    id: '6235',
    project_id: '1',
    title: 'Chat #6235',
    messages: [],
    created_at: new Date().toISOString(),
  },
]

export const useAppStore = create<AppState>((set) => ({
  // Projects
  currentProject: mockProjects[0] || null,
  projects: mockProjects,
  setCurrentProject: (project) => set({ currentProject: project }),
  setProjects: (projects) => set({ projects }),

  // Conversations
  conversations: mockConversations,
  activeConversationId: mockConversations[0]?.id || null,
  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [...state.conversations, conversation],
    })),

  // Sources
  sources: [],
  setSources: (sources) => set({ sources }),
  addSource: (source) =>
    set((state) => ({
      sources: [...state.sources, source],
    })),
  removeSource: (sourceId) =>
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== sourceId),
    })),

  // UI State
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}))

