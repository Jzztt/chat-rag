import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useProjects } from '@/hooks/useProjects';
import { FolderKanban, Plus, Loader2, Trash2 } from 'lucide-react';
import { useState } from 'react';

interface LeftSidebarProps {
  mobile?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

/**
 * LeftSidebar - Responsive sidebar component with API integration
 * Design Pattern: Presentational Component with Responsive Design
 */
export function LeftSidebar({ mobile = false, open, onOpenChange }: LeftSidebarProps) {
  const { projects, currentProject, createProject, deleteProject, setCurrentProject } = useProjects();
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleNewProject = async () => {
    if (!newProjectName.trim()) return;
    
    setIsCreating(true);
    try {
      await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      setNewProjectName('');
      setNewProjectDesc('');
      setDialogOpen(false);
      if (mobile && onOpenChange) {
        onOpenChange(false);
      }
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleProjectClick = (projectId: string, e?: React.MouseEvent) => {
    // Prevent click if clicking on delete button
    if (e && (e.target as HTMLElement).closest('button[data-delete]')) {
      return;
    }
    
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      setCurrentProject(project);
      // Close sidebar on mobile after selection
      if (mobile && onOpenChange) {
        onOpenChange(false);
      }
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    setProjectToDelete(projectId);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!projectToDelete) return;
    
    setIsDeleting(true);
    try {
      await deleteProject(projectToDelete);
      setDeleteDialogOpen(false);
      setProjectToDelete(null);
    } catch (error) {
      console.error('Failed to delete project:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">POLY CHAT</h1>
      </div>

      {/* New Project Button */}
      <div className="p-4 border-b border-border">
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full">
          <Plus className="mr-2 h-4 w-4" />
          New project
        </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium">Project Name</label>
                <Input
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description (Optional)</label>
                <Input
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Enter project description"
                  className="mt-1"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleNewProject}
                disabled={!newProjectName.trim() || isCreating}
              >
                {isCreating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Delete Project Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this project? This action cannot be undone. 
              All conversations and sources in this project will be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setProjectToDelete(null);
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

      {/* Projects List */}
      <div className="flex-1 overflow-hidden">
        <div className="px-4 py-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Projects
          </h2>
        </div>
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1">
            {projects.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                No projects yet
              </div>
            ) : (
              projects.map((project) => (
                <div
                  key={project.id}
                  className="group relative"
                >
                  <button
                    onClick={(e) => handleProjectClick(project.id, e)}
                    className={`w-full text-left px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                      currentProject?.id === project.id
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50 text-foreground'
                    }`}
                  >
                    <FolderKanban className="h-4 w-4 flex-shrink-0" />
                    <span className="truncate flex-1">{project.name}</span>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => handleDeleteClick(e, project.id)}
                    data-delete
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  );

  if (mobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="left" className="w-80 p-0 flex flex-col">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          {sidebarContent}
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col hidden md:flex">
      {sidebarContent}
    </aside>
  );
}
