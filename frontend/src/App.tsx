import { Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { CenterPanel } from '@/components/layout/CenterPanel'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { KnowledgeBasePage } from '@/pages/KnowledgeBasePage'

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route 
          path="/" 
          element={
            <CenterPanel>
              <ChatPanel />
            </CenterPanel>
          } 
        />
        <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MainLayout>
  )
}

export default App
