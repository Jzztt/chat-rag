import { Card, CardContent } from '@/components/ui/card'
import type { Message } from '@/types'
import { User, Bot } from 'lucide-react'

interface MessageBubbleProps {
  message: Message
}

/**
 * MessageBubble - Presentational component for individual message
 * Design Pattern: Presentational Component
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
      }`}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      
      <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <Card className={`max-w-[80%] ${
          isUser 
            ? 'bg-primary text-primary-foreground' 
            : 'bg-muted'
        }`}>
          <CardContent className="p-3">
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </CardContent>
        </Card>
        
        {message.sources && message.sources.length > 0 && (
          <div className="text-xs text-muted-foreground mt-1">
            {message.sources.length} source(s)
          </div>
        )}
      </div>
    </div>
  )
}

