import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { chatApi } from '@/services/api'
import type { ChatResponse } from '@/types'

/**
 * Hook to handle chat messages with streaming support
 */
export function useChat(conversationId: string | null) {
  const { conversations, setConversations, addConversation, setActiveConversationId } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingText, setStreamingText] = useState<string>('')
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null)

  const sendMessage = async (question: string) => {
    setIsLoading(true)
    setError(null)
    setStreamingText('')

    try {
      // Use streaming API
      let finalResponse: ChatResponse | null = null

      await chatApi.sendMessage(
        {
          question,
          conversation_id: conversationId || undefined,
        },
        // onChunk - update streaming text
        (chunk: string) => {
          setStreamingText(prev => prev + chunk)
        },
        // onDone - final response
        async (response: ChatResponse) => {
          finalResponse = response
          setLastResponse(response) // Store response for debug info
          setStreamingText('') // Clear streaming text

          // Load conversation from API to get updated messages
          const conversation = await chatApi.getConversation(response.conversation_id)
          
          // Update messages with debug info from response
          if (conversation.messages && conversation.messages.length > 0) {
            const lastMessage = conversation.messages[conversation.messages.length - 1]
            if (lastMessage.role === 'assistant') {
              lastMessage.used_rag = response.used_rag
              lastMessage.hops = response.hops
              lastMessage.timing = response.timing
              lastMessage.cache_hit = response.cache_hit
              lastMessage.cache_source = response.cache_source
              lastMessage.cache_similarity = response.cache_similarity
            }
          }
          
          // Update or add conversation in store
          const existingIndex = conversations.findIndex(c => c.id === conversation.id)
          if (existingIndex >= 0) {
            setConversations(
              conversations.map(c => c.id === conversation.id ? conversation : c)
            )
          } else {
            addConversation(conversation)
          }

          // Set as active conversation
          setActiveConversationId(conversation.id)
        },
        // onError
        (errorMsg: string) => {
          setError(errorMsg)
          console.error('Streaming error:', errorMsg)
        }
      )

      return finalResponse
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send message'
      setError(errorMessage)
      console.error('Failed to send message:', err)
      throw err
    } finally {
      setIsLoading(false)
      setStreamingText('')
    }
  }

  return {
    sendMessage,
    isLoading,
    error,
    streamingText,
    lastResponse,
  }
}

