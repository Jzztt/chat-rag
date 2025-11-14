import { MainLayout } from '@/components/layout/MainLayout'
import { ChatPanel } from '@/components/chat/ChatPanel'

/**
 * App - Root component
 * Design Pattern: Container Component
 */
function App() {
  return (
    <MainLayout>
      <ChatPanel />
    </MainLayout>
  )
}

export default App
