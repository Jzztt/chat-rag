import { useEffect, useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { chatApi } from '@/services/api'
import type { Conversation, Message } from '@/types'

/**
 * Hook to fetch and manage conversations
 */
export function useConversations(projectId: string | null) {
  const { conversations, setConversations, activeConversationId, setActiveConversationId } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!projectId) {
      setConversations([])
      return
    }

    const fetchConversations = async () => {
      try {
        setIsLoading(true)
        const fetchedConversations = await chatApi.getConversations(projectId)
        setConversations(fetchedConversations)
      } catch (error) {
        console.error('Failed to fetch conversations:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchConversations()
  }, [projectId, setConversations])

  const createConversation = async (title: string = 'New Conversation'): Promise<Conversation> => {
    if (!projectId) {
      throw new Error('No project selected')
    }

    try {
      const newConversation = await chatApi.createConversation(projectId, title)
      setConversations([...conversations, newConversation])
      setActiveConversationId(newConversation.id)
      return newConversation
    } catch (error) {
      console.error('Failed to create conversation:', error)
      throw error
    }
  }

  const deleteConversation = async (conversationId: string) => {
    try {
      await chatApi.deleteConversation(conversationId)
      const updatedConversations = conversations.filter(c => c.id !== conversationId)
      setConversations(updatedConversations)
      
      // If deleted conversation was active, set another one or null
      if (activeConversationId === conversationId) {
        const projectConversations = updatedConversations.filter(c => c.project_id === projectId)
        setActiveConversationId(projectConversations.length > 0 ? projectConversations[0].id : null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      throw error
    }
  }

  const updateConversation = async (conversationId: string, title: string): Promise<Conversation> => {
    try {
      const updatedConversation = await chatApi.updateConversation(conversationId, title)
      setConversations(
        conversations.map(c => c.id === conversationId ? updatedConversation : c)
      )
      return updatedConversation
    } catch (error) {
      console.error('Failed to update conversation:', error)
      throw error
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      setIsLoading(true)
      const conversation = await chatApi.getConversation(conversationId)
      
      // Update conversation in store
      setConversations(
        conversations.map(c => c.id === conversationId ? conversation : c)
      )
      
      return conversation
    } catch (error) {
      console.error('Failed to load conversation:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const refreshConversations = async () => {
    if (!projectId) return
    
    try {
      setIsLoading(true)
      const fetchedConversations = await chatApi.getConversations(projectId)
      setConversations(fetchedConversations)
    } catch (error) {
      console.error('Failed to refresh conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    conversations: conversations.filter(c => c.project_id === projectId),
    activeConversationId,
    isLoading,
    createConversation,
    updateConversation,
    deleteConversation,
    loadConversation,
    refreshConversations,
    setActiveConversationId,
  }
}

