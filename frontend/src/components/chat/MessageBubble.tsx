import { Card, CardContent } from '@/components/ui/card'
import type { Message } from '@/types'
import { User, Bot, Database, RefreshCw } from 'lucide-react'

interface MessageBubbleProps {
  message: Message
}

/**
 * MessageBubble - Responsive presentational component for individual message
 * Design Pattern: Presentational Component with Responsive Design
 */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-2 sm:gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
      }`}>
        {isUser ? <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" /> : <Bot className="h-3.5 w-3.5 sm:h-4 sm:w-4" />}
      </div>
      
      <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1 min-w-0`}>
        <Card className={`max-w-[85%] sm:max-w-[80%] ${
          isUser 
            ? 'bg-primary text-primary-foreground' 
            : 'bg-muted'
        }`}>
          <CardContent className="p-2.5 sm:p-3">
            <p className="text-xs sm:text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </CardContent>
        </Card>
        
        {/* Sources and Debug Info */}
        <div className="flex items-center gap-2 mt-1 px-1 flex-wrap">
          {message.sources && message.sources.length > 0 && (
            <div className="text-xs text-muted-foreground">
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </div>
          )}
          
          {/* Debug Info - Only show for assistant messages */}
          {!isUser && (message.used_rag !== undefined || message.hops !== undefined) && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              {message.used_rag !== undefined && (
                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-muted/50" title={message.used_rag ? 'Used RAG (Retrieval Augmented Generation)' : 'Direct answer (no RAG)'}>
                  <Database className="h-3 w-3" />
                  <span className="hidden sm:inline">{message.used_rag ? 'RAG' : 'Direct'}</span>
                </div>
              )}
              {message.hops !== undefined && message.hops > 1 && (
                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-muted/50" title={`Multi-hop search: ${message.hops} hops`}>
                  <RefreshCw className="h-3 w-3" />
                  <span className="hidden sm:inline">{message.hops}x</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
