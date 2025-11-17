import { useState, useRef, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { useAppStore } from '@/store/useAppStore'
import { useSources } from '@/hooks/useSources'
import { useFileUpload } from '@/hooks/useFileUpload'
import { Upload, FileText, Trash2, Link as LinkIcon, Loader2, Search, BarChart3, RefreshCw, Info } from 'lucide-react'

interface RightSidebarProps {
  mobile?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

/**
 * RightSidebar - Responsive Knowledge Base component with API integration
 * Design Pattern: Container Component with Custom Hook and Responsive Design
 */
export function RightSidebar({ mobile = false, open, onOpenChange }: RightSidebarProps) {
  const { currentProject, activeConversationId } = useAppStore()
  const { 
    sources, 
    isLoading, 
    stats,
    deleteSource, 
    refreshSources,
    fetchStats,
    getFileDetails,
    searchInFile,
    rebuildIndex
  } = useSources(currentProject?.id || null, activeConversationId || null)
  const { handleFileUpload, isUploading } = useFileUpload()
  const [urlInput, setUrlInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResult, setSearchResult] = useState<any>(null)
  const [isRebuilding, setIsRebuilding] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sourceToDelete, setSourceToDelete] = useState<{ id: string; filename: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch stats when project changes
  useEffect(() => {
    if (currentProject?.id) {
      fetchStats()
    }
  }, [currentProject?.id])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (!currentProject) return
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files).then(() => {
        refreshSources()
      })
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0 && currentProject) {
      handleFileUpload(Array.from(files)).then(() => {
        refreshSources()
      })
    }
  }

  const handleUrlSubmit = () => {
    if (urlInput.trim()) {
      // TODO: Handle URL ingestion
      console.log('URL submitted:', urlInput)
      setUrlInput('')
    }
  }

  const handleDeleteSource = (sourceId: string, filename: string) => {
    setSourceToDelete({ id: sourceId, filename })
    setDeleteDialogOpen(true)
  }

  const confirmDeleteSource = async () => {
    if (!sourceToDelete) return
    
    setIsDeleting(true)
    try {
      await deleteSource(sourceToDelete.id)
      setDeleteDialogOpen(false)
      setSourceToDelete(null)
      // Refresh sources after deletion
      await refreshSources()
    } catch (error) {
      console.error('Failed to delete source:', error)
      alert('Failed to delete source. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleSearchInFile = async (sourceId: string, filename: string) => {
    if (!searchQuery.trim()) return
    
    setIsSearching(true)
    try {
      const result = await searchInFile(sourceId, {
        question: searchQuery,
        filename: filename
      })
      setSearchResult(result)
    } catch (error) {
      console.error('Failed to search in file:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleRebuildIndex = async (force: boolean = false) => {
    setIsRebuilding(true)
    try {
      await rebuildIndex(force)
      alert('Index rebuilt successfully!')
    } catch (error) {
      console.error('Failed to rebuild index:', error)
      alert('Failed to rebuild index')
    } finally {
      setIsRebuilding(false)
    }
  }

  const sidebarContent = (
    <>
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Knowledge Base</h2>
      </div>

      <Tabs defaultValue="documents" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-4 mt-4">
          <TabsTrigger value="documents" className="flex-1 text-xs sm:text-sm">Documents</TabsTrigger>
          <TabsTrigger value="settings" className="flex-1 text-xs sm:text-sm">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="flex-1 flex flex-col overflow-hidden mt-4 px-4">
          {!currentProject ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-sm text-muted-foreground text-center">
                Please select a project to manage sources
              </p>
            </div>
          ) : (
            <>
          {/* Add Sources Section */}
          <div className="space-y-4 mb-4">
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Add Sources</h3>
              
              {/* File Upload Area */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-border rounded-lg p-6 sm:p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.csv,.txt"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                    <Upload className="h-6 w-6 sm:h-8 sm:w-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-foreground mb-1">
                  Drop files or click to upload
                </p>
                <p className="text-xs text-muted-foreground">
                  PDF, DOCX, CSV - Max 50MB
                </p>
                {isUploading && (
                      <div className="flex items-center justify-center gap-2 mt-2">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        <p className="text-xs text-primary">Uploading...</p>
                      </div>
                )}
              </div>

              {/* OR Separator */}
              <div className="relative my-4">
                <Separator />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="bg-card px-2 text-xs text-muted-foreground">OR</span>
                </div>
              </div>

              {/* URL Input */}
              <div className="space-y-2">
                <label className="text-sm text-foreground">Paste website URL</label>
                <div className="flex gap-2">
                  <Input
                    type="url"
                    placeholder="https://example.com"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
                        className="text-sm"
                  />
                  <Button 
                    size="icon" 
                    onClick={handleUrlSubmit}
                    disabled={!urlInput.trim()}
                        className="flex-shrink-0"
                  >
                    <LinkIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <Separator className="my-4" />

          {/* Sources List */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <h3 className="text-sm font-medium text-foreground mb-3">Sources</h3>
            <ScrollArea className="flex-1">
                  {isLoading ? (
                    <div className="text-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">Loading sources...</p>
                    </div>
                  ) : sources.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No sources added yet
                </div>
              ) : (
                <div className="space-y-2">
                  {sources.map((source) => (
                    <div
                      key={source.id}
                      className="group p-3 rounded-md border border-border hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground truncate">
                            {source.filename}
                          </p>
                          <p className="text-xs text-muted-foreground">
                              {source.file_type} • {source.file_size_mb ? `${source.file_size_mb.toFixed(2)}MB` : `${Math.round(source.file_size / 1024)}KB`}
                              {source.chunk_count ? ` • ${source.chunk_count} chunks` : ''}
                          </p>
                        </div>
                      </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Dialog>
                            <DialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                                className="h-7 w-7"
                                onClick={() => {
                                  setSearchQuery('')
                                  setSearchResult(null)
                                }}
                              >
                                <Search className="h-3.5 w-3.5" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-[500px]">
                              <DialogHeader>
                                <DialogTitle>Search in {source.filename}</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4">
                                <div>
                                  <Input
                                    placeholder="Enter your question..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter' && searchQuery.trim()) {
                                        handleSearchInFile(source.id, source.filename)
                                      }
                                    }}
                                  />
                                </div>
                                <Button
                                  onClick={() => handleSearchInFile(source.id, source.filename)}
                                  disabled={!searchQuery.trim() || isSearching}
                                  className="w-full"
                                >
                                  {isSearching ? (
                                    <>
                                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                      Searching...
                                    </>
                                  ) : (
                                    <>
                                      <Search className="h-4 w-4 mr-2" />
                                      Search
                                    </>
                                  )}
                                </Button>
                                {searchResult && (
                                  <div className="space-y-2 max-h-[400px] overflow-auto">
                                    <div className="p-3 bg-muted rounded-md">
                                      <p className="text-sm">{searchResult.answer}</p>
                                    </div>
                                    {searchResult.sources && searchResult.sources.length > 0 && (
                                      <div className="space-y-2">
                                        <p className="text-xs font-medium text-muted-foreground">Sources:</p>
                                        {searchResult.sources.map((src: any, idx: number) => (
                                          <div key={idx} className="p-2 bg-muted/50 rounded text-xs">
                                            <p className="font-medium">{src.citation}</p>
                                            <p className="text-muted-foreground mt-1">{src.content.substring(0, 200)}...</p>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </DialogContent>
                          </Dialog>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => handleDeleteSource(source.id, source.filename)}
                            title="Delete source"
                      >
                            <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
            </>
          )}
        </TabsContent>

        {/* Delete Source Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Source</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{sourceToDelete?.filename}"? 
                This action cannot be undone. The file will be removed from this conversation.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeleteSource}
                disabled={isDeleting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <TabsContent value="settings" className="flex-1 overflow-auto mt-4 px-4">
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-foreground">Settings</h3>
            
            {/* Stats Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-medium text-foreground flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Statistics
                </h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchStats()}
                  className="h-6 text-xs"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
              
              {stats ? (
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Files:</span>
                    <span className="text-foreground font-medium">{stats.total_files}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Size:</span>
                    <span className="text-foreground font-medium">{stats.total_size_mb.toFixed(2)} MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Chunks:</span>
                    <span className="text-foreground font-medium">{stats.total_chunks}</span>
                  </div>
                  {Object.keys(stats.by_type).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border">
                      <p className="text-muted-foreground mb-1">By Type:</p>
                      {Object.entries(stats.by_type).map(([type, count]) => (
                        <div key={type} className="flex justify-between">
                          <span className="text-muted-foreground">{type}:</span>
                          <span className="text-foreground">{count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No statistics available</p>
              )}
            </div>

            <Separator />

            {/* Rebuild Index Section */}
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-foreground">Index Management</h4>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRebuildIndex(false)}
                  disabled={isRebuilding}
                  className="w-full text-xs"
                >
                  {isRebuilding ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                      Rebuilding...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-3 w-3 mr-2" />
                      Rebuild Index
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRebuildIndex(true)}
                  disabled={isRebuilding}
                  className="w-full text-xs"
                >
                  Force Rebuild
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </>
  )

  if (mobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-80 sm:w-96 p-0 flex flex-col">
          <SheetHeader className="sr-only">
            <SheetTitle>Knowledge Base</SheetTitle>
          </SheetHeader>
          {sidebarContent}
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <aside className="w-80 border-l border-border bg-card flex flex-col hidden lg:flex">
      {sidebarContent}
    </aside>
  )
}
