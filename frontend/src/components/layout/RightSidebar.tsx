import { useState, useRef } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAppStore } from '@/store/useAppStore'
import { Upload, FileText, Trash2, Link as LinkIcon } from 'lucide-react'
import { useFileUpload } from '@/hooks/useFileUpload'

/**
 * RightSidebar - Knowledge Base component
 * Design Pattern: Container Component with Custom Hook
 */
export function RightSidebar() {
  const { sources, removeSource } = useAppStore()
  const { handleFileUpload, isUploading } = useFileUpload()
  const [urlInput, setUrlInput] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(Array.from(files))
    }
  }

  const handleUrlSubmit = () => {
    if (urlInput.trim()) {
      // TODO: Handle URL ingestion
      console.log('URL submitted:', urlInput)
      setUrlInput('')
    }
  }

  return (
    <aside className="w-80 border-l border-border bg-card flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Knowledge Base</h2>
      </div>

      <Tabs defaultValue="documents" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-4 mt-4">
          <TabsTrigger value="documents" className="flex-1">Documents</TabsTrigger>
          <TabsTrigger value="settings" className="flex-1">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="flex-1 flex flex-col overflow-hidden mt-4 px-4">
          {/* Add Sources Section */}
          <div className="space-y-4 mb-4">
            <div>
              <h3 className="text-sm font-medium text-foreground mb-3">Add Sources</h3>
              
              {/* File Upload Area */}
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
                <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-foreground mb-1">
                  Drop files or click to upload
                </p>
                <p className="text-xs text-muted-foreground">
                  PDF, DOCX, CSV - Max 50MB
                </p>
                {isUploading && (
                  <p className="text-xs text-primary mt-2">Uploading...</p>
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
                  />
                  <Button 
                    size="icon" 
                    onClick={handleUrlSubmit}
                    disabled={!urlInput.trim()}
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
              {sources.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No sources added yet
                </div>
              ) : (
                <div className="space-y-2">
                  {sources.map((source) => (
                    <div
                      key={source.id}
                      className="flex items-center justify-between p-3 rounded-md border border-border hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground truncate">
                            {source.filename}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {source.file_type} • {Math.round(source.file_size / 1024)}KB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 flex-shrink-0"
                        onClick={() => removeSource(source.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </TabsContent>

        <TabsContent value="settings" className="flex-1 overflow-auto mt-4 px-4">
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-foreground">Settings</h3>
            <p className="text-sm text-muted-foreground">
              Settings panel coming soon...
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </aside>
  )
}

