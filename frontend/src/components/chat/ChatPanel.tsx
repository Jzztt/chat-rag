import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAppStore } from '@/store/useAppStore'
import { Send } from 'lucide-react'
import { MessageBubble } from './MessageBubble'

/**
 * ChatPanel - Presentational component for chat interface
 * Design Pattern: Presentational Component
 */
export function ChatPanel() {
  const { activeConversationId, conversations } = useAppStore()
  const [input, setInput] = useState('')
  
  const activeConversation = conversations.find(
    c => c.id === activeConversationId
  )

  const handleSend = () => {
    if (!input.trim()) return
    
    // TODO: Send message to API
    console.log('Sending message:', input)
    setInput('')
  }

  if (!activeConversation) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <p>Select a conversation or start a new one</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-4 max-w-3xl mx-auto">
          {activeConversation.messages.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            activeConversation.messages.map((message) => (
              <MessageBubble key={message.timestamp} message={message} />
            ))
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4 bg-card">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Type your message..."
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={!input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

