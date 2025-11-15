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

export const useAppStore = create<AppState>((set) => ({
  // Projects
  currentProject: null,
  projects: [],
  setCurrentProject: (project) => set({ currentProject: project }),
  setProjects: (projects) => set({ projects }),

  // Conversations
  conversations: [],
  activeConversationId: null,
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

