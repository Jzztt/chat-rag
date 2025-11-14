import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAppStore } from '@/store/useAppStore';
import { FolderKanban, Plus } from 'lucide-react';

/**
 * LeftSidebar - Presentational component
 * Design Pattern: Presentational Component
 */
export function LeftSidebar() {
  const { projects, setCurrentProject, currentProject } = useAppStore();

  const handleNewProject = () => {
    // TODO: Open dialog to create new project
    console.log('New project clicked');
  };

  const handleProjectClick = (projectId: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      setCurrentProject(project);
    }
  };

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">POLY CHAT</h1>
      </div>

      {/* New Project Button */}
      <div className="p-4 border-b border-border">
        <Button className="w-full" onClick={handleNewProject}>
          <Plus className="mr-2 h-4 w-4" />
          New project
        </Button>
      </div>

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
                <button
                  key={project.id}
                  onClick={() => handleProjectClick(project.id)}
                  className={`w-full text-left px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${
                    currentProject?.id === project.id
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-accent/50 text-foreground'
                  }`}
                >
                  <FolderKanban className="h-4 w-4" />
                  <span className="truncate">{project.name}</span>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </aside>
  );
}
