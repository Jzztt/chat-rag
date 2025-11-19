import { ReactNode, useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { LeftSidebar } from './LeftSidebar'
import { Button } from '@/components/ui/button'
import { Menu } from 'lucide-react'

interface MainLayoutProps {
  children?: ReactNode
}

/**
 * MainLayout - Responsive container component for shared navigation layout
 */
export function MainLayout({ children }: MainLayoutProps) {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const location = useLocation()

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setLeftSidebarOpen(false)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const routeTitle = location.pathname === '/knowledge-base' ? 'Knowledge Base' : 'Chat'

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {isMobile && (
        <header className="fixed top-0 left-0 right-0 z-40 h-14 border-b border-border bg-card flex items-center justify-between px-4 md:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setLeftSidebarOpen(true)}
            className="md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <h1 className="text-lg font-bold text-foreground">{routeTitle}</h1>
          
          <span className="text-sm font-medium text-muted-foreground">Poly Chat</span>
        </header>
      )}

      {!isMobile && <LeftSidebar />}
      {isMobile && (
        <LeftSidebar 
          mobile 
          open={leftSidebarOpen} 
          onOpenChange={setLeftSidebarOpen} 
        />
      )}
      
      <div className={`flex-1 flex flex-col overflow-hidden ${isMobile ? 'mt-14' : ''}`}>
        {children}
      </div>
    </div>
  )
}
