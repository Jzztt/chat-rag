import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { fileApi } from '@/services/api'
import type { Source } from '@/types'

/**
 * Custom Hook for File Upload
 * Design Pattern: Custom Hook Pattern
 */
export function useFileUpload() {
  const [isUploading, setIsUploading] = useState(false)
  const { addSource } = useAppStore()

  const handleFileUpload = async (files: File[]) => {
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
        console.error('No valid files to upload')
        return
      }

      // Upload files
      const response = await fileApi.uploadFiles(validFiles)
      
      // TODO: Fetch actual source data from API
      // For now, create mock sources
      validFiles.forEach((file, index) => {
        const mockSource: Source = {
          id: response.file_ids[index] || `file-${Date.now()}-${index}`,
          filename: file.name,
          filepath: file.name,
          file_type: file.type || 'application/pdf',
          file_size: file.size,
          indexed_at: new Date().toISOString(),
          chunk_count: 0,
        }
        addSource(mockSource)
      })
    } catch (error) {
      console.error('File upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  return {
    handleFileUpload,
    isUploading,
  }
}

