import { ReactNode } from 'react'
import { LeftSidebar } from './LeftSidebar'
import { CenterPanel } from './CenterPanel'
import { RightSidebar } from './RightSidebar'

interface MainLayoutProps {
  children?: ReactNode
}

/**
 * MainLayout - Container component for 3-panel layout
 * Design Pattern: Container/Presentational
 */
export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Left Sidebar - Navigation */}
      <LeftSidebar />
      
      {/* Center Panel - Main Content */}
      <CenterPanel>{children}</CenterPanel>
      
      {/* Right Sidebar - Knowledge Base */}
      <RightSidebar />
    </div>
  )
}

