import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAppStore } from '@/store/useAppStore'
import { MessageSquare, Plus } from 'lucide-react'

interface CenterPanelProps {
  children?: ReactNode
}

/**
 * CenterPanel - Presentational component for main content area
 * Design Pattern: Presentational Component
 */
export function CenterPanel({ children }: CenterPanelProps) {
  const { currentProject, conversations, setActiveConversationId, activeConversationId } = useAppStore()

  const handleNewConversation = () => {
    // TODO: Create new conversation
    console.log('New conversation clicked')
  }

  const handleConversationClick = (conversationId: string) => {
    setActiveConversationId(conversationId)
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            {currentProject?.name || 'GenAI Team'}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {currentProject?.description || 'Gen-related docs'}
          </p>
        </div>
        <Button onClick={handleNewConversation}>
          <Plus className="mr-2 h-4 w-4" />
          New conversation
        </Button>
      </header>

      {/* Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar */}
        <aside className="w-64 border-r border-border bg-card flex flex-col">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-foreground">Conversations</h2>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {conversations.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No conversations yet
                </div>
              ) : (
                conversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    onClick={() => handleConversationClick(conversation.id)}
                    className={`w-full text-left px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                      activeConversationId === conversation.id
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50 text-foreground'
                    }`}
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span className="truncate">
                      {conversation.title || `Chat #${conversation.id.slice(-4)}`}
                    </span>
                  </button>
                ))
              )}
            </div>
          </ScrollArea>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children || (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a conversation or start a new one</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

