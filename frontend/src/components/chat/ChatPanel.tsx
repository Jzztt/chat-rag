import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAppStore } from '@/store/useAppStore'
import { useChat } from '@/hooks/useChat'
import { useConversations } from '@/hooks/useConversations'
import { Send, Loader2 } from 'lucide-react'
import { MessageBubble } from './MessageBubble'

/**
 * ChatPanel - Responsive presentational component for chat interface
 */
export function ChatPanel() {
  const { activeConversationId, conversations } = useAppStore()
  const [input, setInput] = useState('')
  const { sendMessage, isLoading, error, streamingText, lastResponse } = useChat(
    activeConversationId
  )
  const { refreshConversations } = useConversations()
  
  const activeConversation = conversations.find(
    c => c.id === activeConversationId
  )

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const question = input.trim()
    setInput('')
    
    try {
      await sendMessage(question)
      // Refresh conversations to get updated conversation with new messages
      await refreshConversations()
    } catch (err) {
      console.error('Error sending message:', err)
    }
  }

  if (!activeConversation) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground p-4">
        <div className="text-center max-w-md">
          <p className="text-sm sm:text-base">Select a conversation or start a new one</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full min-w-0">
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 text-sm">
          {error}
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4 sm:p-6 max-w-3xl mx-auto w-full">
          {activeConversation.messages.length === 0 ? (
            <div className="text-center py-8 sm:py-12 text-muted-foreground">
              <p className="text-sm sm:text-base">No messages yet. Start the conversation!</p>
            </div>
          ) : (
            <>
              {activeConversation.messages.map((message, index) => (
                <MessageBubble 
                  key={message.timestamp || `${message.role}-${index}`} 
                  message={message} 
                />
              ))}
              {isLoading && streamingText && (
                <MessageBubble 
                  message={{
                    role: 'assistant',
                    content: streamingText,
                    timestamp: new Date().toISOString(),
                    used_rag: lastResponse?.used_rag,
                    hops: lastResponse?.hops,
                    timing: lastResponse?.timing,
                  }} 
                />
              )}
            </>
          )}
          {isLoading && !streamingText && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t border-border p-3 sm:p-4 bg-card">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && !isLoading && handleSend()}
            placeholder="Type your message..."
            className="flex-1 text-sm sm:text-base"
            disabled={isLoading}
          />
          <Button 
            onClick={handleSend} 
            disabled={!input.trim() || isLoading}
            size="icon"
            className="flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
            <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
