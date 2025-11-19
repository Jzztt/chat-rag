import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { useSources } from '@/hooks/useSources'
import { useFileUpload } from '@/hooks/useFileUpload'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Upload, FileText, Trash2, Link as LinkIcon, Loader2, Search, BarChart3, RefreshCw, Info } from 'lucide-react'

export function KnowledgeBasePage() {
  const { activeConversationId } = useAppStore()
  const { 
    sources, 
    isLoading, 
    stats,
    deleteSource, 
    refreshSources,
    fetchStats,
    searchInFile,
    rebuildIndex
  } = useSources()
  const { handleFileUpload, isUploading } = useFileUpload()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [urlInput, setUrlInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResult, setSearchResult] = useState<any>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sourceToDelete, setSourceToDelete] = useState<{ id: string; filename: string } | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isRebuilding, setIsRebuilding] = useState(false)
  const [searchDialogOpen, setSearchDialogOpen] = useState(false)
  const [searchSource, setSearchSource] = useState<{ id: string; filename: string } | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files, activeConversationId || undefined).then(() => {
        refreshSources()
        fetchStats()
      })
    }
  }

  const openSearchDialog = (sourceId: string, filename: string) => {
    setSearchSource({ id: sourceId, filename })
    setSearchQuery('')
    setSearchResult(null)
    setSearchDialogOpen(true)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(Array.from(files), activeConversationId || undefined).then(() => {
        refreshSources()
        fetchStats()
      })
    }
  }

  const handleUrlSubmit = () => {
    if (urlInput.trim()) {
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
      await refreshSources()
      await fetchStats()
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
      await refreshSources()
      await fetchStats()
      alert('Index rebuilt successfully!')
    } catch (error) {
      console.error('Failed to rebuild index:', error)
      alert('Failed to rebuild index')
    } finally {
      setIsRebuilding(false)
    }
  }

  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="max-w-5xl mx-auto p-4 sm:p-8 space-y-8">
        <header className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground tracking-wide">GLOBAL KNOWLEDGE BASE</p>
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Knowledge Base</h1>
              <p className="text-sm text-muted-foreground max-w-2xl">
                Upload documents once and let every conversation in Poly Chat access them through a shared ChromaDB.
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => handleRebuildIndex(false)} disabled={isRebuilding}>
                {isRebuilding ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Rebuild Index
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleRebuildIndex(true)} disabled={isRebuilding}>
                Force Rebuild
              </Button>
            </div>
          </div>
        </header>

        <section className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Total Files</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_files ?? 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Total Size</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats ? `${stats.total_size_mb.toFixed(2)} MB` : '0 MB'}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground">Total Chunks</CardTitle>
              <Info className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_chunks ?? 0}</div>
            </CardContent>
          </Card>
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Add Sources</h2>
            <p className="text-sm text-muted-foreground">Files can optionally be linked to the active conversation, but they live in the shared knowledge base.</p>
          </div>
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.csv,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
            <p className="text-sm text-foreground mb-1">
              Drop files or click to upload
            </p>
            <p className="text-xs text-muted-foreground">
              PDF, DOCX, CSV - Max 50MB
            </p>
            {isUploading && (
              <div className="flex items-center justify-center gap-2 mt-2 text-primary text-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading...
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Input
              type="url"
              placeholder="Paste a website URL (coming soon)"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
            />
            <Button 
              size="icon" 
              onClick={handleUrlSubmit}
              disabled={!urlInput.trim()}
            >
              <LinkIcon className="h-4 w-4" />
            </Button>
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Sources</h2>
              <p className="text-sm text-muted-foreground">All documents across conversations</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => { refreshSources(); fetchStats() }}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <ScrollArea className="h-[500px] rounded-lg border border-border">
            <div className="divide-y divide-border">
              {isLoading ? (
                <div className="flex items-center justify-center py-10">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : sources.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground text-sm">
                  No sources added yet
                </div>
              ) : (
                sources.map((source) => (
                  <div key={source.id} className="p-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium text-foreground">{source.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          {source.file_type} • {source.file_size_mb ? `${source.file_size_mb.toFixed(2)}MB` : `${Math.round(source.file_size / 1024)}KB`}
                          {source.chunk_count ? ` • ${source.chunk_count} chunks` : ''}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openSearchDialog(source.id, source.filename)}
                        title="Search in file"
                      >
                        <Search className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteSource(source.id, source.filename)}
                        title="Delete source"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </section>

        <Dialog
          open={searchDialogOpen}
          onOpenChange={(open) => {
            setSearchDialogOpen(open)
            if (!open) {
              setSearchSource(null)
              setSearchQuery('')
              setSearchResult(null)
            }
          }}
        >
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Search in {searchSource?.filename}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Enter your question..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && searchQuery.trim() && searchSource) {
                    handleSearchInFile(searchSource.id, searchSource.filename)
                  }
                }}
              />
              <Button
                onClick={() => searchSource && handleSearchInFile(searchSource.id, searchSource.filename)}
                disabled={!searchQuery.trim() || isSearching || !searchSource}
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

        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Source</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{sourceToDelete?.filename}"? 
                The document will be removed from the shared knowledge base.
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
      </div>
    </div>
  )
}

