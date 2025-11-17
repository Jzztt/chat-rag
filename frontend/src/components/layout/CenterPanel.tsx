import { ReactNode, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { useAppStore } from '@/store/useAppStore'
import { useConversations } from '@/hooks/useConversations'
import { MessageSquare, Plus, Menu, Loader2, Trash2 } from 'lucide-react'

interface CenterPanelProps {
  children?: ReactNode
  mobile?: boolean
  onToggleRightSidebar?: () => void
}

/**
 * CenterPanel - Responsive main content area component with API integration
 * Design Pattern: Presentational Component with Responsive Design
 */
export function CenterPanel({ children, mobile = false, onToggleRightSidebar }: CenterPanelProps) {
  const { currentProject, setActiveConversationId, activeConversationId } = useAppStore()
  const { conversations, createConversation, deleteConversation, isLoading } = useConversations(currentProject?.id || null)
  const [conversationsOpen, setConversationsOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleNewConversation = async () => {
    try {
      const newConv = await createConversation('New Conversation')
      setActiveConversationId(newConv.id)
      if (mobile) {
        setConversationsOpen(false)
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleConversationClick = (conversationId: string, e?: React.MouseEvent) => {
    // Prevent click if clicking on delete button
    if (e && (e.target as HTMLElement).closest('button[data-delete]')) {
      return;
    }
    
    setActiveConversationId(conversationId)
    if (mobile) {
      setConversationsOpen(false)
    }
  }

  const handleDeleteClick = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    setConversationToDelete(conversationId);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!conversationToDelete) return;
    
    setIsDeleting(true);
    try {
      await deleteConversation(conversationToDelete);
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const conversationsContent = (
    <>
          <div className="px-4 py-3 border-b border-border">
            <h2 className="text-sm font-semibold text-foreground">Conversations</h2>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
          {isLoading ? (
            <div className="px-4 py-8 text-center">
              <Loader2 className="h-4 w-4 animate-spin mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Loading...</p>
            </div>
          ) : conversations.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No conversations yet
                </div>
              ) : (
                conversations.map((conversation) => (
              <div
                key={conversation.id}
                className="group relative"
              >
                  <button
                  onClick={(e) => handleConversationClick(conversation.id, e)}
                    className={`w-full text-left px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                      activeConversationId === conversation.id
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50 text-foreground'
                    }`}
                  >
                  <MessageSquare className="h-4 w-4 flex-shrink-0" />
                  <span className="truncate flex-1">
                      {conversation.title || `Chat #${conversation.id.slice(-4)}`}
                    </span>
                  </button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => handleDeleteClick(e, conversation.id)}
                  data-delete
                >
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </div>
                ))
              )}
            </div>
          </ScrollArea>
    </>
  )

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-border bg-card px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {mobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setConversationsOpen(true)}
                className="md:hidden flex-shrink-0"
              >
                <Menu className="h-5 w-5" />
              </Button>
            )}
            <div className="min-w-0 flex-1">
              <h1 className="text-lg sm:text-2xl font-semibold text-foreground truncate">
                {currentProject?.name || 'Select a project'}
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-1 truncate">
                {currentProject?.description || ''}
              </p>
            </div>
          </div>
        </div>
        <Button 
          onClick={handleNewConversation}
          size={mobile ? "sm" : "default"}
          className="flex-shrink-0"
          disabled={!currentProject}
        >
          <Plus className="mr-2 h-4 w-4" />
          <span className="hidden sm:inline">New conversation</span>
          <span className="sm:hidden">New</span>
        </Button>
      </header>

      {/* Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar - Desktop always visible, Mobile as drawer */}
        {!mobile ? (
          <aside className="w-64 border-r border-border bg-card flex flex-col hidden md:flex">
            {conversationsContent}
        </aside>
        ) : (
          <Sheet open={conversationsOpen} onOpenChange={setConversationsOpen}>
            <SheetContent side="left" className="w-64 p-0 flex flex-col">
              <SheetHeader className="sr-only">
                <SheetTitle>Conversations</SheetTitle>
              </SheetHeader>
              {conversationsContent}
            </SheetContent>
          </Sheet>
        )}

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {children || (
            <div className="flex-1 flex items-center justify-center text-muted-foreground p-4">
              <div className="text-center max-w-md">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-sm sm:text-base">Select a conversation or start a new one</p>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Delete Conversation Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this conversation? This action cannot be undone. 
              All messages in this conversation will be permanently deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setConversationToDelete(null);
              }}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
