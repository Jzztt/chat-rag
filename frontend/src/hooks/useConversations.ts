import { useEffect, useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { chatApi } from '@/services/api'
import type { Conversation } from '@/types'

/**
 * Hook to fetch and manage conversations
 */
export function useConversations() {
  const { conversations, setConversations, activeConversationId, setActiveConversationId } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setIsLoading(true)
        const fetchedConversations = await chatApi.getConversations()
        setConversations(fetchedConversations)
      } catch (error) {
        console.error('Failed to fetch conversations:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchConversations()
  }, [setConversations])

  const createConversation = async (title: string = 'New Conversation'): Promise<Conversation> => {
    try {
      const newConversation = await chatApi.createConversation(title)
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
      
      if (activeConversationId === conversationId) {
        setActiveConversationId(updatedConversations.length > 0 ? updatedConversations[0].id : null)
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
    try {
      setIsLoading(true)
      const fetchedConversations = await chatApi.getConversations()
      setConversations(fetchedConversations)
    } catch (error) {
      console.error('Failed to refresh conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    conversations,
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

