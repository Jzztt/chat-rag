import { NavLink } from 'react-router-dom';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { MessageSquare, Upload } from 'lucide-react';

interface LeftSidebarProps {
  mobile?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const navItems = [
  {
    label: 'Chat',
    to: '/',
    icon: MessageSquare,
    description: 'Talk with your assistant'
  },
  {
    label: 'Knowledge Base',
    to: '/knowledge-base',
    icon: Upload,
    description: 'Manage shared sources'
  }
];

function SidebarContent() {
  return (
    <>
      <div className="p-6 border-b border-border">
        <p className="text-xs font-semibold text-muted-foreground tracking-wide">GLOBAL WORKSPACE</p>
        <h1 className="text-xl font-bold text-foreground mt-1">POLY CHAT</h1>
      </div>
      <nav className="flex-1">
        <div className="px-4 py-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Navigation
          </p>
          <div className="space-y-2">
            {navItems.map(({ label, to, icon: Icon, description }) => (
              <NavLink
                key={label}
                to={to}
                className={({ isActive }) =>
                  `flex flex-col rounded-lg border px-3 py-2 transition-colors ${
                    isActive
                      ? 'border-primary bg-primary/10 text-primary-foreground'
                      : 'border-border hover:border-primary/40'
                  }`
                }
              >
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{label}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{description}</p>
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      <div className="p-4 border-t border-border text-xs text-muted-foreground">
        Shared conversations & files use one ChromaDB
      </div>
    </>
  );
}

export function LeftSidebar({ mobile = false, open, onOpenChange }: LeftSidebarProps) {
  if (mobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="left" className="w-72 p-0 flex flex-col">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <SidebarContent />
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col hidden md:flex">
      <SidebarContent />
    </aside>
  );
}
