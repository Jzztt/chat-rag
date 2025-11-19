import { create } from 'zustand'
import type { Conversation, Source } from '@/types'

interface AppState {
  conversations: Conversation[]
  activeConversationId: string | null
  setConversations: (conversations: Conversation[]) => void
  setActiveConversationId: (id: string | null) => void
  addConversation: (conversation: Conversation) => void

  sources: Source[]
  setSources: (sources: Source[]) => void
  removeSource: (sourceId: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  conversations: [],
  activeConversationId: null,
  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (id) => set({ activeConversationId: id }),
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [...state.conversations, conversation],
    })),

  sources: [],
  setSources: (sources) => set({ sources }),
  removeSource: (sourceId) =>
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== sourceId),
    })),
}))

