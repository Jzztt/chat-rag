import { ReactNode, useState, useEffect } from 'react'
import { LeftSidebar } from './LeftSidebar'
import { CenterPanel } from './CenterPanel'
import { RightSidebar } from './RightSidebar'
import { Button } from '@/components/ui/button'
import { Menu, X } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'

interface MainLayoutProps {
  children?: ReactNode
}

/**
 * MainLayout - Responsive container component for 3-panel layout
 * Design Pattern: Container/Presentational with Responsive Design
 */
export function MainLayout({ children }: MainLayoutProps) {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false)
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const { setSidebarOpen } = useAppStore()

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      // Auto-close sidebars on mobile when screen resizes
      if (window.innerWidth >= 768) {
        setLeftSidebarOpen(false)
        setRightSidebarOpen(false)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Update global sidebar state
  useEffect(() => {
    setSidebarOpen(leftSidebarOpen || rightSidebarOpen)
  }, [leftSidebarOpen, rightSidebarOpen, setSidebarOpen])

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Mobile Header with Menu Buttons */}
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
          
          <h1 className="text-lg font-bold text-foreground">POLY CHAT</h1>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setRightSidebarOpen(true)}
            className="md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </header>
      )}

      {/* Left Sidebar - Desktop always visible, Mobile as drawer */}
      {!isMobile && <LeftSidebar />}
      {isMobile && (
        <LeftSidebar 
          mobile 
          open={leftSidebarOpen} 
          onOpenChange={setLeftSidebarOpen} 
        />
      )}
      
      {/* Center Panel - Main Content */}
      <div className={`flex-1 flex flex-col overflow-hidden ${isMobile ? 'mt-14' : ''}`}>
        <CenterPanel 
          mobile={isMobile}
          onToggleRightSidebar={() => setRightSidebarOpen(!rightSidebarOpen)}
        >
          {children}
        </CenterPanel>
      </div>
      
      {/* Right Sidebar - Desktop always visible, Mobile as drawer */}
      {!isMobile && <RightSidebar />}
      {isMobile && (
        <RightSidebar 
          mobile 
          open={rightSidebarOpen} 
          onOpenChange={setRightSidebarOpen} 
        />
      )}
    </div>
  )
}
