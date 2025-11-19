import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { fileApi } from '@/services/api'

/**
 * Custom Hook for File Upload
 * Files can optionally be attached to the active conversation
 */
export function useFileUpload() {
  const [isUploading, setIsUploading] = useState(false)
  const { activeConversationId } = useAppStore()

  const handleFileUpload = async (files: File[], conversationId?: string): Promise<void> => {
    setIsUploading(true)
    try {
      // Validate file size (50MB max)
      const maxSize = 50 * 1024 * 1024
      const validFiles = files.filter(file => {
        if (file.size > maxSize) {
          console.warn(`File ${file.name} exceeds 50MB limit`)
          return false
        }
        return true
      })

      if (validFiles.length === 0) {
        throw new Error('No valid files to upload')
      }

      await fileApi.uploadFiles(
        validFiles, 
        conversationId || activeConversationId || undefined
      )
    } catch (error) {
      console.error('File upload failed:', error)
      throw error
    } finally {
      setIsUploading(false)
    }
  }

  return {
    handleFileUpload,
    isUploading,
  }
}

